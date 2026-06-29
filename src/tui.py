from __future__ import annotations

import asyncio
from pathlib import Path

from rich.markup import escape
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Static

from .agent import stream_response
from .command_parser import CommandType, parse_command
from .config import load_config
from .memory import (
    add_fact,
    add_task,
    delete_fact,
    delete_task,
    get_facts,
    get_file_history,
    get_recent_history,
    get_tasks,
    update_task_status,
)


# ── Widgets ───────────────────────────────────────────────────────────────────

class ChatMessage(Static):
    """Single chat bubble."""

    def __init__(self, role: str, content: str, **kw):
        if role == "user":
            markup = f"[bold #58a6ff]You ›[/bold #58a6ff] [#e6edf3]{escape(content)}[/#e6edf3]"
        elif role == "system":
            markup = f"[dim]{escape(content)}[/dim]"
        else:
            markup = f"[bold #3fb950]Buddy ›[/bold #3fb950] [#e6edf3]{content}[/#e6edf3]"
        super().__init__(markup, **kw)
        self.styles.margin = (0, 0, 1, 0)


class ChatScroll(ScrollableContainer):
    pass


# ── App ───────────────────────────────────────────────────────────────────────

class BuddyApp(App):
    TITLE = "BUDDY"
    SUB_TITLE = "Terminal AI Companion"
    BINDINGS = [
        ("ctrl+q", "quit",        "Quit"),
        ("ctrl+l", "clear",       "Clear chat"),
        ("ctrl+t", "focus_tasks", "Tasks"),
        ("ctrl+m", "focus_mem",   "Memory"),
    ]

    CSS = """
    Screen { background: #0d1117; }

    Header {
        background: #161b22;
        color: #58a6ff;
        text-style: bold;
    }

    #main { height: 1fr; }

    /* ── Chat panel ── */
    #chat-panel {
        width: 3fr;
        border: tall #21262d;
    }

    #chat-scroll {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    #streaming {
        height: auto;
        min-height: 2;
        padding: 0 2 1 2;
        color: #e6edf3;
    }

    #input-row {
        height: 3;
        background: #161b22;
        border-top: tall #21262d;
    }

    #user-input {
        background: #0d1117;
        color: #e6edf3;
        border: none;
        padding: 0 2;
    }

    #user-input:focus { border: none; }

    /* ── Sidebar ── */
    #sidebar {
        width: 28;
        background: #161b22;
        border: tall #21262d;
        padding: 1;
    }

    .section-title {
        color: #58a6ff;
        text-style: bold;
        padding: 0 0 1 0;
    }

    .section-content {
        color: #8b949e;
        padding: 0 0 1 0;
    }

    .divider {
        color: #21262d;
        padding: 0 0 1 0;
    }

    Footer { background: #161b22; color: #8b949e; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="chat-panel"):
                yield ChatScroll(id="chat-scroll")
                yield Static("", id="streaming")
                with Vertical(id="input-row"):
                    yield Input(
                        placeholder="Talk to Buddy… ('help' for commands)",
                        id="user-input",
                    )
            with Vertical(id="sidebar"):
                yield Static("🧠 MEMORY",  classes="section-title")
                yield Static("",           id="mem-content",  classes="section-content")
                yield Static("─" * 22,     classes="divider")
                yield Static("✅ TASKS",   classes="section-title")
                yield Static("",           id="task-content", classes="section-content")
                yield Static("─" * 22,     classes="divider")
                yield Static("📁 FILES",   classes="section-title")
                yield Static("",           id="file-content", classes="section-content")
        yield Footer()

    def on_mount(self) -> None:
        cfg = load_config()
        self.query_one("#user-input", Input).focus()

        # Load last N messages
        chat = self.query_one("#chat-scroll", ChatScroll)
        history = get_recent_history(10)
        if history:
            chat.mount(ChatMessage("system", "── previous session ──"))
            for msg in history:
                chat.mount(ChatMessage(msg["role"], msg["content"]))
            chat.mount(ChatMessage("system", "── new session ──"))

        user = cfg.get("user_name", "there")
        chat.mount(ChatMessage("buddy", f"Hey {user}! 👋 How can I help?"))
        chat.scroll_end(animate=False)
        self._refresh_sidebar()

    # ── Input handler ─────────────────────────────────────────────────────────

    @on(Input.Submitted, "#user-input")
    async def handle_input(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        self.query_one("#user-input", Input).value = ""
        self._process(text)

    # ── Worker (runs in event loop) ───────────────────────────────────────────

    @work(exclusive=False)
    async def _process(self, text: str) -> None:
        chat = self.query_one("#chat-scroll", ChatScroll)
        streaming = self.query_one("#streaming", Static)

        chat.mount(ChatMessage("user", text))
        chat.scroll_end(animate=False)

        cmd = parse_command(text)

        # ── Local commands ────────────────────────────────────────────────────

        if cmd.type == CommandType.QUIT:
            self.exit()
            return

        if cmd.type == CommandType.HELP:
            chat.mount(ChatMessage("buddy", self._help()))

        elif cmd.type == CommandType.REMEMBER:
            add_fact(cmd.args["content"])
            chat.mount(ChatMessage("buddy", f"✅ Got it! Remembered: [italic]{cmd.args['content']}[/italic]"))
            self._refresh_sidebar()

        elif cmd.type == CommandType.FORGET:
            delete_fact(cmd.args["id"])
            chat.mount(ChatMessage("buddy", f"🗑️ Removed memory #{cmd.args['id']}"))
            self._refresh_sidebar()

        elif cmd.type == CommandType.ADD_TASK:
            add_task(cmd.args["title"])
            chat.mount(ChatMessage("buddy", f"📋 Task added: [italic]{cmd.args['title']}[/italic]"))
            self._refresh_sidebar()

        elif cmd.type == CommandType.LIST_TASKS:
            tasks = get_tasks()
            if not tasks:
                chat.mount(ChatMessage("buddy", "No tasks yet! Use: task: <title>"))
            else:
                lines = []
                for t in tasks:
                    icon = "[#3fb950]✓[/#3fb950]" if t["status"] == "done" else "[#f0883e]○[/#f0883e]"
                    lines.append(f"{icon} [{t['id']}] {t['title']}")
                chat.mount(ChatMessage("buddy", "\n".join(lines)))

        elif cmd.type == CommandType.LIST_MEMORY:
            facts = get_facts()
            if not facts:
                chat.mount(ChatMessage("buddy", "No memories yet! Use: remember <fact>"))
            else:
                lines = [f"[#{f['id']}] {f['content']}" for f in facts]
                chat.mount(ChatMessage("buddy", "\n".join(lines)))

        elif cmd.type == CommandType.DONE_TASK:
            update_task_status(cmd.args["id"], "done")
            chat.mount(ChatMessage("buddy", f"✅ Task #{cmd.args['id']} done!"))
            self._refresh_sidebar()

        elif cmd.type == CommandType.DELETE_TASK:
            delete_task(cmd.args["id"])
            chat.mount(ChatMessage("buddy", f"🗑️ Task #{cmd.args['id']} deleted"))
            self._refresh_sidebar()

        elif cmd.type == CommandType.RUN_SHELL:
            cmd_str = cmd.args["command"]
            streaming.update(f"[bold #3fb950]Buddy ›[/bold #3fb950] [dim]$ {escape(cmd_str)}[/dim]")
            from .plugins.shell_plugin import ShellPlugin
            result = await asyncio.get_event_loop().run_in_executor(
                None, ShellPlugin().execute, cmd_str, ""
            )
            streaming.update("")
            chat.mount(ChatMessage("buddy", result))

        elif cmd.type == CommandType.FILE_OP:
            fp, task = cmd.args["file_path"], cmd.args["task"]
            streaming.update(f"[bold #3fb950]Buddy ›[/bold #3fb950] [dim]Processing {escape(fp)}…[/dim]")
            from .plugins.registry import execute_file_task
            result = await asyncio.get_event_loop().run_in_executor(
                None, execute_file_task, fp, task
            )
            streaming.update("")
            chat.mount(ChatMessage("buddy", result))
            self._refresh_sidebar()

        elif cmd.type == CommandType.CONFIG:
            cfg = load_config()
            info = (
                f"[bold]Config[/bold] (~/.buddy/config.json)\n"
                f"• Hermes: {cfg['hermes_ip']}:{cfg['hermes_port']}\n"
                f"• Model:  {cfg['model']}\n"
                f"• Name:   {cfg['user_name']}"
            )
            chat.mount(ChatMessage("buddy", info))

        # ── LLM chat ──────────────────────────────────────────────────────────

        elif cmd.type == CommandType.CHAT:
            streaming.update("[bold #3fb950]Buddy ›[/bold #3fb950] [dim]thinking…[/dim]")
            full = ""

            async def on_chunk(chunk: str) -> None:
                nonlocal full
                full += chunk
                streaming.update(
                    f"[bold #3fb950]Buddy ›[/bold #3fb950] {escape(full)}[blink]▌[/blink]"
                )
                await asyncio.sleep(0)

            await stream_response(text, on_chunk)
            streaming.update("")
            chat.mount(ChatMessage("buddy", full or "❌ No response. Is Hermes reachable?"))

        chat.scroll_end(animate=False)

    # ── Sidebar refresh ───────────────────────────────────────────────────────

    def _refresh_sidebar(self) -> None:
        # Memory
        facts = get_facts()
        if facts:
            mem_lines = []
            for f in facts[:5]:
                snippet = f["content"][:22] + "…" if len(f["content"]) > 22 else f["content"]
                mem_lines.append(f"[dim]#{f['id']}[/dim] {snippet}")
            mem_text = "\n".join(mem_lines)
        else:
            mem_text = "[dim]None. Say 'remember…'[/dim]"
        self.query_one("#mem-content", Static).update(mem_text)

        # Tasks
        tasks = get_tasks()
        if tasks:
            lines = []
            for t in [x for x in tasks if x["status"] == "pending"][:4]:
                lines.append(f"[#f0883e]○[/#f0883e] [dim]#{t['id']}[/dim] {t['title'][:18]}")
            for t in [x for x in tasks if x["status"] == "done"][:2]:
                lines.append(f"[#3fb950]✓[/#3fb950] [dim]#{t['id']}[/dim] {t['title'][:18]}")
            task_text = "\n".join(lines) or "[dim]All done![/dim]"
        else:
            task_text = "[dim]None. Use 'task: …'[/dim]"
        self.query_one("#task-content", Static).update(task_text)

        # Files
        hist = get_file_history(4)
        if hist:
            file_text = "\n".join(f"• {Path(h['file_path']).name}" for h in hist)
        else:
            file_text = "[dim]No files yet.[/dim]"
        self.query_one("#file-content", Static).update(file_text)

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_clear(self) -> None:
        for child in list(self.query_one("#chat-scroll", ChatScroll).children):
            child.remove()

    def action_focus_tasks(self) -> None:
        inp = self.query_one("#user-input", Input)
        inp.value = "tasks"
        inp.focus()

    def action_focus_mem(self) -> None:
        inp = self.query_one("#user-input", Input)
        inp.value = "memory"
        inp.focus()

    # ── Help text ─────────────────────────────────────────────────────────────

    @staticmethod
    def _help() -> str:
        return """\
[bold #58a6ff]Buddy Commands[/bold #58a6ff]

[#3fb950]Memory[/#3fb950]
  remember <fact>          store a memory
  forget #<id>             delete a memory
  memory                   list all memories

[#3fb950]Tasks[/#3fb950]
  task: <title>            add a task
  tasks                    list all tasks
  done #<id>               mark task done
  delete task #<id>        delete task

[#3fb950]Files[/#3fb950]
  <file.ext>: <action>     e.g. resume.pdf: extract text
                           e.g. photo.jpg: resize 800x600
                           e.g. notes.docx: read

[#3fb950]Shell[/#3fb950]
  run: <command>           run shell command
  $ <command>              shorthand

[#3fb950]Other[/#3fb950]
  config                   show current config
  help                     this message
  quit / exit              exit Buddy

[dim]Ctrl+Q quit  Ctrl+L clear  Ctrl+T tasks  Ctrl+M memory[/dim]"""


def start_tui() -> None:
    BuddyApp().run()
