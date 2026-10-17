# Định dạng Level JSON

`Level.load(path)` nạp UTF-8; `Level.from_dict(data, source)` dùng cùng validation. Level lưu tuple và bảng tra tuple; `to_dict()`/`meta` trả bản sao. Lỗi `LevelError` ghi file, source line và lý do; lỗi grid có row index. Khi dùng dict không có văn bản nguồn, line=1. Với lỗi semantic cấp collection, line chỉ tới key collection, không giả vờ biết vị trí token con.

## Ví dụ đầy đủ nhỏ

```json
{
  "id": 101, "name": "Example",
  "grid": ["SooBB#G"],
  "legend": {"S":"start","o":"soft_switch","B":"bridge","#":"floor","G":"goal"},
  "bridges": [{"id":0,"cells":[[0,3],[0,4]],"open":false}],
  "switches": [
    {"cell":[0,1],"type":"soft","mode":"permanent","set":"open","targets":[0]},
    {"cell":[0,2],"type":"soft","mode":"permanent","set":"open","targets":[0]}
  ],
  "meta": {"difficulty":1,"group":3,"hint":"Cross the bridge.","solution":"RRRR","optimal_moves":4}
}
```

Bridge metadata phải gắn với mọi tile có type `bridge`, không phụ thuộc ký tự có thực sự là `B` hay không. Tương tự cho các loại switch. Tên ký tự là tùy chọn qua legend.

## Các trường và validation

- `id`: positive integer; `name`: nonempty string.
- `grid`: mảng chuỗi không rỗng, cùng chiều dài, mọi ký tự có trong legend.
- `legend`: key một ký tự; value thuộc void/floor/start/goal/fragile/bridge/soft_switch/heavy_switch/split_switch.
- Đúng một start và một goal.
- `bridges`: id duy nhất trong 0–63; cells không rỗng, tọa độ nguyên trong board; mỗi bridge tile thuộc đúng một bridge. `open` boolean, mặc định false. ID không cần liên tiếp.
- `switches`: cell đúng loại tile, không trùng, không thiếu definition; type soft/heavy/split; targets là các bridge ID tồn tại, không trùng.
- `mode=toggle`: không có `set`; `mode=permanent`: bắt buộc `set=open` hoặc `closed`.
- Split cần `cubes` gồm hai tọa độ khác nhau, có nền đỡ trong cấu hình ban đầu. Destination có thể là fragile. Khi thực sự teleport, rules kiểm tra lại bitmask hiện thời. Cube thứ nhất trong JSON là cube active ban đầu; chuẩn hóa không đổi identity này.
- Non-split switch không được khai báo cubes.
- `meta.solution`: chuỗi không khoảng trắng, chỉ `U D L R W` với W là SWAP; `optimal_moves` bằng độ dài chuỗi. Loader không chạy tìm kiếm để chứng minh tối ưu.
- `meta.group`: nhóm cố định 1: levels 1–4; 2: 5–6; 3: 7–9; 4: 10–15.
- `meta.verification`: kết quả kiểm chứng ngoại tuyến, gồm expanded_nodes, reachable_discovered và mechanism_ablation. Đây là chứng cứ của lần thiết kế, không phải kết quả solver sinh viên.

API không công khai solution, optimal_moves hay verification. Test replay toàn bộ solution và kiểm tra chỉ thắng ở action cuối. Sau khi chỉnh level, phải cập nhật chứng nhận bằng công cụ tạm ngoài repo rồi xóa công cụ; không commit search implementation.

## Tạo/chỉnh màn

Chỉnh JSON, giữ các bảng bridge/switch nhất quán, chạy `pytest tests/test_level_loading.py tests/test_levels_solutions.py`. Màn dạy soft/heavy/split đã được kiểm tra mất lời giải khi vô hiệu loại switch bắt buộc; màn fragile mất lời giải khi các fragile bị thay bằng void. Điều này chứng minh cần đi qua fragile, không khẳng định chỉ tồn tại một chuỗi action duy nhất (có thể quay lui).
