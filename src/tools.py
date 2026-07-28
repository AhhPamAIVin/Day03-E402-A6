"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

# Thứ tự 4 nhóm câu hỏi trắc nghiệm (dùng để ghép 12 câu trả lời đúng vị trí)
GROUP_ORDER = ["career_interest", "work_style", "personal_strength", "career_value"]

# Bộ 12 câu hỏi cố định: mỗi nhóm 3 câu, mỗi câu gắn 1 nhãn nhóm nghề để chấm điểm.
# Trên cả 12 câu, mỗi nhóm nghề (công nghệ/kinh doanh/sáng tạo/xã hội) xuất hiện đúng 3 lần.
QUIZ_QUESTIONS = {
    "career_interest": [
        ("Bạn có hứng thú với việc tìm hiểu công nghệ mới, lập trình hay không?", "công nghệ"),
        ("Bạn có hứng thú với việc kinh doanh, bán hàng hay khởi nghiệp không?", "kinh doanh"),
        ("Bạn có hứng thú với thiết kế, viết lách hay sáng tác nội dung không?", "sáng tạo"),
    ],
    "work_style": [
        ("Bạn thích làm việc độc lập, tập trung giải quyết vấn đề kỹ thuật?", "công nghệ"),
        ("Bạn thích môi trường cạnh tranh, nhiều deadline, kết quả đo đếm được?", "kinh doanh"),
        ("Bạn thích làm việc nhóm, hỗ trợ và tương tác trực tiếp với người khác?", "xã hội"),
    ],
    "personal_strength": [
        ("Bạn tự nhận thấy mình giỏi tư duy logic, phân tích số liệu?", "công nghệ"),
        ("Bạn tự nhận thấy mình có óc sáng tạo, gu thẩm mỹ tốt?", "sáng tạo"),
        ("Bạn tự nhận thấy mình giỏi lắng nghe, thấu hiểu cảm xúc người khác?", "xã hội"),
    ],
    "career_value": [
        ("Bạn coi trọng thu nhập cao và cơ hội thăng tiến nhanh?", "kinh doanh"),
        ("Bạn coi trọng sự tự do thể hiện bản thân trong công việc?", "sáng tạo"),
        ("Bạn coi trọng việc công việc tạo giá trị/tác động tích cực cho cộng đồng?", "xã hội"),
    ],
}

# Thông tin chi tiết từng nghề: nhóm ngành, mô tả, trình độ tối thiểu, lương, kỹ năng cần có.
CAREER_DETAILS = {
    "Lập trình viên": {
        "field": "công nghệ", "salary": "15-30 triệu",
        "progression": "Junior -> Middle -> Senior Developer -> Tech Lead",
        "roadmap": ["Nền tảng lập trình (Python/C)", "Cấu trúc dữ liệu & giải thuật cơ bản",
                    "Git & làm việc nhóm", "SQL & cơ bản về Database", "Làm dự án cá nhân/thực tập"],
    },
    "Kỹ sư phần mềm": {
        "field": "công nghệ", "salary": "20-40 triệu",
        "progression": "Fresher -> Software Engineer -> Senior Engineer -> Engineering Manager",
        "roadmap": ["Lập trình hướng đối tượng (Java/C++)", "Cấu trúc dữ liệu & giải thuật nâng cao",
                    "Thiết kế hệ thống cơ bản", "Kiểm thử phần mềm (Unit Test)", "Tham gia dự án lớn/thực tập"],
    },
    "Chuyên viên phân tích dữ liệu": {
        "field": "công nghệ", "salary": "18-35 triệu",
        "progression": "Data Analyst -> Senior Analyst -> Data Scientist -> Analytics Manager",
        "roadmap": ["SQL", "Thống kê & xác suất cơ bản", "Excel/Google Sheets nâng cao",
                    "Công cụ trực quan hóa (Power BI/Tableau)", "Python cho phân tích dữ liệu (Pandas)"],
    },
    "Nhân viên kinh doanh": {
        "field": "kinh doanh", "salary": "10-20 triệu",
        "progression": "Nhân viên kinh doanh -> Trưởng nhóm kinh doanh -> Sales Manager",
        "roadmap": ["Kỹ năng giao tiếp & thuyết trình", "Kiến thức sản phẩm/thị trường",
                    "Kỹ năng đàm phán & chốt sale", "Sử dụng công cụ CRM cơ bản", "Thực tập/thử việc vị trí sales"],
    },
    "Chuyên viên marketing": {
        "field": "kinh doanh", "salary": "12-25 triệu",
        "progression": "Marketing Executive -> Marketing Manager -> Marketing Director",
        "roadmap": ["Kiến thức marketing căn bản (4P)", "Content marketing", "Marketing số (SEO/Ads cơ bản)",
                    "Công cụ phân tích thị trường (Google Analytics)", "Thực hành 1 chiến dịch nhỏ"],
    },
    "Quản lý dự án": {
        "field": "kinh doanh", "salary": "20-40 triệu",
        "progression": "Coordinator -> Project Manager -> Program Manager -> PMO Director",
        "roadmap": ["Kiến thức quản lý dự án căn bản", "Lập kế hoạch & quản lý tiến độ",
                    "Công cụ quản lý dự án (Trello/Jira)", "Kỹ năng lãnh đạo nhóm", "Quản lý rủi ro dự án"],
    },
    "Thiết kế đồ họa": {
        "field": "sáng tạo", "salary": "12-25 triệu",
        "progression": "Junior Designer -> Designer -> Senior Designer -> Art Director",
        "roadmap": ["Nguyên lý thiết kế cơ bản (màu sắc, bố cục)", "Photoshop/Illustrator",
                    "Thiết kế bộ nhận diện thương hiệu", "Xây dựng portfolio cá nhân", "Nhận dự án thực tế/freelance nhỏ"],
    },
    "Content creator": {
        "field": "sáng tạo", "salary": "8-20 triệu",
        "progression": "Content Creator -> Content Lead -> Creative Strategist",
        "roadmap": ["Kỹ năng viết nội dung cơ bản", "Dựng/edit video cơ bản (CapCut/Premiere)",
                    "Kiến thức SEO cơ bản", "Xây dựng kênh cá nhân", "Phân tích hiệu quả nội dung (insight)"],
    },
    "Đạo diễn sáng tạo": {
        "field": "sáng tạo", "salary": "20-35 triệu",
        "progression": "Junior Creative -> Creative Director -> Executive Creative Director",
        "roadmap": ["Kỹ năng kể chuyện (storytelling)", "Kiến thức sản xuất hình ảnh/video",
                    "Quản lý ê-kíp nhỏ", "Phát triển ý tưởng (concept) cho dự án", "Dẫn dắt 1 dự án sáng tạo thực tế"],
    },
    "Giáo viên": {
        "field": "xã hội", "salary": "10-18 triệu",
        "progression": "Giáo viên -> Tổ trưởng chuyên môn -> Hiệu phó/Hiệu trưởng",
        "roadmap": ["Kiến thức chuyên môn môn giảng dạy", "Nghiệp vụ sư phạm cơ bản",
                    "Kỹ năng soạn giáo án", "Thực hành đứng lớp/dạy thử", "Kỹ năng quản lý lớp học"],
    },
    "Chuyên viên tư vấn tâm lý": {
        "field": "xã hội", "salary": "15-25 triệu",
        "progression": "Tư vấn viên -> Chuyên viên tâm lý -> Trưởng phòng tham vấn",
        "roadmap": ["Kiến thức tâm lý học cơ bản", "Kỹ năng lắng nghe chủ động",
                    "Đạo đức nghề nghiệp trong tư vấn", "Thực hành tư vấn có giám sát", "Kỹ năng đánh giá/case study"],
    },
    "Nhân viên công tác xã hội": {
        "field": "xã hội", "salary": "9-15 triệu",
        "progression": "Nhân viên công tác xã hội -> Điều phối viên chương trình -> Quản lý dự án cộng đồng",
        "roadmap": ["Kiến thức công tác xã hội cơ bản", "Kỹ năng giao tiếp & hỗ trợ cộng đồng",
                    "Quản lý ca (case management)", "Thực tập tại tổ chức xã hội", "Kỹ năng làm việc đa văn hóa"],
    },
}

def _flatten_field_tags() -> list:
    """Ghép nhãn nhóm nghề của 12 câu hỏi theo đúng thứ tự GROUP_ORDER."""
    tags = []
    for group in GROUP_ORDER:
        for _, field_tag in QUIZ_QUESTIONS[group]:
            tags.append(field_tag)
    return tags


def _find_career(career_name: str):
    """Tìm nghề trong CAREER_DETAILS, khớp không phân biệt hoa/thường."""
    if career_name in CAREER_DETAILS:
        return career_name, CAREER_DETAILS[career_name]
    key = (career_name or "").strip().lower()
    for name, info in CAREER_DETAILS.items():
        if name.lower() == key:
            return name, info
    return None, None

def get_quiz_question(group_name: str) -> str:
    """
    Trả về 3 câu hỏi trắc nghiệm của 1 nhóm trong bộ test đầu vào (12 câu / 4 nhóm).

    Args:
        group_name (str): Một trong GROUP_ORDER =
            ['career_interest', 'work_style', 'personal_strength', 'career_value'].

    Returns:
        str: 3 câu hỏi của nhóm (thang điểm 1-5 mỗi câu), hoặc 'LỖI:' nếu
             group_name không hợp lệ.

    Side effect: Read-only, dữ liệu câu hỏi cố định.
    """
    if group_name not in QUIZ_QUESTIONS:
        return f"LỖI: Nhóm câu hỏi '{group_name}' không hợp lệ (phải là một trong {GROUP_ORDER})."

    questions = [q for q, _ in QUIZ_QUESTIONS[group_name]]
    return f"Nhóm '{group_name}' ({len(questions)} câu, thang điểm 1-5):\n" + "\n".join(
        f"{i}. {q}" for i, q in enumerate(questions, start=1)
    )

def analyze_quiz_and_recommend_careers(answers: list) -> str:
    """
    Chấm điểm 12 câu trả lời (theo đúng thứ tự GROUP_ORDER, mỗi nhóm 3 câu),
    xác định nhóm nghề có điểm cao nhất và trả về danh sách nghề thuộc nhóm đó.

    Args:
        answers (list[int]): 12 điểm số (mỗi câu 1-5), thứ tự khớp với
            get_quiz_question() lần lượt theo GROUP_ORDER.

    Returns:
        str: Nhóm nghề phù hợp nhất (kèm breakdown điểm) + danh sách tên nghề
             thuộc nhóm đó, hoặc 'LỖI:' nếu answers sai số lượng/thang điểm.

    Side effect: Read-only.
    """
    tags = _flatten_field_tags()
    if not isinstance(answers, list) or len(answers) != len(tags):
        return f"LỖI: Cần trả lời đủ {len(tags)} câu hỏi (mỗi câu điểm 1-5)."

    if any(not isinstance(a, int) or a < 1 or a > 5 for a in answers):
        return "LỖI: Mỗi câu trả lời phải là số nguyên trong khoảng 1-5."

    scores = {}
    for tag, value in zip(tags, answers):
        scores[tag] = scores.get(tag, 0) + value

    best_field = max(scores, key=scores.get)
    breakdown = ", ".join(f"{field}: {score}" for field, score in scores.items())
    careers = [name for name, info in CAREER_DETAILS.items() if info["field"] == best_field]

    return (
        f"Nhóm nghề phù hợp nhất: '{best_field}' (điểm chi tiết: {breakdown}).\n"
        f"Danh sách nghề thuộc nhóm '{best_field}':\n" + "\n".join(f"- {c}" for c in careers)
    )

def get_career_profile(career_name: str) -> str:
    """
    Lấy CHỈ những thông tin "khó"/cần update liên tục mà LLM không nên tự
    bịa: mức lương tham khảo và lộ trình thăng tiến. Kiến thức chung về nghề
    (kỹ năng cần có, công việc hàng ngày, mô tả tổng quan...) KHÔNG thuộc
    phạm vi tool này — system prompt sẽ yêu cầu model tự trả lời phần đó
    bằng hiểu biết sẵn có, chỉ gọi tool này để lấy số liệu grounded.

    Args:
        career_name (str): Tên nghề (vd: 'Lập trình viên'), thường lấy từ
            danh sách trả về bởi analyze_quiz_and_recommend_careers().

    Returns:
        str: Lương tham khảo + lộ trình thăng tiến, hoặc 'LỖI:' nếu không
             tìm thấy nghề trong hệ thống.

    Side effect: Read-only.
    """
    name, info = _find_career(career_name)
    if info is None:
        return f"LỖI: Không tìm thấy thông tin nghề nghiệp '{career_name}'."

    return (
        f"{name} — Lương tham khảo: {info['salary']}\n"
        f"Lộ trình thăng tiến: {info['progression']}"
    )


def generate_learning_roadmap(career_name: str) -> str:
    """
    Trả về lộ trình học kỹ năng thực tế, theo đúng thứ tự nên học, để phục vụ
    tốt cho nghề này (vd: Lập trình viên -> nền tảng lập trình -> Git -> SQL...).
    Đây là data cứng theo từng nghề cụ thể để đảm bảo thứ tự nhất quán, không
    phải bậc học vấn (trung học/cao đẳng/đại học).

    Args:
        career_name (str): Tên nghề muốn theo đuổi.

    Returns:
        str: Danh sách bước học kỹ năng theo đúng thứ tự, hoặc 'LỖI:' nếu
             không tìm thấy nghề.

    Side effect: Read-only.
    """
    name, info = _find_career(career_name)
    if info is None:
        return f"LỖI: Không tìm thấy thông tin nghề nghiệp '{career_name}'."

    steps = "\n".join(f"Bước {i}: {s}" for i, s in enumerate(info["roadmap"], start=1))
    return f"Lộ trình học kỹ năng để làm {name}:\n{steps}"


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_quiz_question": get_quiz_question,
    "analyze_quiz_and_recommend_careers": analyze_quiz_and_recommend_careers,
    "get_career_profile": get_career_profile,
    "generate_learning_roadmap": generate_learning_roadmap,
}
