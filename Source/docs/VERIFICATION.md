# Kiểm chứng và giới hạn bàn giao

## Kết quả chốt

Ngày kiểm tra: 17/10/2026. `python -m pytest -q --disable-warnings`: **122 passed, 90 skipped, 0 failed**, 126.77 giây. Có 22 e2e chạy thật; không e2e nào bị skip. 90 skip gồm 75 solver-contract cases và 15 BFS-optimum cases, vì solver còn là stub.

`python -m ruff check .`: All checks passed. `python -m mypy --strict core/`: Success, 7 source files. Một dependency deprecation warning đến từ FastAPI/Starlette TestClient dùng httpx, không phải lỗi test.

Bản cài sạch: FastAPI 0.143.3, uvicorn 0.54.0, pytest 9.1.1, Hypothesis 6.170.1, Playwright 1.56.0, mypy 1.20.2, ruff 0.17.1, matplotlib 3.11.2.

## Phạm vi thực sự đã chạy

Môi trường Linux, Python 3.12.14, Chromium Headless Shell 141 (Playwright 1.56.0), software WebGL. Cài sạch bằng requirements.txt và chạy python main.py; HTML, API, hai vendor JS được phục vụ thành công. Browser bị chặn mọi request ngoài localhost vẫn tải/chơi được.

- Oracle rigid-body xoay tám đỉnh hộp, đối chiếu 3.000 cấu hình ngẫu nhiên có void; property test phép lăn nghịch đảo.
- Kiểm tra fragile/goal/switch/bridge/split/merge, active remap, overlap, đóng cầu dưới block, đích teleport không được đỡ, hash và input immutability.
- 15 lời giải được replay qua core và Chromium. Chỉ thắng ở action cuối.
- 200 sự kiện phím từ PRNG seed cố định; buffer input; hủy animation bằng Restart.
- Chuyển màn 30 lần và quay về màn đầu: số geometry/texture GPU không tăng vượt sai số kiểm tra.
- Undo trước/sau split và merge; Solve thiếu implementation; replay từ state đã chơi một phần, Pause/Step/Speed/Stop.
- Restart trong SOLVING; hai yêu cầu load cạnh tranh; phiên hết hạn; tắt và khởi động lại server thật rồi client tự phục hồi.
- Mobile viewport 390×844, desktop 1280×720 và 1440×900; keyboard và level select.
- Đã chụp và xem 15 ảnh QA: standing, lying H/V, fragile, bridge đóng/mở, heavy, split/swap, stress, level select, win/lose, thông báo solver thiếu và mobile.
- Benchmark với fixture playback cố định: CSV đúng schema, bốn PNG 240 dpi và Markdown. Không coi các số đo fixture là kết quả thực nghiệm solver.
- AST audit xác nhận năm solve và hai heuristic chỉ có docstring + raise NotImplementedError. Không có search implementation trong tracked source hoặc lịch sử commit.

## Màn chơi đã chứng nhận

Expanded dưới đây thuộc lần kiểm chứng tạm theo số action, không phải benchmark solver sinh viên. Công cụ tìm kiếm tạm không nằm trong repo hoặc gói bàn giao.

| Màn | Tên | Optimal actions | Expanded khi kiểm chứng |
|---:|---|---:|---:|
| 1 | First Roll | 6 | 31 |
| 2 | Narrow Path | 8 | 52 |
| 3 | The L | 10 | 89 |
| 4 | Islands | 12 | 123 |
| 5 | Thin Ice | 12 | 13 |
| 6 | Crumble Maze | 14 | 15 |
| 7 | First Switch | 14 | 18 |
| 8 | Heavy Duty | 18 | 21 |
| 9 | Two Keys | 20 | 31 |
| 10 | Splitsville | 24 | 2600 |
| 11 | Reunion | 29 | 4905 |
| 12 | Grand Finale | 33 | 6181 |
| 13 | Stress A | 17 | 3086 |
| 14 | Stress B | 20 | 19379 |
| 15 | Stress C | 24 | 43209 |

Các màn 5–12 có mechanism ablation phù hợp trong meta.verification: bỏ cơ chế bắt buộc làm mất lời giải. Màn 11 dùng permanent bridge theo D14; không có luật pressure-hold ngoài đặc tả.

## Giới hạn chưa được xác nhận

- Chưa chạy trực tiếp trên Windows/macOS hoặc Python 3.10/3.11: môi trường cung cấp Linux/Python 3.12. Code dùng multiprocessing spawn và pathlib để tương thích; nhóm cần chạy README trên máy nộp bài.
- Không chứng nhận 60 fps trên mọi GPU/điện thoại. E2E dùng software WebGL; desktop QA từng ghi nhận xấp xỉ 57 fps, không phải benchmark hiệu năng chuẩn.
- Không có kết quả so sánh BFS/DFS/IDS/UCS/A* thực tế vì nhóm chưa cài solver. Test của các slot đó skip chủ đích.
- Admissibility/consistency của heuristic phải do nhóm chứng minh; không có heuristic nào được cung cấp.
- Audio, thao tác cảm ứng vật lý và phục hồi WebGL context trên GPU thật chưa được kiểm tra trên thiết bị vật lý. Có WebAudio, swipe, responsive và handler context-lost.
- Không có Report.pdf, video hoàn chỉnh hoặc MSSV thật: đây là phần nhóm tự bổ sung theo yêu cầu.

## Đối chiếu rubric phần nền tảng

- [x] GUI 3D, chơi tay, ba orientation, phát hiện rơi/thắng.
- [x] Đủ special tiles, switch modes, split/merge, bridge bitmask trong State.
- [x] JSON dùng chung cho core/API/solver/test/bench.
- [x] New Game, Restart, Undo, Level Select, bốn nút Solve, heuristic selector.
- [x] Metrics và replay được kiểm bằng fixture; sẵn sàng khi nhóm cài solver.
- [x] Source/main.py, README.md, requirements.txt và tài liệu; Report.pdf cố ý dành nhóm.
- [x] Tất cả solver/heuristic vẫn là stub; không có thuật toán tìm kiếm được bàn giao.
