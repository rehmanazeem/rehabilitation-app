# =============================================================================
# hand_detector.py - Hand Detection and Angle Calculation using MediaPipe
# =============================================================================
import cv2
import mediapipe as mp
import numpy as np

from services.hand_math import flexion_reading, open_close_reading

# =============================================================================
# HandDetector Class
# =============================================================================
class HandDetector:
    """Wraps MediaPipe Hands to track a single hand and derive biofeedback
    metrics (index-finger flexion angle, hand open/close percentage) from
    21 hand landmarks, drawing the skeleton onto each processed frame."""

    def __init__(self) -> None:
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

        self.last_valid_value = 0
        self.last_valid_status = "Waiting for hand..."

    def process_frame(self, frame: np.ndarray, exercise_type: str = "flexion") -> tuple[np.ndarray, str, int]:
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
                    value, status_text = flexion_reading(lms)

                elif exercise_type == "open_close":
                    value, status_text = open_close_reading(lms)

                # Update our "Last Known Good" state
                self.last_valid_value = value
                self.last_valid_status = status_text

        return frame, status_text, value

    def reset_state(self) -> None:
        """Clears the history to prevent data bleeding between exercises."""
        self.last_valid_value = 0
        self.last_valid_status = "Initializing..."
        print("[DEBUG] Detector state reset.")
