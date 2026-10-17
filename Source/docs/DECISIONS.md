# Quyết định và cách thay đổi

| # | Quyết định | Lý do / nơi đổi |
|---|---|---|
| D01 | Cube đơn an toàn trên fragile | Nhẹ hơn whole block; đúng default đề. Nhóm xác nhận giảng viên. Đổi check fragile trong rules và test tương ứng. |
| D02 | SWAP cost 1, moves +1; không switch, không merge | SWAP không rời ô; tránh toggle bởi thao tác chọn cube. Nhánh SWAP trong rules. |
| D03 | Directional move xét mọi soft switch đang bị chiếm, kể cả dưới cube không di chuyển | Theo điều kiện “bất kỳ ô nào ... sau nước đi”. Nhận xét trong đề rằng luôn rời hết ô cũ không đúng khi split. Nếu muốn chỉ xét cube vừa đến, đổi vòng switch và test; sẽ đổi state graph/certificates. |
| D04 | Switches row-major, targets theo JSON | Nhiều switch tác động cùng bridge cần thứ tự xác định; validation từ chối duplicate targets. Đổi rules nếu quy ước khác. |
| D05 | Sau split placement kiểm tra support lần nữa | Bridge ở đích có thể đã đóng sau lần load; tránh successor không hợp lệ. Test riêng. |
| D06 | Không cascade switch ở đích teleport; adjacent destinations merge ngay | Giữ đúng thứ tự switch → placement → merge, tránh đệ quy không xác định. Đổi rules và tests. |
| D07 | Cube đầu JSON là active khi split | State tự remap index khi sort; kiểm thử với đích đảo thứ tự. |
| D08 | Invalid SWAP/overlap trả LOST ở core, UI chặn SWAP không split | Hợp đồng StepResult thống nhất. API action sai tên bị 422. |
| D09 | Switch activation cost 1 ưu tiên hơn fragile risk 2 | Khi nằm trên một soft và một fragile, xử lý đúng ngoại lệ switch của đề. `core/costs.py`, có regression test. |
| D10 | expanded_nodes đếm khi lấy node khỏi frontier để mở rộng | Thống nhất contract; solver tự điền, wrapper không đoán. Nhóm phải giữ cùng quy ước cho goal pop. Không kiểm tra số đếm bằng search code phụ. |
| D11 | Time và tracemalloc đo riêng; timeout mỗi pass gồm spawn | Tránh tracemalloc làm sai time. search_time chỉ gồm solve; peak là Python traced allocations trong solve, không phải OS RSS/GPU. |
| D12 | Seq tăng cả restart/undo, moves có thể giảm | Tránh request lặp sau reset. Restart khi animation/in-flight tạo session mới để cách ly request cũ; restart idle gọi endpoint reset. |
| D13 | Replay từ state hiện tại, giữ history; stop tại action boundary | Không cần tự dịch ngược luật; cùng move/animation path. API cũng hỗ trợ from_initial. |
| D14 | Màn 11 dùng switch permanent/latching | Luật toggle/permanent không có pressure-hold bridge. Cube phải tới switch ở bờ kia để mở đường đoàn tụ; không tự đóng khi cube rời. Đây là cách diễn giải “cube giữ switch” phù hợp luật đã chốt; pressure-hold sẽ là cơ chế mới và cần giảng viên xác nhận. |
| D15 | Màn 1–12 dài 6–33 action, không giảm; stress ưu tiên số state | 13–15 có 3.086/19.379/43.209 expanded trong kiểm chứng, không ép độ dài tăng cùng độ khó. Stress cho phép split/switch làm nhánh phụ. Hiệu năng tương đối giữa solver chỉ biết khi nhóm cài xong. |
| D16 | 64 bridge ID tối đa, ID không cần liên tiếp | Chặn dữ liệu vô lý; bitmask Python vẫn có thể mở rộng bằng sửa validator. |
| D17 | Placeholder StudentID1_StudentID2, không tạo Report.pdf | Chưa có toàn bộ MSSV nhóm; user yêu cầu báo cáo do nhóm làm. Đổi tên thư mục ngoài, thêm PDF khi nộp. |
| D18 | Phiên bản JS local: Three 0.160.1, GSAP 3.12.5 | Chạy/quay video offline. Không CDN fallback cần thiết trong bản bàn giao. Giữ header/license vendor. |
| D19 | UI dùng tiếng Anh ngắn; thông báo solver thiếu/timeout tiếng Việt | Nhãn gọn cho video, đúng thông báo yêu cầu. Chỉnh trong UI.js/index.html. |
| D20 | Semantic error line chỉ tới grid row/key collection | JSON parser không giữ vị trí mọi node; không báo line giả chính xác token. `Level.load`. |
| D21 | Headless Chromium dùng software WebGL trong e2e | Môi trường không có GPU vật lý. Kiểm tra functional/pose thật, không chứng nhận 60 fps trên mọi máy. |
| D22 | Session local có TTL và capacity; không authentication | Chỉ bind 127.0.0.1; đúng phạm vi đồ án. Không expose public khi chưa bổ sung bảo vệ. |

Không có heuristic hay search implementation được cung cấp. Optimal metadata đến từ công cụ tạm nằm ngoài repo và đã xóa khi bàn giao; kiểm tra lại bằng BFS của nhóm sau khi tự cài.
