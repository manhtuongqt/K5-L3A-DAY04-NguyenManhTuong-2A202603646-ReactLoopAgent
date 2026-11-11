# CP6 · Eval lần hai và so sánh

## Điều kiện checkpoint

Chạy lại đủ 22 case, giữ nguyên cấu hình và snapshot, so sánh điểm, trace, số lượt gọi và token; điền `NOTES.md` mục 4–5. Không yêu cầu điểm sau phải cao hơn, nhưng phải giải thích kết quả thật và lỗi còn lại.

**Kết luận: đạt điều kiện kỹ thuật CP6.** Cả hai file đều chấm đủ 22/22 case, không có `unscored`, khối `config` giống nhau; các file dữ liệu và grading giữ nguyên. Không có run `error` hoặc `max_steps` ở hai bộ chính.

## Cách chạy

```powershell
python with_env.py evals/run_evals.py --max-steps 8 --workers 2 --output eval_after.json
```

Cấu hình trước/sau: provider `openai` qua CKEY, agent model và judge model đều `claude-opus-5`, max steps 8, dataset `core`, snapshot GitHub/Cloudflare không đổi. Hai workers là số case chạy đồng thời.

## Kết quả

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Tổng điểm judge | 96,73 | 96,27 |
| Case được chấm | 22/22 | 22/22 |
| H3 — tra ID incident | 50 | 100 |
| H2 — kiểm tra cả incident và dịch vụ | 99 | 100 |
| A1 — đối chiếu GitHub/Cloudflare | 97 | 53 |
| Model calls của agent | 56 | 53 |
| Tool calls | 47 | 41 |
| Token agent + judge do API báo | 76.786 | 67.214 |

Điểm tổng giảm **0,46 điểm**. Token giảm **9.572**, nhưng số token ít hơn không tự chứng minh agent tốt hơn: A1 đã bỏ sót thông tin cần đọc.

Chi tiết đủ 22 case trong [bảng so sánh](artifacts/cp6_case_comparison.md) và [JSON](artifacts/cp6_comparison.json). Không bỏ case giảm điểm hoặc thay từng case bằng một lần chạy khác.

## Đọc trace

- **H3 được sửa:** bản trước chỉ gọi `get_status`; bản sau gọi `get_incident_details` với ID đã nêu và nhận kết quả không tìm thấy trong phạm vi tool. Câu trả lời không bịa URL hay xác nhận outage toàn cầu.
- **H2 được giữ đúng sau chỉnh tiếp:** bản cuối gọi cả tool chi tiết và `get_status`, phân biệt resolved của incident với trạng thái dịch vụ/component ở mốc snapshot.
- **A1 hồi quy:** query component là `Cloudflare Spectrum`, trong khi tool tìm chuỗi và dữ liệu dùng tên `Spectrum`; agent không đọc được incident Spectrum ở Phoenix đang monitoring. Judge chấm 53 vì thiếu trạng thái, phạm vi và URL của incident cần đối chiếu. Đây là lỗi về tìm kiếm/lựa chọn bằng chứng còn lại; không khẳng định agent đã giải quyết tốt mọi trường hợp.
- **E5 còn suy luận mạnh hơn nguồn:** nguồn ghi đang điều tra báo cáo hiệu năng ở một số dịch vụ, trong khi câu trả lời diễn đạt như ảnh hưởng đã được xác nhận. Case đạt 90, vẫn cần giữ mức chắc chắn đúng với câu chữ của nguồn.

## Bản cải tiến trung gian

Trước bản cuối có một lượt đủ 22 case đạt 95,55, trong đó H3 tăng 100 nhưng H2 giảm 50. Code, manifest và raw eval giữ nguyên ở `artifacts/cp5_v1/`. Sau khi đọc trace H2, bổ sung quy tắc kiểm tra status riêng khi câu hỏi yêu cầu cả trạng thái dịch vụ và incident, rồi chạy lại đủ bộ.

Việc có thêm lượt điều chỉnh này được công khai. Bản cuối không phải tập kiểm thử độc lập và không dùng kết quả trung gian để ghép thành điểm tốt hơn.

## Chi phí và giới hạn

Metadata CKEY có trường cost nhưng chưa xác minh đơn vị/tiền tệ. Vì vậy không ghi một con số USD hoặc coi đó là hóa đơn. Tổng token trong bảng không bao gồm smoke tests, lượt trung gian hoặc các lần thử cấu hình trước đó.

Judge là đánh giá xấp xỉ, cùng model với agent nên có thể thiên lệch. Một lần mỗi phiên bản không đo được độ ổn định; giảm hoặc tăng vài điểm có thể liên quan biến động model/judge. Kết quả hiện tại cho phép nói lỗi H3 đã được xử lý trong lượt quan sát này, chưa đủ để nói accuracy toàn bộ hoặc độ tin cậy thực tế đã tăng.

Hash hai kết quả ở `artifacts/cp6_integrity.json`; audit cấu hình, tests và dữ liệu ở `artifacts/checkpoint_audit.json`. CP7 được báo cáo riêng.
