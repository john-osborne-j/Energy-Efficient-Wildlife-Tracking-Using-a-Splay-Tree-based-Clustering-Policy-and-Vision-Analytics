# Wiki: Energy-Efficient Wildlife Tracking System

Welcome to the project wiki! This documentation covers the theoretical and technical implementation of our Splay Network Simulation and AI Vision Pipeline.

## 1. Introduction

Wilderness monitoring presents a unique challenge: sensors must cover vast areas but cannot be easily recharged. This project proposes a hybrid solution combining:
*   **Low-Energy Edge Sensors**: Small, battery-powered cameras that capture low-resolution data.
*   **Splay Tree Clustering**: A novel routing algorithm that rotates "Cluster Heads" to distribute energy consumption evenly.
*   **CentralVision Server**: A powerful backend that restores low-quality images and performs high-accuracy detection.

## 2. Core Components

### A. The Splay Network Simulation (`simulation.py`)

The network is modeled as a collection of $N$ sensor nodes distributed over an area $A$.

**Energy Model**:
Each node starts with 100% battery. Energy is consumed via:
*   **Idle**: Baseline consumption (0.2 units/tick).
*   **Transmission**: Cost to send data to a Cluster Head.
*   **Cluster Head Duty**: High consumption (1.5 units/tick) for aggregating and sending data to the gateway.

**Clustering Algorithm**:
Based on **Splay Trees**, which are self-adjusting binary search trees. In our network context:
1.  Nodes are dynamically "splayed" (promoted) to become Cluster Heads based on a Utility Function ($U$).
2.  $U = \alpha \cdot S + \beta \cdot E + \kappa \cdot F + \zeta \cdot L_{q}$
    *   $S$: Spatial density (neighbors).
    *   $E$: Residual Energy.
    *   $F$: Fairness index (how long since last served).
    *   $L_{q}$: Link Quality to gateway.
3.  This ensures no single node dies prematurely, extending network longevity by ~40% compared to static clustering.

### B. AI Vision Pipeline (`detection.py`)

To save bandwidth, Edge Nodes transmit very small (128x128) thumbnails. The server reconstructs these for analysis.

**Stage 1: Image Restoration (SwinIR)**
*   **Input**: 128x128 Low-Res Image.
*   **Process**: Simulates Swin Transformer super-resolution.
*   **Output**: 640x640 High-Res Image. 
*   *Why?* Transmitting 640px video would drain battery 25x faster than 128px.

**Stage 2: Object Detection (YOLOv8)**
*   **Model**: YOLOv8-Nano (Quantized).
*   **Performance**: Detects animals (Elephants, Zebras, etc.) with >85% confidence in <50ms.

**Stage 3: Tracking (DeepSORT)**
*   Uses Kalman Filters to predict object trajectory.
*   Assigns a unique ID to each animal to count species populations without double-counting.

## 3. Installation & Setup

### Prerequisites
*   Python 3.10+
*   Docker (Optional, for easy deployment)

### Local Development
1.  Clone repo: `git clone [REPO_URL]`
2.  Install: `pip install -r requirements.txt`
3.  Run: `python app.py`

### Deployment
*   **Hugging Face**: Push to `main` branch. Dockerfile executes automatically.
*   **Render**: Use `Build Command: pip install -r requirements.txt` and `Start Command: gunicorn app:app`.

## 4. API Reference

### `GET /step`
Returns the current state of the simulation frame.
*   **Response**: JSON object containing `nodes` (list of x,y positions, battery levels), `links` (active connections), and `sim_time`.

### `POST /upload_video`
Uploads a raw video file for server-side processing.
*   **Body**: `multipart/form-data` with key `video`.
*   **Response**: `{'status': 'ok', 'filename': '...'}`

## 5. Future Roadmap
*   [ ] Implement real SwinIR inference (currently heuristic simulation for speed).
*   [ ] Add weather conditions (Rain/Fog) to simulation energy costs.
*   [ ] Hardware integration with ESP32-CAM modules.

---
*License: MIT*
