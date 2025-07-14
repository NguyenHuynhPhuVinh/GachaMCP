# Ví dụ sử dụng GachaMCP

## Workflow cơ bản cho AI chơi game gacha

### 1. Tìm và kết nối với game

```python
# AI sẽ gọi tool này để tìm cửa sổ game
find_game_window("Genshin Impact")
# hoặc
find_game_window("Honkai")
# hoặc tìm theo tên bất kỳ
find_game_window("Game")
```

### 2. Chụp màn hình để phân tích

```python
# Chụp màn hình hiện tại
capture_game_screen()
```

AI sẽ nhận được:
- Screenshot dưới dạng base64
- Thông tin cửa sổ game
- Kích thước hình ảnh

### 3. Phân tích và click

Sau khi AI phân tích screenshot, nó có thể click vào các vị trí cụ thể:

```python
# Click vào nút gacha (ví dụ tọa độ 500, 300)
click_at_position(x=500, y=300, description="Gacha button", click_type="left")

# Click chuột phải vào menu
click_at_position(x=100, y=200, description="Context menu", click_type="right")

# Double click vào item
click_at_position(x=300, y=400, description="Item icon", click_type="double")
```

### 4. Đợi và chụp lại

```python
# Đợi 2 giây để game load rồi chụp lại
wait_and_capture(delay=2.0)

# Đợi lâu hơn cho animation
wait_and_capture(delay=5.0)
```

### 5. Workflow hoàn chỉnh

```python
# 1. Tìm game
find_game_window("Genshin Impact")

# 2. Focus vào game
focus_game_window()

# 3. Chụp màn hình ban đầu
capture_game_screen()

# 4. AI phân tích và quyết định click đâu
# Ví dụ: AI thấy nút "Wish" ở tọa độ (800, 600)
click_at_position(x=800, y=600, description="Wish button")

# 5. Đợi game load
wait_and_capture(delay=3.0)

# 6. AI phân tích màn hình mới
# Ví dụ: AI thấy nút "Wish x10" ở tọa độ (900, 500)
click_at_position(x=900, y=500, description="Wish x10 button")

# 7. Đợi animation gacha
wait_and_capture(delay=8.0)

# 8. AI phân tích kết quả gacha và quyết định hành động tiếp theo
```

## Các tool hỗ trợ

### Liệt kê tất cả cửa sổ
```python
list_all_windows()
```

### Lấy thông tin cửa sổ hiện tại
```python
get_window_info()
```

### Lấy screenshot cuối cùng
```python
get_last_screenshot()
```

## Tips cho AI

1. **Luôn chụp màn hình trước khi click** để đảm bảo hiểu đúng trạng thái game
2. **Sử dụng description có ý nghĩa** khi click để dễ debug
3. **Đợi đủ thời gian** sau mỗi hành động để game kịp phản hồi
4. **Focus cửa sổ** trước khi thực hiện các thao tác quan trọng
5. **Kiểm tra kết quả** của mỗi tool call trước khi tiếp tục

## Xử lý lỗi

Tất cả tools đều trả về format:
```json
{
  "success": true/false,
  "error": "Thông báo lỗi nếu có",
  "data": "Dữ liệu kết quả"
}
```

AI nên kiểm tra `success` trước khi sử dụng dữ liệu.
