#!/usr/bin/env python3
"""
GachaMCP - Python Game Automation MCP Server

MCP Server giúp AI tương tác với Gacha Game thông qua game state analysis và click automation.
Thay vì gửi ảnh, server sẽ phân tích màn hình và trả về structured data.
"""

import asyncio
import os
import time
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
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
last_screenshot_path: Optional[str] = None

# Tạo thư mục screenshots nếu chưa có
SCREENSHOTS_DIR = "screenshots"
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# Initialize EasyOCR reader (supports multiple languages)
ocr_reader = easyocr.Reader(['en', 'ja', 'ko'])  # English, Japanese, Korean for gacha games

@dataclass
class GameState:
    """Trạng thái game được phân tích"""
    screen_type: str
    currency: Dict[str, Any]
    ui_elements: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    suggested_actions: List[str]

def _capture_game_window() -> Tuple[bool, Union[np.ndarray, str]]:
    """
    Internal function để chụp cửa sổ game và trả về numpy array.
    
    Returns:
        Tuple[success, image_array_or_error_message]
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

def _analyze_currency(img: np.ndarray) -> Dict[str, Any]:
    """Phân tích currency từ ảnh"""
    currency_data = {}
    
    try:
        # OCR để đọc numbers
        ocr_results = ocr_reader.readtext(img)
        
        for (bbox, text, confidence) in ocr_results:
            if confidence > 0.6:
                # Tìm số trong text
                numbers = re.findall(r'[\d,]+', text)
                if numbers:
                    center_x = sum([point[0] for point in bbox]) / 4
                    center_y = sum([point[1] for point in bbox]) / 4
                    
                    # Phân loại currency dựa vào vị trí
                    if center_y < img.shape[0] * 0.15:  # Top area
                        if center_x < img.shape[1] * 0.4:  # Left side
                            currency_data["gems"] = {
                                "value": numbers[0].replace(",", ""),
                                "display_value": numbers[0],
                                "position": [int(center_x), int(center_y)]
                            }
                        elif center_x > img.shape[1] * 0.6:  # Right side
                            currency_data["coins"] = {
                                "value": numbers[0].replace(",", ""),
                                "display_value": numbers[0],
                                "position": [int(center_x), int(center_y)]
                            }
    except Exception as e:
        print(f"Error analyzing currency: {e}")
    
    return currency_data

def _detect_ui_elements(img: np.ndarray) -> List[Dict[str, Any]]:
    """Detect UI elements using computer vision"""
    ui_elements = []
    
    try:
        # OCR để tìm text buttons
        ocr_results = ocr_reader.readtext(img)
        
        for (bbox, text, confidence) in ocr_results:
            if confidence > 0.5:
                center_x = int(sum([point[0] for point in bbox]) / 4)
                center_y = int(sum([point[1] for point in bbox]) / 4)
                
                # Identify button types based on text
                text_lower = text.lower()
                button_type = "unknown"
                description = text
                
                if any(word in text_lower for word in ["scout", "gacha", "summon", "pull"]):
                    button_type = "gacha"
                    description = f"Gacha button: {text}"
                elif any(word in text_lower for word in ["menu", "home"]):
                    button_type = "navigation"
                    description = f"Navigation: {text}"
                elif any(word in text_lower for word in ["inventory", "items", "bag"]):
                    button_type = "inventory"
                    description = f"Inventory: {text}"
                elif any(word in text_lower for word in ["shop", "store", "buy"]):
                    button_type = "shop"
                    description = f"Shop: {text}"
                
                ui_elements.append({
                    "text": text,
                    "type": button_type,
                    "position": [center_x, center_y],
                    "bbox": bbox,
                    "confidence": confidence,
                    "description": description,
                    "clickable": True
                })
    
    except Exception as e:
        print(f"Error detecting UI elements: {e}")
    
    return ui_elements

def _detect_notifications(img: np.ndarray) -> List[Dict[str, Any]]:
    """Detect notification badges and alerts"""
    notifications = []
    
    try:
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Detect red notification badges
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2
        
        # Find contours in red areas
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 50 < area < 2000:  # Small circular badges
                x, y, w, h = cv2.boundingRect(contour)
                center_x, center_y = x + w//2, y + h//2
                
                # Check if it's roughly circular
                aspect_ratio = w / h
                if 0.7 < aspect_ratio < 1.3:
                    notifications.append({
                        "type": "red_notification_badge",
                        "position": [center_x, center_y],
                        "size": [w, h],
                        "description": f"Red notification badge at ({center_x}, {center_y})"
                    })
    
    except Exception as e:
        print(f"Error detecting notifications: {e}")
    
    return notifications

def _analyze_game_state(detected_text: List[str]) -> str:
    """Analyze game state based on detected text"""
    text_content = " ".join(detected_text).lower()
    
    if "menu" in text_content or "home" in text_content:
        return "main_menu"
    elif "gacha" in text_content or "scout" in text_content or "summon" in text_content:
        return "gacha_screen"
    elif "inventory" in text_content or "items" in text_content:
        return "inventory_screen"
    elif "battle" in text_content or "fight" in text_content:
        return "battle_screen"
    elif "shop" in text_content or "store" in text_content:
        return "shop_screen"
    elif "loading" in text_content:
        return "loading_screen"
    else:
        return "unknown_screen"

def _suggest_actions(game_state: str, ui_elements: List[Dict], currency: Dict) -> List[str]:
    """Suggest possible actions based on current game state"""
    suggestions = []
    
    if game_state == "main_menu":
        suggestions.extend([
            "Click on gacha/scout button to access summoning",
            "Check inventory for items",
            "Look for daily missions or events"
        ])
    elif game_state == "gacha_screen":
        if currency.get("gems", {}).get("value"):
            gems = int(currency["gems"]["value"])
            if gems >= 1500:
                suggestions.append("Perform 10x summon (recommended)")
            elif gems >= 150:
                suggestions.append("Perform single summon")
            else:
                suggestions.append("Insufficient gems for summoning")
    
    # Add suggestions based on UI elements
    gacha_buttons = [elem for elem in ui_elements if elem["type"] == "gacha"]
    if gacha_buttons:
        suggestions.append(f"Gacha button found at {gacha_buttons[0]['position']}")
    
    return suggestions

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
def analyze_game_state() -> Dict[str, Any]:
    """
    Phân tích trạng thái game hiện tại bằng cách chụp màn hình và sử dụng OCR + Computer Vision.

    Returns:
        Structured data về trạng thái game thay vì file ảnh
    """
    global last_screenshot_path

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
        filename = f"game_analysis_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        cv2.imwrite(filepath, img)
        last_screenshot_path = filepath

        # Phân tích các thành phần
        currency = _analyze_currency(img)
        ui_elements = _detect_ui_elements(img)
        notifications = _detect_notifications(img)

        # Phân tích game state
        detected_text = [elem["text"] for elem in ui_elements]
        game_state = _analyze_game_state(detected_text)
        suggested_actions = _suggest_actions(game_state, ui_elements, currency)

        return {
            "success": True,
            "game_state": game_state,
            "currency": currency,
            "ui_elements": ui_elements,
            "notifications": notifications,
            "suggested_actions": suggested_actions,
            "analysis_timestamp": time.time(),
            "screenshot_saved": os.path.abspath(filepath)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi phân tích game state: {str(e)}"
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
def wait_and_analyze(delay: float = 2.0) -> Dict[str, Any]:
    """
    Đợi một khoảng thời gian rồi phân tích lại trạng thái game.

    Args:
        delay: Thời gian đợi (giây)

    Returns:
        Game state analysis mới sau khi đợi
    """
    try:
        # Đợi
        time.sleep(delay)

        # Phân tích lại game state
        result = analyze_game_state()

        if result["success"]:
            result["delay_applied"] = delay
            result["message"] = f"Đã đợi {delay} giây và phân tích lại game state"

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi trong wait_and_analyze: {str(e)}"
        }

@mcp.tool()
def check_currency_status() -> Dict[str, Any]:
    """
    Kiểm tra trạng thái currency hiện tại (gems, coins, etc.) trong game.

    Returns:
        Thông tin chi tiết về currency và khả năng thực hiện gacha
    """
    # Chụp và phân tích
    success, img_or_error = _capture_game_window()
    if not success:
        return {
            "success": False,
            "error": img_or_error
        }

    img = img_or_error

    try:
        currency_data = _analyze_currency(img)

        # Phân tích khả năng gacha
        gacha_analysis = {}
        if "gems" in currency_data:
            gems = int(currency_data["gems"]["value"])
            gacha_analysis = {
                "single_pull_possible": gems >= 150,  # Typical single pull cost
                "ten_pull_possible": gems >= 1500,   # Typical 10-pull cost
                "estimated_pulls": gems // 150,
                "recommendation": "Enough for gacha" if gems >= 150 else "Need more gems"
            }

        return {
            "success": True,
            "currency": currency_data,
            "gacha_analysis": gacha_analysis,
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi kiểm tra currency: {str(e)}"
        }

@mcp.tool()
def find_gacha_button() -> Dict[str, Any]:
    """
    Tìm nút gacha/scout trên màn hình hiện tại.

    Returns:
        Thông tin về nút gacha nếu tìm thấy
    """
    # Chụp và phân tích
    success, img_or_error = _capture_game_window()
    if not success:
        return {
            "success": False,
            "error": img_or_error
        }

    img = img_or_error

    try:
        ui_elements = _detect_ui_elements(img)

        # Tìm gacha buttons
        gacha_buttons = [elem for elem in ui_elements if elem["type"] == "gacha"]

        if not gacha_buttons:
            return {
                "success": False,
                "error": "Không tìm thấy nút gacha trên màn hình",
                "all_buttons": [elem for elem in ui_elements if elem["clickable"]]
            }

        # Lấy button có confidence cao nhất
        best_button = max(gacha_buttons, key=lambda x: x["confidence"])

        return {
            "success": True,
            "gacha_button": {
                "text": best_button["text"],
                "position": best_button["position"],
                "confidence": best_button["confidence"],
                "description": best_button["description"]
            },
            "total_gacha_buttons": len(gacha_buttons),
            "all_gacha_buttons": gacha_buttons
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi tìm gacha button: {str(e)}"
        }

@mcp.tool()
def get_game_summary() -> Dict[str, Any]:
    """
    Tổng hợp toàn bộ thông tin về màn hình game hiện tại.
    Đây là tool chính để AI hiểu trạng thái game.

    Returns:
        Summary đầy đủ về game state, currency, UI elements, notifications
    """
    try:
        # Phân tích game state
        game_analysis = analyze_game_state()
        if not game_analysis["success"]:
            return game_analysis

        # Kiểm tra currency
        currency_status = check_currency_status()

        # Tìm gacha button
        gacha_info = find_gacha_button()

        # Tổng hợp thông tin
        summary = {
            "success": True,
            "timestamp": time.time(),
            "game_state": game_analysis.get("game_state", "unknown"),
            "currency": currency_status.get("currency", {}),
            "gacha_analysis": currency_status.get("gacha_analysis", {}),
            "gacha_button": gacha_info.get("gacha_button") if gacha_info.get("success") else None,
            "notifications": {
                "found": len(game_analysis.get("notifications", [])) > 0,
                "count": len(game_analysis.get("notifications", [])),
                "details": game_analysis.get("notifications", [])
            },
            "ui_elements": game_analysis.get("ui_elements", []),
            "suggested_actions": game_analysis.get("suggested_actions", []),
            "screenshot_path": game_analysis.get("screenshot_saved", "")
        }

        # Thêm recommendations
        recommendations = []

        if summary["notifications"]["found"]:
            recommendations.append("Có thông báo mới cần kiểm tra")

        if summary["gacha_button"]:
            if summary["gacha_analysis"].get("single_pull_possible", False):
                recommendations.append(f"Có thể thực hiện gacha tại {summary['gacha_button']['position']}")
            else:
                recommendations.append("Tìm thấy nút gacha nhưng không đủ gems")

        if summary["game_state"] == "main_menu":
            recommendations.append("Đang ở main menu - có thể navigate đến các chức năng khác")

        summary["recommendations"] = recommendations

        return summary

    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi tạo game summary: {str(e)}"
        }

if __name__ == "__main__":
    mcp.run()
