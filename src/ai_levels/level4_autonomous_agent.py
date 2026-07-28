"""
CẤP ĐỘ 4: AUTONOMOUS CAREER AGENT

Thêm Planning, Memory và tự đánh giá tiến độ lên trên ReAct Agent cấp 3.
Memory chỉ tồn tại trong phiên chạy, không lưu thông tin cá nhân ra ổ đĩa.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_levels.level3_reactive_agent import AgentResult, run_reactive_agent


@dataclass
class MemoryEntry:
    goal: str
    user_message: str
    answer: str
    completed: bool
    tool_calls: int


@dataclass
class AutonomousResult:
    goal: str
    plan: list[str]
    answer: str
    evaluation: str
    agent_result: AgentResult


@dataclass
class AutonomousCareerAgent:
    """Agent có mục tiêu, kế hoạch và bộ nhớ hội thoại trong phiên."""

    provider: Any
    goal: str = "Xây dựng định hướng nghề nghiệp phù hợp và có bước tiếp theo rõ ràng"
    memory: list[MemoryEntry] = field(default_factory=list)

    def _plan(self, user_input: str) -> list[str]:
        """Lập kế hoạch deterministic để hành vi dễ kiểm thử và giải thích."""
        text = user_input.lower()
        if re.search(r"(12|điểm|câu trả lời|\[[\d,\s]+\])", text):
            return [
                "Kiểm tra người dùng đã cung cấp đủ 12 điểm hợp lệ chưa",
                "Chấm điểm và xác định nhóm nghề phù hợp",
                "Đề xuất bước tìm hiểu sâu hoặc lộ trình tiếp theo",
            ]
        if any(keyword in text for keyword in ("lộ trình", "học như thế nào", "học gì")):
            return [
                "Xác định nghề đang được nhắc đến từ hội thoại",
                "Tra cứu lộ trình học có căn cứ",
                "Đưa ra hành động học tập tiếp theo",
            ]
        if any(keyword in text for keyword in ("lương", "thăng tiến", "thu nhập")):
            return [
                "Xác định chính xác nghề người dùng quan tâm",
                "Tra mức lương và lộ trình thăng tiến trong dữ liệu hệ thống",
                "Giải thích kết quả tham khảo và giới hạn của số liệu",
            ]
        if any(keyword in text for keyword in ("kỹ năng", "công việc", "mô tả", "nghề này")):
            return [
                "Xác định nghề và nhu cầu thông tin của người dùng",
                "Dùng kiến thức nền để giải thích tổng quan, không gọi tool số liệu",
                "Đề xuất một bước trải nghiệm nghề thực tế",
            ]
        return [
            "Làm rõ sở thích, phong cách làm việc, điểm mạnh và giá trị nghề nghiệp",
            "Thu thập dữ liệu bằng bài khảo sát 12 câu nếu cần",
            "Đề xuất nghề và một bước kiểm chứng thực tế",
        ]

    def _history(self) -> list[dict[str, str]]:
        history: list[dict[str, str]] = []
        for entry in self.memory[-5:]:
            history.extend(
                [
                    {"role": "user", "content": entry.user_message},
                    {"role": "assistant", "content": entry.answer},
                ]
            )
        return history

    def execute(self, user_input: str) -> AutonomousResult:
        """Lập kế hoạch, giao việc cho ReAct Agent, đánh giá và lưu memory."""
        plan = self._plan(user_input)
        result = run_reactive_agent(
            user_query=user_input,
            provider=self.provider,
            history=self._history(),
        )
        completed = not result.guardrail_triggered
        evaluation = (
            "Hoàn thành: đã tạo câu trả lời trong giới hạn an toàn."
            if completed
            else "Chưa hoàn thành: guardrail đã dừng vòng lặp; cần người dùng làm rõ."
        )
        self.memory.append(
            MemoryEntry(
                goal=self.goal,
                user_message=user_input,
                answer=result.answer,
                completed=completed,
                tool_calls=result.tool_calls,
            )
        )
        return AutonomousResult(
            goal=self.goal,
            plan=plan,
            answer=result.answer,
            evaluation=evaluation,
            agent_result=result,
        )

    def clear_memory(self) -> None:
        """Xóa bộ nhớ hội thoại trong phiên."""
        self.memory.clear()


if __name__ == "__main__":
    from providers import get_llm_provider

    agent = AutonomousCareerAgent(get_llm_provider("openai"))
    output = agent.execute("Tôi muốn được định hướng nghề nghiệp.")
    print("Kế hoạch:")
    for index, item in enumerate(output.plan, start=1):
        print(f"{index}. {item}")
    print(f"\n{output.answer}\n{output.evaluation}")
