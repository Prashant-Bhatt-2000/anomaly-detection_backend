import os
import time
import base64
import cv2
from celery import Celery, states
from celery.utils.log import get_task_logger
from .settings import settings
from .inference import analyze  # this should perform defect detection and return image

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
    Returns the result as a dict including Base64 image and metadata.
    """
    self.update_state(state=states.STARTED, meta={"stage": "loading"})
    try:
        t0 = time.time()

        processed_img = analyze(file_path) 

        # Encode image to Base64 for frontend
        success, buffer = cv2.imencode(".jpg", processed_img)
        if not success:
            raise ValueError("Failed to encode processed image")

        img_base64 = base64.b64encode(buffer).decode("utf-8")

        # Prepare result
        result = {
            "image_base64": img_base64,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "file_path": file_path
        }

        return result

    except Exception as e:
        logger.exception("Processing failed")
        raise e
