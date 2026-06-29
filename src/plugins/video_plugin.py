import json
import os
import re
import subprocess
from pathlib import Path
from .base import BuddyPlugin


class VideoPlugin(BuddyPlugin):
    name = "video"
    supported_extensions = ["mp4", "avi", "mkv", "mov", "webm", "flv", "wmv", "m4v", "ts"]
    description = "Process video files via ffmpeg/ffprobe"

    def _ffmpeg_ok(self) -> bool:
        return subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0

    def execute(self, file_path: str, task: str) -> str:
        path = self.validate_file(file_path)
        if not self._ffmpeg_ok():
            return "❌ ffmpeg not found. Install: sudo apt install ffmpeg"

        lo = task.lower()
        if any(k in lo for k in ["info", "meta", "details", "duration"]):
            return self._info(path)
        if "convert" in lo:
            return self._convert(path, task)
        if any(k in lo for k in ["trim", "cut", "clip"]):
            return self._trim(path, task)
        if any(k in lo for k in ["audio", "extract audio", "mp3", "wav"]):
            return self._audio(path, task)
        if any(k in lo for k in ["compress", "reduce", "smaller"]):
            return self._compress(path)
        if any(k in lo for k in ["thumbnail", "screenshot", "frame", "snapshot"]):
            return self._thumbnail(path, task)
        if any(k in lo for k in ["mute", "remove audio", "no audio"]):
            return self._mute(path)
        return self._info(path)

    def _run(self, args: list[str]) -> tuple[int, str]:
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        return r.returncode, r.stderr[-300:] if r.stderr else ""

    def _info(self, path: Path) -> str:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            return f"❌ ffprobe error: {r.stderr}"
        data = json.loads(r.stdout)
        fmt = data.get("format", {})
        dur = float(fmt.get("duration", 0))
        m, s = int(dur // 60), int(dur % 60)
        size_mb = int(fmt.get("size", 0)) // (1024 * 1024)
        streams = data.get("streams", [])
        vs = next((s for s in streams if s.get("codec_type") == "video"), {})
        as_ = next((s for s in streams if s.get("codec_type") == "audio"), {})
        lines = [
            f"🎬 {path.name}",
            f"   Duration: {m}m {s}s",
            f"   Size:     {size_mb} MB",
        ]
        if vs:
            lines.append(f"   Video:    {vs.get('codec_name','?')} {vs.get('width','?')}×{vs.get('height','?')}")
        if as_:
            lines.append(f"   Audio:    {as_.get('codec_name','?')} {as_.get('sample_rate','?')}Hz")
        return "\n".join(lines)

    def _convert(self, path: Path, task: str) -> str:
        m = re.search(r'to\s+(mp4|avi|mkv|mov|webm|mp3|wav)', task, re.I)
        if not m:
            return "❌ Format: convert to mp4 / mkv / webm"
        ext = m.group(1).lower()
        out = path.parent / f"{path.stem}.{ext}"
        code, err = self._run(["ffmpeg", "-i", str(path), str(out), "-y"])
        return f"✅ Converted → {out.name}" if code == 0 else f"❌ ffmpeg: {err}"

    def _trim(self, path: Path, task: str) -> str:
        m = re.search(r'from\s+(\d+):(\d+)\s+to\s+(\d+):(\d+)', task)
        if m:
            start = int(m.group(1)) * 60 + int(m.group(2))
            end   = int(m.group(3)) * 60 + int(m.group(4))
        else:
            m2 = re.search(r'(\d+)\s+to\s+(\d+)', task)
            if not m2:
                return "❌ Format: trim from 0:30 to 1:45  or  trim 30 to 90"
            start, end = int(m2.group(1)), int(m2.group(2))
        out = path.parent / f"{path.stem}_trimmed{path.suffix}"
        code, err = self._run([
            "ffmpeg", "-i", str(path),
            "-ss", str(start), "-t", str(end - start),
            "-c", "copy", str(out), "-y",
        ])
        return f"✅ Trimmed ({start}s–{end}s) → {out.name}" if code == 0 else f"❌ ffmpeg: {err}"

    def _audio(self, path: Path, task: str) -> str:
        ext = "wav" if "wav" in task.lower() else "mp3"
        out = path.parent / f"{path.stem}.{ext}"
        args = ["ffmpeg", "-i", str(path), "-q:a", "0", "-map", "a", str(out), "-y"]
        code, err = self._run(args)
        return f"✅ Audio extracted → {out.name}" if code == 0 else f"❌ ffmpeg: {err}"

    def _compress(self, path: Path) -> str:
        out = path.parent / f"{path.stem}_compressed.mp4"
        code, err = self._run([
            "ffmpeg", "-i", str(path),
            "-vcodec", "libx264", "-crf", "28",
            str(out), "-y",
        ])
        if code != 0:
            return f"❌ ffmpeg: {err}"
        orig = os.path.getsize(str(path))
        new  = os.path.getsize(str(out))
        pct  = (1 - new / orig) * 100
        return f"✅ Compressed {pct:.1f}% → {out.name} ({new // (1024*1024)} MB)"

    def _thumbnail(self, path: Path, task: str) -> str:
        m = re.search(r'at\s+(\d+)', task)
        t = m.group(1) if m else "5"
        out = path.parent / f"{path.stem}_thumb.jpg"
        code, err = self._run([
            "ffmpeg", "-i", str(path), "-ss", t, "-vframes", "1", str(out), "-y",
        ])
        return f"✅ Thumbnail at {t}s → {out.name}" if code == 0 else f"❌ ffmpeg: {err}"

    def _mute(self, path: Path) -> str:
        out = path.parent / f"{path.stem}_muted{path.suffix}"
        code, err = self._run([
            "ffmpeg", "-i", str(path), "-an", "-c:v", "copy", str(out), "-y",
        ])
        return f"✅ Audio removed → {out.name}" if code == 0 else f"❌ ffmpeg: {err}"
