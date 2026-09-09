"""Render a weekly memo (memos/YYYY-Www.md) to reports/memos/YYYY-Www.pdf, prefixed with
the fund's current summary so the PDF is self-contained. Uses pandoc + wkhtmltopdf.
Usage: python scripts/render_memo.py [memos/2026-W37.md]   (default: latest memo)"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = """body{font-family:Arial,Helvetica,sans-serif;font-size:9.5pt;line-height:1.35;color:#111}
h1{font-size:16pt;margin-bottom:4pt}h2{font-size:12.5pt;margin-top:14pt;border-bottom:1px solid #999}
h3{font-size:10.5pt;margin-top:10pt}table{border-collapse:collapse;width:100%;font-size:8pt;margin:6pt 0}
th,td{border:1px solid #bbb;padding:3pt 4pt;vertical-align:top;text-align:left}th{background:#eee}
a{color:#1a4a8a;text-decoration:none;word-break:break-all}.box{border:1px solid #999;padding:6pt;background:#f7f7f7}"""

def main():
    memos = sorted((ROOT / "memos").glob("20??-W??.md"))
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else memos[-1]
    out_dir = ROOT / "reports" / "memos"; out_dir.mkdir(parents=True, exist_ok=True)
    summary = (ROOT / "reports" / "summary.md")
    body = src.read_text()
    if summary.exists():
        body = body + "\n\n---\n\n## Appendix: fund state at render time\n\n" + summary.read_text().replace("# Paper fund summary", "### Paper fund summary")
    tmp_md = out_dir / (src.stem + ".tmp.md"); tmp_md.write_text(body)
    css = out_dir / "memo.css"; css.write_text(CSS)
    html = out_dir / (src.stem + ".html"); pdf = out_dir / (src.stem + ".pdf")
    subprocess.run(["pandoc", str(tmp_md), "-o", str(html), "--standalone", "--css", css.name,
                    "--metadata", f"title=Paper fund memo {src.stem}"], check=True)
    subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "-q", "--page-size", "A4",
                    "--margin-top", "12mm", "--margin-bottom", "12mm", "--margin-left", "12mm", "--margin-right", "12mm",
                    str(html), str(pdf)], check=True)
    for f in (tmp_md, html, css): f.unlink()
    print("wrote", pdf)

if __name__ == "__main__":
    main()
