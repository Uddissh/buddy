# 🤖 Buddy — Terminal AI Companion

A Rich TUI terminal companion powered by Ollama (local LLM).  
Chats with you, stores memories, manages tasks, and edits files — all from the terminal.

---

## Features

| Category | What Buddy can do |
|----------|------------------|
| 💬 Chat | Stream conversations with your local Ollama model |
| 🧠 Memory | Store & recall facts across sessions (SQLite) |
| ✅ Tasks | Add, list, complete, delete tasks |
| 📄 PDF | Extract text, watermark, merge, split, compress |
| 📝 Word | Read, append, find/replace DOCX files |
| 📊 Slides | Read, add slides, find/replace PPTX |
| 🖼️ Images | Resize, crop, convert, compress, grayscale (Pillow) |
| 🎬 Video | Info, trim, convert, extract audio, compress (ffmpeg) |
| 📁 Text/Code | Read, append, find/replace any text or code file |
| 🖥️ Shell | Run shell commands with output capture |

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) running on another machine (Hermes)
- ffmpeg (optional, for video ops): `sudo apt install ffmpeg`

---

## Installation

```bash
git clone https://github.com/Uddissh/buddy.git
cd buddy
chmod +x setup.sh
./setup.sh
```

The setup script will ask for:
- **Hermes IP** — the LAN IP of your Ollama server
- **Your name** — used in Buddy's greeting & system prompt
- **Model** — e.g. `gemma3:4b`, `qwen3:1.7b`

Then just type:

```bash
buddy
```

---

## Usage

### TUI mode (default)
```bash
buddy
```

### One-shot mode
```bash
buddy "remember I have an exam on Monday"
buddy "tasks"
buddy "resume.pdf: extract text"
buddy "$ ls -la"
```

---

## Command Reference

```
Memory
  remember <fact>          Store a memory
  forget #<id>             Delete a memory
  memory                   List all memories

Tasks
  task: <title>            Add a task
  tasks                    List all tasks
  done #<id>               Mark task done
  delete task #<id>        Delete task

Files
  <file.ext>: <action>     Examples:
    resume.pdf: extract text
    photo.jpg: resize 800x600
    notes.docx: read
    clip.mp4: trim from 0:30 to 1:45
    script.py: read

Shell
  run: <command>           Run a shell command
  $ <command>              Shorthand

Other
  config                   Show current config
  help                     Show all commands
  quit / exit              Exit Buddy
```

### TUI Keybindings
| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit |
| `Ctrl+L` | Clear chat |
| `Ctrl+T` | Quick-fill tasks |
| `Ctrl+M` | Quick-fill memory |

---

## Config

Config lives at `~/.buddy/config.json`:

```json
{
  "hermes_ip":   "192.168.1.100",
  "hermes_port": 11434,
  "model":       "gemma3:4b",
  "user_name":   "Uddissh",
  "max_history": 20,
  "stream":      true
}
```

---

## Data

All data is stored locally in `~/.buddy/`:

```
~/.buddy/
├── config.json     ← your settings
├── db.sqlite       ← conversations, facts, tasks, file history
└── logs/           ← future audit logs
```

---

## Roadmap — V2

- 🎤 Voice input via `faster-whisper`
- 🔊 Voice output via `piper` TTS
- 🌐 Web browsing agent
- 🤖 Autonomous code writing + execution
- 🔗 Git operations
- 🔔 Reminders & scheduled tasks

---

## Plugin System

Each file type is handled by a plugin in `src/plugins/`.  
Adding a new plugin is simple:

```python
# src/plugins/my_plugin.py
from .base import BuddyPlugin

class MyPlugin(BuddyPlugin):
    name = "myplugin"
    supported_extensions = ["xyz"]
    description = "Handle .xyz files"

    def execute(self, file_path: str, task: str) -> str:
        ...
```

Then register it in `src/plugins/registry.py`.

---

## License

MIT
