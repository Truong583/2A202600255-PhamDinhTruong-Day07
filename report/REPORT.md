# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Phạm Đình Trường]
**Nhóm:** [VinFast_C2]
**Ngày:** [10/04/2026]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity nghĩa là hai vector đại diện cho hai đoạn văn bản đang hướng về cùng một phía trong không gian đa chiều, cho thấy chúng có sự tương đồng rất lớn về mặt nội dung hoặc ngữ nghĩa.

**Ví dụ HIGH similarity:**
- Sentence A: Tôi rất thích ăn trái táo.
- Sentence B: Quả táo là loại trái cây khoái khẩu của tôi.
- Tại sao tương đồng: Dù sử dụng từ ngữ và cấu trúc khác nhau, cả hai câu đều cùng diễn đạt một ý nghĩa về sở thích cá nhân đối với việc ăn táo.

**Ví dụ LOW similarity:**
- Sentence A: Tôi rất thích ăn trái táo.
- Sentence B: Giá cổ phiếu của công ty Apple hôm nay giảm mạnh.
- Tại sao khác: Mặc dù cả hai đều chứa từ "táo/Apple", nhưng ngữ cảnh hoàn toàn khác nhau (một bên là thực phẩm, một bên là thị trường tài chính), dẫn đến hướng của hai vector này rất xa nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity được ưu tiên vì nó chỉ quan tâm đến hướng của vector (ngữ nghĩa) mà không bị ảnh hưởng bởi độ lớn (độ dài của văn bản). Điều này giúp so sánh chính xác hai tài liệu có nội dung giống nhau nhưng độ dài ký tự khác nhau đáng kể.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* > Sử dụng công thức: num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))
> num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)
> *Đáp án:* 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunk sẽ tăng lên thành 25 (ceil(9900 / 400)). Việc tăng overlap giúp duy trì ngữ cảnh liên tục giữa các đoạn cắt, tránh việc thông tin quan trọng bị chia cắt đột ngột ở ranh giới giữa hai chunk, giúp mô hình AI hiểu tài liệu tốt hơn.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Hệ thống hỗ trợ giải đáp chính sách bán hàng và hậu mãi xe điện VinFast (2026).

**Tại sao nhóm chọn domain này?**
> Các chính sách ưu đãi, voucher và quy định về trạm sạc của VinFast thường có cấu trúc phức tạp với nhiều điều kiện áp dụng khắt khe. Việc sử dụng RAG giúp nhân viên và khách hàng truy xuất chính xác các con số thực tế (fact-level), tránh nhầm lẫn giữa các mốc thời gian và dòng xe khác nhau.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | tailieu.md | Chính sách VinFast | 4,500 | `category: sales_policy` |
| 2 | customer_support_playbook.txt | Quy trình hỗ trợ | 3,200 | `category: support_guide` |
| 3 | rag_system_design.md | Tài liệu kỹ thuật | 5,800 | `category: technical_doc` |
| 4 | vi_retrieval_notes.md | Ghi chú nghiên cứu | 2,100 | `category: research_note` |
| 5 | chunking_experiment_report.md | Báo cáo thí nghiệm | 3,500 | `category: experiment` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | String | `sales_policy` | Giúp thu hẹp phạm vi tìm kiếm (filtering) vào đúng nhóm tài liệu liên quan, tránh nhiễu thông tin từ các tài liệu kỹ thuật. |
| `source_file` | String | `tailieu.md` | Hỗ trợ việc truy vết nguồn gốc thông tin và cho phép thực hiện các thao tác xóa hoặc cập nhật theo file. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu `tailieu.md`:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| tailieu.md | FixedSizeChunker (`fixed_size`) | 12 | 400 | No (Dễ cắt ngang các điều khoản quan trọng) |
| tailieu.md | SentenceChunker (`by_sentences`) | 15 | 320 | Partial (Giữ trọn vẹn ý nghĩa từng câu đơn) |
| tailieu.md | RecursiveChunker (`recursive`) | 9 | 480 | Yes (Giữ đúng cấu trúc đoạn văn và danh sách) |

### Strategy Của Tôi

**Loại:** RecursiveChunker (Separator-based).

**Mô tả cách hoạt động:**
> Chiến thuật này sử dụng một danh sách các dấu phân cách ưu tiên như `\n\n`, `\n`, và dấu cách để chia nhỏ văn bản một cách có hệ thống. Thuật toán hoạt động đệ quy: đầu tiên thử cắt theo đoạn văn để bảo tồn tính toàn vẹn của chủ đề, và chỉ khi đoạn đó vẫn vượt quá `chunk_size` thì mới tiếp tục băm nhỏ bằng các dấu phân cách cấp thấp hơn cho đến khi đạt kích thước mục tiêu.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Các chính sách bán hàng thường trình bày dưới dạng đoạn văn kèm danh sách liệt kê các điều kiện (bullet points). RecursiveChunker giúp giữ các điều khoản liên quan ở lại cùng một chunk, tránh tình trạng thông tin về ưu đãi bị tách rời khỏi thông tin về dòng xe áp dụng.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| tailieu.md | best baseline (Sentence) | 15 | 320 | Khá tốt nhưng dễ mất liên kết đoạn |
| tailieu.md | của tôi (Recursive) | 9 | 480 | Tốt nhất (Bảo toàn được logic chính sách) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phạm Đình Trường | RecursiveChunker| 3 | Bảo toàn ngữ cảnh theo cấu trúc tự nhiên (đoạn văn, câu); giữ được tính logic của các điều khoản. | Mock embedder làm giảm chất lượng truy xuất thực tế; cần tinh chỉnh Separators. |
| Phạm Việt Hoàng | Recursive (OpenAI API) | 8 | Đưa ra khá đúng ngữ nghĩa trong đa số trường hợp; chunk có độ dài ổn định. | Chi phí API và phụ thuộc vào kết nối mạng bên ngoài. |
| Bùi Minh Ngọc | SentenceChunker | 6 | Giữ nguyên ý nghĩa từng điều khoản, không cắt đứt câu văn giữa chừng. | Chunk có thể rất dài nếu câu văn dài; bảng Markdown bị xử lý kém. |
| Phan Tuấn Minh | CustomChunker + Local Embed | 6 | Giữ nguyên bảng giá, không bị cắt ngang giữa chừng. | Chunk lớn (755 ký tự); thỉnh thoảng embedding bị khớp nhầm từ khóa. |
| Thùy Linh | Parent-Child / Small-to-Big | 4 | Bảo toàn ngữ cảnh toàn bộ policy; cân bằng tốt giữa lấy fact và bối cảnh. | Cần metadata filtering để tối ưu; Mock embedder làm giảm chất lượng truy xuất. |
| Việt Anh | SentenceChunker | 3 | Phân mảnh dựa trên đơn vị câu giúp giữ trọn vẹn ý nghĩa từng phát biểu; cấu trúc gọn gàng. | Dễ làm mất ngữ cảnh liên kết giữa các câu; hiệu quả tìm kiếm thấp do Embedder. |
| Lê Đức Thanh | SentenceChunker | 0/5 (top-3) | Giữ ý theo câu, dễ đọc và dễ giải thích cho người dùng cuối. | Chưa tối ưu nếu câu quá dài hoặc tài liệu chứa nhiều bảng dữ liệu. |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Với dữ liệu chính sách VinFast, strategy cho kết quả tốt nhất là **RecursiveChunker kết hợp Semantic Embedding (OpenAI API)** của bạn Hoàng vì đạt điểm retrieval cao nhất (8/10). Việc chia nhỏ dựa trên cấu trúc tự nhiên giúp duy trì tính logic, trong khi mô hình nhúng mạnh giúp vượt qua rào cản tìm kiếm từ khóa thô mà Mock Embedder mắc phải. Tuy nhiên, hướng tiếp cận **Parent-Child / Small-to-Big** cũng rất tiềm năng nếu được nâng cấp chất lượng embedder và thêm metadata filtering.

---
## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Mình dùng Regex `(?<=[.!?])\s+` để tách câu dựa trên dấu chấm, hỏi, than mà không làm mất dấu câu đó. Cách này xử lý tốt các câu dính liền nhau và mình dùng thêm `strip()` để dọn dẹp khoảng trắng thừa cho từng chunk.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán sẽ thử cắt văn bản theo danh sách dấu phân cách từ lớn đến nhỏ (như `\n\n`, `\n`, rồi đến dấu cách). Nếu một đoạn vẫn quá dài, hàm sẽ tự gọi lại chính nó (đệ quy) để băm nhỏ tiếp cho đến khi đạt kích thước mục tiêu.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Dữ liệu được mình lưu trong một danh sách các Dictionary ngay trên RAM để truy xuất nhanh. Khi tìm kiếm, mình tính tích vô hướng (Dot Product) giữa các vector để đo độ tương đồng, sau đó sắp xếp lấy ra những kết quả có điểm số cao nhất.

**`search_with_filter` + `delete_document`** — approach:
> Mình thực hiện lọc metadata trước (pre-filtering) để thu hẹp phạm vi rồi mới tính similarity, giúp hệ thống chạy nhanh hơn. Với hàm xóa, mình dùng List Comprehension để loại bỏ tất cả các chunk có `doc_id` tương ứng ra khỏi kho lưu trữ.

### KnowledgeBaseAgent

**`answer`** — approach:
> Mình lấy các chunk liên quan nhất nối lại thành một khối ngữ cảnh (context) rồi nhét vào Prompt theo mẫu có sẵn. Trong Prompt, mình quy định rõ AI chỉ được trả lời dựa trên thông tin này để tránh việc nó tự "chế" ra câu trả lời không có trong tài liệu.

### Test Results

```
# Paste output of: pytest tests/ -v
```
=========================================== test session starts ===========================================
platform win32 -- Python 3.13.1, pytest-9.0.3, pluggy-1.6.0 -- D:\Lab07\Day-07-Lab-Data-Foundations\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Lab07\Day-07-Lab-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                [  2%] 
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                         [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                  [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                   [  9%] 
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                        [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED        [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED              [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED               [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED             [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                               [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED               [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                          [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                      [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED       [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED           [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED     [ 40%] 
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED           [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                               [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                 [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                   [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                         [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED              [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                [ 57%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED    [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                 [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                          [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                         [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                    [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED           [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED               [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                     [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED               [ 80%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 
83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED          [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED         [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

=========================================== 42 passed in 0.45s ============================================ 
**Số tests pass:** 42/ 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chương trình voucher Giờ Trái Đất áp dụng khi nào? | Đoạn văn bản chứa thông tin về mốc thời gian đặt cọc xe tháng 3/2026. | High | 0.825 | Đúng |
| 2 | Giá trị voucher cho xe VF 8 là bao nhiêu? | Danh sách ưu đãi voucher cho các dòng xe điện VinFast. | High | 0.794 | Đúng |
| 3 | Chính sách Mua xe 0 Đồng vay tối đa bao nhiêu %? | Hướng dẫn xử lý lỗi thanh toán billing (billing errors). | High | 0.155 | Sai |
| 4 | Ưu đãi cho VF 8 trong Tương lai Xanh là gì? | Tài liệu thiết kế hệ thống trợ lý ảo nội bộ (RAG System Design). | High | 0.172 | Sai |
| 5 | Chính sách ưu đãi sạc pin áp dụng như thế nào? | Ghi chú về cách tìm kiếm tài liệu tiếng Việt (Retrieval notes). | High | 0.146 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là sự chênh lệch điểm số cực lớn giữa các chunk chứa từ khóa đúng (0.825) và các chunk không liên quan (0.146), dù cùng sử dụng Mock Embedder. Điều này cho thấy hệ thống hiện tại đang phụ thuộc rất nhiều vào việc khớp từ khóa thô; nếu câu hỏi không chứa các từ khóa trùng lặp với tài liệu, Embeddings sẽ không thể nhận diện được sự tương đồng về ngữ nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|---|---|
| 1 | Chương trình voucher Giờ Trái Đất áp dụng cho khách hàng trong thời gian nào? | Áp dụng cho khách hàng đặt cọc mua xe trong các giai đoạn 20-22/03/2026 và 26-30/03/2026, đồng thời xuất hóa đơn đến hết ngày 30/06/2026. |
| 2 | Giá trị voucher dành cho dòng xe VF 8 trong chương trình Giờ Trái Đất là bao nhiêu? | Giá trị voucher của VF 8 là 15.000.000 VNĐ. |
| 3 | Chính sách “Mua xe 0 Đồng” cho phép khách hàng vay tối đa bao nhiêu phần trăm giá trị xe? | Khách hàng được vay tối đa 100% giá trị xe và không cần vốn đối ứng. |
| 4 | Trong chương trình “Mãnh liệt vì Tương lai Xanh”, khách hàng mua VF 8 được hưởng những ưu đãi gì? | Khách hàng mua VF 8 được chọn một trong hai ưu đãi: giảm 10% MSRP hoặc hỗ trợ lãi suất cố định 5%/năm trong 3 năm đầu. |
| 5 | Chính sách ưu đãi sạc pin áp dụng như thế nào đối với xe mua từ ngày 10/02/2026? | Với xe mua từ ngày 10/02/2026, EC Van và Minio Green được miễn phí 20 lần sạc đầu tiên/xe/tháng tại trụ sạc V-Green đến hết 10/02/2029, còn các dòng xe khác được miễn phí 10 lần sạc đầu tiên/xe/tháng. |

### Kết Quả Của Tôi (Thử nghiệm thực tế)

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|---|---|---|---|---|
| 1 | Chương trình voucher Giờ Trái Đất áp dụng cho khách hàng trong thời gian nào? | `tailieu.md`: Đoạn văn bản chứa thông tin về các mốc thời gian đặt cọc xe tháng 3/2026. | 0.825 | **Yes** | Chương trình áp dụng cho khách đặt cọc từ 20-22/03 và 26-30/03/2026; hóa đơn xuất trước 30/06/2026. |
| 2 | Giá trị voucher dành cho dòng xe VF 8 trong chương trình Giờ Trái Đất là bao nhiêu? | `tailieu.md`: Danh sách ưu đãi voucher cho các dòng xe điện VinFast. | 0.794 | **Yes** | Theo tài liệu, voucher dành cho dòng xe VF 8 trong chương trình này có giá trị là 15.000.000 VNĐ. |
| 3 | Chính sách "Mua xe 0 Đồng" cho phép khách hàng vay tối đa bao nhiêu phần trăm giá trị xe? | `customer_support_playbook.txt`: Hướng dẫn xử lý lỗi thanh toán billing. | 0.155 | Không | Agent trả lời không biết vì tài liệu lấy ra chỉ nói về quy trình xử lý lỗi billing, không có thông tin về tỷ lệ vay vốn. |
| 4 | Trong chương trình "Mãnh liệt vì Tương lai Xanh", khách hàng mua VF 8 được hưởng những ưu đãi gì? | `rag_system_design.md`: Tài liệu thiết kế hệ thống trợ lý ảo nội bộ. | 0.172 | Không | Agent không tìm thấy thông tin ưu đãi cho VF 8; ngữ cảnh hiện tại đang nói về kiến trúc hệ thống RAG. |
| 5 | Chính sách ưu đãi sạc pin áp dụng như thế nào đối với xe mua từ ngày 10/02/2026? | `vi_retrieval_notes.md`: Ghi chú về cách tìm kiếm tài liệu tiếng Việt. | 0.146 | Không | Agent phản hồi không có dữ liệu về chính sách sạc pin trong các tài liệu được cung cấp. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 2 / 5

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được cách quản lý môi trường ảo (venv) và xử lý các lỗi đường dẫn script khi chạy trên Windows PowerShell sao cho mượt mà nhất. Ngoài ra, việc thống nhất cấu trúc thư mục `src` ngay từ đầu giúp cả nhóm phối hợp viết code và chạy `pytest` rất nhanh mà không bị xung đột module.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhìn demo của các nhóm khác, tôi thấy họ xử lý bài toán tìm kiếm tiếng Việt tốt hơn hẳn nhờ việc sử dụng các mô hình nhúng chuyên dụng thay vì dùng Mock. Họ cũng chia sẻ kinh nghiệm về việc tinh chỉnh tham số `overlap` tùy theo độ dài của từng loại văn bản pháp lý, điều mà trước đó tôi chưa thực sự chú trọng.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi chắc chắn sẽ thay thế bộ nhúng hiện tại bằng một mô hình nhúng chuyên dụng  để hệ thống có thể hiểu được sâu ngữ nghĩa của các thuật ngữ kỹ thuật VinFast. Đồng thời, tôi sẽ áp dụng kỹ thuật "Small-to-Big Retrieval" để vừa đảm bảo tìm kiếm chính xác mảnh thông tin nhỏ, vừa cung cấp đủ ngữ cảnh rộng cho Agent trả lời.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân |5 / 5 |
| Document selection | Nhóm |10 / 10 |
| Chunking strategy | Nhóm |14 / 15 |
| My approach | Cá nhân | 9/ 10 |
| Similarity predictions | Cá nhân |4 / 5 |
| Results | Cá nhân | 9/ 10 |
| Core implementation (tests) | Cá nhân |28 / 30 |
| Demo | Nhóm | 4/ 5 |
| **Tổng** | | **/ 100** |
