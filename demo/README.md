# Demo trực quan CP2–CP7

Chạy ở thư mục Day04:

```powershell
python with_env.py demo/server.py
```

Mở http://127.0.0.1:8504. Không cần cài thư viện bổ sung.

## Các mục trên giao diện

- **CP2:** nhập câu hỏi, gọi API thật, quan sát model/tool và ID; có nút đọc lại log cũ.
- **CP3:** chạy mô phỏng offline lỗi JSON, timeout, output bị cắt và hết bước. FakeProvider được ghi rõ, không phải API thật.
- **CP4:** xem đủ 22 kết quả trước cải tiến và mở trace từng case.
- **CP5:** xem lỗi H3 trước/sau; mô phỏng thiếu URL thực thi đúng agent loop và event `validation_missing_source`.
- **CP6:** so sánh toàn bộ case, điểm, token, model calls và cấu hình trước/sau.
- **CP7:** bảng gate của từng CP, bằng chứng và link GitHub; LMS do người học tự nộp.
- **BONUS:** điểm bộ 10 case và trace từng case đã lưu; không gọi API khi xem.

Khi có dữ liệu mới, dùng nút làm mới trên giao diện. Các file eval gốc không bị sửa bởi demo. Chỉ CP2 có nút gọi API thật; các mục đọc bằng chứng không tự chạy lại toàn bộ eval.

Chọn tình huống và bấm chạy API thật để xem từng model call, tool call và observation. Key đọc từ `.env` phía máy chủ, không đưa xuống trình duyệt. Dữ liệu tool là snapshot 09/11/2026, không phải trạng thái live hiện tại.

Ba tình huống minh họa một tool, điều tra hai bước và đối chiếu hai nhà cung cấp. Model tự quyết định thứ tự calls. Giao diện quan sát cùng `run_agent` hiện tại, bao gồm xử lý lỗi CP3 và validation nguồn CP5. Không thay đổi prompt hoặc code agent để phục vụ demo.

Tự kiểm tra CP2: có tool call, model nhận lại observation gắn đúng ID, mọi calls của một lượt được trả kết quả trước model call tiếp theo, cuối cùng `status=completed`. Các chỉ báo này không chấm tính đúng đắn của toàn bộ câu trả lời và không thay thế unit tests hoặc eval 22 case.

Nút xem log đã lưu đọc kết quả Opus từ lần thử CP2 trước, không gọi API. Log cũ không lưu đủ message IDs nên hai kiểm tra ID được ghi là chưa quan sát, không suy đoán đạt. Lần chạy thật có ghi nhận IDs ở ranh giới provider.

Có thể tải transcript JSON. Bản chạy mới cũng được lưu vào `demo_runs/`, được Git bỏ qua. Không tự động dùng log demo làm kết quả eval hoặc đưa vào báo cáo chấm điểm.
