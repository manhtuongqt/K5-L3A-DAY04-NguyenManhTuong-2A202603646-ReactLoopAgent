# CP7 · Demo, chốt bài và nộp

## Bài cá nhân

Nguyễn Mạnh Tường — 2A202603646 — L3A.

Repo nộp: https://github.com/manhtuongqt/K5-L3A-DAY04-NguyenManhTuong-2A202603646-ReactLoopAgent

## Kịch bản demo

Các trace cần trình bày đều có trong hai file eval ở gốc repo. Nếu muốn quan sát bằng giao diện cục bộ, xem `demo/README.md`; không nộp link web.

1. **Trace nhiều bước:** mở CP4 hoặc CP6, chọn E2 và xem model lấy status rồi đọc chi tiết incident. Chỉ ra snapshot timestamp, phạm vi FedRAMP và URL. Hoặc dùng CP2 tình huống điều tra hai bước để gọi API lại; có thể phát sinh phí.
2. **Một lỗi agent thật:** mở H3 trước cải tiến. Agent chỉ gọi `get_status`; giải thích vì sao danh sách 5 mục không đủ để xác nhận ID vắng mặt trong 50 incident. Mở H3 sau cải tiến để đối chiếu việc tra trực tiếp ID.
3. **Validation nguồn:** ở CP5, chạy mô phỏng thiếu URL. Đây là FakeProvider offline chạy qua loop thật; cần thấy `validation_missing_source` rồi câu trả lời được sửa. Không gọi đây là lần chạy API thật.
4. **Kết quả và giới hạn:** mở CP6 để đọc bảng trước/sau, bao gồm các case giảm điểm. Mở CP7 để đối chiếu gate và sản phẩm của từng CP.

Log mô phỏng không thay thế trace API; demo trên trình duyệt không tự xác nhận người học đã trình bày và giải thích được code với trợ giảng.

## Checklist trước khi nộp

- Code: `agent.py`, không dùng framework agent.
- Hai kết quả thật: `eval_before.json`, `eval_after.json`; đủ 22 case, điểm tổng khác `null`.
- Cấu hình model/judge/dataset/max steps giống nhau; fixtures và grading không đổi.
- `NOTES.md` đủ năm mục; CP3, CP4, CP5, CP6 được báo cáo riêng.
- Toàn bộ unit tests đạt; bằng chứng trong `artifacts/final_unit_tests.txt` và `artifacts/checkpoint_audit.json`.
- Repo public, đúng tên L3A; không chứa `.env` hoặc key.
- Trạng thái push và commit có trên demo, lấy từ Git; chỉ báo pushed yêu cầu HEAD trùng origin/main và working tree sạch.
- **Người học tự nộp link repo lên LMS. Chưa có bằng chứng đã nộp.**

## Phần người học thực hiện

Đăng nhập https://aithucchien.vinuni.edu.vn bằng tài khoản cá nhân, mở bài Day04, dán link repo ở trên và lưu/xác nhận nộp theo giao diện. Kiểm tra lại trạng thái nộp và hạn của ca học hoặc thông báo của key coach. Không coi push GitHub là đã nộp LMS.

**Gate CP7:** phần kỹ thuật và bằng chứng demo được kiểm tra riêng; checkpoint vẫn ghi hoàn thành một phần đến khi có xác nhận nộp LMS và phần trình bày theo yêu cầu lớp học. Không tự đánh dấu các hành động của người học là đã xong.
