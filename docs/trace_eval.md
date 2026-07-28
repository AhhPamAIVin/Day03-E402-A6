# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

*Đề tài: AI định hướng nghề nghiệp — Role 5: Observability & Reviewer*

---

## 1. Bảng chấm điểm Agentic Fit

| Tiêu chí | Điểm (1–5) | Bằng chứng trong hệ thống |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Luồng đầy đủ gồm: lấy 4 nhóm câu hỏi → thu 12 điểm → chấm nhóm nghề → chọn nghề → tra lương/thăng tiến → tạo roadmap kỹ năng. Kết quả bước sau phụ thuộc dữ liệu bước trước. |
| 🛠️ **Tool Interaction** | `4/5` | Agent sử dụng 4 tool thật: `get_quiz_question`, `analyze_quiz_and_recommend_careers`, `get_career_profile`, `generate_learning_roadmap`. Observation do Python application chèn, không do LLM tự bịa. |
| 🔀 **Dynamic Decision** | `4/5` | Câu kiến thức chung được trả lời trực tiếp; yêu cầu định hướng gọi bộ câu hỏi; có đủ 12 điểm mới gọi tool phân tích; hỏi lương/thăng tiến và roadmap đi theo hai tool khác nhau. |
| ⏳ **Long Horizon** | `3/5` | Hệ thống giữ lịch sử hội thoại để hiểu các câu nối tiếp như “nghề này”, đồng thời cấp 4 có Planning và Memory trong phiên. Memory chưa được lưu bền vững qua lần khởi động lại. |
| **Tổng điểm Fit** | **15/20** | **Bài toán phù hợp để xây dựng theo mô hình AI Agent. Chatbot thuần vẫn phù hợp hơn cho các câu hỏi lý thuyết đơn giản.** |

---

## 2. Môi trường và phương pháp kiểm tra

- **Ngày kiểm tra:** 28/07/2026.
- **Provider:** OpenAI, model cấu hình khi chạy: `gpt-4o`.
- **Guardrail:** `MAX_ITERATIONS = 6`, timeout mỗi tool `10 giây`.
- **Phương pháp:** tool test deterministic, HTTP API test cục bộ, parser/guardrail test có kiểm soát và một lượt chạy trực tiếp bằng OpenAI.
- **Bảo mật:** API key chỉ đọc từ biến môi trường `OPENAI_API_KEY`; key không xuất hiện trong trace hoặc tài liệu này.

---

## 3. Kết quả kiểm tra Tool độc lập

Lệnh kiểm tra: `python src/app.py --mode tools`

| Kiểm tra | Kết quả | Ghi chú |
| :--- | :---: | :--- |
| `get_quiz_question(career_interest)` | ✅ Pass | Trả đúng 3 câu, thang điểm 1–5. |
| `get_quiz_question(work_style)` | ✅ Pass | Trả đúng 3 câu. |
| `get_quiz_question(personal_strength)` | ✅ Pass | Trả đúng 3 câu. |
| `get_quiz_question(career_value)` | ✅ Pass | Trả đúng 3 câu. |
| `analyze_quiz_and_recommend_careers` với 12 điểm hợp lệ | ✅ Pass | Trả nhóm nghề, breakdown điểm và danh sách nghề. |
| `analyze_quiz_and_recommend_careers` với thiếu điểm | ✅ Pass | Trả chuỗi `LỖI:`, application không crash. |
| `get_career_profile("Lập trình viên")` | ✅ Pass | Trả lương tham khảo và lộ trình thăng tiến. |
| `get_career_profile` với nghề không tồn tại | ✅ Pass | Trả chuỗi `LỖI:`, không bịa dữ liệu. |
| `generate_learning_roadmap("Lập trình viên")` | ✅ Pass | Trả đủ 5 bước kỹ năng theo thứ tự. |
| **Tổng** | **9/9 Pass** | **Tool layer hoạt động độc lập và có error semantics an toàn.** |

---

## 4. So sánh Chatbot Baseline và ReAct Agent — Test Case #3

**Câu hỏi:** “Tôi muốn được định hướng nghề nghiệp.”

### 4.1 Chatbot Baseline — chạy trực tiếp bằng OpenAI

**Số LLM call:** `1`
**Số tool call:** `0`

**Phản hồi thực tế (rút gọn, giữ nguyên ý):**

> Chatbot hỏi bốn câu chung về hoạt động yêu thích, môn học/lĩnh vực hứng thú, môi trường làm việc mong muốn và sở thích làm việc độc lập hay theo nhóm. Chatbot đề nghị người dùng trả lời để có thể gợi ý ngành nghề.

**Đánh giá:**

- Trả lời tự nhiên, phù hợp phạm vi.
- Không gọi tool nên không sử dụng bộ khảo sát chuẩn 12 câu của hệ thống.
- Không có Observation hay dữ liệu chấm điểm để làm bằng chứng.
- Phù hợp làm baseline và phù hợp với tư vấn khái quát, nhưng chưa đủ grounded cho luồng đánh giá chuẩn hóa.

### 4.2 ReAct Agent — trace trực tiếp bằng OpenAI sau khi sửa parser

**Kết quả định lượng:**

| Chỉ số | Giá trị |
| :--- | :---: |
| Iterations | `6` |
| Tool calls thành công | `4` |
| Nhóm câu hỏi lấy được | `4/4` |
| Observation từ application | `4` |
| Guardrail triggered | `Không` |
| Final Answer | `Có` |

**Trace:**

```text
Question: Tôi muốn được định hướng nghề nghiệp.

Step 1
Thought: Cần bắt đầu bằng nhóm câu hỏi về sở thích nghề nghiệp.
Action: get_quiz_question[career_interest]
Observation: Nhóm 'career_interest' gồm 3 câu hỏi, thang điểm 1-5.

Step 2
Action: get_quiz_question[group_name="work_style"]
Observation: Nhóm 'work_style' gồm 3 câu hỏi, thang điểm 1-5.

Step 3
Action: get_quiz_question[personal_strength]
Observation: Nhóm 'personal_strength' gồm 3 câu hỏi, thang điểm 1-5.

Step 4
Action: get_quiz_question[group_name="career_value"]
Observation: Nhóm 'career_value' gồm 3 câu hỏi, thang điểm 1-5.

Step 5
Model trả câu trả lời tự nhiên nhưng thiếu nhãn "Final Answer:".
Observation: LỖI PARSER: Phản hồi không có Action hoặc Final Answer.

Step 6
Thought: Đã có đủ thông tin để trả lời.
Final Answer: Người dùng đã có đủ bộ câu hỏi và được yêu cầu trả lời
12 câu theo thang điểm 1-5 để tiếp tục phân tích nghề nghiệp.
```

**Nhận xét:**

- Agent gọi đúng thứ tự bốn nhóm tool và nhận dữ liệu thật từ `tools.py`.
- Hai biến thể tham số đều được parser hỗ trợ:
  - `get_quiz_question[career_interest]`
  - `get_quiz_question[group_name="work_style"]`
- Bước 5 cho thấy parser recovery hoạt động: output sai format không làm application crash; lỗi được đưa lại thành Observation và model tự sửa ở bước 6.
- Agent dùng hết 6 vòng nhưng vẫn tạo Final Answer đúng trong giới hạn, vì vậy guardrail không phải cưỡng chế ngắt.

### 4.3 Chấm Test Case #3 theo rubric

| Tiêu chí | Điểm (0–2) | Lý do |
| :--- | :---: | :--- |
| Factual correctness | `2/2` | Hiển thị đúng 12 câu từ dữ liệu tool. |
| Grounding | `2/2` | Có 4 Observation thật từ application. |
| Tool selection | `2/2` | Gọi đúng `get_quiz_question` cho đủ 4 nhóm. |
| Termination | `2/2` | Tự phục hồi lỗi format và kết thúc ở vòng 6, không crash. |
| **Tổng** | **8/8** | **Đạt yêu cầu ReAct Agent cho test case này.** |

---

## 5. Failed Trace → Root Cause → Agent V2

### 5.1 Failed trace phát hiện khi chạy OpenAI lần đầu

```text
Step 1
Action: get_quiz_question[career_interest]
Observation: Thành công.

Step 2
Action: get_quiz_question[group_name="work_style"]
Observation: LỖI: group_name nhận nguyên chuỗi
'group_name="work_style"' nên không khớp GROUP_ORDER.

Step 3-6
Model lặp lại cùng Action.
Observation: Repeated-action guardrail chặn thực thi lại.

Safe fallback
Agent dừng ở MAX_ITERATIONS = 6, không crash và không bịa kết quả.
```

**Số liệu failed run:** `6 iterations`, `2 tool calls`, `guardrail triggered = Có`.

### 5.2 Root Cause Analysis

| Thành phần | Phân tích |
| :--- | :--- |
| Hiện tượng | Prompt mô tả dạng `tool[tham_số]`, nhưng model hợp lý hóa thành cú pháp keyword `tool[group_name="value"]`. |
| Root cause | Parser chỉ loại bỏ dấu nháy, chưa tách tiền tố `group_name=`/`career_name=`/`answers=`. |
| Rủi ro | Tool nhận sai chuỗi nghiệp vụ; model tiếp tục thử lại và tiêu hết iteration budget. |
| Guardrail đã bảo vệ | Repeated-action detection ngăn tool bị gọi lặp vô hạn; `MAX_ITERATIONS` tạo safe fallback. |

### 5.3 Bản sửa Agent V2

Parser được nâng cấp để chấp nhận an toàn cả positional và keyword-style:

```text
get_quiz_question[work_style]
get_quiz_question[group_name="work_style"]

get_career_profile[Lập trình viên]
get_career_profile[career_name="Lập trình viên"]

analyze_quiz_and_recommend_careers[[1, 2, ...]]
analyze_quiz_and_recommend_careers[answers=[1, 2, ...]]
```

Parser dùng `ast.literal_eval`, không dùng `eval`. Sau sửa, cùng câu hỏi đã lấy thành công đủ `4/4` nhóm câu hỏi và tạo Final Answer.

---

## 6. Guardrails và khả năng chịu lỗi

| Failure mode | Cơ chế phòng vệ | Kết quả kiểm tra |
| :--- | :--- | :---: |
| Unknown tool | Trả Observation liệt kê các tool hợp lệ. | ✅ Pass |
| Malformed arguments | Parser/`TypeError` được chuyển thành Observation. | ✅ Pass |
| Keyword-style arguments | Chuẩn hóa tên tham số trước khi gọi tool. | ✅ Pass |
| Repeated Action | Lưu action key đã gọi, không thực thi lại cùng tool + arguments. | ✅ Pass |
| Tool exception | Bắt exception và trả chuỗi `LỖI:`. | ✅ Pass |
| Tool chạy quá lâu | Timeout `10 giây`. | ✅ Có guardrail |
| Vòng lặp vô hạn | Dừng tại `MAX_ITERATIONS = 6`. | ✅ Pass |
| OpenAI mất kết nối | Trả thông báo kiểm tra key/model/mạng, không crash. | ✅ Pass |
| Câu hỏi ngoài phạm vi | Prompt yêu cầu Final Answer từ chối lịch sự, không gọi tool. | ✅ Có guardrail |

---

## 7. Kiểm tra giao diện Web Chatbot

Giao diện được kiểm tra qua HTTP server cục bộ, không đưa API key xuống browser.

| Hạng mục | Kết quả |
| :--- | :---: |
| Trang web chatbot tải thành công | ✅ |
| Bootstrap trả đúng 4 nhóm / 12 câu hỏi | ✅ |
| Chat cấp 1 hoạt động không cần OpenAI | ✅ |
| API phân tích 12 điểm trả danh sách nghề | ✅ |
| API lương & thăng tiến hoạt động | ✅ |
| API roadmap 5 bước hoạt động | ✅ |
| Trace panel nhận dữ liệu Action/Observation | ✅ |
| Responsive sidebar và quiz modal có trong UI | ✅ |

**Tổng kiểm tra Web API:** `Pass` cho HTML, bootstrap, level 1 chat, quiz analysis, career profile và learning roadmap.

---

## 8. Kết luận

1. Baseline Chatbot phù hợp với hỏi đáp và tư vấn chung vì chỉ cần một LLM call.
2. ReAct Agent vượt trội khi cần dùng bộ câu hỏi chuẩn, chấm điểm, tra dữ liệu nghề và tạo roadmap có căn cứ.
3. Failed trace thực tế chứng minh parser và guardrails là thành phần bắt buộc, không chỉ là yêu cầu lý thuyết.
4. Agent V2 đã tự phục hồi được biến thể cú pháp từ OpenAI, không crash và không lặp vô hạn.
5. Giao diện web giúp người dùng tiếp cận luồng Agent như một chatbot thông thường, còn trace vẫn có thể mở khi cần quan sát hoặc trình bày bài Lab.
