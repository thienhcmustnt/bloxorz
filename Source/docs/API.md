# HTTP API

Cùng origin với frontend, không CORS. Body JSON, lỗi FastAPI `{ "detail": "..." }` hoặc danh sách lỗi schema. Mọi request từ chối field không biết.

| Endpoint | Body | Kết quả |
|---|---|---|
| GET `/api/levels` | — | `{id,name,difficulty,group}[]` |
| GET `/api/levels/{id}` | — | Level JSON công khai, không chứa lời giải |
| POST `/api/game/new` | `{level_id:1}` | Snapshot và session_id mới |
| POST `/api/game/move` | `{session_id,action:"RIGHT",seq:1}` | StepResult + moves + seq |
| POST `/api/game/restart` | `{session_id}` | Snapshot ban đầu, seq tăng, history xóa |
| POST `/api/game/undo` | `{session_id}` | Snapshot trước action cuối, seq tăng |
| POST `/api/solve` | `{session_id,algo,heuristic?,from_initial?,timeout?,cost_model?}` | SearchResult + start_state + measurement_reason |

Snapshot: `{session_id,level_id,state,status,moves,seq}`.

State: `{cubes:[[r,c],...],split,active,bridges,orientation,bridges_open:[id,...]}`. Orientation là standing/lying_h/lying_v/split. State ở response move thua bằng null. Server giữ state trước lần thua chỉ để hỗ trợ Undo; không cho move/solve-current từ trạng thái LOST.

Move: action UP/DOWN/LEFT/RIGHT/SWAP, phân biệt hoa thường. `seq` phải đúng seq hiện tại +1; không chỉ lớn hơn. Move lặp/cũ hoặc gap trả 409. Restart/Undo tăng seq để vô hiệu request cũ. Client dùng seq server trả, không suy từ số moves. Lock giữ toàn bộ validate + step + cập nhật session atomically.

Solve:

- algo bfs/dfs/ids/ucs/astar; heuristic center/relaxed; cost_model unit/risk.
- from_initial=false mặc định. Snapshot được lấy trước khi giải, không sửa session.
- timeout mặc định 30 giây, lớn hơn 0 và không quá 120; áp dụng **mỗi pass**.
- time pass trước, memory pass riêng nếu tìm thấy. `measurement_reason` ghi lỗi memory pass; không giả memory=0 là đo thành công.
- Worker dùng multiprocessing spawn, luôn thu dọn process; endpoint dùng `asyncio.to_thread`, không chặn event loop.
- Chưa cài: HTTP 200, found=false, reason=not_implemented. Timeout: HTTP 200, reason=timeout. Exception: HTTP 200, reason bắt đầu error và traceback ngắn.
- SearchResult: found/path/solution_length/cost/expanded_nodes/search_time/peak_memory_kb/reason. Path là các tên action, không phải chuỗi mã một chữ.

Mã lỗi: 404 level/session không có hoặc session hết hạn; 409 seq/terminal game/no undo; 422 validation; 503 quá 2000 session đang sống. Đây là server local phục vụ đồ án, không phải dịch vụ multi-user công khai có authentication.

TTL mặc định 3600 giây idle, đổi bằng `BLOXORZ_SESSION_TTL`. Dọn định kỳ và khi truy cập. Restart server xóa session; frontend nhận 404 sẽ tạo session mới cùng level. Session không được persist xuống disk.
