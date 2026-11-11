# Chạy agent cơ bản CP2

Tài liệu này giữ hướng dẫn và kết quả ở mốc CP2. Bản agent hiện tại đã có xử lý lỗi CP3 và validation CP5; xem `CP5_DANH_GIA.md`, `CP6_DANH_GIA.md` và `CP7_NOP_BAI.md` để biết trạng thái cuối. Các số tests 12/12 bên dưới là kết quả lịch sử của bộ tests cơ bản, không phải tổng số tests cuối.

## Cấu hình cục bộ

File `.env` chứa `PROVIDER`, `MODEL`, `OPENAI_BASE_URL`, `OPENAI_API_KEY` và được Git bỏ qua. Model đang cấu hình là `gemini-2.5-flash-lite` qua gateway CKEY, địa chỉ `https://api.xah.io/v1`. Đây là tên model do gateway cung cấp, không phải xác nhận độc lập về backend.

Không nhập key vào `.env.example`. File này chỉ chứa mẫu cấu hình công khai.

`providers.py` hỗ trợ `OPENAI_BASE_URL` khi provider là `openai`; nếu không đặt biến này thì vẫn dùng endpoint OpenAI mặc định. Không dùng key CKEY với endpoint OpenAI chính thức.

## Lệnh chạy trong PowerShell

Mở terminal ở thư mục repo:

```powershell
python with_env.py run.py "GitHub Actions hiện có sự cố không? Hãy kiểm tra incident gần đây."
python -m unittest discover -s tests -p test_lab.py -v
```

`with_env.py` đọc `.env` thành biến môi trường cho tiến trình con, không chạy nội dung file như mã shell. Không cần cài thêm package. Khi dùng launcher này, cấu hình trong `.env` được ưu tiên hơn biến môi trường có sẵn.

## Loop hoạt động thế nào

1. Tạo messages chứa system prompt và câu hỏi.
2. Gọi `provider.complete(messages, SCHEMAS)`.
3. Giữ nguyên assistant message, ghi trace và usage.
4. Nếu có tool calls, parse JSON, gọi `tools.execute` và trả từng kết quả đúng `tool_call_id`.
5. Xử lý hết các calls rồi mới gọi model tiếp.
6. Khi model dừng bằng `stop` và không còn calls, trả `completed`; hết budget trả `max_steps`; dừng bất thường hoặc lỗi provider trả `error`.

Một step tính theo lần gọi model. Loop có xử lý lỗi cơ bản để không crash khi arguments sai hoặc tool ném exception. Chưa triển khai validation nguồn của CP5.

## Kết quả kiểm tra ngày 11/11/2026

- 12/12 tests trong `tests/test_lab.py` đạt. Đây là tests offline, không phải accuracy của model.
- API thật qua CKEY: `completed`, 2 lần gọi model và 1 lần gọi `get_status` trên snapshot. Trace và answer được lưu trong `artifacts/cp2/cp2_run.json`.
- Đây không phải dữ liệu trạng thái live: snapshot GitHub được chụp ngày 09/11/2026.
- Câu trả lời chạy thử còn nói “hiện đang” mà chưa nêu mốc snapshot và thiếu URL nguồn. Đây là hạn chế quan sát được, chưa phải kết quả eval CP4 hay chứng nhận câu trả lời đúng hoàn toàn.
- Chưa chạy bộ eval 22 case, chưa hoàn thành CP5 hoặc toàn bộ lab.

Không sửa fixtures, eval cases, scenarios, grading hoặc tests của đề.

## Thử model CKEY bổ sung

- `artifacts/cp2/ckey_model_probe.json`: cả `tranhieu13102003/gpt-6-luna` và `claude-opus-5` trả native tool call qua Chat Completions. Opus cũng phản hồi tool-use qua Messages API trong phép thử riêng.
- `artifacts/cp2/ckey_cp2_comparison.json`: cùng câu hỏi đọc status rồi chi tiết incident. Opus hoàn thành sau 3 model calls, gọi đủ hai tools; Luna gặp lỗi provider trước khi có model response thành công.
- Trace: `artifacts/cp2/cp2_ckey_opus_run.json` và `artifacts/cp2/cp2_ckey_luna_run.json`. Chỉ một lượt mỗi model, không suy ra accuracy hoặc độ ổn định.
- `PROVIDER=openai` chỉ giao thức tương thích, không có nghĩa model thuộc OpenAI. Tên model/backend là thông tin gateway cung cấp, chưa xác minh độc lập.
- Adapter gửi User-Agent `StatusAgentLab/1.0`. Các probe dùng User-Agent mặc định Python từng bị HTTP 403; chưa đủ bằng chứng quy mọi lỗi 403 về một nguyên nhân.
- Không chạy trình cài đặt từ xa hoặc thay đổi cấu hình Codex toàn máy.
