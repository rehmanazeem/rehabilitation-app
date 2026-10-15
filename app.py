import os
import signal
import cv2
from flask import Flask, render_template, Response, request, jsonify
from services.hand_detector import HandDetector

# =============================================================================
# Global Configuration & Initialization
# =============================================================================
os.environ['TK_SILENCE_DEPRECATION'] = '1'

app = Flask(__name__)
detector = HandDetector()
camera = cv2.VideoCapture(0)

# Initialize with a type tag
latest_stats = {"status": "No hand detected", "value": 0, "type": "none"}

# =============================================================================
# Flask Routes
# =============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/get_stats')
def get_stats():
    """Endpoint for the frontend JS to fetch live hand data."""
    return jsonify(latest_stats)

@app.route('/video_feed')
def video_feed():
    """Stream the annotated webcam feed as MJPEG for the selected exercise.

    Reads the ``exercise`` query parameter ("flexion" or "open_close"),
    resets detector state, and continuously yields processed JPEG frames
    while publishing the latest metric to ``latest_stats``.
    """
    exercise_type = request.args.get('exercise', 'flexion')
    detector.reset_state()
    
    global latest_stats
    latest_stats = {"status": "Switching...", "value": 0, "type": exercise_type}

    def generate():
        global latest_stats
        while True:
            success, frame = camera.read()
            if not success: break
            
            processed_frame, status, val = detector.process_frame(frame, exercise_type)
            
            # Tag the data so the frontend knows which exercise this belongs to
            latest_stats = {
                "status": status, 
                "value": val, 
                "type": exercise_type
            }
            
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# =============================================================================
# Lifecycle Management
# =============================================================================

def signal_handler(sig, frame):
    """Release the camera and exit cleanly on SIGINT (Ctrl+C)."""
    print('\n[SYSTEM] Shutting down gracefully...')
    if camera.isOpened():
        camera.release()
    cv2.destroyAllWindows()
    print('[SYSTEM] Camera released. Cleanup complete.')
    os._exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # Port 8000 matches your terminal output
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True, use_reloader=False)