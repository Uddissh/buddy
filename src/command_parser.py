import re
from dataclasses import dataclass, field
from enum import Enum


class CommandType(Enum):
    REMEMBER    = "remember"
    FORGET      = "forget"
    ADD_TASK    = "add_task"
    DONE_TASK   = "done_task"
    DELETE_TASK = "delete_task"
    LIST_TASKS  = "list_tasks"
    LIST_MEMORY = "list_memory"
    RUN_SHELL   = "run_shell"
    FILE_OP     = "file_op"
    CHAT        = "chat"
    QUIT        = "quit"
    HELP        = "help"
    CONFIG      = "config"


@dataclass
class ParsedCommand:
    type: CommandType
    args: dict = field(default_factory=dict)


def parse_command(text: str) -> ParsedCommand:
    t = text.strip()
    lo = t.lower()

    # ── Quit ──────────────────────────────────────────────────────────────────
    if lo in {"quit", "exit", "bye", ":q"}:
        return ParsedCommand(CommandType.QUIT)

    # ── Help ──────────────────────────────────────────────────────────────────
    if lo in {"help", "?", ":h"}:
        return ParsedCommand(CommandType.HELP)

    # ── List tasks ────────────────────────────────────────────────────────────
    if lo in {"tasks", "list tasks", "show tasks", ":t"}:
        return ParsedCommand(CommandType.LIST_TASKS)

    # ── List memory ───────────────────────────────────────────────────────────
    if lo in {"memory", "facts", "show memory", ":m"}:
        return ParsedCommand(CommandType.LIST_MEMORY)

    # ── Config ────────────────────────────────────────────────────────────────
    if lo in {"config", "settings", ":c"}:
        return ParsedCommand(CommandType.CONFIG)

    # ── Remember ──────────────────────────────────────────────────────────────
    m = re.match(r"^remember\s+(?:that\s+)?(.+)$", t, re.I)
    if m:
        return ParsedCommand(CommandType.REMEMBER, {"content": m.group(1).strip()})

    # ── Forget ────────────────────────────────────────────────────────────────
    m = re.match(r"^forget\s+#?(\d+)$", t, re.I)
    if m:
        return ParsedCommand(CommandType.FORGET, {"id": int(m.group(1))})

    # ── Add task ──────────────────────────────────────────────────────────────
    m = re.match(r"^(?:add\s+)?(?:task|todo)[:\s]+(.+)$", t, re.I)
    if m:
        return ParsedCommand(CommandType.ADD_TASK, {"title": m.group(1).strip()})

    # ── Done task ─────────────────────────────────────────────────────────────
    m = re.match(r"^(?:done|complete|finish)\s+(?:task\s+)?#?(\d+)$", t, re.I)
    if not m:
        m = re.match(r"^mark\s+#?(\d+)\s+(?:as\s+)?done$", t, re.I)
    if m:
        return ParsedCommand(CommandType.DONE_TASK, {"id": int(m.group(1))})

    # ── Delete task ───────────────────────────────────────────────────────────
    m = re.match(r"^(?:delete|remove)\s+task\s+#?(\d+)$", t, re.I)
    if m:
        return ParsedCommand(CommandType.DELETE_TASK, {"id": int(m.group(1))})

    # ── Shell ─────────────────────────────────────────────────────────────────
    m = re.match(r"^(?:run|execute|shell|cmd)[:\s]+(.+)$", t, re.I)
    if not m:
        m = re.match(r"^\$\s*(.+)$", t)
    if m:
        return ParsedCommand(CommandType.RUN_SHELL, {"command": m.group(1).strip()})

    # ── File op: "path/to/file.ext: task description" ────────────────────────
    m = re.match(r"^([^\s:]+\.\w+)\s*:\s*(.+)$", t, re.I)
    if m:
        return ParsedCommand(CommandType.FILE_OP, {
            "file_path": m.group(1).strip(),
            "task":      m.group(2).strip(),
        })

    # ── Default: chat ─────────────────────────────────────────────────────────
    return ParsedCommand(CommandType.CHAT, {"message": t})
