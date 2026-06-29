import json
from pathlib import Path

BUDDY_DIR = Path.home() / ".buddy"
CONFIG_FILE = BUDDY_DIR / "config.json"
DB_FILE = BUDDY_DIR / "db.sqlite"
LOGS_DIR = BUDDY_DIR / "logs"

DEFAULT_CONFIG = {
    "hermes_ip": "192.168.1.100",
    "hermes_port": 11434,
    "model": "gemma3:4b",
    "name": "Buddy",
    "user_name": "User",
    "max_history": 20,
    "stream": True,
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE) as f:
        return {**DEFAULT_CONFIG, **json.load(f)}


def save_config(config: dict) -> None:
    BUDDY_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_ollama_url(config: dict) -> str:
    return f"http://{config['hermes_ip']}:{config['hermes_port']}"
