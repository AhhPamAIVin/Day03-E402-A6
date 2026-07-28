"""
ỨNG DỤNG AI ĐỊNH HƯỚNG NGHỀ NGHIỆP

Ghép bốn cấp độ AI, OpenAI provider, tool registry, ReAct trace, bài trắc
nghiệm 12 câu và giao diện desktop. API key chỉ được đọc từ OPENAI_API_KEY.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from ai_levels.level1_rule_based import rule_based_bot
from ai_levels.level2_llm_chatbot import llm_chatbot
from ai_levels.level3_reactive_agent import AgentResult, run_reactive_agent
from ai_levels.level4_autonomous_agent import AutonomousCareerAgent
from providers import get_llm_provider
from tools import (
    AVAILABLE_TOOLS,
    CAREER_DETAILS,
    GROUP_ORDER,
    QUIZ_QUESTIONS,
)


load_dotenv(PROJECT_ROOT / ".env")


def load_test_cases() -> list[dict[str, Any]]:
    """Đọc và kiểm tra sơ bộ bộ test cases của nhóm."""
    config_path = PROJECT_ROOT / "config" / "test_cases.json"
    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("config/test_cases.json phải chứa một JSON array.")
    return data


def create_openai_provider() -> Any:
    """Ép ứng dụng dùng OpenAI, không phụ thuộc LLM_PROVIDER trong .env."""
    return get_llm_provider("openai")


def validate_openai_configuration(provider: Any) -> tuple[bool, str]:
    """Kiểm tra cấu hình cục bộ mà không gửi request hoặc làm lộ API key."""
    api_key = getattr(provider, "api_key", None) or os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        return (
            False,
            "Chưa có OPENAI_API_KEY. Thêm OPENAI_API_KEY=<key-của-bạn> vào file .env.",
        )
    model = getattr(provider, "model_name", None) or os.getenv("LLM_MODEL") or "mặc định"
    return True, f"OpenAI sẵn sàng · {model}"


def run_baseline_chatbot(
    user_query: str,
    provider: Any,
    history: list[dict[str, str]] | None = None,
    verbose: bool = True,
) -> str:
    """Chạy baseline đúng một LLM call và không gọi tool."""
    answer = llm_chatbot(user_query, provider, history)
    if verbose:
        print(f"\n💬 [CẤP 2 - LLM CHATBOT]\n{answer}")
        print("📊 Tool calls: 0")
    return answer


def _print_trace(result: AgentResult) -> None:
    for event in result.trace:
        if event["type"] == "model":
            print(f"\n🧠 LLM step {event['iteration']}:\n{event['content']}")
        elif event["type"] == "action":
            arguments = json.dumps(event["arguments"], ensure_ascii=False)
            print(f"🛠️ Action: {event['tool']} {arguments}")
        elif event["type"] == "observation":
            print(f"👁️ Observation: {event['content']}")


def run_react_agent(
    user_query: str,
    provider: Any,
    history: list[dict[str, str]] | None = None,
    verbose: bool = True,
) -> AgentResult:
    """Chạy ReAct Agent và tùy chọn in trace."""
    result = run_reactive_agent(user_query, provider, history)
    if verbose:
        _print_trace(result)
        print(f"\n🏁 Final Answer:\n{result.answer}")
        print(
            f"📊 Iterations: {result.iterations} | Tool calls: {result.tool_calls} | "
            f"Guardrail: {'ON' if result.guardrail_triggered else 'OFF'}"
        )
    return result


def run_tool_smoke_tests() -> bool:
    """Kiểm tra deterministic toàn bộ tool mà không cần OpenAI key."""
    checks: list[tuple[str, bool, str]] = []
    quiz_tool = AVAILABLE_TOOLS["get_quiz_question"]
    for group in GROUP_ORDER:
        output = quiz_tool(group)
        checks.append((f"get_quiz_question({group})", not output.startswith("LỖI:"), output))

    analyze = AVAILABLE_TOOLS["analyze_quiz_and_recommend_careers"]
    valid_answers = [5, 1, 1, 5, 1, 1, 5, 1, 1, 1, 1, 1]
    valid_analysis = analyze(valid_answers)
    invalid_analysis = analyze([5])
    checks.append(("analyze(valid)", not valid_analysis.startswith("LỖI:"), valid_analysis))
    checks.append(("analyze(invalid)", invalid_analysis.startswith("LỖI:"), invalid_analysis))

    profile = AVAILABLE_TOOLS["get_career_profile"]
    valid_profile = profile("Lập trình viên")
    invalid_profile = profile("Phi hành gia")
    checks.append(("profile(valid)", "Lộ trình thăng tiến:" in valid_profile, valid_profile))
    checks.append(("profile(unknown)", invalid_profile.startswith("LỖI:"), invalid_profile))

    roadmap = AVAILABLE_TOOLS["generate_learning_roadmap"]
    valid_roadmap = roadmap("Lập trình viên")
    checks.append(("roadmap(valid)", "Bước 5:" in valid_roadmap, valid_roadmap))

    print("\n=== TOOL SMOKE TESTS ===")
    for name, passed, output in checks:
        print(f"{'✅' if passed else '❌'} {name}")
        if not passed:
            print(f"   {output}")
    passed_all = all(passed for _, passed, _ in checks)
    print(f"Kết quả: {sum(passed for _, passed, _ in checks)}/{len(checks)} checks pass.")
    return passed_all


def run_all_test_cases(provider: Any, show_trace: bool = True) -> None:
    """Chạy tuần tự test cases và giữ context cho các câu “nghề này”."""
    history: list[dict[str, str]] = []
    for test in load_test_cases():
        question = str(test.get("question", ""))
        print("\n" + "=" * 72)
        print(f"TEST #{test.get('id')} — {test.get('category')}")
        print(f"User: {question}")
        result = run_react_agent(question, provider, history, verbose=show_trace)
        history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": result.answer},
            ]
        )


def run_four_level_demo(provider: Any, query: str) -> None:
    """So sánh cùng một câu hỏi qua bốn cấp độ AI."""
    print("\n=== CẤP 1: RULE-BASED ===")
    print(rule_based_bot(query))
    print("\n=== CẤP 2: OPENAI LLM CHATBOT ===")
    run_baseline_chatbot(query, provider)
    print("\n=== CẤP 3: REACT AGENT ===")
    run_react_agent(query, provider)
    print("\n=== CẤP 4: AUTONOMOUS AGENT ===")
    autonomous = AutonomousCareerAgent(provider)
    result = autonomous.execute(query)
    print("📋 Planning:")
    for index, step in enumerate(result.plan, start=1):
        print(f"{index}. {step}")
    _print_trace(result.agent_result)
    print(f"\n🏁 Final Answer:\n{result.answer}")
    print(f"🎯 Goal evaluation: {result.evaluation}")


def interactive_chat(provider: Any, level: int = 3) -> None:
    """CLI hội thoại nhiều lượt."""
    history: list[dict[str, str]] = []
    autonomous = AutonomousCareerAgent(provider)
    print(
        f"\nCareerBot đang chạy ở cấp {level}. "
        "Gõ /quit để thoát, /clear để xóa lịch sử."
    )
    while True:
        try:
            user_query = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            return
        if not user_query:
            continue
        if user_query.lower() in {"/quit", "/exit"}:
            print("Tạm biệt! Chúc bạn tìm được hướng đi phù hợp.")
            return
        if user_query.lower() == "/clear":
            history.clear()
            autonomous.clear_memory()
            print("Đã xóa lịch sử hội thoại trong phiên.")
            continue

        if level == 1:
            answer = rule_based_bot(user_query)
            print(f"\nCareerBot: {answer}")
        elif level == 2:
            answer = run_baseline_chatbot(user_query, provider, history)
        elif level == 4:
            output = autonomous.execute(user_query)
            print("📋 Planning: " + " → ".join(output.plan))
            _print_trace(output.agent_result)
            answer = output.answer
            print(f"\nCareerBot: {answer}\n🎯 {output.evaluation}")
        else:
            output = run_react_agent(user_query, provider, history)
            answer = output.answer

        history.extend(
            [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": answer},
            ]
        )


class CareerDesktopApp:
    """Giao diện desktop dùng tkinter, không cần dependency bổ sung."""

    COLORS = {
        "navy": "#10233F",
        "blue": "#246BFD",
        "blue_hover": "#1857D9",
        "cyan": "#18B6A4",
        "bg": "#F3F6FB",
        "card": "#FFFFFF",
        "text": "#17233C",
        "muted": "#667085",
        "line": "#DFE5EF",
        "user": "#E8F0FF",
        "assistant": "#EAF9F5",
        "warning": "#C2410C",
    }

    LEVELS = {
        "Cấp 1 · Rule-based": 1,
        "Cấp 2 · LLM Chatbot": 2,
        "Cấp 3 · ReAct Agent": 3,
        "Cấp 4 · Autonomous": 4,
    }

    def __init__(self, root: Any, provider: Any, configured: bool, config_message: str):
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText

        self.tk = tk
        self.ttk = ttk
        self.ScrolledText = ScrolledText
        self.root = root
        self.provider = provider
        self.configured = configured
        self.history: list[dict[str, str]] = []
        self.autonomous = AutonomousCareerAgent(provider)
        self.quiz_vars: list[Any] = []
        self.busy = False

        root.title("Career Compass AI · Định hướng nghề nghiệp")
        root.geometry("1220x800")
        root.minsize(1000, 680)
        root.configure(bg=self.COLORS["bg"])
        self._configure_styles()
        self._build_header(config_message)
        self._build_main()
        self._append_chat(
            "assistant",
            "Xin chào! Mình là Career Compass AI. Bạn có thể trò chuyện trực tiếp "
            "hoặc sang tab Trắc nghiệm để khám phá nhóm nghề phù hợp.",
        )

    def _configure_styles(self) -> None:
        style = self.ttk.Style()
        try:
            style.theme_use("clam")
        except self.tk.TclError:
            pass
        style.configure("App.TNotebook", background=self.COLORS["bg"], borderwidth=0)
        style.configure(
            "App.TNotebook.Tab",
            font=("Segoe UI", 11, "bold"),
            padding=(22, 12),
            background="#E7ECF4",
            foreground=self.COLORS["muted"],
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", self.COLORS["card"])],
            foreground=[("selected", self.COLORS["blue"])],
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(16, 10),
            background=self.COLORS["blue"],
            foreground="white",
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.COLORS["blue_hover"]), ("disabled", "#AAB7CF")],
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            padding=(12, 8),
            background="#E8EEF9",
            foreground=self.COLORS["text"],
            borderwidth=0,
        )
        style.map("Secondary.TButton", background=[("active", "#D9E4F7")])
        style.configure(
            "Career.TCombobox",
            padding=7,
            font=("Segoe UI", 10),
        )

    def _build_header(self, config_message: str) -> None:
        header = self.tk.Frame(self.root, bg=self.COLORS["navy"], height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = self.tk.Frame(header, bg=self.COLORS["navy"])
        brand.pack(side="left", padx=30, pady=16)
        self.tk.Label(
            brand,
            text="CAREER COMPASS",
            font=("Segoe UI", 18, "bold"),
            bg=self.COLORS["navy"],
            fg="white",
        ).pack(anchor="w")
        self.tk.Label(
            brand,
            text="AI định hướng nghề nghiệp · ReAct Agent",
            font=("Segoe UI", 10),
            bg=self.COLORS["navy"],
            fg="#B9C7DB",
        ).pack(anchor="w")

        status_color = "#6EE7B7" if self.configured else "#FDBA74"
        status = self.tk.Frame(header, bg="#183454", padx=14, pady=9)
        status.pack(side="right", padx=30)
        self.tk.Label(
            status,
            text="●",
            font=("Segoe UI", 11),
            bg="#183454",
            fg=status_color,
        ).pack(side="left", padx=(0, 7))
        self.tk.Label(
            status,
            text=config_message,
            font=("Segoe UI", 9),
            bg="#183454",
            fg="white",
        ).pack(side="left")

    def _build_main(self) -> None:
        container = self.tk.Frame(self.root, bg=self.COLORS["bg"])
        container.pack(fill="both", expand=True, padx=24, pady=20)
        self.notebook = self.ttk.Notebook(container, style="App.TNotebook")
        self.notebook.pack(fill="both", expand=True)
        self.chat_tab = self.tk.Frame(self.notebook, bg=self.COLORS["card"])
        self.quiz_tab = self.tk.Frame(self.notebook, bg=self.COLORS["card"])
        self.trace_tab = self.tk.Frame(self.notebook, bg=self.COLORS["card"])
        self.notebook.add(self.chat_tab, text="  Tư vấn AI  ")
        self.notebook.add(self.quiz_tab, text="  Trắc nghiệm 12 câu  ")
        self.notebook.add(self.trace_tab, text="  Agent Trace  ")
        self._build_chat_tab()
        self._build_quiz_tab()
        self._build_trace_tab()

    def _build_chat_tab(self) -> None:
        toolbar = self.tk.Frame(self.chat_tab, bg=self.COLORS["card"])
        toolbar.pack(fill="x", padx=22, pady=(18, 10))
        self.tk.Label(
            toolbar,
            text="Chế độ tư vấn",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
        ).pack(side="left")
        self.level_var = self.tk.StringVar(value="Cấp 3 · ReAct Agent")
        level_box = self.ttk.Combobox(
            toolbar,
            textvariable=self.level_var,
            values=list(self.LEVELS),
            state="readonly",
            width=24,
            style="Career.TCombobox",
        )
        level_box.pack(side="left", padx=12)
        self.clear_button = self.ttk.Button(
            toolbar,
            text="Xóa hội thoại",
            style="Secondary.TButton",
            command=self._clear_chat,
        )
        self.clear_button.pack(side="right")

        quick = self.tk.Frame(self.chat_tab, bg=self.COLORS["card"])
        quick.pack(fill="x", padx=22, pady=(0, 10))
        for label, prompt in (
            ("Bắt đầu định hướng", "Tôi muốn được định hướng nghề nghiệp."),
            ("Tìm hiểu nghề", "Công việc hàng ngày của Lập trình viên là gì?"),
            ("Hỏi về lương", "Lương và lộ trình thăng tiến của Lập trình viên thế nào?"),
            ("Lộ trình học", "Tôi nên học như thế nào để trở thành Lập trình viên?"),
        ):
            self.ttk.Button(
                quick,
                text=label,
                style="Secondary.TButton",
                command=lambda text=prompt: self._use_quick_prompt(text),
            ).pack(side="left", padx=(0, 8))

        self.chat_box = self.ScrolledText(
            self.chat_tab,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#F8FAFD",
            fg=self.COLORS["text"],
            relief="flat",
            padx=18,
            pady=14,
            spacing1=4,
            spacing3=8,
        )
        self.chat_box.pack(fill="both", expand=True, padx=22, pady=(0, 12))
        self.chat_box.tag_configure(
            "user_title", foreground=self.COLORS["blue"], font=("Segoe UI", 10, "bold")
        )
        self.chat_box.tag_configure(
            "assistant_title", foreground="#087F6F", font=("Segoe UI", 10, "bold")
        )
        self.chat_box.tag_configure("message", lmargin1=8, lmargin2=8, rmargin=8)
        self.chat_box.configure(state="disabled")

        composer = self.tk.Frame(self.chat_tab, bg=self.COLORS["card"])
        composer.pack(fill="x", padx=22, pady=(0, 18))
        self.message_input = self.tk.Text(
            composer,
            height=3,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#F7F9FC",
            fg=self.COLORS["text"],
            insertbackground=self.COLORS["blue"],
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=9,
        )
        self.message_input.pack(side="left", fill="x", expand=True)
        self.message_input.bind("<Control-Return>", lambda _event: self._send_message())
        self.send_button = self.ttk.Button(
            composer,
            text="Gửi  ➜",
            style="Primary.TButton",
            command=self._send_message,
        )
        self.send_button.pack(side="right", padx=(12, 0), fill="y")
        self.chat_status = self.tk.StringVar(value="Sẵn sàng · Ctrl+Enter để gửi")
        self.tk.Label(
            self.chat_tab,
            textvariable=self.chat_status,
            anchor="w",
            font=("Segoe UI", 9),
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
        ).pack(fill="x", padx=24, pady=(0, 10))

    def _build_quiz_tab(self) -> None:
        top = self.tk.Frame(self.quiz_tab, bg=self.COLORS["card"])
        top.pack(fill="x", padx=24, pady=(20, 10))
        self.tk.Label(
            top,
            text="Khám phá nhóm nghề phù hợp",
            font=("Segoe UI", 17, "bold"),
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
        ).pack(anchor="w")
        self.tk.Label(
            top,
            text="Chọn mức độ phù hợp từ 1 (hoàn toàn không đúng) đến 5 (rất đúng với bạn).",
            font=("Segoe UI", 10),
            bg=self.COLORS["card"],
            fg=self.COLORS["muted"],
        ).pack(anchor="w", pady=(4, 0))

        body = self.tk.PanedWindow(
            self.quiz_tab,
            orient="horizontal",
            bg=self.COLORS["line"],
            sashwidth=5,
            relief="flat",
        )
        body.pack(fill="both", expand=True, padx=24, pady=(4, 20))

        question_card = self.tk.Frame(body, bg="#F8FAFD")
        result_card = self.tk.Frame(body, bg=self.COLORS["card"])
        body.add(question_card, minsize=540, stretch="always")
        body.add(result_card, minsize=350, stretch="always")

        canvas = self.tk.Canvas(question_card, bg="#F8FAFD", highlightthickness=0)
        scrollbar = self.ttk.Scrollbar(question_card, orient="vertical", command=canvas.yview)
        self.question_frame = self.tk.Frame(canvas, bg="#F8FAFD")
        self.question_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.question_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        group_labels = {
            "career_interest": "Sở thích nghề nghiệp",
            "work_style": "Phong cách làm việc",
            "personal_strength": "Điểm mạnh cá nhân",
            "career_value": "Giá trị nghề nghiệp",
        }
        question_number = 0
        for group in GROUP_ORDER:
            self.tk.Label(
                self.question_frame,
                text=group_labels.get(group, group),
                font=("Segoe UI", 12, "bold"),
                bg="#F8FAFD",
                fg=self.COLORS["blue"],
            ).pack(anchor="w", padx=18, pady=(18, 8))
            for question, _field in QUIZ_QUESTIONS[group]:
                question_number += 1
                card = self.tk.Frame(
                    self.question_frame,
                    bg="white",
                    highlightbackground=self.COLORS["line"],
                    highlightthickness=1,
                    padx=14,
                    pady=10,
                )
                card.pack(fill="x", padx=18, pady=5)
                self.tk.Label(
                    card,
                    text=f"{question_number}. {question}",
                    wraplength=520,
                    justify="left",
                    anchor="w",
                    font=("Segoe UI", 9),
                    bg="white",
                    fg=self.COLORS["text"],
                ).pack(fill="x")
                value = self.tk.IntVar(value=3)
                self.quiz_vars.append(value)
                scale_row = self.tk.Frame(card, bg="white")
                scale_row.pack(fill="x", pady=(7, 0))
                self.tk.Label(
                    scale_row, text="1", bg="white", fg=self.COLORS["muted"]
                ).pack(side="left")
                self.tk.Scale(
                    scale_row,
                    from_=1,
                    to=5,
                    orient="horizontal",
                    variable=value,
                    showvalue=True,
                    resolution=1,
                    bg="white",
                    fg=self.COLORS["blue"],
                    troughcolor="#DDE7F8",
                    activebackground=self.COLORS["blue"],
                    highlightthickness=0,
                ).pack(side="left", fill="x", expand=True, padx=8)
                self.tk.Label(
                    scale_row, text="5", bg="white", fg=self.COLORS["muted"]
                ).pack(side="right")

        actions = self.tk.Frame(result_card, bg=self.COLORS["card"])
        actions.pack(fill="x", padx=18, pady=(4, 10))
        self.ttk.Button(
            actions,
            text="Phân tích kết quả",
            style="Primary.TButton",
            command=self._analyze_quiz,
        ).pack(side="left")
        self.ttk.Button(
            actions,
            text="Đặt lại",
            style="Secondary.TButton",
            command=self._reset_quiz,
        ).pack(side="left", padx=8)

        self.quiz_result = self.ScrolledText(
            result_card,
            wrap="word",
            height=15,
            font=("Segoe UI", 10),
            bg="#F8FAFD",
            fg=self.COLORS["text"],
            relief="flat",
            padx=14,
            pady=12,
        )
        self.quiz_result.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self.quiz_result.insert(
            "1.0",
            "Kết quả sẽ xuất hiện tại đây sau khi bạn hoàn thành 12 câu hỏi.",
        )
        self.quiz_result.configure(state="disabled")

        career_tools = self.tk.Frame(result_card, bg=self.COLORS["card"])
        career_tools.pack(fill="x", padx=18, pady=(0, 18))
        self.career_var = self.tk.StringVar()
        self.career_box = self.ttk.Combobox(
            career_tools,
            textvariable=self.career_var,
            values=list(CAREER_DETAILS),
            state="readonly",
            style="Career.TCombobox",
        )
        self.career_box.pack(fill="x", pady=(0, 8))
        button_row = self.tk.Frame(career_tools, bg=self.COLORS["card"])
        button_row.pack(fill="x")
        self.ttk.Button(
            button_row,
            text="Lương & thăng tiến",
            style="Secondary.TButton",
            command=self._show_career_profile,
        ).pack(side="left")
        self.ttk.Button(
            button_row,
            text="Lộ trình học",
            style="Secondary.TButton",
            command=self._show_roadmap,
        ).pack(side="left", padx=8)
        self.ttk.Button(
            career_tools,
            text="Tư vấn sâu với AI  ➜",
            style="Primary.TButton",
            command=self._consult_quiz_with_ai,
        ).pack(fill="x", pady=(10, 0))

    def _build_trace_tab(self) -> None:
        toolbar = self.tk.Frame(self.trace_tab, bg=self.COLORS["card"])
        toolbar.pack(fill="x", padx=22, pady=(18, 8))
        self.tk.Label(
            toolbar,
            text="Thought → Action → Observation",
            font=("Segoe UI", 16, "bold"),
            bg=self.COLORS["card"],
            fg=self.COLORS["text"],
        ).pack(side="left")
        self.ttk.Button(
            toolbar,
            text="Xóa trace",
            style="Secondary.TButton",
            command=lambda: self._set_trace([]),
        ).pack(side="right")
        self.trace_box = self.ScrolledText(
            self.trace_tab,
            wrap="word",
            font=("Consolas", 10),
            bg="#0E1B2C",
            fg="#D9E7F5",
            insertbackground="white",
            relief="flat",
            padx=18,
            pady=16,
        )
        self.trace_box.pack(fill="both", expand=True, padx=22, pady=(0, 22))
        self.trace_box.configure(state="disabled")
        self._set_trace([])

    def _append_chat(self, role: str, message: str) -> None:
        self.chat_box.configure(state="normal")
        title_tag = "user_title" if role == "user" else "assistant_title"
        title = "BẠN" if role == "user" else "CAREER COMPASS"
        self.chat_box.insert("end", f"{title}\n", title_tag)
        self.chat_box.insert("end", f"{message.strip()}\n\n", "message")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _use_quick_prompt(self, prompt: str) -> None:
        self.message_input.delete("1.0", "end")
        self.message_input.insert("1.0", prompt)
        self._send_message()

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.send_button.configure(state="disabled" if busy else "normal")
        self.clear_button.configure(state="disabled" if busy else "normal")
        self.chat_status.set(
            "Đang phân tích và gọi tool khi cần..."
            if busy
            else "Sẵn sàng · Ctrl+Enter để gửi"
        )

    def _send_message(self) -> None:
        if self.busy:
            return
        query = self.message_input.get("1.0", "end").strip()
        if not query:
            return
        level = self.LEVELS[self.level_var.get()]
        if level > 1 and not self.configured:
            self._append_chat(
                "assistant",
                "Chưa có OPENAI_API_KEY hợp lệ. Bạn vẫn có thể dùng Cấp 1 và "
                "tab Trắc nghiệm; hãy cấu hình key để dùng các cấp AI.",
            )
            return
        self.message_input.delete("1.0", "end")
        self._append_chat("user", query)
        self._set_busy(True)

        def worker() -> None:
            try:
                if level == 1:
                    payload = {"answer": rule_based_bot(query), "trace": []}
                elif level == 2:
                    payload = {
                        "answer": run_baseline_chatbot(
                            query, self.provider, self.history, verbose=False
                        ),
                        "trace": [],
                    }
                elif level == 4:
                    output = self.autonomous.execute(query)
                    payload = {
                        "answer": output.answer,
                        "trace": output.agent_result.trace,
                        "plan": output.plan,
                        "evaluation": output.evaluation,
                    }
                else:
                    output = run_react_agent(
                        query, self.provider, self.history, verbose=False
                    )
                    payload = {"answer": output.answer, "trace": output.trace}
            except Exception as exc:
                payload = {
                    "answer": f"Ứng dụng gặp lỗi khi xử lý: {exc}",
                    "trace": [],
                }
            self.root.after(0, lambda: self._finish_message(query, payload))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_message(self, query: str, payload: dict[str, Any]) -> None:
        answer = str(payload["answer"])
        if payload.get("plan"):
            plan_text = "\n".join(
                f"{index}. {step}" for index, step in enumerate(payload["plan"], start=1)
            )
            answer = f"Kế hoạch xử lý:\n{plan_text}\n\n{answer}\n\n{payload['evaluation']}"
        self._append_chat("assistant", answer)
        self.history.extend(
            [
                {"role": "user", "content": query},
                {"role": "assistant", "content": str(payload["answer"])},
            ]
        )
        self._set_trace(payload.get("trace", []))
        self._set_busy(False)

    def _clear_chat(self) -> None:
        self.history.clear()
        self.autonomous.clear_memory()
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self._set_trace([])
        self._append_chat("assistant", "Đã xóa lịch sử. Chúng ta bắt đầu lại nhé!")

    def _set_trace(self, trace: list[dict[str, Any]]) -> None:
        self.trace_box.configure(state="normal")
        self.trace_box.delete("1.0", "end")
        if not trace:
            self.trace_box.insert(
                "1.0",
                "Chưa có trace.\n\nHãy chọn Cấp 3 hoặc Cấp 4 và gửi một câu hỏi "
                "cần dữ liệu tool để quan sát vòng lặp Agent.",
            )
        else:
            lines = []
            for event in trace:
                iteration = event.get("iteration", "-")
                if event["type"] == "model":
                    lines.append(f"━━ STEP {iteration} · MODEL ━━\n{event['content']}")
                elif event["type"] == "action":
                    args = json.dumps(event["arguments"], ensure_ascii=False)
                    lines.append(f"ACTION  ▶ {event['tool']} {args}")
                elif event["type"] == "observation":
                    lines.append(f"OBSERVE ◀ {event['content']}")
            self.trace_box.insert("1.0", "\n\n".join(lines))
        self.trace_box.configure(state="disabled")

    def _set_quiz_result(self, text: str, append: bool = False) -> None:
        self.quiz_result.configure(state="normal")
        if not append:
            self.quiz_result.delete("1.0", "end")
        else:
            self.quiz_result.insert("end", "\n\n")
        self.quiz_result.insert("end", text)
        self.quiz_result.configure(state="disabled")
        self.quiz_result.see("end")

    def _analyze_quiz(self) -> None:
        answers = [value.get() for value in self.quiz_vars]
        result = AVAILABLE_TOOLS["analyze_quiz_and_recommend_careers"](answers)
        self._set_quiz_result(result)
        for field_name in ("công nghệ", "kinh doanh", "sáng tạo", "xã hội"):
            if f"'{field_name}'" in result:
                careers = [
                    name
                    for name, details in CAREER_DETAILS.items()
                    if details["field"] == field_name
                ]
                self.career_box.configure(values=careers)
                if careers:
                    self.career_var.set(careers[0])
                break

    def _reset_quiz(self) -> None:
        for value in self.quiz_vars:
            value.set(3)
        self.career_var.set("")
        self.career_box.configure(values=list(CAREER_DETAILS))
        self._set_quiz_result(
            "Kết quả sẽ xuất hiện tại đây sau khi bạn hoàn thành 12 câu hỏi."
        )

    def _selected_career(self) -> str | None:
        career = self.career_var.get().strip()
        if not career:
            self._set_quiz_result("Hãy chọn một nghề trước.", append=True)
            return None
        return career

    def _show_career_profile(self) -> None:
        career = self._selected_career()
        if career:
            result = AVAILABLE_TOOLS["get_career_profile"](career)
            self._set_quiz_result(result, append=True)

    def _show_roadmap(self) -> None:
        career = self._selected_career()
        if career:
            result = AVAILABLE_TOOLS["generate_learning_roadmap"](career)
            self._set_quiz_result(result, append=True)

    def _consult_quiz_with_ai(self) -> None:
        answers = [value.get() for value in self.quiz_vars]
        prompt = (
            "Đây là 12 điểm bài trắc nghiệm của tôi theo đúng thứ tự câu hỏi: "
            f"{answers}. Hãy phân tích và định hướng nghề nghiệp phù hợp."
        )
        self.level_var.set("Cấp 3 · ReAct Agent")
        self.notebook.select(self.chat_tab)
        self.message_input.delete("1.0", "end")
        self.message_input.insert("1.0", prompt)
        self._send_message()


def launch_desktop_ui(provider: Any, configured: bool, config_message: str) -> int:
    """Khởi chạy GUI; trả mã lỗi rõ ràng nếu máy không có tkinter/display."""
    try:
        import tkinter as tk
    except ImportError:
        print("Không tìm thấy tkinter. Hãy cài Python có hỗ trợ Tcl/Tk.")
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Không thể mở giao diện desktop: {exc}")
        return 1
    CareerDesktopApp(root, provider, configured, config_message)
    root.mainloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI định hướng nghề nghiệp dùng OpenAI")
    parser.add_argument(
        "--mode",
        choices=("ui", "chat", "demo", "tests", "tools"),
        default="ui",
        help="ui: giao diện; chat: CLI; demo: 4 cấp; tests: test cases; tools: test tool",
    )
    parser.add_argument("--level", type=int, choices=(1, 2, 3, 4), default=3)
    parser.add_argument(
        "--query",
        default="Tôi muốn được định hướng nghề nghiệp.",
        help="Câu hỏi dùng cho mode demo",
    )
    parser.add_argument("--no-trace", action="store_true", help="Ẩn trace khi chạy test cases")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.mode == "tools":
        return 0 if run_tool_smoke_tests() else 1

    provider = create_openai_provider()
    configured, message = validate_openai_configuration(provider)
    if args.mode == "ui":
        return launch_desktop_ui(provider, configured, message)

    print("=" * 72)
    print("AI ĐỊNH HƯỚNG NGHỀ NGHIỆP — CHATBOT VS REACT AGENT")
    print("=" * 72)
    print(f"🔌 {message}")
    llm_required = args.mode in {"demo", "tests"} or (
        args.mode == "chat" and args.level > 1
    )
    if llm_required and not configured:
        return 1

    if args.mode == "demo":
        run_four_level_demo(provider, args.query)
    elif args.mode == "tests":
        run_all_test_cases(provider, show_trace=not args.no_trace)
    else:
        interactive_chat(provider, level=args.level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
