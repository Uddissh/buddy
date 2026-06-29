import os
import subprocess
from .base import BuddyPlugin


class ShellPlugin(BuddyPlugin):
    name = "shell"
    supported_extensions = []
    description = "Execute shell commands"

    def execute(self, command: str, _task: str = "") -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.expanduser("~"),
            )
            parts = []
            if result.stdout:
                parts.append(result.stdout.strip())
            if result.stderr:
                parts.append(f"[stderr]\n{result.stderr.strip()}")

            code = result.returncode
            icon = "✅" if code == 0 else "❌"
            body = "\n".join(parts) if parts else "(no output)"
            return f"{icon} exit {code}\n{body}"

        except subprocess.TimeoutExpired:
            return "❌ Command timed out (30 s limit)"
        except Exception as e:
            return f"❌ Error: {e}"
