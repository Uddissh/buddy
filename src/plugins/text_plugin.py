import os
import re
from pathlib import Path
from .base import BuddyPlugin


class TextPlugin(BuddyPlugin):
    name = "text"
    supported_extensions = [
        # Prose
        "txt", "md", "markdown", "rst", "log", "csv", "tsv", "xml",
        # Config
        "json", "yaml", "yml", "toml", "ini", "cfg", "env", "conf",
        # Code
        "py", "js", "ts", "jsx", "tsx", "html", "css", "scss", "sass",
        "sh", "bash", "zsh", "fish", "c", "cpp", "h", "hpp",
        "java", "go", "rs", "rb", "php", "swift", "kt", "lua", "r",
        "sql", "graphql", "proto",
    ]
    description = "Read and edit text and code files"

    def execute(self, file_path: str, task: str) -> str:
        path = self.validate_file(file_path)
        lo = task.lower()

        if any(k in lo for k in ["read", "show", "cat", "content", "view", "open"]):
            return self._read(path)
        if any(k in lo for k in ["append", "add line", "add text"]):
            return self._append(path, task)
        if any(k in lo for k in ["replace", "find"]):
            return self._replace(path, task)
        if any(k in lo for k in ["lines", "wc", "count words", "word count"]):
            return self._wc(path)
        if any(k in lo for k in ["info", "metadata", "meta"]):
            return self._info(path)
        if any(k in lo for k in ["clear", "empty", "wipe"]):
            return self._clear(path)
        # Default
        return self._read(path)

    def _read(self, path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"❌ Could not read: {e}"
        if not text.strip():
            return "📄 File is empty."
        if len(text) > 3000:
            return f"📄 {path.name} (first 3000 chars):\n\n{text[:3000]}…"
        return f"📄 {path.name}:\n\n{text}"

    def _append(self, path: Path, task: str) -> str:
        m = re.search(r'(?:append|add)[:\s]+(.+)', task, re.I | re.DOTALL)
        if not m:
            return "❌ Format: append: your new content here"
        content = m.group(1).strip()
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(f"\n{content}")
        return f"✅ Appended to {path.name}"

    def _replace(self, path: Path, task: str) -> str:
        m = re.search(r'replace\s+"(.+?)"\s+with\s+"(.+?)"', task, re.I)
        if not m:
            m = re.search(r'replace\s+(.+?)\s+with\s+(.+)', task, re.I)
        if not m:
            return '❌ Format: replace "old" with "new"'
        old, new = m.group(1).strip(), m.group(2).strip()
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count == 0:
            return f"❌ '{old}' not found in {path.name}"
        path.write_text(text.replace(old, new), encoding="utf-8")
        return f"✅ Replaced {count} instance(s) in {path.name}"

    def _wc(self, path: Path) -> str:
        text = path.read_text(encoding="utf-8", errors="replace")
        return (
            f"📄 {path.name}\n"
            f"   Lines: {text.count(chr(10)) + 1}\n"
            f"   Words: {len(text.split())}\n"
            f"   Chars: {len(text)}"
        )

    def _info(self, path: Path) -> str:
        size = os.path.getsize(str(path))
        ext = path.suffix[1:].upper() if path.suffix else "Text"
        text = path.read_text(encoding="utf-8", errors="replace")
        return (
            f"📄 {path.name}\n"
            f"   Type:  {ext}\n"
            f"   Size:  {size} bytes\n"
            f"   Lines: {text.count(chr(10)) + 1}"
        )

    def _clear(self, path: Path) -> str:
        path.write_text("", encoding="utf-8")
        return f"✅ {path.name} cleared."
