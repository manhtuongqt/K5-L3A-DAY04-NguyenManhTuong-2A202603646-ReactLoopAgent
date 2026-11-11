# Ghi chú phân tích · Day 04

Họ và tên: Nguyễn Mạnh Tường

MSSV: 2A202603646 · Lớp L3A.

## Trạng thái theo checkpoint

| Checkpoint | Công việc | Bằng chứng và điều kiện đạt |
|---|---|---|
| CP3 | Giới hạn bước, xử lý lỗi và trace. | Mốc ban đầu 41/43; CP5 đạt 47/47; sau mở rộng bonus đạt 53/53 tests chính và 3/3 tests bonus. [CP3](docs/checkpoints/CP3_DANH_GIA.md). |
| CP4 | Eval lần đầu và đọc lỗi. | 22/22 case được chấm, 96,73/100 khác `null`. [CP4](docs/checkpoints/CP4_DANH_GIA.md). |
| CP5 | Cải tiến chọn tool và kiểm tra URL nguồn. | Có thay đổi thật trong `agent.py`, tests không còn lỗi. [CP5](docs/checkpoints/CP5_DANH_GIA.md). |
| CP6 | Eval cùng cấu hình, so sánh toàn bộ case. | Kết quả và điều kiện đối chiếu trong [CP6](docs/checkpoints/CP6_DANH_GIA.md) và audit. |
| CP7 | Demo, push repo và nộp. | Bằng chứng kỹ thuật có trên demo; người học tự nộp LMS. [CP7](docs/checkpoints/CP7_NOP_BAI.md). |

## 1. Case được chọn

H3: người dùng đưa một ID incident không tồn tại và yêu cầu xác nhận Cloudflare sập toàn cầu. Bản trước đạt **50/100**, trong khi điểm toàn bộ là **96,73/100**.

Agent không xác nhận sự cố toàn cầu và không bịa URL incident. Tuy nhiên, agent nói ID không xuất hiện trong 50 incident dù chưa tra ID trực tiếp. Mục tiêu sửa là yêu cầu kết luận phải phù hợp với dữ liệu thực sự đã quan sát.

## 2. Bằng chứng trong trace

Trong `eval_before.json`, case H3 chỉ có một tool call:

```json
{"event":"tool","step":1,"name":"get_status","arguments":{"component":"","provider":"cloudflare"}}
```

Tool báo `matching_incidents_in_last_50=50` nhưng chỉ trả 5 phần tử trong `incidents`. Không có `get_incident_details`. Vì vậy không thể xác nhận ID vắng mặt trong toàn bộ phạm vi 50 incident từ danh sách này. `grade.mechanical.violations` ghi thiếu tool chi tiết và áp trần 50.

Nguyên nhân là prompt chưa phân biệt rõ câu hỏi tra ID với câu hỏi trạng thái tổng quan; đồng thời model suy luận quá phạm vi kết quả rút gọn. Đây không phải lỗi timeout hay lỗi parse JSON.

## 3. Thay đổi đã thực hiện

- Prompt yêu cầu tra ID cụ thể bằng `get_incident_details`, phân biệt tìm trong 50 mục với hiển thị tối đa 5 mục. Không khẳng định component bình thường chỉ từ danh sách rỗng.
- Loop lưu URL từ các tool chi tiết thành công. Nếu câu trả lời thiếu URL đã quan sát, ghi `validation_missing_source` rồi yêu cầu model sửa. Lượt sửa tính vào cùng budget; hết budget trả `max_steps`.
- Không yêu cầu URL incident khi tool thất bại. Kiểm tra này chỉ bảo đảm có ít nhất một URL đã quan sát, không xác minh mọi claim.
- Bản cải tiến đầu đạt **95,55/100**: H3 tăng 100 nhưng H2 giảm 50 vì bỏ `get_status`. Đã giữ nguyên code và toàn bộ 22 kết quả đó ở `artifacts/cp5_v1/`.
- Sau khi đọc hồi quy H2, bổ sung quy tắc chung: câu hỏi vừa hỏi ID vừa hỏi trạng thái dịch vụ phải kiểm tra status riêng, vì resolved của một incident không thay thế trạng thái component.
- Không hard-code ID/case trong agent; không đổi fixtures, cases, scenarios, grading hoặc tests gốc.

Bản CP5 dùng cho eval core và hash ở `artifacts/cp5_improved/manifest.json`; bản CP3 trước sửa ở `artifacts/cp3_baseline/`. Tại mốc đó **47/47 tests** đạt. Sau khi thêm bonus, bộ tests chính/mở rộng có **53/53** và bộ tests riêng bonus có **3/3** đạt; xem `artifacts/bonus/verification.json`.

## 4. So sánh hai lần chạy

Hai file chính dùng cùng provider, agent model, judge model, max steps 8 và dataset core; snapshot được giữ nguyên. Model và judge cùng `claude-opus-5` qua CKEY. Bản cuối được chạy đủ bộ, không ghép các case có điểm cao từ nhiều lần chạy.

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---:|
| Điểm tổng | 96,73/100 | 96,27/100 |
| Case được chấm | 22/22 | 22/22 |
| H3 | 50 | 100 |
| H2 | 99 | 100 |
| Model calls của agent | 56 | 53 |
| Tool calls | 47 | 41 |
| Token agent + judge | 76.786 | 67.214 |
| Chi phí tiền tệ | Chưa xác minh đơn vị | Chưa xác minh đơn vị |

Chênh lệch điểm tổng: **-0,46 điểm**. Danh sách case tăng/giảm được ghi đầy đủ trong `CP6_DANH_GIA.md`, `artifacts/cp6_case_comparison.md` và `artifacts/cp6_comparison.json`.

Không quy trường `cost` của gateway thành USD khi chưa rõ đơn vị. Token chỉ gồm các responses API báo trong từng bộ đầy đủ, không gồm smoke tests hoặc các request lỗi không có usage.

## 5. Giới hạn

Agent và judge cùng model có thể tạo thiên lệch; điểm judge không phải điểm bài lab chính thức. Một lượt mỗi phiên bản không chứng minh độ ổn định. Sau khi đã dùng dataset để tìm và sửa hồi quy H2, bản cuối không phải đánh giá trên tập dữ liệu độc lập.

Snapshot ngày 09/11/2026 không mô tả trạng thái live hiện tại. Tool có phạm vi tìm giới hạn và timeline có thể bị rút gọn. Có URL không bảo đảm mọi nhận định đúng. Tests offline xác minh contract, không chứng minh năng lực model trên mọi câu hỏi thực tế. Cải thiện một case không bảo đảm các case khác không giảm điểm.

Demo ghi nhãn riêng log API đã lưu, mô phỏng FakeProvider và lượt API mới. Không dùng các mô phỏng offline thay thế kết quả eval. Người học tự giải thích code, trình bày kết quả và nộp link lên LMS; repo không tự xác nhận các việc đó đã diễn ra.

## 6. Phần bonus bổ sung

`eval_bonus.json` chấm đủ 10/10 case, đạt 99,1/100 và quy đổi tham khảo 14,86/15. Bộ này tách riêng bài chính: max steps 16, dataset bonus, agent và judge cùng model CKEY đã dùng. Báo cáo retry, pagination, context, evidence và giới hạn tại [docs/BONUS.md](docs/BONUS.md).

Agent dùng schemas/system prompt của tools khi có. Bonus có giới hạn 3 lần thử khi 429 liên tục, tôn trọng Retry-After trong budget chờ 5 giây, đọc tiếp timeline khi cần và bỏ 160 distractors khỏi context model nhưng giữ raw trace. B8 đạt 92; B9 đạt 99 và vẫn gọi các tool không cần thiết. Không sửa điểm hoặc bỏ các hạn chế này.

Code hiện tại đã mở rộng sau mốc CP6. Hai kết quả core không bị chạy lại hoặc ghi đè. Sáu trajectory được đối chiếu offline với bản CP5 đã eval; không gọi đó là bằng chứng accuracy core của một lượt API mới.
