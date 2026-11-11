# CP4: eval lần 1

## Mục tiêu và kết luận checkpoint

CP4 yêu cầu chạy eval lần đầu trên đủ 22 case, đọc `summary`, `grade.reason`, `grade.mechanical`, answer và trace, rồi lập danh sách lỗi. CP4 chưa yêu cầu triển khai cải tiến hoặc chạy eval sau cải tiến.

**Kết luận: đạt điều kiện kỹ thuật CP4.** `eval_before.json` có đủ 22/22 case được chấm, `summary.score_0_100=96.73` khác `null`; đã phân tích H3 và các điểm cần xem lại. Đây là kết quả tự đối chiếu checkpoint, không phải điểm bài lab chính thức.

| Yêu cầu CP4 | Kết quả thực tế | Bằng chứng |
|---|---|---|
| Chạy đủ dataset | 22 case E1–E6, A1–A8, H1–H8. | `eval_before.json`: `summary.total_cases=22`. |
| Chấm được toàn bộ | 22 scored, 0 unscored, điểm tổng 96,73. | `summary.scored_cases`, `summary.unscored_cases`, `summary.score_0_100`. |
| Đọc lý do và kiểm tra bằng code | H3 thiếu tool chi tiết, bị áp trần 50. | H3: `grade.reason`, `grade.mechanical.violations`, trace và answer. |
| Có danh sách lỗi | H3 xác minh ID chưa đủ; A5/H8 diễn đạt phạm vi kết quả chưa rõ; H5 suy luận từ danh sách component rỗng. | Phân tích bên dưới; `NOTES.md` mục 1–2. |
| Hiểu giới hạn kết quả | `completed` không đồng nghĩa đúng; judge chỉ là ước lượng. | Mục giới hạn bên dưới. |

CP3 được trình bày riêng tại [CP3_DANH_GIA.md](CP3_DANH_GIA.md). Bản agent đã qua CP3 được giữ nguyên trong suốt lượt eval CP4.

## Eval lần đầu

Thử cấu hình agent và judge bằng E2 trước: 100/100, gọi `get_status` rồi `get_incident_details`, phân biệt đúng phạm vi FedRAMP. Kết quả ở `eval_results_cp3_e2.json`.

Lệnh chạy đủ bộ:

```powershell
python with_env.py evals/run_evals.py --max-steps 8 --workers 2 --output eval_before.json
```

Agent và judge cùng `claude-opus-5`, provider `openai` qua CKEY, dataset `core`, snapshot cố định, max steps 8. Hai workers là số case chạy đồng thời.

Kết quả: **96,73/100**, đủ **22/22 case được chấm**, không có `unscored`. Tất cả runs có status `completed`, không có `error` hoặc `max_steps`.

| Nhóm | Điểm từng case |
|---|---|
| E1–E6 | 100, 100, 100, 100, 100, 100 |
| A1–A8 | 97, 100, 100, 100, 95, 97, 100, 98 |
| H1–H8 | 99, 99, 50, 100, 98, 99, 99, 97 |

- Agent: 56 model calls, 47 tool calls, 43.170 token được API báo.
- Judge: 22 calls có usage, 33.616 token được API báo.
- Tổng: 76.786 token, không gồm smoke test E2 và các phép thử trước đó.
- Metadata gateway có trường `cost` nhưng chưa xác minh đơn vị/tiền tệ, nên không quy đổi thành USD hoặc coi là hóa đơn.

## Lỗi H3 và hướng CP5

Agent chỉ gọi `get_status(provider="cloudflare", component="")`, không gọi `get_incident_details` với ID người dùng cung cấp. Tool trả số lượng 50 incident khớp nhưng chỉ hiển thị 5 mục; không thể dựa vào danh sách hiển thị này để nói đã xác minh ID không có trong toàn bộ 50 incident. Vì vậy kết luận về ID vượt quá bằng chứng đã đọc.

Agent không xác nhận Cloudflare sập toàn cầu và không bịa URL incident. Tuy nhiên, mechanical check ghi thiếu `get_incident_details` và áp trần 50; judge cũng chấm 50. Chưa sửa hoặc chạy lại case này.

Hướng CP5: khi người dùng cung cấp ID cụ thể, hướng dẫn model tra trực tiếp bằng tool chi tiết trước khi kết luận; nếu không tìm thấy thì nêu giới hạn và hỏi thêm ID/thời gian đúng. Đồng thời hoàn thiện validation URL nguồn để vượt qua hai tests còn lại. Không hard-code ID, câu trả lời hoặc case H3 vào agent.

## Giới hạn khi đọc kết quả

A5 và H8 diễn đạt chưa rõ việc tìm trong 50 incident nhưng chỉ hiển thị tối đa 5. H5 nói không có component đang gặp sự cố trong khi danh sách component rỗng chưa đủ để kết luận điều đó. Điểm judge cao không thay thế việc đọc trace.

Agent và judge cùng model có thể thiên lệch. Một lượt eval không chứng minh độ ổn định. Snapshot không chứng minh trạng thái live hiện tại. Đây là bản kết quả tại mốc CP4; các bước sau được ghi riêng trong `CP5_DANH_GIA.md`, `CP6_DANH_GIA.md` và `NOTES.md`. Bản số liệu CP4 ở `artifacts/cp3_baseline/eval_summary.json`.
