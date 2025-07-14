#!/usr/bin/env python3
"""
GachaMCP - Python Game Automation MCP Server

MCP Server với 1 tool OCR chung để phân tích bất kỳ màn hình game nào.
"""

import asyncio
import os
import time
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
import re
import json

# MCP imports
from mcp.server.fastmcp import FastMCP

# Game automation imports
import pyautogui
import pygetwindow as gw
from PIL import Image as PILImage
import mss
import numpy as np
import cv2
import pytesseract
import easyocr

# Disable pyautogui failsafe for automation
pyautogui.FAILSAFE = False

# Create MCP server
mcp = FastMCP("GachaMCP")

# Global state
current_game_window: Optional[gw.Window] = None

# Tạo thư mục screenshots nếu chưa có
SCREENSHOTS_DIR = "screenshots"
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# Initialize EasyOCR reader (supports multiple languages)
ocr_reader = easyocr.Reader(['en', 'ja', 'ko'])  # English, Japanese, Korean for gacha games

def _capture_game_window() -> Tuple[bool, Union[np.ndarray, str]]:
    """
    Internal function để chụp cửa sổ game và trả về numpy array.
    """
    global current_game_window
    
    if not current_game_window:
        return False, "Chưa chọn cửa sổ game. Hãy dùng find_game_window() trước."
    
    try:
        # Refresh window info
        current_game_window = gw.getWindowsWithTitle(current_game_window.title)[0]
        
        # Focus cửa sổ để đảm bảo nó ở foreground
        current_game_window.activate()
        time.sleep(0.3)  # Đợi cửa sổ focus
        
        # Lấy tọa độ cửa sổ
        left = current_game_window.left
        top = current_game_window.top
        width = current_game_window.width
        height = current_game_window.height
        
        # Chụp màn hình chỉ cửa sổ game bằng mss
        with mss.mss() as sct:
            monitor = {
                "top": top,
                "left": left,
                "width": width,
                "height": height
            }
            
            # Chụp màn hình
            screenshot = sct.grab(monitor)
            
            # Convert sang numpy array cho OpenCV
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            
            return True, img_bgr
            
    except Exception as e:
        return False, f"Lỗi khi chụp màn hình: {str(e)}"

# ===== MCP TOOLS =====

@mcp.tool()
def find_game_window(window_title: str) -> Dict[str, Any]:
    """
    Tìm cửa sổ game theo tên.
    
    Args:
        window_title: Tên cửa sổ game (có thể là một phần của tên)
    
    Returns:
        Thông tin cửa sổ game tìm được
    """
    global current_game_window
    
    try:
        # Tìm tất cả cửa sổ
        windows = gw.getAllWindows()
        
        # Tìm cửa sổ có tên chứa window_title
        matching_windows = []
        for window in windows:
            if window_title.lower() in window.title.lower() and window.visible:
                matching_windows.append({
                    "title": window.title,
                    "x": window.left,
                    "y": window.top,
                    "width": window.width,
                    "height": window.height,
                    "is_active": window.isActive
                })
        
        if not matching_windows:
            return {
                "success": False,
                "error": f"Không tìm thấy cửa sổ game với tên '{window_title}'",
                "available_windows": [w.title for w in windows if w.visible and w.title.strip()]
            }
        
        # Chọn cửa sổ đầu tiên tìm được
        selected_window = matching_windows[0]
        
        # Lưu reference đến cửa sổ game
        for window in windows:
            if window.title == selected_window["title"]:
                current_game_window = window
                break
        
        return {
            "success": True,
            "window": selected_window,
            "total_found": len(matching_windows),
            "all_matches": matching_windows
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi tìm cửa sổ: {str(e)}"
        }

@mcp.tool()
def read_screen_text() -> Dict[str, Any]:
    """
    Tool OCR chung để đọc tất cả text trên màn hình game hiện tại.
    Hoạt động với bất kỳ game nào - không cụ thể cho game nào cả.
    
    Returns:
        Tất cả text tìm được với tọa độ và thông tin chi tiết
    """
    # Chụp màn hình
    success, img_or_error = _capture_game_window()
    if not success:
        return {
            "success": False,
            "error": img_or_error
        }
    
    img = img_or_error
    
    try:
        # Lưu ảnh để debug (optional)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_ocr_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        cv2.imwrite(filepath, img)
        
        # OCR để đọc tất cả text
        ocr_results = ocr_reader.readtext(img)
        
        # Xử lý kết quả OCR
        text_elements = []
        for (bbox, text, confidence) in ocr_results:
            if confidence > 0.4:  # Threshold thấp để capture nhiều text
                center_x = int(sum([point[0] for point in bbox]) / 4)
                center_y = int(sum([point[1] for point in bbox]) / 4)
                
                # Phân loại text dựa vào pattern chung
                text_type = "text"
                if re.search(r'^\d+[,\d]*$', text.replace(',', '').replace('.', '')):
                    text_type = "number"
                elif re.search(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]', text):
                    text_type = "symbol"
                elif len(text) <= 3 and text.isupper():
                    text_type = "short_label"
                elif any(word in text.lower() for word in ["button", "click", "tap", "press"]):
                    text_type = "button_text"
                
                text_elements.append({
                    "text": text,
                    "type": text_type,
                    "confidence": confidence,
                    "position": [center_x, center_y],
                    "bbox": {
                        "x": min([point[0] for point in bbox]),
                        "y": min([point[1] for point in bbox]),
                        "width": max([point[0] for point in bbox]) - min([point[0] for point in bbox]),
                        "height": max([point[1] for point in bbox]) - min([point[1] for point in bbox])
                    },
                    "clickable": True  # Tất cả text đều có thể click được
                })
        
        # Sắp xếp theo confidence
        text_elements.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Tạo summary
        summary = {
            "total_text_found": len(text_elements),
            "numbers_found": len([t for t in text_elements if t["type"] == "number"]),
            "buttons_found": len([t for t in text_elements if t["type"] == "button_text"]),
            "all_text": " ".join([t["text"] for t in text_elements[:20]])  # First 20 texts
        }
        
        return {
            "success": True,
            "text_elements": text_elements,
            "summary": summary,
            "timestamp": time.time(),
            "screenshot_saved": os.path.abspath(filepath)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi đọc text từ màn hình: {str(e)}"
        }

@mcp.tool()
def click_at_position(x: int, y: int, description: str = "") -> Dict[str, Any]:
    """
    Click tại tọa độ cụ thể trên cửa sổ game.

    Args:
        x: Tọa độ X (relative to game window)
        y: Tọa độ Y (relative to game window)
        description: Mô tả về vị trí click

    Returns:
        Kết quả click
    """
    global current_game_window

    if not current_game_window:
        return {
            "success": False,
            "error": "Chưa chọn cửa sổ game. Hãy dùng find_game_window() trước."
        }

    try:
        # Refresh window info
        current_game_window = gw.getWindowsWithTitle(current_game_window.title)[0]

        # Tính tọa độ tuyệt đối
        absolute_x = current_game_window.left + x
        absolute_y = current_game_window.top + y

        # Focus cửa sổ trước khi click
        current_game_window.activate()
        time.sleep(0.2)

        # Thực hiện click
        pyautogui.click(absolute_x, absolute_y)

        return {
            "success": True,
            "click_info": {
                "relative_position": {"x": x, "y": y},
                "absolute_position": {"x": absolute_x, "y": absolute_y},
                "description": description,
                "window_title": current_game_window.title
            },
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi click: {str(e)}"
        }

@mcp.tool()
def wait_and_read(delay: float = 2.0) -> Dict[str, Any]:
    """
    Đợi một khoảng thời gian rồi đọc lại text trên màn hình.

    Args:
        delay: Thời gian đợi (giây)

    Returns:
        Text mới sau khi đợi
    """
    try:
        # Đợi
        time.sleep(delay)

        # Đọc lại text
        result = read_screen_text()

        if result["success"]:
            result["delay_applied"] = delay
            result["message"] = f"Đã đợi {delay} giây và đọc lại màn hình"

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi trong wait_and_read: {str(e)}"
        }

if __name__ == "__main__":
    mcp.run()
