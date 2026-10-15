# =============================================================================
# hand_detector.py - Hand Detection and Angle Calculation using MediaPipe
# =============================================================================
import math
import cv2
import mediapipe as mp
import numpy as np

# =============================================================================
# HandDetector Class
# =============================================================================
class HandDetector:
    """Wraps MediaPipe Hands to track a single hand and derive biofeedback
    metrics (index-finger flexion angle, hand open/close percentage) from
    21 hand landmarks, drawing the skeleton onto each processed frame."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

        self.last_valid_value = 0
        self.last_valid_status = "Waiting for hand..."

    def get_distance(self, p1, p2):
        """Return the 2D Euclidean distance between two normalized landmarks."""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def process_frame(self, frame, exercise_type="flexion"):
        """Detect the hand in a BGR frame and compute the exercise metric.

        Draws the hand skeleton on ``frame`` and returns a tuple of
        ``(annotated_frame, status_text, value)`` for the given
        ``exercise_type`` ("flexion" -> joint angle in degrees,
        "open_close" -> openness percentage). The last valid reading is
        reused when no hand is detected to keep the UI stable.
        """
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        
        # Start with the last known good values to prevent "juggling" to 0
        status_text = self.last_valid_status
        value = self.last_valid_value

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_lms, self.mp_hands.HAND_CONNECTIONS)
                lms = hand_lms.landmark

                if exercise_type == "flexion":
                    angle = self._calculate_angle(lms[5], lms[6], lms[7])
                    value = int(angle)
                    status_text = f"Flexion: {value}°"
                
                elif exercise_type == "open_close":
                    dist = self.get_distance(lms[4], lms[20])
                    value = int(np.interp(dist, [0.05, 0.4], [0, 100]))
                    is_closed = value < 65
                    status_text = f"Hand: {'Open' if not is_closed else 'Closed'} ({value}%)"

                # Update our "Last Known Good" state
                self.last_valid_value = value
                self.last_valid_status = status_text

        return frame, status_text, value

    def reset_state(self):
        """Clears the history to prevent data bleeding between exercises."""
        self.last_valid_value = 0
        self.last_valid_status = "Initializing..."
        print("[DEBUG] Detector state reset.")
    
    def _calculate_angle(self, a, b, c):
        """Return the interior angle (degrees, 0-180) at vertex ``b``."""
        ang = math.degrees(math.atan2(c.y-b.y, c.x-b.x) - math.atan2(a.y-b.y, a.x-b.x))
        ang = abs(ang)
        if ang > 180: ang = 360 - ang
        return ang
    