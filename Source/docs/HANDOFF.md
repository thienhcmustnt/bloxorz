# Bàn giao cho nhóm

## Có sẵn / phần nhóm làm

Có sẵn: luật, immutable State/Level, 15 JSON và chứng nhận, API session, process runner, GUI offline, replay, benchmark, unit/property/oracle/e2e tests.

Nhóm tự làm: `solvers/bfs.py`, `dfs.py`, `ids.py`, `ucs.py`, `astar.py`, `heuristics.py`; Report.pdf; video demo có phần so sánh solver; thông tin MSSV và link nộp. DFS/IDS có hai slot riêng dù rubric thường gộp một họ thuật toán.

**Không copy đường đi từ meta.solution vào solver.** Meta chỉ phục vụ kiểm chứng level và test harness. UI/API không nhận chuỗi này.

## Contract để cắm solver

```python
def solve(problem: Problem) -> SearchResult:
    # Input/output contract only; students provide implementation.
    raise NotImplementedError
```

Problem có `initial_state`, `level`, `cost_model`, `heuristic`; chỉ dùng `problem.successors(state)` cho transition, `problem.is_goal(state)` cho goal, `problem.step_cost(...)` khi cần cost. A* nhận callable tại `problem.heuristic`; tên center/relaxed được runner resolve. Không sửa signature solve.

Solver điền found, path (`list[Action]`), cost, expanded_nodes, reason nếu thất bại. SearchResult có default cho các field đo đạc. Runner điền solution_length, search_time, peak_memory_kb; bắt NotImplementedError, exception, timeout. Không tự bật tracemalloc bên trong solver.

`expanded_nodes`: đếm lúc lấy một node ra khỏi frontier để mở rộng. Nhóm nêu rõ trong báo cáo goal node có được tính khi lấy ra không và dùng cùng quy ước ở mọi solver. Tests yêu cầu số dương trên bộ level có lời giải. Runner phát hiện sửa Problem/Level ngoài hợp đồng.

```sh
python -m pytest tests/test_solver_contract.py tests/test_levels_solutions.py -q
python bench/run_bench.py --algos bfs dfs ids ucs astar --repeat 3 --timeout 30
```

Tests kiểm replay, cost, length, BFS optimal_moves, UCS unit length, UCS risk không tệ hơn các lời giải khác, A* so UCS cho hai heuristic khi đã cài. DFS/IDS chỉ bắt buộc lời giải hợp lệ. So sánh A*/UCS trên 15 màn là regression check, **không phải chứng minh admissibility trên mọi state**.

## Cost và các nghĩa vụ toán học

Unit action cost=1. Risk như RULES: action thông thường 1, lying fragile 2, switch/SWAP 1. BFS tối ưu số action không đồng nghĩa tối ưu risk cost. UCS/A* so sánh tổng cost. Một heuristic h admissible khi `0 ≤ h(s) ≤ h*(s)` và h(goal)=0; consistent khi `h(s) ≤ c(s,a,s') + h(s')` cho mọi transition. Nhóm tự xây dựng và chứng minh các hàm này; bản bàn giao không đưa công thức hay cách cài heuristic.

Trong báo cáo, tách tuyên bố lý thuyết khỏi số đo. Optimal metadata của level được xác nhận lại bằng BFS của nhóm. Time và memory chạy riêng; tracemalloc không là toàn bộ RAM process. Không ghi timeout là time=0, không gán missing memory thành đo thành công.

## Báo cáo và thực nghiệm

- Algorithm Description: định nghĩa state/action/goal/cost, completeness/optimality theo giả định tương ứng, expanded_nodes, repeated-state policy, điều kiện dừng, heuristic proof nếu dùng.
- Implementation: interface giữa core và solver, bitmask, normalization, event ordering, spawn timeout, FSM và animation ownership.
- Experiments: bốn nhóm màn, hardware/OS/Python, timeout, số repeat, median, seed nếu có; bốn biểu đồ và bảng cost; giải thích solver thất bại/timeout.
- Không dùng fake solver tests làm baseline. Không tự suy ra A* sẽ nhanh hơn nếu chưa chạy solver của nhóm.
- Liệt kê và xác nhận D01/D03/D14 với giảng viên: fragile cube, stationary soft switch, permanent bridge ở màn 11.

## Câu hỏi phỏng vấn nên tự trả lời

1. Vì sao bridges nằm trong hash State, còn moves/UI status thì không?
2. Sort cubes có thể làm sai active như thế nào? Test nào bắt được?
3. Vì sao kiểm tra support lần hai sau switch và thêm sau teleport?
4. Vì sao SWAP không kích hoạt switch hoặc merge?
5. Vì sao goal chỉ thắng khi whole block đứng, còn fragile chỉ vỡ trong cấu hình đó?
6. Oracle 3D độc lập với transition table ở điểm nào?
7. Frontend nhận gì từ roll event? Vì sao phải snap pose sau animation?
8. Vì sao timeout dùng process thay vì chỉ một timer trong thread?
9. Nếu Restart xảy ra trong lúc fetch hoặc GSAP tween chưa xong, epoch/generation xử lý ra sao?
10. Undo cần khôi phục field nào? Vì sao seq không được giảm cùng moves?
11. Tracemalloc đo phần nào, khác resident memory ở đâu?
12. Vì sao benchmark tách pass thời gian và bộ nhớ?

Đọc code theo thứ tự: State → Level → rules.step → tests/oracle → Problem/runner → API → GameController → BlockAnimator/AnimationQueue.

## Video demo gợi ý (nhóm tự quay)

1. Mở game offline; màn 1 và ba orientation; thử rơi rồi Undo/Restart.
2. Màn 5/7/8: fragile, bridge toggle, heavy permanent; mở legend.
3. Màn 12: split, Swap, merge, các bridge mask; bật debug để giải thích.
4. Sau khi tự cài solver: bấm bốn nút Solve, chỉ rõ metrics; Pause, Step, Speed, Stop.
5. Màn 13–15: bảng benchmark và khác biệt đã đo, không đọc số liệu fake.

## Checklist nộp

- [ ] Đổi StudentID1_StudentID2 thành đúng MSSV.
- [ ] Nhóm đã tự viết và hiểu 5 slot search (BFS/DFS/IDS/UCS/A*) và heuristic.
- [ ] Test solver không còn skip cho các thuật toán phải nộp.
- [ ] Chạy hai lệnh README trên máy giảng viên/Windows thực tế.
- [ ] Đặt Report.pdf bên cạnh Source, không bên trong Source.
- [ ] Báo cáo có cost, heuristic proof, experiments, decisions được xác nhận.
- [ ] Video demo, link repository/video truy cập được, không chứa đường dẫn máy cá nhân.
- [ ] Source/main.py, README, requirements, levels, vendor/license đều có.
- [ ] Không đưa .venv/cache/benchmark tạm vào gói nộp; giữ kết quả thực nghiệm đã chọn trong báo cáo.

Các phần thuật toán, Report.pdf và video cố ý chưa được làm hộ. Xem VERIFICATION.md cho giới hạn kiểm chứng thực tế của bản bàn giao.
