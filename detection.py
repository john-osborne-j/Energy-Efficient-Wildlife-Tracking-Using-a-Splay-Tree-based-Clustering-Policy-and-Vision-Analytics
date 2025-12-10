import cv2
import numpy as np
import torch
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import os

# ==========================================
# 1. SwinIR Restoration Module (Server-Side)
# ==========================================
class SwinIRRestorer:
    """
    Simulates the SwinIR restoration step. 
    In the paper, this recovers 640x640 images from 64x64/128x128 thumbnails.
    """
    def __init__(self, target_size=(640, 640)):
        self.target_size = target_size
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Restoration Module loaded on: {self.device}")
        
    def restore(self, low_res_image):
        # Simulating restoration for the demo:
        restored_img = cv2.resize(low_res_image, self.target_size, interpolation=cv2.INTER_CUBIC)
        
        # Optional: Apply slight sharpening to mimic SwinIR texture recovery
        kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
        restored_img = cv2.filter2D(restored_img, -1, kernel)
        
        return restored_img

# ==========================================
# 2. Wildlife Analytics Module (Server-Side)
# ==========================================
class WildlifeAnalytics:
    def __init__(self, confidence_threshold=0.4):
        # Load YOLOv8 Model
        print("Loading YOLOv8 Detector...")
        try:
             self.detector = YOLO('yolov8n.pt')
        except Exception as e:
             print(f"Failed to load YOLO model: {e}")
             self.detector = None
        

        # Load DeepSORT Tracker
        print("Loading DeepSORT Tracker...")
        # Reduced n_init to 1 to show boxes immediately for moving animals
        self.tracker = DeepSort(max_age=30, n_init=1, nms_max_overlap=1.0)
        
        # Paper specifies confidence > 0.4 
        self.conf_threshold = confidence_threshold

    def process_frame(self, frame):
        if self.detector is None:
             return []

        # 1. Detection
        results = self.detector(frame, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf > self.conf_threshold:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cls = int(box.cls[0])
                class_name = self.detector.names[cls]
                
                # Filter for animals if possible, but for demo we take all
                w, h = x2 - x1, y2 - y1
                detections.append(([x1, y1, w, h], conf, class_name))

        # 2. Tracking
        tracks = self.tracker.update_tracks(detections, frame=frame)
        
        return tracks

class VideoProcessor:
    def __init__(self):
        self.restorer = SwinIRRestorer(target_size=(640, 640))
        self.analytics = WildlifeAnalytics(confidence_threshold=0.4)
        self.current_video_path = None
        self.cap = None

    def set_source(self, video_path):
        self.current_video_path = video_path
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(video_path)

    def generate_frames(self):
        if not self.cap or not self.cap.isOpened():
            return

        while True:
            ret, full_res_frame = self.cap.read()
            if not ret:
                # Loop video for demo purposes
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # --- STEP 1: Simulate Node Capture (Edge) ---
            node_thumbnail = cv2.resize(full_res_frame, (128, 128))

            # --- STEP 2: Restore Image (Server) ---
            restored_frame = self.restorer.restore(node_thumbnail)

            # --- STEP 3: Detect & Track (Server) ---
            tracks = self.analytics.process_frame(restored_frame)

            # --- STEP 4: Visualization ---
            for track in tracks:
                if not track.is_confirmed() and track.time_since_update > 1:
                    continue
                
                track_id = track.track_id
                ltrb = track.to_ltrb()
                class_name = track.det_class if track.det_class else "Object"

                # Draw Bounding Box - Cyan for high visibility
                # Using a dynamic thickness based on confidence or just thick enough
                cv2.rectangle(restored_frame, (int(ltrb[0]), int(ltrb[1])), 
                              (int(ltrb[2]), int(ltrb[3])), (255, 255, 0), 3)
                
                # Label with background for readability
                label = f"ID:{track_id} {class_name}"
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                cv2.rectangle(restored_frame, (int(ltrb[0]), int(ltrb[1]) - 20), (int(ltrb[0]) + w, int(ltrb[1])), (255, 255, 0), -1)
                
                cv2.putText(restored_frame, label, (int(ltrb[0]), int(ltrb[1])-5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            # Combined View for the web feed
            # Resize thumbnail to match height/scale for side-by-side
            viz_thumbnail = cv2.resize(node_thumbnail, (640, 640), interpolation=cv2.INTER_NEAREST)
            
            # Create a nice layout: Left (Low Res Mockup), Right (High Res Result)
            # Add labels
            cv2.putText(viz_thumbnail, "EDGE NODE (128px)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(restored_frame, "SERVER (Restored + AI)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            combined_view = np.hstack((viz_thumbnail, restored_frame))
            
            # Scale down slightly for web performance if needed
            combined_view = cv2.resize(combined_view, (1000, 500))

            # Encode JPEG
            ret, buffer = cv2.imencode('.jpg', combined_view)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
