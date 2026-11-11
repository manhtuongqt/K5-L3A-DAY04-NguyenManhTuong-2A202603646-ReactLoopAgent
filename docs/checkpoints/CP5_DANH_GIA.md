# CP5 · Phân tích và cải tiến

## Lỗi được chọn

H3 trong `eval_before.json` đạt 50/100. Agent gọi `get_status` nhưng không gọi `get_incident_details` để kiểm tra ID người dùng đưa ra. Kết quả danh sách chỉ hiển thị 5 incident, dù số incident khớp trong phạm vi tra cứu là 50. Agent kết luận ID không xuất hiện trong cả 50 mục là vượt quá bằng chứng đã đọc.

Nguồn bằng chứng: `cases[id=H3].result.trace`, answer và `grade.mechanical`. Chi tiết ghi trong `NOTES.md` mục 1–2.

## Thay đổi trong agent.py

1. Bổ sung prompt: nếu có ID cụ thể thì tra trực tiếp bằng tool chi tiết trước khi kết luận; phân biệt phạm vi tìm kiếm với số mục được hiển thị. Nhắc không suy ra component hoạt động bình thường từ danh sách rỗng.
2. Lưu URL từ các lần `get_incident_details` thành công. Nếu final answer chưa chứa URL incident đã quan sát, ghi `validation_missing_source` và yêu cầu model sửa trong cùng `max_steps`.
3. Nếu budget hết sau yêu cầu sửa, trả `max_steps`; tool thất bại không tạo nghĩa vụ dẫn URL incident không tồn tại.

Nguyên nhân H3 chủ yếu là lựa chọn tool và suy luận từ dữ liệu bị giới hạn; xử lý bằng prompt. Kiểm tra URL là điều kiện trong loop. Không tăng giới hạn dữ liệu, không hard-code ID hoặc case, không sửa fixtures/eval/grading để tăng điểm.

## Kiểm tra và điều kiện đạt

- Các tests gốc về source validation đã đạt. Bản kiểm tra ngay sau sửa: 43/43 tests, 0 lỗi; log ở `artifacts/cp5_improved/unit_tests.txt`.
- Thử API riêng H3: 100/100, lưu tại `artifacts/cp5_improved/h3_smoke.json` và bản sao trong `artifacts/cp5_improved/`. Đây là một case, không thay thế toàn bộ eval CP6.
- Bản code và SHA-256 lưu trong `artifacts/cp5_improved/manifest.json`.
- Tests demo bổ sung được ghi nhận riêng trong audit cuối; không làm mất bản kết quả 43/43 ban đầu.

**Đạt CP5 khi:** `NOTES.md` mục 1–3 có lỗi, trace, nguyên nhân và thay đổi thật; toàn bộ tests chạy cuối không còn failure/error. Kết quả đối chiếu cuối có trong `artifacts/checkpoint_audit.json`.

## Giới hạn

Validation chỉ kiểm tra có ít nhất một URL incident đã quan sát trong câu trả lời, chưa chứng minh mọi nhận định đều có nguồn hoặc mọi incident được dẫn đầy đủ. Prompt hướng dẫn chọn tool không phải một bảo đảm tuyệt đối. CP6 sẽ đánh giá lại cùng bộ 22 case và ghi cả cải thiện lẫn hồi quy.

## Hồi quy phát hiện khi đánh giá bản cải tiến đầu

Bản cải tiến đầu đạt 95,55/100; H3 tăng lên 100 nhưng H2 giảm từ 99 xuống 50. Trong H2, agent chỉ đọc incident đã resolved mà không gọi `get_status` để kiểm tra trạng thái Actions tại thời điểm snapshot. Đây là hai câu hỏi khác nhau, cần hai nguồn quan sát khác nhau.

Đã bổ sung một quy tắc chung: nếu câu hỏi vừa đề cập ID incident vừa hỏi trạng thái dịch vụ/component, cần kiểm tra status riêng; trạng thái một incident lịch sử không thay thế trạng thái dịch vụ. Không hard-code case H2 hoặc ID vào agent.

Toàn bộ kết quả 22 case và code của bản cải tiến đầu được giữ ở `artifacts/cp5_v1/`, không sửa điểm hoặc trộn case để tạo bản cuối. Bản `eval_after.json` cuối là một lượt đầy đủ mới với cùng cấu hình. Việc đã dùng bộ eval để phát hiện và sửa lỗi làm tăng nguy cơ quá khớp; đây không phải đánh giá trên tập kiểm thử độc lập.
