from pathlib import Path

from .pdf_plugin   import PDFPlugin
from .docx_plugin  import DOCXPlugin
from .pptx_plugin  import PPTXPlugin
from .image_plugin import ImagePlugin
from .video_plugin import VideoPlugin
from .text_plugin  import TextPlugin

PLUGINS = [
    PDFPlugin(),
    DOCXPlugin(),
    PPTXPlugin(),
    ImagePlugin(),
    VideoPlugin(),
    TextPlugin(),
]


def get_plugin_for_file(file_path: str):
    ext = Path(file_path).suffix.lower().lstrip(".")
    for plugin in PLUGINS:
        if plugin.can_handle(ext):
            return plugin
    return None


def supported_extensions() -> list[str]:
    exts = []
    for p in PLUGINS:
        exts.extend(p.supported_extensions)
    return sorted(set(exts))


def execute_file_task(file_path: str, task: str) -> str:
    from ..memory import add_file_history

    plugin = get_plugin_for_file(file_path)
    if not plugin:
        ext = Path(file_path).suffix
        return (
            f"❌ No plugin for '{ext}' files.\n"
            f"Supported: {', '.join(supported_extensions())}"
        )
    try:
        result = plugin.execute(file_path, task)
        add_file_history(file_path, task, "success")
        return result
    except FileNotFoundError as e:
        add_file_history(file_path, task, "error", str(e))
        return f"❌ {e}"
    except Exception as e:
        add_file_history(file_path, task, "error", str(e))
        return f"❌ Plugin error ({plugin.name}): {e}"
