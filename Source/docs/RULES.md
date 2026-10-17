# Luật Bloxorz

Nguồn sự thật: `core/rules.py`. Frontend chỉ gửi action và diễn hoạt event; không tính luật.

## State và tọa độ

`(r,c)`: row tăng xuống, column tăng sang phải. `State(cubes, split, active, bridges)` bất biến và hashable. `cubes` được sort theo `(r,c)`. Nếu split, `active` được remap theo vị trí cube, không giữ mù quáng index cũ. Khi không split, active chuẩn hóa về 0. `bridges` là bitmask; bit `i` bằng 1 khi bridge `i` mở.

Block đứng: một footprint cell; block nằm: hai cell kề nhau. Không lưu orientation riêng. Cube split có chiều cao một đơn vị; block đứng cao hai đơn vị. State JSON thêm orientation/bridges_open chỉ để vẽ.

| Orientation và ô gốc | UP | DOWN | LEFT | RIGHT |
|---|---|---|---|---|
| S tại `(r,c)` | V `(r-2,c)` | V `(r+1,c)` | H `(r,c-2)` | H `(r,c+1)` |
| H tại `(r,c),(r,c+1)` | H `(r-1,c)` | H `(r+1,c)` | S `(r,c-1)` | S `(r,c+2)` |
| V tại `(r,c),(r+1,c)` | S `(r-1,c)` | S `(r+2,c)` | V `(r,c-1)` | V `(r,c+1)` |

H dùng ô trái nhất, V dùng ô trên cùng làm ô gốc.

## Tile

| Tile | Nền đỡ và điều kiện |
|---|---|
| void / ngoài board | Không đỡ, LOST |
| floor/start | Đỡ mọi cấu hình |
| fragile | Block đứng đầy đủ làm vỡ và LOST; block nằm/cube đơn an toàn |
| goal | Chỉ WON khi block đầy đủ đứng trên đó; các cấu hình khác vẫn được đỡ |
| bridge | Đóng: không đỡ; mở: như floor |
| soft_switch | Sau directional move, bất kỳ cube/block chiếm ô này đều kích hoạt |
| heavy_switch | Chỉ block đầy đủ đứng thẳng kích hoạt |
| split_switch | Chỉ block đầy đủ đứng thẳng kích hoạt; đặt cube theo JSON |

`toggle` đảo từng bridge liên kết. `permanent` đặt open/closed; bấm lại vẫn cùng giá trị. Mỗi switch bị chiếm được kích hoạt tối đa một lần trong một directional action. Nhiều switch được xử lý theo tọa độ row-major; targets theo thứ tự trong JSON. Nếu hai toggle cùng tác động một bridge, cả hai lần đảo đều diễn ra.

`SWAP`: đổi cube active, không di chuyển, không merge, không kích hoạt switch, cost và moves đều tăng 1. SWAP không split trả LOST ở core; UI chặn thao tác này.

Khi split, chỉ cube active di chuyển một ô; cube còn lại giữ nguyên. Hai cube trùng ô là LOST. Sau directional move (kể cả sau split placement), Manhattan distance bằng 1 thì tự merge thành H/V. `SWAP` không merge dù hai cube kề nhau.

## Thứ tự step

1. Tính footprint mới, hoặc xử lý SWAP control-only.
2. Kiểm tra support và overlap. Sai: `roll → fall`, state=None, LOST.
3. Kiểm tra fragile. Sai: `roll → fragile_break`, state=None, LOST.
4. Xử lý switch và bitmask, ghi event theo thứ tự xác định.
5. Kiểm tra lại support dưới footprint hiện tại. Cầu vừa đóng dưới block gây `fall`.
6. Nếu split switch, đặt hai cube theo JSON; kiểm tra support của đích dưới **bitmask mới**. Sau đó merge nếu kề nhau.
7. Kiểm tra goal, ghi `win` và WON nếu phù hợp.

Switch tại đích teleport không kích hoạt trong chính bước teleport (tránh chain không được đặc tả). Nó được xét trong directional action tiếp theo. Nền đỡ đích teleport vẫn phải hợp lệ ngay.

## Event và animation

`roll` luôn đứng đầu directional action: from_cells, to_cells, direction, from_orientation, to_orientation, cube_index (null nếu không split). Khi split, to_cells giữ thứ tự cube cũ để animate đúng identity; state cuối được chuẩn hóa độc lập.

Sau roll: `switch_pressed`, tiếp theo các `bridge_changed` thực sự đổi giá trị của switch đó; lặp cho switch tiếp theo; rồi `split`, `merge`, `win` nếu có. `fall` chấm dứt bước tại chỗ phát hiện mất support. Fragile mất support dùng riêng `fragile_break` (GUI thực hiện cả vỡ và rơi). `swap` là event duy nhất của SWAP.

`split` có from_cells, to_cells theo thứ tự đích JSON và active_cell. `merge` có cells và orientation. `bridge_changed` có bridge_id/open. `fall` có cells/reason. Event serialize thành object `{type,...payload}`.

## Cost

`unit`: mọi action cost 1.

`risk`: mặc định 1; action kết thúc với block đầy đủ **nằm** trên ít nhất một fragile là 2. Ngoại lệ SWAP hoặc kích hoạt switch là 1, kể cả khi một footprint còn lại là fragile. Move LOST báo cost 1 nhưng không có trong successors. Có thể cắm callable trong `core/costs.py`; benchmark/API dùng hai tên unit/risk.

Built-in minimum cost bằng 1. Một lower bound hợp lệ theo số action vẫn là lower bound cho risk cost. Điều này không tự chứng minh rằng một heuristic cụ thể là admissible.

`successors` trả duy nhất mỗi action không LOST, bao gồm action dẫn đến WON; goal state không có successor. `legal_actions` lọc cùng nguồn luật. UI đếm mọi action hợp lệ đã gửi server, kể cả action thua và SWAP; Undo phục hồi số moves trước đó, seq vẫn tăng.
