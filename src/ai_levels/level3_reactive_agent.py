"""
CẤP ĐỘ 3: REACTIVE CAREER AGENT (Thought -> Action -> Observation)

Model quyết định bước tiếp theo theo REACT_SYSTEM_PROMPT của nhóm. Application
parse cú pháp ``tool[tham_số]``, thực thi tool thật và đưa Observation trở lại
model. Không có Observation nào do model tự tạo được tin cậy.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ToolTimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from prompts import MAX_ITERATIONS, REACT_SYSTEM_PROMPT, TIMEOUT_SECONDS
from tools import AVAILABLE_TOOLS


@dataclass
class AgentResult:
    """Kết quả có cấu trúc để CLI và GUI cùng sử dụng."""

    answer: str
    trace: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    tool_calls: int = 0
    guardrail_triggered: bool = False


def _format_history(history: Iterable[Mapping[str, str]] | None) -> str:
    """Giới hạn lịch sử gần nhất để prompt gọn nhưng vẫn hiểu “nghề này”."""
    if not history:
        return "(Chưa có lịch sử)"
    formatted = []
    for message in list(history)[-10:]:
        role = "Người dùng" if message.get("role") == "user" else "Trợ lý"
        content = str(message.get("content", "")).strip()
        if content:
            formatted.append(f"{role}: {content}")
    return "\n".join(formatted) or "(Chưa có lịch sử)"


def _extract_final_answer(model_output: str) -> str | None:
    match = re.search(r"Final\s*Answer\s*:\s*(.+)", model_output, flags=re.I | re.S)
    return match.group(1).strip() if match else None


def _parse_scalar(raw_value: str) -> str:
    """Parse chuỗi có/không có dấu nháy mà không dùng eval nguy hiểm."""
    value = raw_value.strip()
    if not value:
        raise ValueError("Tool đang thiếu tham số.")
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        parsed = value
    if not isinstance(parsed, str):
        parsed = str(parsed)
    return parsed.strip()


def _parse_answers(raw_value: str) -> list[Any]:
    """Chấp nhận cả tool[[1,...]] và tool[1,2,...]."""
    value = raw_value.strip()
    if not value:
        raise ValueError("Tool chấm điểm đang thiếu danh sách answers.")
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        try:
            parsed = ast.literal_eval(f"[{value}]")
        except (ValueError, SyntaxError) as exc:
            raise ValueError("answers phải là danh sách 12 số nguyên từ 1 đến 5.") from exc
    if isinstance(parsed, tuple):
        parsed = list(parsed)
    if not isinstance(parsed, list):
        parsed = [parsed]
    return parsed


def _extract_action(model_output: str) -> tuple[str, dict[str, Any]]:
    """
    Parse Action theo đúng prompt mới: ``tool[tham_số]``.

    Vẫn chấp nhận Action JSON của phiên bản cũ để Agent có khả năng tự phục hồi
    khi model trả định dạng khác nhưng không mơ hồ.
    """
    marker = re.search(r"Action\s*:\s*", model_output, flags=re.I)
    if not marker:
        raise ValueError("Phản hồi không có Action hoặc Final Answer.")
    action_text = model_output[marker.end():].strip()

    if action_text.startswith("{"):
        try:
            payload, _ = json.JSONDecoder().raw_decode(action_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Action JSON không hợp lệ: {exc.msg}.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Action JSON phải là object.")
        tool_name = payload.get("tool")
        arguments = payload.get("arguments", {})
        if not isinstance(tool_name, str) or not isinstance(arguments, dict):
            raise ValueError("Action JSON thiếu tool hoặc arguments hợp lệ.")
        return tool_name.strip(), arguments

    bracket_match = re.match(
        r"(?P<tool>[A-Za-z_][A-Za-z0-9_]*)\s*\[(?P<args>.*)\]\s*$",
        action_text,
        flags=re.S,
    )
    if not bracket_match:
        raise ValueError("Action phải có dạng tên_tool[tham_số].")

    tool_name = bracket_match.group("tool")
    raw_args = bracket_match.group("args")
    if tool_name == "get_quiz_question":
        arguments = {"group_name": _parse_scalar(raw_args)}
    elif tool_name == "analyze_quiz_and_recommend_careers":
        arguments = {"answers": _parse_answers(raw_args)}
    elif tool_name in {"get_career_profile", "generate_learning_roadmap"}:
        arguments = {"career_name": _parse_scalar(raw_args)}
    else:
        # Giữ raw argument để executor trả lỗi unknown-tool có căn cứ.
        arguments = {"argument": raw_args.strip()}
    return tool_name, arguments


def _safe_execute(
    tool_name: str,
    arguments: dict[str, Any],
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> str:
    """Thực thi tool có timeout và chuyển mọi exception thành Observation."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        valid = ", ".join(AVAILABLE_TOOLS)
        return f"LỖI: Tool '{tool_name}' không tồn tại. Tool hợp lệ: {valid}."

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(tool, **arguments)
    try:
        result = future.result(timeout=max(1, timeout_seconds))
    except ToolTimeoutError:
        future.cancel()
        return f"LỖI: Tool '{tool_name}' vượt quá timeout {timeout_seconds} giây."
    except TypeError as exc:
        return f"LỖI: Đối số của tool '{tool_name}' không hợp lệ: {exc}."
    except Exception as exc:
        return f"LỖI: Tool '{tool_name}' tạm thời gặp sự cố: {exc}."
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    return str(result)


def _build_prompt(
    user_query: str,
    history: Iterable[Mapping[str, str]] | None,
    scratchpad: list[str],
) -> str:
    previous_steps = "\n\n".join(scratchpad) if scratchpad else "(Chưa có Action)"
    return (
        "LỊCH SỬ HỘI THOẠI:\n"
        f"{_format_history(history)}\n\n"
        "CÂU HỎI HIỆN TẠI:\n"
        f"{user_query.strip()}\n\n"
        "TRACE CỦA LƯỢT HIỆN TẠI:\n"
        f"{previous_steps}\n\n"
        "Hãy trả đúng một Action dạng tên_tool[tham_số], hoặc Final Answer."
    )


def _provider_failed(model_output: str) -> bool:
    return model_output.startswith(
        (
            "[OpenAI Error]",
            "[OpenAI Exception]",
            "[Gemini Error]",
            "[Gemini Exception]",
            "[Anthropic Error]",
            "[Anthropic Exception]",
            "[OpenRouter API Error",
            "[OpenRouter Exception]",
        )
    )


def run_reactive_agent(
    user_query: str,
    provider: Any,
    history: Iterable[Mapping[str, str]] | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> AgentResult:
    """Chạy ReAct loop với parser recovery, chống lặp và guardrail."""
    if not isinstance(user_query, str) or not user_query.strip():
        return AgentResult(answer="Bạn hãy nhập câu hỏi về định hướng nghề nghiệp.")

    iteration_limit = max(1, int(max_iterations))
    trace: list[dict[str, Any]] = []
    scratchpad: list[str] = []
    seen_actions: set[str] = set()
    tool_calls = 0

    for iteration in range(1, iteration_limit + 1):
        prompt = _build_prompt(user_query, history, scratchpad)
        model_output = str(
            provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT) or ""
        ).strip()
        trace.append({"type": "model", "iteration": iteration, "content": model_output})

        if _provider_failed(model_output):
            return AgentResult(
                answer=(
                    "Không thể kết nối mô hình AI lúc này. Hãy kiểm tra "
                    "OPENAI_API_KEY, LLM_MODEL và kết nối mạng rồi thử lại."
                ),
                trace=trace,
                iterations=iteration,
                tool_calls=tool_calls,
            )

        if not model_output:
            observation = "LỖI: Mô hình không trả về nội dung."
            scratchpad.append(f"Observation: {observation}")
            trace.append({"type": "observation", "iteration": iteration, "content": observation})
            continue

        final_answer = _extract_final_answer(model_output)
        if final_answer:
            return AgentResult(
                answer=final_answer,
                trace=trace,
                iterations=iteration,
                tool_calls=tool_calls,
            )

        try:
            tool_name, arguments = _extract_action(model_output)
        except ValueError as exc:
            observation = f"LỖI PARSER: {exc}"
            scratchpad.append(
                f"{model_output}\nObservation: {observation}\n"
                "Hãy sửa đúng cú pháp Action ở vòng tiếp theo."
            )
            trace.append({"type": "observation", "iteration": iteration, "content": observation})
            continue

        action_key = json.dumps(
            {"tool": tool_name, "arguments": arguments},
            ensure_ascii=False,
            sort_keys=True,
        )
        if action_key in seen_actions:
            observation = (
                "LỖI: Action này đã được gọi trước đó. Không được lặp; hãy dùng "
                "Observation đã có để trả Final Answer hoặc chọn bước khác."
            )
        else:
            seen_actions.add(action_key)
            tool_calls += 1
            observation = _safe_execute(tool_name, arguments)

        scratchpad.append(f"Action: {action_key}\nObservation: {observation}")
        trace.append(
            {
                "type": "action",
                "iteration": iteration,
                "tool": tool_name,
                "arguments": arguments,
            }
        )
        trace.append({"type": "observation", "iteration": iteration, "content": observation})

    return AgentResult(
        answer=(
            "Mình chưa thể hoàn tất tư vấn trong giới hạn xử lý an toàn. "
            "Bạn hãy nêu rõ tên nghề hoặc gửi đủ 12 điểm (mỗi điểm từ 1 đến 5) "
            "để mình hỗ trợ chính xác hơn."
        ),
        trace=trace,
        iterations=iteration_limit,
        tool_calls=tool_calls,
        guardrail_triggered=True,
    )


if __name__ == "__main__":
    from providers import get_llm_provider

    demo = run_reactive_agent(
        "Tôi muốn được định hướng nghề nghiệp.",
        get_llm_provider("openai"),
    )
    print(demo.answer)
    print(json.dumps(demo.trace, ensure_ascii=False, indent=2))
