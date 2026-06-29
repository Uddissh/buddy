#!/usr/bin/env python3
"""Buddy — Your Terminal AI Companion"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.memory import init_db


def main():
    init_db()
    args = sys.argv[1:]

    if not args:
        from src.tui import start_tui
        start_tui()
    else:
        one_shot(" ".join(args))


def one_shot(message: str):
    import asyncio
    from src.command_parser import parse_command, CommandType
    from src.memory import (
        add_fact, add_task, update_task_status,
        delete_task, delete_fact, get_facts, get_tasks
    )
    from src.plugins.registry import execute_file_task
    from src.plugins.shell_plugin import ShellPlugin

    cmd = parse_command(message)

    if cmd.type == CommandType.REMEMBER:
        add_fact(cmd.args["content"])
        print(f"✅ Remembered: {cmd.args['content']}")

    elif cmd.type == CommandType.ADD_TASK:
        add_task(cmd.args["title"])
        print(f"✅ Task added: {cmd.args['title']}")

    elif cmd.type == CommandType.LIST_TASKS:
        tasks = get_tasks()
        if not tasks:
            print("No tasks yet.")
        for t in tasks:
            icon = "✓" if t["status"] == "done" else "○"
            print(f"  {icon} [{t['id']}] {t['title']}")

    elif cmd.type == CommandType.LIST_MEMORY:
        facts = get_facts()
        if not facts:
            print("No memories yet.")
        for f in facts:
            print(f"  [{f['id']}] {f['content']}")

    elif cmd.type == CommandType.RUN_SHELL:
        plugin = ShellPlugin()
        print(plugin.execute(cmd.args["command"], ""))

    elif cmd.type == CommandType.FILE_OP:
        print(execute_file_task(cmd.args["file_path"], cmd.args["task"]))

    elif cmd.type == CommandType.CHAT:
        async def run():
            from src.agent import stream_response
            async def on_chunk(chunk):
                print(chunk, end="", flush=True)
            await stream_response(message, on_chunk)
            print()
        asyncio.run(run())

    else:
        print(f"Unknown command. Try: buddy 'remember I like coffee'")


if __name__ == "__main__":
    main()
