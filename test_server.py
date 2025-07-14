#!/usr/bin/env python3
"""
Test script để kiểm tra server.py có import được không
"""

try:
    print("Testing imports...")
    
    # Test MCP import
    from mcp.server.fastmcp import FastMCP
    print("✓ MCP import successful")
    
    # Test game automation imports
    import pyautogui
    print("✓ pyautogui import successful")
    
    import pygetwindow as gw
    print("✓ pygetwindow import successful")
    
    from PIL import Image as PILImage
    print("✓ PIL import successful")
    
    import mss
    print("✓ mss import successful")
    
    import numpy as np
    print("✓ numpy import successful")
    
    print("\n✅ All imports successful!")
    print("🎮 GachaMCP server is ready to run!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Please install missing dependencies with: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
