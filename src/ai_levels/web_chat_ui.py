"""
Web UI dạng chatbot cho ứng dụng AI định hướng nghề nghiệp.

Server chỉ bind localhost theo mặc định. OPENAI_API_KEY luôn ở Python backend
và không bao giờ được gửi xuống trình duyệt.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ai_levels.level1_rule_based import rule_based_bot
from ai_levels.level2_llm_chatbot import llm_chatbot
from ai_levels.level3_reactive_agent import AgentResult, run_reactive_agent
from ai_levels.level4_autonomous_agent import AutonomousCareerAgent
from tools import AVAILABLE_TOOLS, CAREER_DETAILS, GROUP_ORDER, QUIZ_QUESTIONS


GROUP_LABELS = {
    "career_interest": "Sở thích nghề nghiệp",
    "work_style": "Phong cách làm việc",
    "personal_strength": "Điểm mạnh cá nhân",
    "career_value": "Giá trị nghề nghiệp",
}


PAGE_HTML = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Career Compass AI</title>
  <style>
    :root {
      --ink: #172033;
      --muted: #667085;
      --line: #e6e9ef;
      --surface: #ffffff;
      --soft: #f7f8fa;
      --accent: #2563eb;
      --accent-dark: #1d4ed8;
      --mint: #0f9f85;
      --nav: #111827;
      --shadow: 0 16px 50px rgba(15, 23, 42, .10);
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; }
    body {
      color: var(--ink);
      background: var(--surface);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      overflow: hidden;
    }
    button, textarea, select { font: inherit; }
    button { cursor: pointer; }
    .app { display: flex; height: 100vh; }
    .sidebar {
      width: 274px;
      flex: 0 0 274px;
      display: flex;
      flex-direction: column;
      padding: 18px 14px;
      color: #fff;
      background: var(--nav);
      transition: transform .2s ease;
    }
    .brand {
      display: flex;
      gap: 11px;
      align-items: center;
      padding: 4px 8px 18px;
    }
    .brand-mark {
      width: 38px; height: 38px;
      display: grid; place-items: center;
      border-radius: 12px;
      color: #fff;
      background: linear-gradient(135deg, #3b82f6, #14b8a6);
      font-weight: 800;
    }
    .brand strong { display: block; font-size: 15px; letter-spacing: .01em; }
    .brand small { color: #9ca3af; font-size: 11px; }
    .new-chat {
      width: 100%;
      padding: 11px 13px;
      border: 1px solid #374151;
      border-radius: 11px;
      color: #fff;
      background: transparent;
      text-align: left;
    }
    .new-chat:hover { background: #1f2937; }
    .side-section { margin-top: 22px; padding: 0 6px; }
    .side-label {
      margin: 0 0 8px;
      color: #9ca3af;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .level-select {
      width: 100%;
      padding: 10px 11px;
      border: 1px solid #374151;
      border-radius: 10px;
      color: #f9fafb;
      background: #1f2937;
      outline: none;
    }
    .side-action {
      width: 100%;
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 8px;
      padding: 10px 11px;
      border: 0;
      border-radius: 9px;
      color: #e5e7eb;
      background: transparent;
      text-align: left;
    }
    .side-action:hover, .side-action.active { background: #1f2937; color: #fff; }
    .side-footer { margin-top: auto; padding: 12px 8px 2px; }
    .api-status {
      display: flex; gap: 8px; align-items: flex-start;
      padding: 10px;
      border: 1px solid #374151;
      border-radius: 10px;
      color: #d1d5db;
      font-size: 11px;
      line-height: 1.45;
    }
    .status-dot {
      width: 8px; height: 8px; flex: 0 0 8px;
      margin-top: 4px; border-radius: 50%; background: #f59e0b;
    }
    .status-dot.ready { background: #34d399; box-shadow: 0 0 0 3px rgba(52,211,153,.13); }
    .main { position: relative; flex: 1; min-width: 0; background: var(--surface); }
    .topbar {
      height: 58px;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 22px;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,.93);
      backdrop-filter: blur(10px);
    }
    .topbar-title { font-weight: 650; font-size: 14px; }
    .topbar-meta { color: var(--muted); font-size: 12px; }
    .icon-button {
      padding: 8px 11px;
      border: 1px solid var(--line);
      border-radius: 9px;
      color: var(--ink);
      background: #fff;
    }
    .icon-button:hover { background: var(--soft); }
    .mobile-menu { display: none; }
    .chat-shell {
      height: calc(100vh - 58px);
      display: flex;
      flex-direction: column;
    }
    .messages {
      flex: 1;
      overflow-y: auto;
      scroll-behavior: smooth;
      padding: 28px 24px 170px;
    }
    .welcome {
      max-width: 720px;
      margin: 9vh auto 0;
      text-align: center;
    }
    .welcome-badge {
      width: 54px; height: 54px;
      display: grid; place-items: center;
      margin: 0 auto 18px;
      border-radius: 17px;
      color: #fff;
      background: linear-gradient(135deg, #2563eb, #0f9f85);
      font-size: 24px;
      box-shadow: 0 12px 30px rgba(37,99,235,.2);
    }
    .welcome h1 {
      margin: 0;
      font-size: clamp(27px, 4vw, 38px);
      line-height: 1.2;
      letter-spacing: -.035em;
    }
    .welcome p {
      max-width: 570px;
      margin: 13px auto 26px;
      color: var(--muted);
      line-height: 1.65;
    }
    .suggestions {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      text-align: left;
    }
    .suggestion {
      min-height: 78px;
      padding: 14px 15px;
      border: 1px solid var(--line);
      border-radius: 14px;
      color: var(--ink);
      background: #fff;
      transition: border-color .15s, transform .15s, box-shadow .15s;
    }
    .suggestion:hover {
      transform: translateY(-1px);
      border-color: #b9ccf8;
      box-shadow: 0 8px 24px rgba(15,23,42,.06);
    }
    .suggestion strong { display: block; margin-bottom: 4px; font-size: 13px; }
    .suggestion span { color: var(--muted); font-size: 12px; line-height: 1.4; }
    .message {
      max-width: 780px;
      display: flex;
      gap: 13px;
      margin: 0 auto 25px;
      animation: rise .18s ease-out;
    }
    @keyframes rise { from { opacity: 0; transform: translateY(6px); } }
    .avatar {
      width: 32px; height: 32px; flex: 0 0 32px;
      display: grid; place-items: center;
      border-radius: 9px;
      color: #fff;
      background: var(--accent);
      font-size: 12px;
      font-weight: 800;
    }
    .message.user .avatar { background: #334155; }
    .message-body { min-width: 0; flex: 1; padding-top: 3px; }
    .message-name { margin-bottom: 6px; font-size: 12px; font-weight: 700; }
    .message-text {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 14px;
      line-height: 1.72;
    }
    .message-meta { margin-top: 8px; color: var(--muted); font-size: 11px; }
    .typing { display: inline-flex; gap: 5px; padding-top: 8px; }
    .typing i {
      width: 6px; height: 6px; border-radius: 50%; background: #94a3b8;
      animation: pulse 1s infinite alternate;
    }
    .typing i:nth-child(2) { animation-delay: .18s; }
    .typing i:nth-child(3) { animation-delay: .36s; }
    @keyframes pulse { to { opacity: .25; transform: translateY(-3px); } }
    .composer-wrap {
      position: absolute;
      left: 0; right: 0; bottom: 0;
      padding: 20px 24px 17px;
      background: linear-gradient(to top, #fff 70%, rgba(255,255,255,0));
    }
    .composer {
      max-width: 800px;
      display: flex; align-items: flex-end; gap: 10px;
      margin: 0 auto;
      padding: 10px 10px 10px 16px;
      border: 1px solid #d8dee9;
      border-radius: 18px;
      background: #fff;
      box-shadow: 0 10px 35px rgba(15,23,42,.10);
    }
    .composer:focus-within { border-color: #9bb7f8; box-shadow: 0 10px 40px rgba(37,99,235,.13); }
    .composer textarea {
      min-height: 28px; max-height: 130px; flex: 1;
      resize: none;
      padding: 5px 0;
      border: 0;
      outline: 0;
      color: var(--ink);
      background: transparent;
      line-height: 1.45;
    }
    .send {
      width: 38px; height: 38px; flex: 0 0 38px;
      border: 0; border-radius: 12px;
      color: #fff; background: var(--accent);
      font-size: 17px;
    }
    .send:hover { background: var(--accent-dark); }
    .send:disabled { cursor: default; opacity: .45; }
    .hint { max-width: 800px; margin: 8px auto 0; color: #98a2b3; font-size: 10px; text-align: center; }
    .trace-panel {
      position: fixed;
      top: 0; right: 0; bottom: 0;
      z-index: 30;
      width: min(430px, 92vw);
      display: flex; flex-direction: column;
      background: #0f172a;
      color: #dbeafe;
      box-shadow: -20px 0 60px rgba(0,0,0,.22);
      transform: translateX(105%);
      transition: transform .22s ease;
    }
    .trace-panel.open { transform: translateX(0); }
    .trace-head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 18px;
      border-bottom: 1px solid #26334a;
    }
    .trace-head strong { font-size: 14px; }
    .trace-close { border: 0; color: #cbd5e1; background: transparent; font-size: 21px; }
    .trace-content {
      flex: 1; overflow: auto;
      padding: 18px;
      font: 12px/1.65 "Cascadia Code", Consolas, monospace;
      white-space: pre-wrap;
    }
    .trace-empty { color: #8291a9; }
    .overlay {
      position: fixed; inset: 0; z-index: 40;
      display: none;
      align-items: center; justify-content: center;
      padding: 24px;
      background: rgba(15,23,42,.58);
      backdrop-filter: blur(4px);
    }
    .overlay.open { display: flex; }
    .quiz-modal {
      width: min(980px, 96vw);
      max-height: 92vh;
      display: flex; flex-direction: column;
      border-radius: 20px;
      background: #fff;
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .modal-head {
      display: flex; align-items: flex-start; justify-content: space-between;
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
    }
    .modal-head h2 { margin: 0 0 5px; font-size: 20px; }
    .modal-head p { margin: 0; color: var(--muted); font-size: 12px; }
    .modal-close { border: 0; color: var(--muted); background: transparent; font-size: 24px; }
    .quiz-layout { min-height: 0; display: grid; grid-template-columns: 1.3fr .8fr; }
    .questions { overflow-y: auto; padding: 20px 24px 28px; background: var(--soft); }
    .question-group h3 { margin: 8px 0 10px; color: var(--accent); font-size: 13px; }
    .question-card {
      margin-bottom: 9px;
      padding: 13px 14px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #fff;
    }
    .question-card label { display: block; font-size: 12px; line-height: 1.45; }
    .range-row { display: flex; align-items: center; gap: 9px; margin-top: 9px; color: var(--muted); font-size: 11px; }
    .range-row input { flex: 1; accent-color: var(--accent); }
    .range-value {
      width: 27px; height: 27px; display: grid; place-items: center;
      border-radius: 8px; color: var(--accent); background: #eaf0ff; font-weight: 700;
    }
    .quiz-result { display: flex; flex-direction: column; padding: 22px; min-width: 0; }
    .result-box {
      flex: 1; min-height: 210px;
      padding: 14px;
      border-radius: 12px;
      color: var(--ink);
      background: var(--soft);
      white-space: pre-wrap;
      overflow-y: auto;
      font-size: 12px;
      line-height: 1.6;
    }
    .primary {
      padding: 11px 15px;
      border: 0; border-radius: 10px;
      color: #fff; background: var(--accent);
      font-weight: 700;
    }
    .primary:hover { background: var(--accent-dark); }
    .career-select {
      width: 100%; margin-top: 12px; padding: 10px;
      border: 1px solid var(--line); border-radius: 9px; background: #fff;
    }
    .tool-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
    .secondary {
      padding: 9px 10px; border: 1px solid var(--line); border-radius: 9px;
      color: var(--ink); background: #fff; font-size: 11px;
    }
    .secondary:hover { background: var(--soft); }
    .toast {
      position: fixed; left: 50%; bottom: 104px; z-index: 80;
      padding: 10px 14px; border-radius: 10px;
      color: #fff; background: #1f2937;
      transform: translate(-50%, 20px); opacity: 0; pointer-events: none;
      transition: .2s ease;
      box-shadow: var(--shadow);
      font-size: 12px;
    }
    .toast.show { transform: translate(-50%, 0); opacity: 1; }
    @media (max-width: 800px) {
      .sidebar {
        position: fixed; inset: 0 auto 0 0; z-index: 60;
        transform: translateX(-105%);
      }
      .sidebar.open { transform: translateX(0); box-shadow: 20px 0 60px rgba(0,0,0,.25); }
      .mobile-menu { display: inline-block; }
      .topbar { padding: 0 13px; }
      .messages { padding: 22px 15px 160px; }
      .composer-wrap { padding-inline: 12px; }
      .suggestions { grid-template-columns: 1fr; }
      .welcome { margin-top: 5vh; }
      .quiz-layout { grid-template-columns: 1fr; overflow-y: auto; }
      .questions { overflow: visible; }
      .quiz-result { border-top: 1px solid var(--line); }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <div class="brand-mark">CC</div>
        <div><strong>Career Compass</strong><small>AI Career Advisor</small></div>
      </div>
      <button class="new-chat" id="newChat">＋ Cuộc trò chuyện mới</button>
      <div class="side-section">
        <p class="side-label">Cấp độ AI</p>
        <select class="level-select" id="level">
          <option value="1">Cấp 1 · Rule-based</option>
          <option value="2">Cấp 2 · LLM Chatbot</option>
          <option value="3" selected>Cấp 3 · ReAct Agent</option>
          <option value="4">Cấp 4 · Autonomous</option>
        </select>
      </div>
      <div class="side-section">
        <p class="side-label">Khám phá</p>
        <button class="side-action" id="openQuiz">◎ Trắc nghiệm 12 câu</button>
        <button class="side-action" id="openTrace">⌁ Xem Agent Trace</button>
      </div>
      <div class="side-footer">
        <div class="api-status">
          <span class="status-dot" id="statusDot"></span>
          <span id="apiStatus">Đang kiểm tra cấu hình...</span>
        </div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div>
          <button class="icon-button mobile-menu" id="mobileMenu">☰</button>
          <span class="topbar-title">Tư vấn định hướng nghề nghiệp</span>
        </div>
        <span class="topbar-meta" id="modeLabel">ReAct Agent · Có công cụ</span>
      </header>
      <section class="chat-shell">
        <div class="messages" id="messages">
          <div class="welcome" id="welcome">
            <div class="welcome-badge">✦</div>
            <h1>Bạn muốn khám phá điều gì về sự nghiệp?</h1>
            <p>Trao đổi tự nhiên với AI, làm trắc nghiệm định hướng hoặc tìm hiểu
              lương, lộ trình thăng tiến và kỹ năng cho nghề bạn quan tâm.</p>
            <div class="suggestions">
              <button class="suggestion" data-prompt="Tôi muốn được định hướng nghề nghiệp.">
                <strong>Bắt đầu định hướng</strong><span>Khám phá sở thích và nhóm nghề phù hợp</span>
              </button>
              <button class="suggestion" data-prompt="Công việc hàng ngày của Lập trình viên là gì?">
                <strong>Tìm hiểu một nghề</strong><span>Công việc, kỹ năng và môi trường làm việc</span>
              </button>
              <button class="suggestion" data-prompt="Lương và lộ trình thăng tiến của Lập trình viên thế nào?">
                <strong>Lương & thăng tiến</strong><span>Dữ liệu grounded từ công cụ nghề nghiệp</span>
              </button>
              <button class="suggestion" data-prompt="Tôi nên học như thế nào để trở thành Lập trình viên?">
                <strong>Xây lộ trình học</strong><span>Các kỹ năng nên học theo đúng thứ tự</span>
              </button>
            </div>
          </div>
        </div>
        <div class="composer-wrap">
          <div class="composer">
            <textarea id="input" rows="1" placeholder="Nhắn Career Compass..."></textarea>
            <button class="send" id="send" aria-label="Gửi tin nhắn">↑</button>
          </div>
          <div class="hint">Enter để gửi · Shift+Enter để xuống dòng · Kết quả chỉ mang tính tham khảo</div>
        </div>
      </section>
    </main>
  </div>

  <aside class="trace-panel" id="tracePanel">
    <div class="trace-head"><strong>Agent Trace</strong><button class="trace-close" id="closeTrace">×</button></div>
    <div class="trace-content trace-empty" id="traceContent">Chưa có trace. Hãy dùng Cấp 3 hoặc Cấp 4 và gửi câu hỏi cần gọi tool.</div>
  </aside>

  <div class="overlay" id="quizOverlay">
    <section class="quiz-modal">
      <header class="modal-head">
        <div><h2>Trắc nghiệm định hướng nghề nghiệp</h2><p>1 = hoàn toàn không đúng · 5 = rất đúng với bạn</p></div>
        <button class="modal-close" id="closeQuiz">×</button>
      </header>
      <div class="quiz-layout">
        <div class="questions" id="questions"></div>
        <div class="quiz-result">
          <button class="primary" id="analyzeQuiz">Phân tích kết quả</button>
          <div class="result-box" id="quizResult">Hoàn thành 12 câu hỏi để xem nhóm nghề phù hợp.</div>
          <select class="career-select" id="careerSelect"><option value="">Chọn nghề để tìm hiểu sâu</option></select>
          <div class="tool-row">
            <button class="secondary" id="careerProfile">Lương & thăng tiến</button>
            <button class="secondary" id="careerRoadmap">Lộ trình học</button>
          </div>
          <button class="primary" id="consultAI" style="margin-top:8px">Tiếp tục tư vấn với AI</button>
        </div>
      </div>
    </section>
  </div>
  <div class="toast" id="toast"></div>

  <script>
    const state = { history: [], trace: [], busy: false, bootstrap: null, quizAnswers: [] };
    const $ = (s) => document.querySelector(s);
    const messages = $("#messages");
    const input = $("#input");
    const send = $("#send");

    function toast(message) {
      const el = $("#toast"); el.textContent = message; el.classList.add("show");
      setTimeout(() => el.classList.remove("show"), 2200);
    }
    async function api(path, body) {
      const response = await fetch(path, {
        method: body === undefined ? "GET" : "POST",
        headers: body === undefined ? {} : {"Content-Type": "application/json"},
        body: body === undefined ? undefined : JSON.stringify(body)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Yêu cầu thất bại");
      return data;
    }
    function hideWelcome() { const welcome = $("#welcome"); if (welcome) welcome.remove(); }
    function addMessage(role, text, meta="") {
      hideWelcome();
      const row = document.createElement("article");
      row.className = `message ${role}`;
      const avatar = document.createElement("div");
      avatar.className = "avatar"; avatar.textContent = role === "user" ? "B" : "AI";
      const body = document.createElement("div"); body.className = "message-body";
      const name = document.createElement("div"); name.className = "message-name";
      name.textContent = role === "user" ? "Bạn" : "Career Compass";
      const content = document.createElement("div"); content.className = "message-text"; content.textContent = text;
      body.append(name, content);
      if (meta) { const m = document.createElement("div"); m.className = "message-meta"; m.textContent = meta; body.append(m); }
      row.append(avatar, body); messages.append(row); messages.scrollTop = messages.scrollHeight;
      return row;
    }
    function addTyping() {
      const row = addMessage("assistant", "");
      row.id = "typing";
      const content = row.querySelector(".message-text");
      content.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
    }
    function renderTrace(trace) {
      state.trace = trace || [];
      const box = $("#traceContent");
      if (!state.trace.length) {
        box.className = "trace-content trace-empty";
        box.textContent = "Chưa có trace. Hãy dùng Cấp 3 hoặc Cấp 4 và gửi câu hỏi cần gọi tool.";
        return;
      }
      box.className = "trace-content";
      box.textContent = state.trace.map(event => {
        if (event.type === "model") return `━━ STEP ${event.iteration} · MODEL ━━\n${event.content}`;
        if (event.type === "action") return `ACTION  ▶ ${event.tool} ${JSON.stringify(event.arguments)}`;
        return `OBSERVE ◀ ${event.content}`;
      }).join("\n\n");
    }
    async function sendMessage(prefill) {
      if (state.busy) return;
      const message = (prefill ?? input.value).trim();
      if (!message) return;
      state.busy = true; send.disabled = true; input.value = ""; resizeInput();
      addMessage("user", message); addTyping();
      try {
        const data = await api("/api/chat", {
          message, level: Number($("#level").value), history: state.history
        });
        $("#typing")?.remove();
        const plan = data.plan?.length ? `Kế hoạch: ${data.plan.join(" → ")}\n\n` : "";
        addMessage("assistant", plan + data.answer,
          `${data.iterations ?? 0} vòng · ${data.tool_calls ?? 0} tool call${data.guardrail ? " · Guardrail bật" : ""}`);
        state.history.push({role:"user", content:message}, {role:"assistant", content:data.answer});
        renderTrace(data.trace);
      } catch (error) {
        $("#typing")?.remove(); addMessage("assistant", `Không thể xử lý: ${error.message}`);
      } finally { state.busy = false; send.disabled = false; input.focus(); }
    }
    function resizeInput() { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 130) + "px"; }
    function updateMode() {
      const labels = {
        1:"Rule-based · Không dùng LLM", 2:"LLM Chatbot · Không có tool",
        3:"ReAct Agent · Có công cụ", 4:"Autonomous · Planning & Memory"
      };
      $("#modeLabel").textContent = labels[$("#level").value];
    }
    async function newChat() {
      state.history = []; renderTrace([]); messages.innerHTML = "";
      await api("/api/reset", {});
      location.reload();
    }
    function openQuiz() { $("#quizOverlay").classList.add("open"); $("#sidebar").classList.remove("open"); }
    function closeQuiz() { $("#quizOverlay").classList.remove("open"); }
    function buildQuiz(groups) {
      const container = $("#questions"); container.innerHTML = ""; state.quizAnswers = [];
      let index = 0;
      groups.forEach(group => {
        const section = document.createElement("section"); section.className = "question-group";
        const title = document.createElement("h3"); title.textContent = group.label; section.append(title);
        group.questions.forEach(question => {
          const current = index++;
          state.quizAnswers[current] = 3;
          const card = document.createElement("div"); card.className = "question-card";
          const label = document.createElement("label"); label.textContent = `${current + 1}. ${question}`;
          const row = document.createElement("div"); row.className = "range-row";
          row.append(document.createTextNode("1"));
          const range = document.createElement("input"); range.type = "range"; range.min = 1; range.max = 5; range.value = 3;
          const value = document.createElement("span"); value.className = "range-value"; value.textContent = "3";
          range.addEventListener("input", () => { state.quizAnswers[current] = Number(range.value); value.textContent = range.value; });
          row.append(range, document.createTextNode("5"), value); card.append(label, row); section.append(card);
        });
        container.append(section);
      });
    }
    async function analyzeQuiz() {
      try {
        const data = await api("/api/quiz/analyze", {answers: state.quizAnswers});
        $("#quizResult").textContent = data.result;
        const select = $("#careerSelect"); select.innerHTML = '<option value="">Chọn nghề để tìm hiểu sâu</option>';
        data.careers.forEach(career => { const option = document.createElement("option"); option.value = option.textContent = career; select.append(option); });
        if (data.careers.length) select.value = data.careers[0];
      } catch (error) { toast(error.message); }
    }
    async function careerTool(path) {
      const career = $("#careerSelect").value;
      if (!career) return toast("Hãy chọn một nghề trước");
      try {
        const data = await api(path, {career_name: career});
        $("#quizResult").textContent += `\n\n${data.result}`;
      } catch (error) { toast(error.message); }
    }
    function consultAI() {
      closeQuiz(); $("#level").value = "3"; updateMode();
      sendMessage(`Đây là 12 điểm bài trắc nghiệm của tôi theo đúng thứ tự: [${state.quizAnswers.join(", ")}]. Hãy phân tích và định hướng nghề nghiệp phù hợp.`);
    }
    async function bootstrap() {
      try {
        state.bootstrap = await api("/api/bootstrap");
        $("#apiStatus").textContent = state.bootstrap.config_message;
        $("#statusDot").classList.toggle("ready", state.bootstrap.configured);
        buildQuiz(state.bootstrap.quiz_groups);
      } catch (error) { $("#apiStatus").textContent = "Không kết nối được backend"; }
    }
    send.addEventListener("click", () => sendMessage());
    input.addEventListener("input", resizeInput);
    input.addEventListener("keydown", event => {
      if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); }
    });
    document.querySelectorAll("[data-prompt]").forEach(button => button.addEventListener("click", () => sendMessage(button.dataset.prompt)));
    $("#level").addEventListener("change", updateMode);
    $("#newChat").addEventListener("click", newChat);
    $("#openTrace").addEventListener("click", () => $("#tracePanel").classList.add("open"));
    $("#closeTrace").addEventListener("click", () => $("#tracePanel").classList.remove("open"));
    $("#openQuiz").addEventListener("click", openQuiz);
    $("#closeQuiz").addEventListener("click", closeQuiz);
    $("#quizOverlay").addEventListener("click", event => { if (event.target === $("#quizOverlay")) closeQuiz(); });
    $("#analyzeQuiz").addEventListener("click", analyzeQuiz);
    $("#careerProfile").addEventListener("click", () => careerTool("/api/career/profile"));
    $("#careerRoadmap").addEventListener("click", () => careerTool("/api/career/roadmap"));
    $("#consultAI").addEventListener("click", consultAI);
    $("#mobileMenu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
    updateMode(); bootstrap(); input.focus();
  </script>
</body>
</html>
"""


def _trace_payload(result: AgentResult) -> dict[str, Any]:
    return {
        "answer": result.answer,
        "trace": result.trace,
        "iterations": result.iterations,
        "tool_calls": result.tool_calls,
        "guardrail": result.guardrail_triggered,
    }


class CareerWebApplication:
    """State dùng chung cho một local web server."""

    def __init__(self, provider: Any, configured: bool, config_message: str):
        self.provider = provider
        self.configured = configured
        self.config_message = config_message
        self.autonomous = AutonomousCareerAgent(provider)
        self.memory_lock = threading.Lock()

    def bootstrap(self) -> dict[str, Any]:
        quiz_groups = []
        for group_name in GROUP_ORDER:
            quiz_groups.append(
                {
                    "name": group_name,
                    "label": GROUP_LABELS.get(group_name, group_name),
                    "questions": [question for question, _field in QUIZ_QUESTIONS[group_name]],
                }
            )
        return {
            "configured": self.configured,
            "config_message": self.config_message,
            "quiz_groups": quiz_groups,
            "careers": list(CAREER_DETAILS),
        }

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = str(payload.get("message", "")).strip()
        if not message:
            raise ValueError("Tin nhắn không được để trống.")
        level = int(payload.get("level", 3))
        history = payload.get("history", [])
        if not isinstance(history, list):
            history = []
        if level > 1 and not self.configured:
            raise ValueError("Chưa cấu hình OPENAI_API_KEY hợp lệ.")

        if level == 1:
            return {
                "answer": rule_based_bot(message),
                "trace": [],
                "iterations": 0,
                "tool_calls": 0,
                "guardrail": False,
            }
        if level == 2:
            return {
                "answer": llm_chatbot(message, self.provider, history),
                "trace": [],
                "iterations": 1,
                "tool_calls": 0,
                "guardrail": False,
            }
        if level == 4:
            with self.memory_lock:
                output = self.autonomous.execute(message)
            response = _trace_payload(output.agent_result)
            response.update({"plan": output.plan, "evaluation": output.evaluation})
            return response
        return _trace_payload(run_reactive_agent(message, self.provider, history))

    def reset(self) -> dict[str, bool]:
        with self.memory_lock:
            self.autonomous.clear_memory()
        return {"ok": True}

    @staticmethod
    def analyze_quiz(payload: dict[str, Any]) -> dict[str, Any]:
        answers = payload.get("answers", [])
        result = AVAILABLE_TOOLS["analyze_quiz_and_recommend_careers"](answers)
        careers = []
        for field_name in ("công nghệ", "kinh doanh", "sáng tạo", "xã hội"):
            if f"'{field_name}'" in result:
                careers = [
                    name
                    for name, details in CAREER_DETAILS.items()
                    if details["field"] == field_name
                ]
                break
        return {"result": result, "careers": careers}

    @staticmethod
    def career_tool(payload: dict[str, Any], tool_name: str) -> dict[str, str]:
        career_name = str(payload.get("career_name", "")).strip()
        if not career_name:
            raise ValueError("Hãy chọn một nghề.")
        return {"result": str(AVAILABLE_TOOLS[tool_name](career_name))}


def make_handler(application: CareerWebApplication) -> type[BaseHTTPRequestHandler]:
    """Tạo HTTP handler gắn với application hiện tại."""

    class Handler(BaseHTTPRequestHandler):
        server_version = "CareerCompass/1.0"

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def _read_json(self) -> dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > 1_000_000:
                return {}
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("JSON request không hợp lệ.") from exc
            if not isinstance(payload, dict):
                raise ValueError("Request body phải là JSON object.")
            return payload

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/":
                content = PAGE_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
            elif path == "/api/bootstrap":
                self._send_json(application.bootstrap())
            else:
                self._send_json({"error": "Không tìm thấy endpoint."}, 404)

        def do_POST(self) -> None:
            path = self.path.split("?", 1)[0]
            try:
                payload = self._read_json()
                if path == "/api/chat":
                    result = application.chat(payload)
                elif path == "/api/reset":
                    result = application.reset()
                elif path == "/api/quiz/analyze":
                    result = application.analyze_quiz(payload)
                elif path == "/api/career/profile":
                    result = application.career_tool(payload, "get_career_profile")
                elif path == "/api/career/roadmap":
                    result = application.career_tool(payload, "generate_learning_roadmap")
                else:
                    self._send_json({"error": "Không tìm thấy endpoint."}, 404)
                    return
                self._send_json(result)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
            except Exception:
                self._send_json(
                    {"error": "Backend gặp lỗi khi xử lý yêu cầu. Vui lòng thử lại."},
                    500,
                )

    return Handler


def create_web_server(
    provider: Any,
    configured: bool,
    config_message: str,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> ThreadingHTTPServer:
    """Tạo server riêng để CLI và test có thể quản lý vòng đời."""
    application = CareerWebApplication(provider, configured, config_message)
    return ThreadingHTTPServer((host, port), make_handler(application))


def launch_web_ui(
    provider: Any,
    configured: bool,
    config_message: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
) -> int:
    """Chạy giao diện web cục bộ cho đến khi người dùng nhấn Ctrl+C."""
    try:
        server = create_web_server(provider, configured, config_message, host, port)
    except OSError as exc:
        print(f"Không thể mở web server tại {host}:{port}: {exc}")
        return 1

    actual_host, actual_port = server.server_address[:2]
    browser_host = "127.0.0.1" if actual_host in {"0.0.0.0", "::"} else actual_host
    url = f"http://{browser_host}:{actual_port}"
    print(f"Career Compass đang chạy tại: {url}")
    print("Nhấn Ctrl+C để dừng.")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng Career Compass.")
    finally:
        server.server_close()
    return 0
