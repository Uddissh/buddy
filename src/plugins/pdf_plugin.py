import re
from pathlib import Path
from .base import BuddyPlugin


class PDFPlugin(BuddyPlugin):
    name = "pdf"
    supported_extensions = ["pdf"]
    description = "Read, extract, watermark, merge, split PDFs"

    def execute(self, file_path: str, task: str) -> str:
        path = self.validate_file(file_path)
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return "❌ PyMuPDF not installed. Run: pip install pymupdf"

        lo = task.lower()
        if any(k in lo for k in ["read", "extract", "text", "content", "show"]):
            return self._text(path, fitz)
        if any(k in lo for k in ["info", "meta", "details"]):
            return self._info(path, fitz)
        if any(k in lo for k in ["pages", "count", "how many"]):
            return self._pages(path, fitz)
        if "watermark" in lo:
            return self._watermark(path, task, fitz)
        if "merge" in lo or "combine" in lo:
            return self._merge_help(path, task, fitz)
        if "split" in lo:
            return self._split(path, task, fitz)
        if "compress" in lo or "reduce" in lo:
            return self._compress(path, fitz)
        return self._text(path, fitz)

    # ── Operations ─────────────────────────────────────────────────────────────

    def _text(self, path: Path, fitz) -> str:
        doc = fitz.open(str(path))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        if not text.strip():
            return "❌ No extractable text (scanned/image PDF?)"
        if len(text) > 3000:
            return f"📄 Text (first 3000 chars):\n\n{text[:3000]}\n\n[…{len(text)} total chars]"
        return f"📄 Text:\n\n{text}"

    def _info(self, path: Path, fitz) -> str:
        doc = fitz.open(str(path))
        m = doc.metadata
        lines = [
            f"📄 {path.name}",
            f"   Pages:   {doc.page_count}",
            f"   Title:   {m.get('title')  or 'N/A'}",
            f"   Author:  {m.get('author') or 'N/A'}",
            f"   Created: {m.get('creationDate') or 'N/A'}",
        ]
        doc.close()
        return "\n".join(lines)

    def _pages(self, path: Path, fitz) -> str:
        doc = fitz.open(str(path))
        n = doc.page_count
        doc.close()
        return f"📄 {path.name} → {n} page{'s' if n != 1 else ''}."

    def _watermark(self, path: Path, task: str, fitz) -> str:
        m = re.search(r'watermark[:\s]+["\']?(.+?)["\']?$', task, re.I)
        wm_text = m.group(1).strip() if m else "CONFIDENTIAL"
        doc = fitz.open(str(path))
        for page in doc:
            page.insert_text(
                (page.rect.width / 4, page.rect.height / 2),
                wm_text, fontsize=48, color=(0.8, 0.8, 0.8), rotate=45,
            )
        out = path.parent / f"{path.stem}_watermarked.pdf"
        doc.save(str(out))
        doc.close()
        return f"✅ Watermark '{wm_text}' added → {out.name}"

    def _merge_help(self, path: Path, task: str, fitz) -> str:
        m = re.search(r'with\s+(.+\.pdf)', task, re.I)
        if not m:
            return "❌ Specify second file: e.g. 'merge with other.pdf'"
        other = Path(m.group(1).strip()).expanduser()
        if not other.exists():
            return f"❌ File not found: {other}"
        merged = fitz.open()
        for p in [path, other]:
            doc = fitz.open(str(p))
            merged.insert_pdf(doc)
            doc.close()
        out = path.parent / f"{path.stem}_merged.pdf"
        merged.save(str(out))
        return f"✅ Merged → {out.name}"

    def _split(self, path: Path, task: str, fitz) -> str:
        m = re.search(r'(?:at\s+)?page\s+(\d+)', task, re.I)
        if not m:
            return "❌ Specify page: e.g. 'split at page 5'"
        split_at = int(m.group(1))
        doc = fitz.open(str(path))
        if split_at >= doc.page_count:
            return f"❌ PDF only has {doc.page_count} pages"
        for i, (frm, to, suffix) in enumerate([
            (0, split_at - 1, "part1"),
            (split_at, doc.page_count - 1, "part2"),
        ]):
            part = fitz.open()
            part.insert_pdf(doc, from_page=frm, to_page=to)
            out = path.parent / f"{path.stem}_{suffix}.pdf"
            part.save(str(out))
        doc.close()
        return f"✅ Split at page {split_at} → {path.stem}_part1.pdf, {path.stem}_part2.pdf"

    def _compress(self, path: Path, fitz) -> str:
        import os
        doc = fitz.open(str(path))
        out = path.parent / f"{path.stem}_compressed.pdf"
        doc.save(str(out), garbage=4, deflate=True, clean=True)
        doc.close()
        orig = os.path.getsize(str(path))
        new  = os.path.getsize(str(out))
        pct  = (1 - new / orig) * 100
        return f"✅ Compressed {pct:.1f}% → {out.name} ({new // 1024} KB)"
