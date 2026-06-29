import os
import re
from pathlib import Path
from .base import BuddyPlugin


class ImagePlugin(BuddyPlugin):
    name = "image"
    supported_extensions = [
        "jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif", "ico",
    ]
    description = "Resize, crop, convert, compress images via Pillow"

    def execute(self, file_path: str, task: str) -> str:
        path = self.validate_file(file_path)
        try:
            from PIL import Image
        except ImportError:
            return "❌ Pillow not installed. Run: pip install Pillow"

        lo = task.lower()
        if any(k in lo for k in ["info", "size", "dimensions", "meta"]):
            return self._info(path, Image)
        if any(k in lo for k in ["resize", "scale"]):
            return self._resize(path, task, Image)
        if any(k in lo for k in ["convert", "to png", "to jpg", "to webp", "to bmp"]):
            return self._convert(path, task, Image)
        if any(k in lo for k in ["grayscale", "greyscale", "black and white", " bw", "b&w"]):
            return self._grayscale(path, Image)
        if "crop" in lo:
            return self._crop(path, task, Image)
        if any(k in lo for k in ["compress", "optimize", "reduce size"]):
            return self._compress(path, Image)
        if any(k in lo for k in ["rotate", "flip"]):
            return self._rotate(path, task, Image)
        if any(k in lo for k in ["thumbnail", "thumb"]):
            return self._thumbnail(path, task, Image)
        return self._info(path, Image)

    def _info(self, path: Path, Image) -> str:
        img = Image.open(str(path))
        size = os.path.getsize(str(path))
        result = (
            f"🖼️ {path.name}\n"
            f"   Format:    {img.format}\n"
            f"   Dimensions:{img.size[0]}×{img.size[1]} px\n"
            f"   Mode:      {img.mode}\n"
            f"   File size: {size // 1024} KB"
        )
        img.close()
        return result

    def _resize(self, path: Path, task: str, Image) -> str:
        # "resize 800x600" or "resize 50%"
        m = re.search(r'(\d+)\s*[x×]\s*(\d+)', task)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            img = Image.open(str(path))
            img = img.resize((w, h), Image.LANCZOS)
            out = path.parent / f"{path.stem}_resized{path.suffix}"
            img.save(str(out))
            img.close()
            return f"✅ Resized to {w}×{h} → {out.name}"

        m = re.search(r'(\d+)\s*%', task)
        if m:
            pct = int(m.group(1)) / 100
            img = Image.open(str(path))
            nw, nh = int(img.size[0] * pct), int(img.size[1] * pct)
            img = img.resize((nw, nh), Image.LANCZOS)
            out = path.parent / f"{path.stem}_resized{path.suffix}"
            img.save(str(out))
            img.close()
            return f"✅ Resized to {pct*100:.0f}% ({nw}×{nh}) → {out.name}"

        return "❌ Format: resize 800x600  or  resize 50%"

    def _convert(self, path: Path, task: str, Image) -> str:
        m = re.search(r'to\s+(png|jpg|jpeg|webp|bmp|gif|tiff)', task, re.I)
        if not m:
            return "❌ Format: convert to png / jpg / webp"
        ext = m.group(1).lower()
        img = Image.open(str(path))
        if img.mode in ("RGBA", "P") and ext in ("jpg", "jpeg"):
            img = img.convert("RGB")
        out = path.parent / f"{path.stem}.{ext}"
        img.save(str(out))
        img.close()
        return f"✅ Converted to {ext.upper()} → {out.name}"

    def _grayscale(self, path: Path, Image) -> str:
        img = Image.open(str(path)).convert("L")
        out = path.parent / f"{path.stem}_bw{path.suffix}"
        img.save(str(out))
        img.close()
        return f"✅ Grayscale → {out.name}"

    def _crop(self, path: Path, task: str, Image) -> str:
        m = re.search(r'crop\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', task)
        if not m:
            return "❌ Format: crop <left> <top> <right> <bottom>"
        box = tuple(int(m.group(i)) for i in range(1, 5))
        img = Image.open(str(path))
        out = path.parent / f"{path.stem}_cropped{path.suffix}"
        img.crop(box).save(str(out))
        img.close()
        return f"✅ Cropped {box} → {out.name}"

    def _compress(self, path: Path, Image) -> str:
        img = Image.open(str(path))
        out = path.parent / f"{path.stem}_compressed{path.suffix}"
        sfx = path.suffix.lower()
        if sfx in (".jpg", ".jpeg"):
            img.save(str(out), quality=60, optimize=True)
        elif sfx == ".png":
            img.save(str(out), optimize=True, compress_level=9)
        else:
            img.save(str(out))
        img.close()
        orig = os.path.getsize(str(path))
        new  = os.path.getsize(str(out))
        pct  = (1 - new / orig) * 100
        return f"✅ Compressed {pct:.1f}% → {out.name} ({new // 1024} KB)"

    def _rotate(self, path: Path, task: str, Image) -> str:
        lo = task.lower()
        img = Image.open(str(path))
        if "flip horizontal" in lo:
            result = img.transpose(Image.FLIP_LEFT_RIGHT)
            label = "flipped_h"
        elif "flip vertical" in lo:
            result = img.transpose(Image.FLIP_TOP_BOTTOM)
            label = "flipped_v"
        else:
            m = re.search(r'(\d+)', task)
            angle = int(m.group(1)) if m else 90
            result = img.rotate(angle, expand=True)
            label = f"rotated{angle}"
        out = path.parent / f"{path.stem}_{label}{path.suffix}"
        result.save(str(out))
        img.close()
        return f"✅ {label.replace('_', ' ').title()} → {out.name}"

    def _thumbnail(self, path: Path, task: str, Image) -> str:
        m = re.search(r'(\d+)\s*[x×]\s*(\d+)', task)
        size = (int(m.group(1)), int(m.group(2))) if m else (256, 256)
        img = Image.open(str(path))
        img.thumbnail(size, Image.LANCZOS)
        out = path.parent / f"{path.stem}_thumb{path.suffix}"
        img.save(str(out))
        img.close()
        return f"✅ Thumbnail {size[0]}×{size[1]} → {out.name}"
