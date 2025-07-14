# GachaMCP - Python Game Automation MCP Server

MCP Server giúp AI tương tác với Gacha Game thông qua screenshot và click automation!

## Tính năng

- 🖼️ **Chụp màn hình game** - Capture cửa sổ game để AI phân tích
- 🖱️ **Click automation** - Click theo tọa độ trên cửa sổ game
- 🪟 **Window management** - Tìm và quản lý cửa sổ game
- ⏱️ **Smart delays** - Đợi và chụp lại sau mỗi hành động
- 🎮 **Game state tracking** - Theo dõi trạng thái game

## Cài đặt

```bash
# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

## Sử dụng

### Development Mode

```bash
uv run mcp dev server.py
```

### Claude Desktop Integration

```bash
uv run mcp install server.py --name "GachaMCP"
```

## MCP Tools

- `find_game_window` - Tìm cửa sổ game theo tên
- `capture_game_screen` - Chụp màn hình cửa sổ game (lưu file)
- `click_at_position` - Click tại tọa độ cụ thể
- `wait_and_capture` - Đợi và chụp lại màn hình
- `get_window_info` - Lấy thông tin cửa sổ game
- `focus_game_window` - Focus vào cửa sổ game
- `list_all_windows` - Liệt kê tất cả cửa sổ
- `get_last_screenshot` - Lấy đường dẫn screenshot cuối
- `list_screenshots` - Liệt kê tất cả screenshots
- `clear_screenshots` - Xóa tất cả screenshots

## Ví dụ sử dụng

AI có thể sử dụng các tools này để:

1. Tìm cửa sổ game: `find_game_window("Genshin Impact")`
2. Chụp màn hình: `capture_game_screen()` → Trả về đường dẫn file ảnh
3. AI đọc ảnh từ đường dẫn để phân tích
4. Click vào nút: `click_at_position(x=500, y=300, description="Gacha button")`
5. Đợi và chụp lại: `wait_and_capture(delay=2.0)` → Ảnh mới

**Lưu ý:** Screenshots được lưu trong thư mục `screenshots/` với tên file có timestamp.
