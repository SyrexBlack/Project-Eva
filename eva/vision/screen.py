"""
Eva's Vision Module

Handles screen capture and visual understanding.
Eva can see what's on your screen.
"""

import os
import base64
from datetime import datetime
from typing import Optional, Tuple
import mss
import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Screenshot storage
SCREENSHOTS_PATH = "./data/screenshots"


class EvaVision:
    """
    Eva's eyes — captures and analyzes screen content.
    
    Uses MSS for fast screen capture.
    Images are saved locally and can be sent to vision models.
    """
    
    def __init__(self, save_path: str = SCREENSHOTS_PATH):
        """
        Initialize Eva's vision.
        
        Args:
            save_path: Where to save screenshots
        """
        self.save_path = save_path
        os.makedirs(save_path, exist_ok=True)
        
        # MSS instance for fast capture
        try:
            self.sct = mss.mss()
            self.monitor = self.sct.monitors[1]
            self._available = True
        except Exception as e:
            print(f"⚠️ Screen capture not available (no X-server): {e}")
            self.sct = None
            self.monitor = None
            self._available = False
    
    def capture_screen(self, filename: Optional[str] = None) -> str:
        """
        Capture the entire screen.
        
        Args:
            filename: Optional custom filename
        
        Returns:
            Path to saved screenshot
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_{timestamp}.png"
        
        filepath = os.path.join(self.save_path, filename)
        
        # Capture screen
        screenshot = self.sct.grab(self.monitor)
        
        # Save as PNG
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
        
        return filepath
    
    def capture_region(self, x: int, y: int, width: int, height: int, 
                      filename: Optional[str] = None) -> str:
        """
        Capture a specific region of the screen.
        
        Args:
            x, y: Top-left corner
            width, height: Region dimensions
            filename: Optional custom filename
        
        Returns:
            Path to saved screenshot
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"region_{timestamp}.png"
        
        filepath = os.path.join(self.save_path, filename)
        
        # Define region
        region = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        
        # Capture region
        screenshot = self.sct.grab(region)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
        
        return filepath
    
    def encode_image_base64(self, filepath: str) -> str:
        """
        Encode image as base64 for API transmission.
        
        Args:
            filepath: Path to image
        
        Returns:
            Base64 encoded image string
        """
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def get_screen_info(self) -> dict:
        """
        Get information about the screen.
        
        Returns:
            Dict with screen dimensions and monitors
        """
        return {
            "monitor": self.monitor,
            "num_monitors": len(self.sct.monitors) - 1,  # Exclude "all monitors"
            "monitors": self.sct.monitors
        }
    
    def detect_game_window(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect if a game window is active.
        
        This is a placeholder — in a real implementation,
        you'd use win32gui on Windows or similar on other platforms.
        
        Returns:
            (x, y, width, height) of game window, or None
        """
        # TODO: Implement platform-specific game window detection
        # On Windows: use win32gui
        # On Linux: use X11 or wmctrl
        
        # For now, return None
        return None
    
    def get_active_window_title(self) -> Optional[str]:
        """
        Get the title of the currently active window.
        
        Returns:
            Window title or None
        """
        # TODO: Implement platform-specific active window detection
        return None
    
    def close(self):
        """Clean up resources."""
        self.sct.close()


# Global instance
_vision: Optional[EvaVision] = None


def get_vision() -> EvaVision:
    """Get or create global vision instance."""
    global _vision
    if _vision is None:
        _vision = EvaVision()
    return _vision
