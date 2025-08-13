# Defect Detection Web App

> ⚠️ **Note:** This is just a showcase model for defect detection.  
> The frontend is basic and not fully polished. Use it to understand the workflow and demo defect detection.

A full-stack web application to detect defects in images (blurry, scratches, rust/color anomalies) using **OpenCV**, **FastAPI**, **Celery**, and **ReactJS**. Users can upload multiple images, and the system will analyze them for defects, returning **metrics**, **defect scores**, and optionally **highlighted images**.

---

## Features

- Upload multiple images at once via ReactJS frontend.
- Asynchronous processing with **Celery**.
- Detects defects based on:
  - **Blurriness** (Laplacian variance)
  - **Scratches or cracks** (edge density)
  - **Color anomalies / rust** (red dominance)
- Returns:
  - **Elapsed processing time**
  - **Defect score**
  - **Defective / OK status**
- Simple responsive card layout using Tailwind CSS.

---

## Tech Stack

- **Frontend:** ReactJS, Tailwind CSS
- **Backend:** FastAPI, Uvicorn
- **Task Queue:** Celery
- **Worker:** OpenCV for image analysis
- **Message Broker:** Redis (for Celery)
- **Python Libraries:** `opencv-python`, `numpy`, `fastapi`, `celery`

---

## Installation & Run

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/defect-detection.git
cd defect-detection
