"""
Face detector for headcount.
This module uses Haar Cascade classifier to detect and count faces/heads in images.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import os


class HeadcountDetector:
    """
    Uses Haar Cascade classifier to detect and count heads/faces in images.
    """

    def __init__(self):
        """
        Initialize the Haar Cascade face detector.
        """
        # Load the Haar Cascade classifier for frontal faces
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        print(f"[DEBUG] Haar Cascade XML file path: {cascade_path}")
        
        # Verify cascade file exists
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(
                f"Haar Cascade XML file not found at: {cascade_path}\n"
                f"Please ensure OpenCV is properly installed."
            )
        
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Verify cascade loaded successfully
        if self.face_cascade.empty():
            raise ValueError(
                f"Failed to load Haar Cascade classifier from: {cascade_path}\n"
                f"The XML file may be corrupted or invalid."
            )

    def detect_people(self, image: np.ndarray) -> Tuple[int, list]:
        """
        Detect faces/heads in an image using Haar Cascade.

        Args:
            image: Input image as numpy array (BGR format from OpenCV)

        Returns:
            Tuple of (count, detections)
        
        Raises:
            ValueError: If image is invalid or cannot be processed
        """
        # Validate input image
        if image is None:
            raise ValueError("Input image is None")
        
        if not isinstance(image, np.ndarray):
            raise ValueError(f"Input must be a numpy array, got {type(image)}")
        
        if image.size == 0:
            raise ValueError("Input image is empty")
        
        if len(image.shape) < 2:
            raise ValueError(f"Invalid image shape: {image.shape}")
        
        # Convert to grayscale for face detection
        # Handle different image formats safely
        if len(image.shape) == 2:
            # Image is already grayscale
            gray_image = image
        elif len(image.shape) == 3:
            if image.shape[2] == 1:
                # Single channel (already grayscale)
                gray_image = image[:, :, 0]
            elif image.shape[2] == 3:
                # BGR format (standard OpenCV)
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif image.shape[2] == 4:
                # BGRA format, convert to BGR first
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                raise ValueError(f"Unsupported number of channels: {image.shape[2]}")
        else:
            raise ValueError(f"Unsupported image dimensions: {image.shape}")
        
        # Verify grayscale conversion succeeded
        if gray_image is None or gray_image.size == 0:
            raise ValueError("Failed to convert image to grayscale")
        
        # Detect faces in the image
        # detectMultiScale returns a tuple of arrays, or empty tuple if no faces found
        faces = self.face_cascade.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=10,
            minSize=(50, 50)
        )

        # Handle empty detections (detectMultiScale returns empty tuple or empty array)
        if len(faces) == 0:
            return 0, []

        # Store detections
        detections = []
        for (x, y, w, h) in faces:
            detections.append({
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h)
            })

        return len(detections), detections

    def count_people(self,
                     image_path: Optional[str] = None,
                     image_array: Optional[np.ndarray] = None) -> int:
        """
        Count people in an image.
        """

        if image_path:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")

        elif image_array is not None:
            image = image_array

        else:
            raise ValueError("Either image_path or image_array must be provided")

        count, _ = self.detect_people(image)
        return count


# Global instance
# Initialize with error handling
try:
    headcount_detector = HeadcountDetector()
except (FileNotFoundError, ValueError) as e:
    import sys
    print(f"ERROR: Failed to initialize HeadcountDetector: {e}", file=sys.stderr)
    print("The AI headcount feature will not be available.", file=sys.stderr)
    # Create a dummy detector that will raise errors when used
    headcount_detector = None
