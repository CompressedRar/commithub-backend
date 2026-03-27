"""
Supporting Documents Report — PowerPoint Compiler (Norzagaray College Template)
================================================================================
Builds a clean .pptx by working directly at the zip/XML level.
This avoids the duplicate-entry bug that occurs when python-pptx clones slides.

Slide structure
───────────────
  1. Cover slide  (cloned from template slide 1)
  Per task group:
    a. Section-divider slide  (cloned from template slide 2)
    b. One content slide per document  (cloned from template slide 3)

Template requirements
─────────────────────
Set TEMPLATE_PATH to the .pptx file's location on the server.
The three donor slides must remain as slides 1, 2, 3 in the template.

Dependencies
────────────
    pip install lxml Pillow pdf2image requests --break-system-packages
"""

import io
import re
import zipfile
from copy import deepcopy
from datetime import datetime

import requests
from lxml import etree
from PIL import Image
from pdf2image import convert_from_bytes
from flask import send_file

# ── Template config ───────────────────────────────────────────────────────────

TEMPLATE_PATH = "excels/presentation-template.pptx"

# Donor slide filenames inside the template zip (0-based index → 1-based filename)
DONOR_COVER   = "slide1.xml"   # full cover: building + swoops + logo
DONOR_SECTION = "slide2.xml"   # section divider: ghosted building + wavy footer
DONOR_CONTENT = "slide3.xml"   # content layout: title + wavy footer + dot pattern

# ── File type constants ───────────────────────────────────────────────────────

IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
PDF_TYPE    = "application/pdf"
WORD_TYPES  = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# ── XML namespaces ────────────────────────────────────────────────────────────

NS = {
    "a":   "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p":   "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct":  "http://schemas.openxmlformats.org/package/2006/content-types",
}

SLIDE_CT = (
    "application/vnd.openxmlformats-officedocument"
    ".presentationml.slide+xml"
)
SLIDE_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument"
    "/2006/relationships/slide"
)


def _qn(prefix, local):
    return f"{{{NS[prefix]}}}{local}"


def _parse(data: bytes) -> etree._Element:
    return etree.fromstring(data)


def _serialise(root: etree._Element) -> bytes:
    return etree.tostring(
        root, xml_declaration=True, encoding="utf-8", standalone=True
    )


# ── Template reader ───────────────────────────────────────────────────────────

class Template:
    """Reads the template zip once and exposes donor slide data."""

    def __init__(self, path: str):
        with zipfile.ZipFile(path, "r") as zf:
            self._all: dict[str, bytes] = {n: zf.read(n) for n in zf.namelist()}

        self.donors = {
            "cover":   self._slide_pair(DONOR_COVER),
            "section": self._slide_pair(DONOR_SECTION),
            "content": self._slide_pair(DONOR_CONTENT),
        }

    def _slide_pair(self, fname: str):
        xml  = self._all[f"ppt/slides/{fname}"]
        rels = self._all[f"ppt/slides/_rels/{fname}.rels"]
        return (xml, rels)

    def non_slide_entries(self) -> dict[str, bytes]:
        """Return all zip entries that are NOT the original 9 slides."""
        out = {}
        for name, data in self._all.items():
            if re.match(r"ppt/slides/slide\d+\.xml$", name):
                continue
            if re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels$", name):
                continue
            out[name] = data
        return out


# ── XML helpers for slide editing ────────────────────────────────────────────

def _find_shape(root: etree._Element, name: str):
    """Return the <p:sp> element whose cNvPr name= matches."""
    for sp in root.iter(_qn("p", "sp")):
        cnv = sp.find(".//" + _qn("p", "cNvPr"))
        if cnv is None:
            cnv = sp.find(".//" + _qn("a", "cNvPr"))
        if cnv is not None and cnv.get("name") == name:
            return sp
    return None


def _set_shape_text(root: etree._Element, shape_name: str,
                    lines: list[tuple]):
    """
    Replace all text in a named shape.
    `lines` is a list of (text, size_pt, bold, hex_color) tuples.
    One tuple = one paragraph.
    """
    sp = _find_shape(root, shape_name)
    if sp is None:
        return
    txBody = sp.find(_qn("p", "txBody"))
    if txBody is None:
        return

    # Preserve bodyPr and lstStyle, remove all <a:p>
    for para in txBody.findall(_qn("a", "p")):
        txBody.remove(para)

    for text, size_pt, bold, hex_color in lines:
        para = etree.SubElement(txBody, _qn("a", "p"))
        pPr  = etree.SubElement(para, _qn("a", "pPr"))
        pPr.set("algn", "ctr")
        lnSpc = etree.SubElement(pPr, _qn("a", "lnSpc"))
        etree.SubElement(lnSpc, _qn("a", "spcPct")).set("val", "100000")
        etree.SubElement(pPr, _qn("a", "buNone"))

        run  = etree.SubElement(para, _qn("a", "r"))
        rPr  = etree.SubElement(run, _qn("a", "rPr"))
        rPr.set("lang", "en-US")
        rPr.set("sz",   str(int(size_pt * 100)))
        rPr.set("b",    "1" if bold else "0")
        rPr.set("u",    "none")
        rPr.set("strike", "noStrike")
        fill = etree.SubElement(rPr, _qn("a", "solidFill"))
        etree.SubElement(fill, _qn("a", "srgbClr")).set("val", hex_color)
        etree.SubElement(rPr, _qn("a", "effectLst"))
        etree.SubElement(rPr, _qn("a", "uFillTx"))
        t = etree.SubElement(run, _qn("a", "t"))
        t.text = text

    # Add a terminal endParaRPr
    endPara = etree.SubElement(txBody, _qn("a", "p"))
    etree.SubElement(endPara, _qn("a", "endParaRPr")).set("lang", "en-US")


def _remove_tables_and_photos(root: etree._Element):
    """Strip all <p:tbl> tables and <p:pic> pictures from the slide spTree."""
    spTree = root.find(".//" + _qn("p", "spTree"))
    if spTree is None:
        return
    for tag in (_qn("p", "pic"), _qn("p", "graphicFrame")):
        for el in spTree.findall(tag):
            spTree.remove(el)


def _add_txb(spTree: etree._Element, text: str,
             x_emu: int, y_emu: int, cx_emu: int, cy_emu: int,
             size_pt: float, bold: bool, italic: bool,
             hex_color: str, align: str = "l") -> etree._Element:
    """Append a plain text box to spTree and return the <p:sp> element."""
    sp    = etree.SubElement(spTree, _qn("p", "sp"))
    nvSpPr = etree.SubElement(sp, _qn("p", "nvSpPr"))
    cNvPr  = etree.SubElement(nvSpPr, _qn("p", "cNvPr"))
    cNvPr.set("id",   str(abs(hash(text + str(x_emu))) % 90000 + 10000))
    cNvPr.set("name", f"txb_{x_emu}_{y_emu}")
    etree.SubElement(nvSpPr, _qn("p", "cNvSpPr")).set(
        "{http://schemas.openxmlformats.org/drawingml/2006/main}txBox", "1"
    )
    # Actually set the right attribute
    nvSpPr[-1].clear()
    cNvSpPr = nvSpPr[-1]
    cNvSpPr.set("txBox", "1")
    etree.SubElement(nvSpPr, _qn("p", "nvPr"))

    spPr   = etree.SubElement(sp, _qn("p", "spPr"))
    xfrm   = etree.SubElement(spPr, _qn("a", "xfrm"))
    etree.SubElement(xfrm, _qn("a", "off")).set("x", str(x_emu))
    xfrm[-1].set("y", str(y_emu))
    etree.SubElement(xfrm, _qn("a", "ext")).set("cx", str(cx_emu))
    xfrm[-1].set("cy", str(cy_emu))
    prstGeom = etree.SubElement(spPr, _qn("a", "prstGeom"))
    prstGeom.set("prst", "rect")
    etree.SubElement(prstGeom, _qn("a", "avLst"))
    etree.SubElement(spPr, _qn("a", "noFill"))

    txBody = etree.SubElement(sp, _qn("p", "txBody"))
    bodyPr = etree.SubElement(txBody, _qn("a", "bodyPr"))
    bodyPr.set("wrap", "square")
    etree.SubElement(txBody, _qn("a", "lstStyle"))

    para  = etree.SubElement(txBody, _qn("a", "p"))
    pPr   = etree.SubElement(para,   _qn("a", "pPr"))
    pPr.set("algn", align)
    etree.SubElement(pPr, _qn("a", "buNone"))
    run   = etree.SubElement(para, _qn("a", "r"))
    rPr   = etree.SubElement(run,  _qn("a", "rPr"))
    rPr.set("lang",   "en-US")
    rPr.set("sz",     str(int(size_pt * 100)))
    rPr.set("b",      "1" if bold   else "0")
    rPr.set("i",      "1" if italic else "0")
    rPr.set("u",      "none")
    rPr.set("strike", "noStrike")
    fill = etree.SubElement(rPr, _qn("a", "solidFill"))
    etree.SubElement(fill, _qn("a", "srgbClr")).set("val", hex_color)
    etree.SubElement(rPr, _qn("a", "effectLst"))
    etree.SubElement(rPr, _qn("a", "uFillTx"))
    latin = etree.SubElement(rPr, _qn("a", "latin"))
    latin.set("typeface", "Calibri")
    t = etree.SubElement(run, _qn("a", "t"))
    t.text = text

    return sp


def _add_rect_shape(spTree: etree._Element,
                    x_emu: int, y_emu: int, cx_emu: int, cy_emu: int,
                    hex_fill: str) -> etree._Element:
    """Append a filled rectangle with no border."""
    sp    = etree.SubElement(spTree, _qn("p", "sp"))
    nvSpPr = etree.SubElement(sp, _qn("p", "nvSpPr"))
    cNvPr  = etree.SubElement(nvSpPr, _qn("p", "cNvPr"))
    cNvPr.set("id",   str(abs(hash(hex_fill + str(x_emu))) % 90000 + 10000))
    cNvPr.set("name", f"rect_{x_emu}_{y_emu}")
    etree.SubElement(nvSpPr, _qn("p", "cNvSpPr"))
    etree.SubElement(nvSpPr, _qn("p", "nvPr"))
    spPr  = etree.SubElement(sp, _qn("p", "spPr"))
    xfrm  = etree.SubElement(spPr, _qn("a", "xfrm"))
    etree.SubElement(xfrm, _qn("a", "off")).set("x", str(x_emu))
    xfrm[-1].set("y", str(y_emu))
    etree.SubElement(xfrm, _qn("a", "ext")).set("cx", str(cx_emu))
    xfrm[-1].set("cy", str(cy_emu))
    prstGeom = etree.SubElement(spPr, _qn("a", "prstGeom"))
    prstGeom.set("prst", "rect")
    etree.SubElement(prstGeom, _qn("a", "avLst"))
    fill = etree.SubElement(spPr, _qn("a", "solidFill"))
    etree.SubElement(fill, _qn("a", "srgbClr")).set("val", hex_fill)
    ln = etree.SubElement(spPr, _qn("a", "ln"))
    etree.SubElement(ln, _qn("a", "noFill"))
    # Empty txBody required
    txBody = etree.SubElement(sp, _qn("p", "txBody"))
    etree.SubElement(txBody, _qn("a", "bodyPr"))
    etree.SubElement(txBody, _qn("a", "lstStyle"))
    etree.SubElement(txBody, _qn("a", "p"))
    return sp


# ── Image embedding ───────────────────────────────────────────────────────────

def _png_stream(img: Image.Image) -> bytes:
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _fit(iw: int, ih: int, bw_emu: int, bh_emu: int):
    """Return (width_emu, height_emu, x_off_emu, y_off_emu) — centre-fit."""
    scale = min(bw_emu / iw, bh_emu / ih)
    fw    = int(iw * scale)
    fh    = int(ih * scale)
    return fw, fh, (bw_emu - fw) // 2, (bh_emu - fh) // 2


class _SlideBuilder:
    """
    Builds one slide's XML and accumulates extra media files it needs.
    Caller registers media via add_image(); the images are returned as
    {rId: (filename, png_bytes)} and must be written into the zip.
    """

    SLIDE_NS = {
        "xmlns:a":   NS["a"],
        "xmlns:p":   NS["p"],
        "xmlns:r":   NS["r"],
    }

    def __init__(self, donor_xml: bytes, donor_rels: bytes):
        self.root     = _parse(donor_xml)
        self._rels    = _parse(donor_rels)
        self._images: dict[str, tuple[str, bytes]] = {}   # rId → (fname, data)
        # Find next available rId number in donor rels
        existing = [int(m) for el in self._rels
                    for m in re.findall(r"rId(\d+)", el.get("Id", ""))]
        self._next_rid = max(existing) + 1 if existing else 10

    def add_image(self, png_bytes: bytes, hint: str = "img") -> str:
        """Register image data; return the rId to use in XML."""
        import uuid
        rid  = f"rId{self._next_rid}"
        fname = f"image_{hint}_{self._next_rid}{uuid.uuid4().hex}.png"
        self._images[rid] = (fname, png_bytes)
        self._next_rid += 1
        # Add relationship entry
        rel = etree.SubElement(self._rels, "Relationship")
        rel.set("Id",     rid)
        rel.set("Type",   "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
        rel.set("Target", f"../media/{fname}")
        return rid

    def embed_picture(self, spTree: etree._Element,
                      png_bytes: bytes,
                      x_emu: int, y_emu: int, cx_emu: int, cy_emu: int,
                      hint: str = "img"):
        """Add a <p:pic> element to spTree for the given image."""
        rid  = self.add_image(png_bytes, hint)
        pic  = etree.SubElement(spTree, _qn("p", "pic"))
        nvPicPr = etree.SubElement(pic, _qn("p", "nvPicPr"))
        cNvPr   = etree.SubElement(nvPicPr, _qn("p", "cNvPr"))
        cNvPr.set("id",   str(abs(hash(rid)) % 90000 + 10000))
        cNvPr.set("name", f"pic_{x_emu}")
        etree.SubElement(nvPicPr, _qn("p", "cNvPicPr"))
        etree.SubElement(nvPicPr, _qn("p", "nvPr"))
        blipFill = etree.SubElement(pic, _qn("p", "blipFill"))
        blip     = etree.SubElement(blipFill, _qn("a", "blip"))
        blip.set(_qn("r", "embed"), rid)
        etree.SubElement(blipFill, _qn("a", "stretch"))
        spPr  = etree.SubElement(pic, _qn("p", "spPr"))
        xfrm  = etree.SubElement(spPr, _qn("a", "xfrm"))
        off   = etree.SubElement(xfrm, _qn("a", "off"))
        off.set("x", str(x_emu)); off.set("y", str(y_emu))
        ext   = etree.SubElement(xfrm, _qn("a", "ext"))
        ext.set("cx", str(cx_emu)); ext.set("cy", str(cy_emu))
        prstGeom = etree.SubElement(spPr, _qn("a", "prstGeom"))
        prstGeom.set("prst", "rect")
        etree.SubElement(prstGeom, _qn("a", "avLst"))
        etree.SubElement(spPr, _qn("a", "noFill"))
        ln = etree.SubElement(spPr, _qn("a", "ln"))
        etree.SubElement(ln, _qn("a", "noFill"))

    def xml_bytes(self) -> bytes:
        return _serialise(self.root)

    def rels_bytes(self) -> bytes:
        return _serialise(self._rels)


# ── EMU constants ─────────────────────────────────────────────────────────────

def _in(inches: float) -> int:
    return int(inches * 914400)


# ── Slide-type builders ───────────────────────────────────────────────────────

def _build_cover(tpl: Template, report_title: str,
                 dept_name: str, generated_on: str,
                 total_docs: int) -> _SlideBuilder:
    sb = _SlideBuilder(*tpl.donors["cover"])
    root = sb.root

    # PlaceHolder 1: main title + subtitle row
    _set_shape_text(root, "PlaceHolder 1", [
        (report_title,  32, True,  "0070c0"),
        (dept_name,     20, False, "080808") if dept_name else ("", 14, False, "888888"),
    ])

    # PlaceHolder 2: meta lines
    _set_shape_text(root, "PlaceHolder 2", [
        (f"Generated: {generated_on}",          13, True,  "080808"),
        (f"Total Documents: {total_docs}",       13, False, "080808"),
        ("Classification: Official · Internal Use Only", 10, False, "595959"),
    ])
    return sb


def _build_section(tpl: Template, task_name: str) -> _SlideBuilder:
    sb = _SlideBuilder(*tpl.donors["section"])
    _set_shape_text(sb.root, "PlaceHolder 1", [
        (task_name, 36, True, "1F72C4"),
    ])
    return sb


def _build_content(tpl: Template, doc_data: dict, seq_num: int,
                   content_bytes: bytes | None,
                   file_type: str, file_name: str) -> _SlideBuilder:

    sb     = _SlideBuilder(*tpl.donors["content"])
    root   = sb.root
    spTree = root.find(".//" + _qn("p", "spTree"))

    # ── Title ──────────────────────────────────────────────────────────────
    title = doc_data.get("title") or "Untitled Document"
    _set_shape_text(root, "PlaceHolder 1", [
        (f"{seq_num}.  {title}", 18, True, "1F72C4"),
    ])

    # ── Remove tables / photos from donor ─────────────────────────────────
    _remove_tables_and_photos(root)

    # ── Metadata (left column) ────────────────────────────────────────────
    event_date = doc_data.get("event_date")
    if event_date and hasattr(event_date, "strftime"):
        event_date = event_date.strftime("%B %d, %Y")
    elif event_date:
        event_date = str(event_date)[:10]
    else:
        event_date = "N/A"

    user_name = doc_data.get("user_name") or "—"
    desc      = doc_data.get("desc")      or "—"

    # Orange badge
    BADGE_X = _in(0.35);  BADGE_Y = _in(1.55)
    BADGE_S = _in(0.52)
    _add_rect_shape(spTree, BADGE_X, BADGE_Y, BADGE_S, BADGE_S, "FFA500")
    _add_txb(spTree, str(seq_num),
             BADGE_X, BADGE_Y, BADGE_S, BADGE_S,
             15, True, False, "FFFFFF", align="ctr")

    # Employee name
    _add_txb(spTree, user_name,
             BADGE_X + _in(0.62), BADGE_Y, _in(3.6), _in(0.52),
             13, True, False, "1F72C4")

    ry = BADGE_Y + _in(0.65)
    for label, value in [
        ("EVENT DATE",   event_date),
        ("DESCRIPTION",  desc),
        ("SUBMITTED BY", user_name),
        ("FILE",         file_name or "—"),
    ]:
        _add_txb(spTree, label,
                 BADGE_X, ry, _in(4.4), _in(0.26),
                 7, True, False, "FFA500")
        ry += _in(0.26)
        _add_txb(spTree, str(value),
                 BADGE_X, ry, _in(4.4), _in(0.48),
                 10, False, False, "262626")
        ry += _in(0.52)

    # ── Attachment (right column) ─────────────────────────────────────────
    AX = _in(5.1);   AY = _in(1.45)
    AW = _in(7.8);   AH = _in(5.55)

    if content_bytes and file_type in IMAGE_TYPES:
        _embed_image_content(sb, spTree, content_bytes, AX, AY, AW, AH)
    elif content_bytes and file_type == PDF_TYPE:
        _embed_pdf_content(sb, spTree, content_bytes, AX, AY, AW, AH)
    elif content_bytes and file_type in WORD_TYPES:
        _embed_docx_content(sb, spTree, content_bytes, AX, AY, AW, AH)
    else:
        _embed_unsupported_notice(spTree, file_name, file_type, AX, AY, AW, AH)

    return sb


# ── Attachment content helpers ─────────────────────────────────────────────────

def _embed_image_content(sb: _SlideBuilder, spTree, data: bytes,
                          ax, ay, aw, ah):
    try:
        img       = Image.open(io.BytesIO(data))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        fw, fh, ox, oy = _fit(img.width, img.height, aw, ah)
        png = _png_stream(img)
        sb.embed_picture(spTree, png, ax + ox, ay + oy, fw, fh, "img")
    except Exception as e:
        _embed_error_notice(spTree, f"Image error: {e}", ax, ay, aw)


def _embed_pdf_content(sb: _SlideBuilder, spTree, data: bytes,
                        ax, ay, aw, ah):
    try:
        pages = convert_from_bytes(data, dpi=120, first_page=1, last_page=4)
        n     = len(pages)
        cols  = 2 if n > 1 else 1
        rows  = (n + 1) // 2
        cw    = aw // cols - _in(0.06)
        ch    = ah // rows - _in(0.06)
        for i, pg in enumerate(pages):
            fw, fh, ox, oy = _fit(pg.width, pg.height, cw, ch)
            px = ax + (i % cols) * (cw + _in(0.06)) + ox
            py = ay + (i // cols) * (ch + _in(0.06)) + oy
            sb.embed_picture(spTree, _png_stream(pg), px, py, fw, fh, f"pdf{i}")
    except Exception as e:
        _embed_error_notice(spTree, f"PDF error: {e}", ax, ay, aw)


def _embed_docx_content(sb: _SlideBuilder, spTree, data: bytes,
                         ax, ay, aw, ah):
    try:
        from docx import Document as DocxDoc
        inner = DocxDoc(io.BytesIO(data))
        lines = [p.text for p in inner.paragraphs if p.text.strip()][:35]
        _add_rect_shape(spTree, ax, ay, aw, ah, "F4F6F9")
        _add_txb(spTree, "EXTRACTED TEXT",
                 ax + _in(0.2), ay + _in(0.15), aw - _in(0.4), _in(0.3),
                 8, True, False, "1F72C4")
        _add_txb(spTree, "\n".join(lines),
                 ax + _in(0.2), ay + _in(0.5), aw - _in(0.4), ah - _in(0.7),
                 8, False, False, "262626")
    except Exception as e:
        _embed_error_notice(spTree, f"DOCX error: {e}", ax, ay, aw)


def _embed_unsupported_notice(spTree, file_name: str, file_type: str,
                               ax, ay, aw, ah):
    _add_rect_shape(spTree, ax, ay, aw, ah, "F4F6F9")
    _add_txb(spTree, "ATTACHMENT",
             ax + _in(0.2), ay + _in(0.5), aw - _in(0.4), _in(0.3),
             8, True, False, "1F72C4")
    _add_txb(spTree, file_name or "Unnamed File",
             ax + _in(0.2), ay + _in(0.9), aw - _in(0.4), _in(0.5),
             13, True, False, "262626")
    _add_txb(spTree, f"Type: {file_type or 'unknown'}",
             ax + _in(0.2), ay + _in(1.5), aw - _in(0.4), _in(0.3),
             9, False, False, "595959")
    _add_txb(spTree,
             "This file type cannot be previewed inline.\n"
             "Please download the original from the system portal.",
             ax + _in(0.2), ay + _in(1.95), aw - _in(0.4), _in(0.9),
             9, False, True, "595959")


def _embed_error_notice(spTree, msg: str, ax, ay, aw):
    _add_txb(spTree, f"⚠  {msg}",
             ax + _in(0.1), ay + _in(0.2), aw - _in(0.2), _in(0.5),
             9, False, False, "C00000")


# ── Zip assembler ─────────────────────────────────────────────────────────────

def _assemble_zip(tpl: Template,
                  slides: list[_SlideBuilder]) -> bytes:
    """
    Build a clean .pptx zip:
    - All non-slide template entries unchanged
    - presentation.xml with new sldIdLst
    - ppt/_rels/presentation.xml.rels with new slide relationships
    - [Content_Types].xml with Override entries for new slides
    - New slide XML + rels + any extra media
    """
    base = tpl.non_slide_entries()

    # ── Parse and rewrite presentation.xml ───────────────────────────────
    pres_root = _parse(base["ppt/presentation.xml"])
    sldIdLst  = pres_root.find(".//" + _qn("p", "sldIdLst"))
    for child in list(sldIdLst):
        sldIdLst.remove(child)

    # ── Parse and rewrite ppt/_rels/presentation.xml.rels ─────────────────
    pres_rels_root = _parse(base["ppt/_rels/presentation.xml.rels"])
    for rel in list(pres_rels_root):
        tgt = rel.get("Target", "")
        if "slides/slide" in tgt and "Layout" not in tgt and "Master" not in tgt:
            pres_rels_root.remove(rel)

    existing_rids = [
        int(m)
        for rel in pres_rels_root
        for m in re.findall(r"rId(\d+)", rel.get("Id", ""))
    ]
    next_rid = max(existing_rids) + 1 if existing_rids else 10
    next_id  = 256

    # ── Parse [Content_Types].xml ─────────────────────────────────────────
    ct_root = _parse(base["[Content_Types].xml"])
    # Remove existing slide overrides
    for ov in list(ct_root):
        pn = ov.get("PartName", "")
        if re.match(r"/ppt/slides/slide\d+\.xml$", pn):
            ct_root.remove(ov)

    # ── Per-slide entries ─────────────────────────────────────────────────
    slide_entries: list[tuple[str, bytes]] = []   # (zip_path, data)

    for i, sb in enumerate(slides, 1):
        sname = f"slide{i}.xml"
        rid   = f"rId{next_rid}"

        # presentation.xml sldId entry
        sldId_el = etree.SubElement(sldIdLst, _qn("p", "sldId"))
        sldId_el.set("id", str(next_id))
        sldId_el.set(_qn("r", "id"), rid)

        # presentation.xml.rels entry
        rel_el = etree.SubElement(pres_rels_root, "Relationship")
        rel_el.set("Id",     rid)
        rel_el.set("Type",   SLIDE_REL_TYPE)
        rel_el.set("Target", f"slides/{sname}")

        # [Content_Types].xml Override
        ov = etree.SubElement(ct_root, "Override")
        ov.set("PartName",    f"/ppt/slides/{sname}")
        ov.set("ContentType", SLIDE_CT)

        slide_entries.append((f"ppt/slides/{sname}",            sb.xml_bytes()))
        slide_entries.append((f"ppt/slides/_rels/{sname}.rels", sb.rels_bytes()))

        # Extra media files from this slide
        for img_rid, (img_fname, img_data) in sb._images.items():
            slide_entries.append((f"ppt/media/{img_fname}", img_data))

        next_rid += 1
        next_id  += 1

    # ── Write zip ─────────────────────────────────────────────────────────
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in base.items():
            if name == "ppt/presentation.xml":
                zout.writestr(name, _serialise(pres_root))
            elif name == "ppt/_rels/presentation.xml.rels":
                zout.writestr(name, _serialise(pres_rels_root))
            elif name == "[Content_Types].xml":
                zout.writestr(name, _serialise(ct_root))
            else:
                zout.writestr(name, data)
        for name, data in slide_entries:
            zout.writestr(name, data)

    out.seek(0)
    return out.read()


# ── Data collectors (unchanged API) ──────────────────────────────────────────

def collect_by_ipcr(ipcr_id):
    from models.PCR import Supporting_Document, IPCR
    try:
        ipcr = IPCR.query.get(ipcr_id)
        if not ipcr:
            return []
        return [d.to_dict() for d in ipcr.supporting_documents if d.status]
    except Exception as e:
        print("collect_by_ipcr error:", e)
        return []


def collect_by_department(dept_id):
    from models.PCR import Supporting_Document
    from models.System_Settings import System_Settings
    try:
        settings = System_Settings.get_default_settings()
        all_docs = Supporting_Document.query.filter_by(
            period=settings.current_period_id
        ).all()
        return [
            d.to_dict() for d in all_docs
            if str(d.ipcr.user.department.id) == str(dept_id) and d.status
        ]
    except Exception as e:
        print("collect_by_department error:", e)
        return []


# ── Main entry point ──────────────────────────────────────────────────────────

def into_presentation(documents: list[dict],
                      report_title: str = "Supporting Documents Report",
                      dept_name: str = "",
                      template_path: str | None = None) -> object:
    """
    Build and return a Flask send_file response (.pptx) styled with the
    Norzagaray College accomplishment report template.

    Parameters
    ----------
    documents     : list[dict]  — same schema as the docx compiler
    report_title  : str
    dept_name     : str         — optional department label on cover
    template_path : str | None  — overrides TEMPLATE_PATH constant

    Returns None if documents is empty.
    """
    if not documents:
        return None

    generated_on = datetime.now().strftime("%B %d, %Y")
    documents.sort(key=lambda x: (
        x.get("task_name") or "Unassigned",
        x.get("user_name") or "",
        str(x.get("event_date") or ""),
    ))

    tpl = Template(template_path or TEMPLATE_PATH)

    slide_builders: list[_SlideBuilder] = []

    # Cover
    slide_builders.append(
        _build_cover(tpl, report_title, dept_name, generated_on, len(documents))
    )

    current_task = None
    seq_num      = 0

    for doc_data in documents:
        task_name    = doc_data.get("task_name") or "Unassigned Task"
        file_type    = (doc_data.get("file_type") or "").lower().strip()
        file_name    = doc_data.get("file_name") or ""
        download_url = doc_data.get("download_url") or ""

        if task_name != current_task:
            slide_builders.append(_build_section(tpl, task_name))
            current_task = task_name

        content_bytes = None
        if download_url:
            try:
                resp = requests.get(download_url, timeout=30)
                resp.raise_for_status()
                content_bytes = resp.content
            except Exception as e:
                print(f"Fetch error ({download_url}): {e}")

        seq_num += 1
        slide_builders.append(
            _build_content(tpl, doc_data, seq_num,
                           content_bytes, file_type, file_name)
        )

    pptx_bytes = _assemble_zip(tpl, slide_builders)

    print("generating presentation")

    return send_file(
        io.BytesIO(pptx_bytes),
        as_attachment=True,
        download_name="Supporting_Documents_Report.pptx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation"
        ),
    )