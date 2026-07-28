"""
CẤP ĐỘ 2: OPENAI LLM CAREER CHATBOT

Chatbot sinh câu trả lời tự nhiên bằng OpenAI nhưng tuyệt đối không gọi tool.
Đây là baseline dùng để so sánh công bằng với ReAct Agent.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from prompts import CHATBOT_BASELINE_PROMPT


def _format_history(history: Iterable[Mapping[str, str]] | None) -> str:
    """Chuyển lịch sử hội thoại thành ngữ cảnh text ngắn gọn."""
    if not history:
        return "(Chưa có lịch sử hội thoại)"
    lines = []
    for message in list(history)[-8:]:
        role = "Người dùng" if message.get("role") == "user" else "Trợ lý"
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) or "(Chưa có lịch sử hội thoại)"


def llm_chatbot(
    user_input: str,
    provider: Any,
    history: Iterable[Mapping[str, str]] | None = None,
) -> str:
    """
    Gọi đúng một lần LLM và không cung cấp bất kỳ tool nào.

    Args:
        user_input: Câu hỏi hiện tại.
        provider: Provider có phương thức ``generate(prompt, system_prompt)``.
        history: Lịch sử hội thoại tùy chọn để xử lý câu hỏi nối tiếp.

    Returns:
        Nội dung trả lời của OpenAI hoặc thông báo lỗi thân thiện.
    """
    if not isinstance(user_input, str) or not user_input.strip():
        return "Bạn hãy nhập một câu hỏi về định hướng nghề nghiệp."

    prompt = (
        "LỊCH SỬ HỘI THOẠI GẦN ĐÂY:\n"
        f"{_format_history(history)}\n\n"
        "CÂU HỎI HIỆN TẠI:\n"
        f"{user_input.strip()}\n\n"
        "Chỉ trả lời câu hỏi hiện tại. Không được tuyên bố rằng bạn đã gọi tool "
        "hoặc đã tra cứu dữ liệu bên ngoài."
    )
    response = provider.generate(prompt, system_prompt=CHATBOT_BASELINE_PROMPT)
    if not isinstance(response, str) or not response.strip():
        return "Mình chưa nhận được phản hồi từ OpenAI. Bạn vui lòng thử lại."
    return response.strip()


if __name__ == "__main__":
    from providers import get_llm_provider

    openai_provider = get_llm_provider("openai")
    print("=== DEMO CẤP ĐỘ 2: OPENAI LLM CHATBOT ===")
    print(llm_chatbot("Ngành Công nghệ Thông tin là gì?", openai_provider))
