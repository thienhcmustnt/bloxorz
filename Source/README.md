# BLOXORZ · Solver Lab

Đồ án CSC14003 — game Python/FastAPI với GUI Three.js chạy offline.
**BFS, DFS, IDS, UCS, A\* và hai heuristic đều là stub có chủ đích.** Không có search algorithm trong game, test hay benchmark. Nhóm tự viết phần thuật toán và báo cáo.

## Chạy ngay

Mở terminal **trong thư mục `Source/`**, Python 3.10 trở lên:

```sh
pip install -r requirements.txt
python main.py
```

Trình duyệt tự mở tại http://127.0.0.1:8000. Cần mạng để cài Python dependencies lần đầu; sau đó game, texture và JS đều chạy offline, không cần Node hay bundler. Nếu trình duyệt không tự mở, truy cập URL trên. Có thể dùng `python -m pip` thay cho `pip` khi máy có nhiều Python.

```sh
python main.py --no-browser --port 8001
```

Khuyến nghị môi trường riêng: `python -m venv .venv`; Ubuntu/macOS: `source .venv/bin/activate`; Windows PowerShell: `.venv\Scripts\Activate.ps1`. Hai lệnh cài/chạy ở trên không đổi.

## Điều khiển

| Phím / nút | Tác dụng |
|---|---|
| ↑ ↓ ← → / W A S D | Lăn block / di chuyển cube đang chọn |
| Space / Swap cube | Đổi cube khi split, tính 1 action |
| R / Restart | Chơi lại màn; hủy animation đang chạy |
| U / Backspace / Undo | Lùi một action, khôi phục cả bridge và split |
| Esc / Level Select | Chọn màn |
| ? | Chú giải tile và cơ chế |
| D-pad / vuốt | Điều khiển bằng chuột hoặc cảm ứng |
| Sound | WebAudio, mặc định tắt |

Thua tự chơi lại; thắng tự sang màn kế. Qua màn 15 trở về menu. Progress được lưu bằng localStorage; game vẫn hoạt động nếu trình duyệt chặn storage. `?unlock=all` hoặc nút **Unlock all** mở mọi màn để chấm/video.

Solve chưa được cài sẽ hiển thị thông báo, **không** lấy `meta.solution` để giả làm kết quả tìm kiếm. Khi nhóm cài solver, panel hiện Time, Memory, Expanded Nodes, Length, Cost; replay có Pause/Play, Step, Speed và Stop. Replay tính từ state hiện tại, giữ nguyên bridge mask; input tay bị khóa.

## Cấu trúc

```text
StudentID1_StudentID2/
  Source/
    main.py, requirements.txt, pyproject.toml, README.md
    core/       state, loader, rules, tile metadata, cost
    solvers/    contracts, process runner, student stubs
    api/        FastAPI requests and session orchestration
    web/        ES modules, procedural 3D, local vendor JS
    levels/     15 validated JSON levels
    tests/      rules, geometry oracle, API, solver contracts, e2e
    bench/      measurement harness and figures
    docs/       rules, format, decisions, API, handoff, verification
  Report.pdf    nhóm tự tạo, không có trong gói bàn giao
```

Đổi tên thư mục ngoài thành MSSV thật của nhóm trước khi nộp. Các lớp phụ thuộc theo hướng web → API → solver → core → dữ liệu JSON; core không import API/solver/GUI.

## Test và kiểm tra code

```sh
python -m pytest -m "not e2e" -q
python -m mypy --strict core/
python -m ruff check .
python -m playwright install chromium
python -m pytest -m e2e -q
python -m pytest -q
```

E2E tự mở server tại port trống, chạy Chromium headless rồi đóng cả hai. Tự skip khi không có trình duyệt. Trên Linux thiếu thư viện hệ thống, dùng hướng dẫn của Playwright (`python -m playwright install --with-deps chromium`, có thể cần quyền quản trị). `BLOXORZ_BROWSER` cho phép dùng đường dẫn Chromium khác. Test solver skip khi gặp `NotImplementedError`; lỗi khác không được che thành skip. `tests/fake_solver.py` chỉ replay chuỗi cố định để kiểm tra plumbing, không phải solver và không được đăng ký ở production.

Chế độ `?debug=1&unlock=all`: overlay state/FPS, tọa độ tile, kiểm tra pose, `window.__bloxorz`. Hook debug chỉ tồn tại với `debug=1`. `holdTerminal` là hook cho e2e để quan sát WON/LOST trước khi chuyển màn tự động.

## Benchmark

```sh
python bench/run_bench.py --algos bfs dfs ids ucs astar --groups 1 2 3 4 --repeat 3 --timeout 30 --cost-model risk --out bench/results
python bench/run_bench.py --algos ucs astar:center --levels 1-4 7 10-15 --cost-model unit --repeat 3
python bench/plots.py bench/results/results.csv
```

Kết quả: `results.csv`, `environment.json`, bốn PNG 240 dpi và `summary.md`. Không có solver thì CSV chỉ có header và biểu đồ ghi “No successful measurements”. Đây không phải số liệu thực nghiệm. Mỗi repeat chạy time và tracemalloc trong **hai process riêng**; timeout tính cả startup. Với solver ngẫu nhiên, nhóm phải quy định seed và báo cáo chính sách seed.

## Xử lý sự cố

- Port 8000 bận: `python main.py --port 8001`.
- Trang trắng/WebGL không khả dụng: bật hardware acceleration hoặc dùng trình duyệt hỗ trợ WebGL; lỗi context có nút Reload. Không mở trực tiếp `index.html` bằng `file://`.
- Solver thông báo chưa cài: xem `docs/HANDOFF.md`; đây là chủ đích của đồ án.
- Server restart/session hết hạn: thao tác tiếp theo tạo session mới và đưa về đầu màn. Khi server đang tắt, thông báo cho phép nhấn Restart thử lại.
- Windows multiprocessing: giữ guard `if __name__ == '__main__'` của entry point; module solver phải import được bằng tên module.
- Không thấy metrics/controls trên điện thoại: cuộn xuống dưới board.

Đọc `docs/VERIFICATION.md` để phân biệt phần đã chạy thực tế và phần cần nhóm xác nhận trên máy nộp bài.
