"""
CẤP ĐỘ 1: RULE-BASED CAREER BOT

Minh họa chatbot dựa trên luật: nhanh, không cần API key, nhưng chỉ xử lý
được một số ý định đã được lập trình sẵn.
"""

from __future__ import annotations

import unicodedata


OUT_OF_SCOPE_MESSAGE = (
    "Mình chỉ hỗ trợ các câu hỏi về định hướng nghề nghiệp, ngành học, "
    "kỹ năng và lộ trình phát triển. Bạn muốn khám phá sở thích nghề nghiệp "
    "hay tìm hiểu một nghề cụ thể?"
)


def _normalize(text: str) -> str:
    """Chuẩn hóa tiếng Việt để khớp từ khóa ổn định hơn."""
    normalized = unicodedata.normalize("NFD", text or "")
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.lower().strip()


def is_career_related(user_input: str) -> bool:
    """Kiểm tra nhanh câu hỏi có thuộc phạm vi định hướng nghề nghiệp không."""
    text = _normalize(user_input)
    career_keywords = (
        "nghe", "nganh", "su nghiep", "huong nghiep", "viec lam", "ky nang",
        "lo trinh", "hoc gi", "luong", "cv", "phong van", "so thich",
        "diem manh", "chuyen nganh", "cong viec",
    )
    greetings = ("chao", "hello", "hi ", "xin chao")
    return any(keyword in text for keyword in career_keywords + greetings)


def rule_based_bot(user_input: str) -> str:
    """Trả lời bằng các luật cố định, không sử dụng LLM hoặc tool."""
    text = _normalize(user_input)

    if not text:
        return "Bạn hãy nhập câu hỏi về định hướng nghề nghiệp nhé."
    if any(word in text for word in ("chao", "hello", "xin chao")):
        return (
            "Xin chào! Mình là CareerBot cấp 1. Mình có thể giải thích cách "
            "chọn ngành, gợi ý câu hỏi tự khám phá và hướng dẫn bước bắt đầu."
        )
    if not is_career_related(user_input):
        return OUT_OF_SCOPE_MESSAGE
    if "dinh huong" in text or "huong nghiep" in text or "chon nganh" in text:
        return (
            "Bạn hãy bắt đầu bằng 4 nhóm thông tin: sở thích, phong cách làm "
            "việc, điểm mạnh và giá trị nghề nghiệp. Cấp độ 1 chưa thể tự chấm "
            "bài khảo sát; hãy dùng ReAct Agent để làm bài test 12 câu."
        )
    if "cong nghe thong tin" in text or text.endswith(" cntt"):
        return (
            "Công nghệ Thông tin là nhóm ngành nghiên cứu và ứng dụng máy tính, "
            "phần mềm, dữ liệu và hệ thống thông tin để giải quyết vấn đề."
        )
    if "lo trinh" in text or "hoc gi" in text:
        return (
            "Lộ trình chung: tìm hiểu nghề → học kiến thức nền → làm dự án nhỏ "
            "→ xin phản hồi từ người trong nghề → điều chỉnh mục tiêu."
        )
    if "luong" in text:
        return (
            "Mức lương phụ thuộc nghề, kinh nghiệm và địa điểm. Cấp độ 1 không "
            "có dữ liệu để tra cứu; hãy nêu tên nghề cụ thể cho ReAct Agent."
        )
    return (
        "Mình hiểu đây là câu hỏi nghề nghiệp nhưng tập luật hiện tại chưa đủ "
        "để tư vấn cá nhân hóa. Hãy thử ReAct Agent hoặc mô tả rõ nghề bạn quan tâm."
    )


if __name__ == "__main__":
    print("=== DEMO CẤP ĐỘ 1: RULE-BASED CAREER BOT ===")
    for query in (
        "Chào bạn",
        "Ngành Công nghệ Thông tin là gì?",
        "Tôi muốn được định hướng nghề nghiệp",
        "Viết một bài thơ về mùa thu",
    ):
        print(f"User: {query}")
        print(f"Bot : {rule_based_bot(query)}\n")
