# CP3: xử lý lỗi và trace

Tài liệu này giữ kết quả tại mốc CP3 trước cải tiến. Kết quả tests cuối và trạng thái hiện tại được ghi riêng trong `CP5_DANH_GIA.md` và `artifacts/checkpoint_audit.json`.

## Mục tiêu và kết luận checkpoint

CP3 yêu cầu agent có giới hạn bước, xử lý lỗi và trace đủ để debug. Phần này được kiểm tra bằng tests offline, không dùng điểm eval để kết luận đạt CP3.

**Kết luận: đạt điều kiện kỹ thuật CP3.** Lệnh tests chạy 43 test, 41 đạt; chỉ còn hai test kiểm tra nguồn thuộc Bài 4/CP5 chưa đạt, đúng mốc tự kiểm tra trong `CHECKPOINTS.md`. Đây chưa phải xác nhận điểm của giảng viên.

| Yêu cầu CP3 | Việc đã làm | Bằng chứng |
|---|---|---|
| Giới hạn bước | Giới hạn số lần gọi model, hết budget trả `max_steps`. | `agent.py`; `LoopTests.test_max_steps`. |
| JSON lỗi | Trả `INVALID_ARGUMENTS` cho model, không crash. | `LoopTests.test_invalid_json_sent_back_to_model`; test JSON không phải object trong `test_cp3.py`. |
| Tool lỗi | Đưa lỗi thành observation; một call lỗi không bỏ sót các call còn lại. | Tests tool timeout và partial failure trong `test_cp3.py`. |
| Model bị cắt | `finish=length` trả `error`, không báo hoàn thành. | `LoopTests.test_model_truncation_is_not_completed`; test finish bất thường. |
| Provider lỗi | Kết thúc run bằng `error`, ghi loại lỗi vào trace. | `RobustnessTests.test_provider_exception_stops_without_disclosing_message`. |
| Trace đúng format | Có `event`, `step`; tool event có `name`, `arguments`, `result`. | `agent.py`, các tests loop và full trajectory. |

**Cần giải thích:** lỗi tool trả lại model để model có thể sửa hoặc báo thiếu dữ liệu; lỗi provider hoặc output bị cắt kết thúc run; hết budget là `max_steps`. Trace không yêu cầu model công khai chain-of-thought.

Kết quả chạy 22 case thuộc **CP4**, được trình bày riêng tại [CP4_DANH_GIA.md](CP4_DANH_GIA.md).

## Cấu hình và phạm vi

API chính là `claude-opus-5` qua CKEY, dùng giao thức OpenAI-compatible. Key nằm trong `.env` được Git bỏ qua. Không cài framework agent hoặc thay đổi cấu hình Codex toàn máy.

## Xử lý lỗi và trace

| Tình huống | Cách xử lý |
|---|---|
| JSON arguments sai hoặc không phải object | Trả `INVALID_ARGUMENTS`, giữ đúng tool-call ID để model có thể sửa. |
| Tool không tồn tại, provider status không hợp lệ, tool timeout | Registry trả observation lỗi; loop đưa về model, không coi lỗi lấy dữ liệu là outage. |
| Tool ném exception ngoài registry | Trả loại exception, không sao chép nội dung exception có thể chứa thông tin nhạy cảm. |
| Một call lỗi trong response nhiều calls | Vẫn trả kết quả cho mọi call trước model call tiếp theo. |
| Lỗi API model | Dừng với `status=error`, ghi `provider_error` và loại exception vào trace. |
| `finish=length` | Trả `OUTPUT_TRUNCATED`, không thực thi calls có thể bị cắt. |
| Finish bất thường hoặc thiếu calls | Dừng với `error`, ghi event lỗi. |
| Hết budget | Trả `max_steps` và event cùng tên; mỗi step là một lần gọi model. |
| Budget không phải số nguyên dương | Trả `INVALID_MAX_STEPS` trước khi gọi model. |

Trace gồm model step, finish reason, số calls, tên tool, arguments, result và các sự kiện lỗi. Không yêu cầu model in chain-of-thought. Usage lưu theo từng model response thành công; token của request thất bại không quan sát được đầy đủ.

## Tests offline

```powershell
python -m unittest discover -s tests -v
```

Kết quả: **43 tests, 41 đạt, 2 không đạt, không có test error**. Hai test chưa đạt là:

- `EvidenceGateTests.test_missing_url_gets_revision_within_budget`.
- `EvidenceGateTests.test_missing_url_at_budget_limit_is_not_completed`.

Đây là validation nguồn của CP5. Kết quả đáp ứng checkpoint CP3 theo `CHECKPOINTS.md`, chưa đáp ứng yêu cầu toàn bộ tests đạt của CP5 và checklist nộp bài.

Sáu tests mới ở `tests/test_cp3.py` kiểm tra thêm các nhánh lỗi. Tests của đề được giữ nguyên. Log đầy đủ ở `artifacts/cp3_baseline/unit_tests.txt`.

## Bản mốc trước cải tiến

`artifacts/cp3_baseline/` lưu bản sao `agent.py`, `providers.py`, `with_env.py` và manifest SHA-256. Bản mốc chưa có validation nguồn. Manifest cũng lưu hash của fixtures, dataset, scenarios, grading và rubric để đối chiếu tính nguyên vẹn. Các hash đều khớp sau eval; không thay đổi code agent trong quá trình chạy.
