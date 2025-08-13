import cv2
import numpy as np
from pathlib import Path
import base64


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}


import cv2
import numpy as np
from pathlib import Path
import base64


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def analyze_image(path: Path) -> dict:
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "error": "Unable to read image"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- Blur detection ---
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Adjusted threshold for blurry detection
    blurry = fm < 50.0  

    # --- Edge detection ---
    edges = cv2.Canny(gray, 100, 200)
    edge_density_norm = float(edges.mean()) / 255.0

    # --- Red dominance detection ---
    b, g, r = cv2.split(img)
    red_ratio = float(np.mean((r > 150) & (g < 120) & (b < 120)))

    defect_score = 0
    defect_score += 0.6 if blurry else 0.0
    defect_score += min(edge_density_norm / 0.33, 0.3) 
    defect_score += min(red_ratio / 0.3, 0.4)  
    defect_score = min(defect_score, 1.0) 

    # --- Determine defect presence ---
    has_defect = blurry or (red_ratio > 0.12) or (edge_density_norm > 0.15) or defect_score >= 0.45

    # --- Draw defects on image ---
    result_img = img.copy()
    if blurry:
        cv2.putText(result_img, "Blurry!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    if red_ratio > 0.12:
        cv2.putText(result_img, "Red anomaly!", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    if edge_density_norm > 0.15:
        result_img[edges > 0] = [255, 0, 0]

    # --- Encode to Base64 ---
    _, buffer = cv2.imencode(".jpg", result_img)
    img_base64 = base64.b64encode(buffer).decode("utf-8")

    return {
        "ok": True,
        "type": "image",
        "metrics": {
            "laplacian_var": float(fm),
            "edge_density": float(edge_density_norm),
            "red_ratio": float(red_ratio),
            "defect_score": float(defect_score),
        },
        "defect_detected": bool(has_defect),
        "image_base64": img_base64,
        "processed_image": result_img
    }



def analyze_video(path: Path, frame_stride: int = 15, max_frames: int = 300) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"ok": False, "error": "Unable to open video"}

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    checked = 0
    defect_frames = 0
    fm_vals, edge_vals, red_vals = [], [], []

    idx = 0
    while True:
        ret = cap.grab()
        if not ret:
            break
        if idx % frame_stride == 0:
            ret, frame = cap.retrieve()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fm = cv2.Laplacian(gray, cv2.CV_64F).var()
            edges = cv2.Canny(gray, 100, 200)
            edge_density = float(edges.mean()) / 255.0
            b, g, r = cv2.split(frame)
            red_ratio = float(np.mean((r > 150) & (g < 120) & (b < 120)))

            defect_score = (1.0 if fm < 80.0 else 0.0) * 0.6 + edge_density * 0.3 + red_ratio * 0.4
            is_defect = (defect_score >= 0.45) or (fm < 80.0) or (red_ratio > 0.12)
            if is_defect:
                defect_frames += 1

            fm_vals.append(float(fm))
            edge_vals.append(float(edge_density))
            red_vals.append(float(red_ratio))
            checked += 1

            if checked >= max_frames:
                break
        idx += 1

    cap.release()

    defect_ratio = (defect_frames / checked) if checked else 0.0

    return {
        "ok": True,
        "type": "video",
        "meta": {"frames_sampled": checked, "fps": float(fps), "approx_total_frames": total},
        "metrics": {
            "mean_laplacian_var": float(np.mean(fm_vals) if fm_vals else 0.0),
            "mean_edge_density": float(np.mean(edge_vals) if edge_vals else 0.0),
            "mean_red_ratio": float(np.mean(red_vals) if red_vals else 0.0),
            "defect_ratio": float(defect_ratio),
        },
        "defect_detected": bool(defect_ratio > 0.2),
    }


def analyze(path_str: str) -> dict:
    path = Path(path_str)
    if _is_image(path):
        return analyze_image(path)
    if _is_video(path):
        return analyze_video(path)
    return {"ok": False, "error": f"Unsupported file type: {path.suffix}"}