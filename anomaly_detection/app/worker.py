import os
import time
import base64
import cv2
import numpy as np
from PIL import Image
from celery import Celery, states
from celery.utils.log import get_task_logger
from .settings import settings
from .inference import analyze  # should perform defect detection and return dict with 'processed_image'

logger = get_task_logger(__name__)

# Initialize Celery
celery_app = Celery(
    "defect_worker",
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND,
)
celery_app.conf.task_track_started = True
celery_app.conf.worker_prefetch_multiplier = 2
celery_app.conf.result_expires = 3600 * 6

@celery_app.task(bind=True)
def process_media(self, file_path: str):
    """
    Celery task to process an image for defect detection.
    Returns a dict including Base64 image, metrics, and metadata.
    """
    self.update_state(state=states.STARTED, meta={"stage": "loading"})
    
    try:
        t0 = time.time()

        # Run defect detection
        processed_data = analyze(file_path)

        # Extract image and metrics
        processed_img = processed_data.get("processed_image")
        metrics = processed_data.get("metrics", {})

        # Validate processed image
        if processed_img is None:
            raise ValueError(f"No processed image returned for {file_path}")

        # Convert PIL Image to NumPy array if needed
        if isinstance(processed_img, Image.Image):
            processed_img = np.array(processed_img)

        # Ensure it's a NumPy array
        if not isinstance(processed_img, np.ndarray):
            raise TypeError(f"Processed image is not a NumPy array: {type(processed_img)}")

        # Encode image to Base64
        success, buffer = cv2.imencode(".jpg", processed_img)
        if not success:
            raise ValueError("Failed to encode processed image")

        img_base64 = base64.b64encode(buffer).decode("utf-8")

        # Prepare and return result
        result = {
            "image_base64": img_base64,
            "metrics": metrics,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "file_path": file_path
        }

        return result

    except Exception as e:
        logger.exception(f"Processing failed for {file_path}")
        raise e
