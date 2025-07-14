#!/usr/bin/env python3
"""
GachaMCP - Python Game Automation MCP Server

MCP Server giúp AI tương tác với Gacha Game thông qua screenshot và click automation.
"""

import asyncio
import base64
import io
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# MCP imports
from mcp.server.fastmcp import FastMCP, Image

# Game automation imports
import pyautogui
import pygetwindow as gw
from PIL import Image as PILImage
import mss
import numpy as np

# Disable pyautogui failsafe for automation
pyautogui.FAILSAFE = False

# Create MCP server
mcp = FastMCP("GachaMCP")

# Global state to track current game window
current_game_window: Optional[gw.Window] = None
last_screenshot: Optional[str] = None

@dataclass
class WindowInfo:
    """Thông tin cửa sổ game"""
    title: str
    x: int
    y: int
    width: int
    height: int
    is_active: bool
    process_name: str = ""

@dataclass
class ClickResult:
    """Kết quả click"""
    success: bool
    x: int
    y: int
    description: str
    error: Optional[str] = None

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
def get_window_info() -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết về cửa sổ game hiện tại.
    
    Returns:
        Thông tin chi tiết về cửa sổ game
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
        
        return {
            "success": True,
            "window": {
                "title": current_game_window.title,
                "x": current_game_window.left,
                "y": current_game_window.top,
                "width": current_game_window.width,
                "height": current_game_window.height,
                "is_active": current_game_window.isActive,
                "is_maximized": current_game_window.isMaximized,
                "is_minimized": current_game_window.isMinimized,
                "center_x": current_game_window.left + current_game_window.width // 2,
                "center_y": current_game_window.top + current_game_window.height // 2
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi lấy thông tin cửa sổ: {str(e)}"
        }

@mcp.tool()
def focus_game_window() -> Dict[str, Any]:
    """
    Focus vào cửa sổ game để đảm bảo nó ở foreground.
    
    Returns:
        Kết quả focus cửa sổ
    """
    global current_game_window
    
    if not current_game_window:
        return {
            "success": False,
            "error": "Chưa chọn cửa sổ game. Hãy dùng find_game_window() trước."
        }
    
    try:
        # Activate và bring to front
        current_game_window.activate()
        time.sleep(0.5)  # Đợi cửa sổ focus
        
        return {
            "success": True,
            "message": f"Đã focus vào cửa sổ '{current_game_window.title}'"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi focus cửa sổ: {str(e)}"
        }

@mcp.tool()
def capture_game_screen() -> Dict[str, Any]:
    """
    Chụp màn hình cửa sổ game hiện tại.

    Returns:
        Screenshot dưới dạng base64 và thông tin hình ảnh
    """
    global current_game_window, last_screenshot

    if not current_game_window:
        return {
            "success": False,
            "error": "Chưa chọn cửa sổ game. Hãy dùng find_game_window() trước."
        }

    try:
        # Refresh window info
        current_game_window = gw.getWindowsWithTitle(current_game_window.title)[0]

        # Lấy tọa độ cửa sổ
        left = current_game_window.left
        top = current_game_window.top
        width = current_game_window.width
        height = current_game_window.height

        # Chụp màn hình bằng mss (nhanh hơn)
        with mss.mss() as sct:
            # Định nghĩa vùng chụp
            monitor = {
                "top": top,
                "left": left,
                "width": width,
                "height": height
            }

            # Chụp màn hình
            screenshot = sct.grab(monitor)

            # Convert sang PIL Image
            img = PILImage.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # Convert sang base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            # Lưu screenshot cuối cùng
            last_screenshot = img_base64

            return {
                "success": True,
                "screenshot": img_base64,
                "window_info": {
                    "title": current_game_window.title,
                    "x": left,
                    "y": top,
                    "width": width,
                    "height": height
                },
                "image_info": {
                    "format": "PNG",
                    "size": len(img_base64),
                    "dimensions": f"{width}x{height}"
                },
                "timestamp": time.time()
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi chụp màn hình: {str(e)}"
        }

@mcp.tool()
def click_at_position(x: int, y: int, description: str = "", click_type: str = "left") -> Dict[str, Any]:
    """
    Click tại tọa độ cụ thể trên cửa sổ game.

    Args:
        x: Tọa độ X (relative to game window)
        y: Tọa độ Y (relative to game window)
        description: Mô tả về vị trí click (ví dụ: "Gacha button", "Menu icon")
        click_type: Loại click ("left", "right", "double")

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

        # Kiểm tra tọa độ có nằm trong cửa sổ không
        if (x < 0 or x > current_game_window.width or
            y < 0 or y > current_game_window.height):
            return {
                "success": False,
                "error": f"Tọa độ ({x}, {y}) nằm ngoài cửa sổ game (0, 0, {current_game_window.width}, {current_game_window.height})"
            }

        # Focus cửa sổ trước khi click
        current_game_window.activate()
        time.sleep(0.2)

        # Thực hiện click
        if click_type == "left":
            pyautogui.click(absolute_x, absolute_y)
        elif click_type == "right":
            pyautogui.rightClick(absolute_x, absolute_y)
        elif click_type == "double":
            pyautogui.doubleClick(absolute_x, absolute_y)
        else:
            return {
                "success": False,
                "error": f"Loại click không hợp lệ: {click_type}. Chỉ hỗ trợ: left, right, double"
            }

        return {
            "success": True,
            "click_info": {
                "relative_position": {"x": x, "y": y},
                "absolute_position": {"x": absolute_x, "y": absolute_y},
                "click_type": click_type,
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
def wait_and_capture(delay: float = 2.0) -> Dict[str, Any]:
    """
    Đợi một khoảng thời gian rồi chụp lại màn hình game.

    Args:
        delay: Thời gian đợi (giây)

    Returns:
        Screenshot mới sau khi đợi
    """
    try:
        # Đợi
        time.sleep(delay)

        # Chụp màn hình mới
        result = capture_game_screen()

        if result["success"]:
            result["delay_applied"] = delay
            result["message"] = f"Đã đợi {delay} giây và chụp màn hình mới"

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi trong wait_and_capture: {str(e)}"
        }

@mcp.tool()
def list_all_windows() -> Dict[str, Any]:
    """
    Liệt kê tất cả cửa sổ có sẵn trên hệ thống.

    Returns:
        Danh sách tất cả cửa sổ visible
    """
    try:
        windows = gw.getAllWindows()

        window_list = []
        for window in windows:
            if window.visible and window.title.strip():  # Chỉ lấy cửa sổ visible và có title
                window_list.append({
                    "title": window.title,
                    "x": window.left,
                    "y": window.top,
                    "width": window.width,
                    "height": window.height,
                    "is_active": window.isActive,
                    "is_maximized": window.isMaximized,
                    "is_minimized": window.isMinimized
                })

        return {
            "success": True,
            "total_windows": len(window_list),
            "windows": window_list
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi liệt kê cửa sổ: {str(e)}"
        }

@mcp.tool()
def get_last_screenshot() -> Dict[str, Any]:
    """
    Lấy screenshot cuối cùng đã chụp.

    Returns:
        Screenshot cuối cùng nếu có
    """
    global last_screenshot

    if not last_screenshot:
        return {
            "success": False,
            "error": "Chưa có screenshot nào được chụp. Hãy dùng capture_game_screen() trước."
        }

    return {
        "success": True,
        "screenshot": last_screenshot,
        "message": "Screenshot cuối cùng đã được chụp"
    }

if __name__ == "__main__":
    mcp.run()
