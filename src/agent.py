import httpx
import json
from typing import Callable, Awaitable

from .config import load_config, get_ollama_url
from .memory import get_recent_history, get_facts, get_tasks, add_message

_SYSTEM = """\
You are Buddy, a warm and smart terminal AI companion for {user_name}.

You help with:
- Conversations & answering questions
- Remembering facts  (user says "remember…" → you confirm)
- Managing tasks      (user says "task: …", "done #id")
- File operations     (PDF, Word, images, video, code …)
- Running shell commands ("run: ls -la")

Known facts about {user_name}:
{facts}

Pending tasks:
{tasks}

Be concise, friendly, and direct. If someone asks you to remember something,
always confirm it. If they mention a new task, suggest they add it."""


def _build_system(config: dict) -> str:
    facts = get_facts()
    tasks = get_tasks(status="pending")
    facts_str = "\n".join(f"• {f['content']}" for f in facts) or "None yet."
    tasks_str = "\n".join(f"• [{t['id']}] {t['title']}" for t in tasks) or "No pending tasks."
    return _SYSTEM.format(
        user_name=config.get("user_name", "User"),
        facts=facts_str,
        tasks=tasks_str,
    )


async def stream_response(
    user_message: str,
    callback: Callable[[str], Awaitable[None]],
) -> str:
    """Stream a response from Ollama, calling callback with each text chunk."""
    config = load_config()
    url = get_ollama_url(config) + "/api/chat"

    history = get_recent_history(config.get("max_history", 20))
    messages = [
        {"role": "system", "content": _build_system(config)},
        *history,
        {"role": "user", "content": user_message},
    ]

    payload = {
        "model": config.get("model", "gemma3:4b"),
        "messages": messages,
        "stream": True,
    }

    full_response = ""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            full_response += chunk
                            await callback(chunk)
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass

    except httpx.ConnectError:
        ip = config["hermes_ip"]
        port = config["hermes_port"]
        msg = f"❌ Cannot reach Hermes at {ip}:{port}. Check config: ~/.buddy/config.json"
        await callback(msg)
        return msg

    except Exception as e:
        msg = f"❌ Error: {e}"
        await callback(msg)
        return msg

    if full_response:
        add_message("user", user_message)
        add_message("assistant", full_response)

    return full_response
