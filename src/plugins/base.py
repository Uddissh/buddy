from abc import ABC, abstractmethod
from pathlib import Path


class BuddyPlugin(ABC):
    name: str = "base"
    supported_extensions: list[str] = []
    description: str = ""

    @abstractmethod
    def execute(self, file_path: str, task: str) -> str:
        """Execute a task on the file. Returns result message."""
        pass

    def can_handle(self, extension: str) -> bool:
        return extension.lower().lstrip(".") in [e.lower() for e in self.supported_extensions]

    def validate_file(self, file_path: str) -> Path:
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path
