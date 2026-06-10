"""Render a Markdown report to a styled PDF: roomy line spacing, clickable citation
links, and a real page-numbered Table of Contents (numbers verified by a two-pass
layout). Pure-Python (markdown2 + fpdf2) — no system libraries.

Uses a Unicode TTF if one is found (env REPORT_FONT, or a common system font); otherwise
falls back to a built-in core font with text sanitized to its range.
"""
import os
import re

import markdown2
from fpdf import FPDF
from fpdf.fonts import FontFace

LINE_HEIGHT = 1.7
TOC_LEVELS = 2

_REPLACE = {"→": "->", "←": "<-", "↔": "<->", "⇒": "=>", "•": "-", "…": "...",
            "“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "–": "-",
            "✅": "", "⚠️": "", "⚠": "", "❌": "", "❓": "", "🚫": "", "️": ""}


def _variant(base, kind):
    d, name = os.path.dirname(base), os.path.basename(base)
    stem, ext = os.path.splitext(name)
    pats = {
        "B":  [f"{stem} Bold{ext}", f"{stem}-Bold{ext}", f"{stem}bd{ext}", f"{stem}b{ext}"],
        "I":  [f"{stem} Italic{ext}", f"{stem}-Italic{ext}", f"{stem}-Oblique{ext}", f"{stem}i{ext}"],
        "BI": [f"{stem} Bold Italic{ext}", f"{stem}-BoldItalic{ext}", f"{stem}-BoldOblique{ext}", f"{stem}bi{ext}"],
    }
    for p in pats.get(kind, []):
        c = os.path.join(d, p)
        if os.path.exists(c):
            return c
    return base


def _pick_font():
    for base in [os.environ.get("REPORT_FONT"),
                 "/System/Library/Fonts/Supplemental/Georgia.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/Library/Fonts/Arial.ttf",
                 "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if base and os.path.exists(base):
            return base
    return None


FONT_FILE = _pick_font()
CORE_MODE = FONT_FILE is None
FAMILY = "ReportFont" if not CORE_MODE else "Helvetica"

H1 = FontFace(family=FAMILY, emphasis="BOLD", size_pt=18, color=(11, 61, 94))
H2 = FontFace(family=FAMILY, emphasis="BOLD", size_pt=14, color=(31, 90, 130))
H3 = FontFace(family=FAMILY, emphasis="BOLD", size_pt=12, color=(44, 110, 155))
LINK = FontFace(family=FAMILY, color=(11, 83, 148))
TAG_STYLES = {"h1": H1, "h2": H2, "h3": H3, "h4": H3, "a": LINK}


class _ReportPDF(FPDF):
    number_pages = True

    def footer(self):
        if not self.number_pages or self.page_no() == 1:
            return
        self.set_y(-13)
        self.set_font(FAMILY, "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, str(self.page_no()), align="C")


def _new_pdf():
    pdf = _ReportPDF(format="A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(auto=True, margin=16)
    if not CORE_MODE:
        pdf.add_font(FAMILY, "", FONT_FILE)
        pdf.add_font(FAMILY, "B", _variant(FONT_FILE, "B"))
        pdf.add_font(FAMILY, "I", _variant(FONT_FILE, "I"))
        pdf.add_font(FAMILY, "BI", _variant(FONT_FILE, "BI"))
    return pdf


def _md_to_html(chunk):
    html = markdown2.markdown(
        chunk, extras=["tables", "fenced-code-blocks", "header-ids", "strike", "cuddled-lists"])

    def _strip_cell(m):
        cell = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", m.group(0), flags=re.S)
        return re.sub(r"</?(strong|b|em|i|code|del|s)\b[^>]*>", "", cell)

    html = re.sub(r"<td\b.*?</td>", _strip_cell, html, flags=re.S)
    html = re.sub(r"<th\b.*?</th>", _strip_cell, html, flags=re.S)
    html = re.sub(r"<p(?=[ >])", f'<p style="line-height:{LINE_HEIGHT}"', html)
    html = re.sub(r"<li(?=[ >])", f'<li style="line-height:{LINE_HEIGHT}"', html)
    return html


def render(src, out):
    """Render Markdown file `src` to PDF file `out`. Returns `out`."""
    md = open(src, encoding="utf-8").read()
    for bad, good in _REPLACE.items():
        md = md.replace(bad, good)
    if CORE_MODE:
        md = md.encode("latin-1", "replace").decode("latin-1")

    heading_re = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
    segments, cur = [], None
    for line in md.split("\n"):
        m = heading_re.match(line)
        if m:
            cur = {"level": len(m.group(1)), "title": m.group(2).strip(), "body": []}
            segments.append(cur)
        elif cur is not None:
            cur["body"].append(line)

    title_text = next((s["title"] for s in segments if s["level"] == 1), "Research Report")
    content = [s for s in segments
               if s["level"] >= 2 and not s["title"].lower().startswith("table of contents")]
    toc_list = [(i, s["level"] - 2, s["title"])
                for i, s in enumerate(content) if (s["level"] - 2) < TOC_LEVELS]

    def render_title(pdf):
        pdf.add_page()
        pdf.set_y(95)
        pdf.set_font(FAMILY, "B", 24)
        pdf.set_text_color(11, 61, 94)
        pdf.multi_cell(0, 11, title_text, align="C")
        pdf.ln(6)
        pdf.set_draw_color(44, 110, 155)
        pdf.set_line_width(0.6)
        pdf.line(60, pdf.get_y(), pdf.w - 60, pdf.get_y())

    def render_toc(pdf, page_for):
        pdf.add_page()
        pdf.set_font(FAMILY, "B", 18)
        pdf.set_text_color(11, 61, 94)
        pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_text_color(25, 25, 25)
        dot_w = pdf.get_string_width(".")
        for idx, level, title in toc_list:
            indent = 5 * level
            pdf.set_font(FAMILY, "B" if level == 0 else "", 11 if level == 0 else 10)
            name = title
            mx = 82 - level * 8
            if len(name) > mx:
                name = name[: mx - 3].rstrip() + "..."
            page = str(page_for(idx)) if page_for else "00"
            avail = pdf.epw - indent - pdf.get_string_width(name + " ") - pdf.get_string_width(" " + page)
            dots = "." * max(0, int(avail / dot_w))
            pdf.set_x(pdf.l_margin + indent)
            pdf.cell(0, 7.5, f"{name} {dots} {page}", new_x="LMARGIN", new_y="NEXT")

    def render_body(pdf, record=None):
        pdf.add_page()
        for i, s in enumerate(content):
            if s["level"] == 2 and pdf.get_y() > (pdf.h - pdf.b_margin - 28):
                pdf.add_page()
            if record is not None:
                record[i] = pdf.page_no()
            pdf.start_section(s["title"], level=min(s["level"] - 2, 2), strict=False)
            chunk = ("#" * s["level"]) + " " + s["title"] + "\n\n" + "\n".join(s["body"])
            pdf.set_font(FAMILY, size=11)
            pdf.set_text_color(20, 20, 20)
            pdf.write_html(_md_to_html(chunk), font_family=FAMILY,
                           table_line_separators=True, tag_styles=TAG_STYLES)

    # pass 1: measure
    toc_probe = _new_pdf(); toc_probe.number_pages = False
    render_toc(toc_probe, page_for=None)
    n_toc = toc_probe.page_no()
    body_probe = _new_pdf(); body_probe.number_pages = False
    render_title(body_probe)
    measured = {}
    render_body(body_probe, record=measured)
    final_page = {i: p + n_toc for i, p in measured.items()}

    # pass 2: final
    pdf = _new_pdf()
    render_title(pdf)
    render_toc(pdf, page_for=lambda i: final_page[i])
    render_body(pdf)
    pdf.output(out)
    return out
