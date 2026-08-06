"""T2.1/T2.3/T2.5 RED: 文档加载器测试。

覆盖 Markdown / PDF / Word 三种格式解析与按扩展名分发。
"""
from pathlib import Path

import docx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def _write_markdown(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_pdf(path: Path, text: str) -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("STSong-Light", 14)
    c.drawString(100, 700, text)
    c.save()


def _write_docx(path: Path, text: str) -> None:
    d = docx.Document()
    d.add_paragraph(text)
    d.save(str(path))


def test_load_markdown_strips_syntax(tmp_path):
    from app.rag.loaders import load_markdown

    md = tmp_path / "note.md"
    _write_markdown(md, "# 标题\n\n这是一段**加粗**内容。\n\n- 项目一\n- 项目二\n")
    docs = load_markdown(md)

    assert len(docs) == 1
    content = docs[0].page_content
    assert "标题" in content
    assert "加粗" in content
    assert "项目一" in content
    # 应去除 markdown 语法符号
    assert "**" not in content
    assert docs[0].metadata["source"] == str(md)
    assert docs[0].metadata["format"] == "markdown"


def test_load_pdf_extracts_text(tmp_path):
    from app.rag.loaders import load_pdf

    pdf = tmp_path / "doc.pdf"
    _write_pdf(pdf, "PDF 测试内容抽取")
    docs = load_pdf(pdf)

    assert len(docs) >= 1
    full = "\n".join(d.page_content for d in docs)
    assert "PDF 测试内容抽取" in full
    assert docs[0].metadata["format"] == "pdf"
    assert docs[0].metadata["page"] == 1


def test_load_docx_extracts_text(tmp_path):
    from app.rag.loaders import load_docx

    docx_path = tmp_path / "doc.docx"
    _write_docx(docx_path, "Word 文档测试内容")
    docs = load_docx(docx_path)

    assert len(docs) == 1
    assert "Word 文档测试内容" in docs[0].page_content
    assert docs[0].metadata["format"] == "docx"


def test_load_document_dispatches_by_extension(tmp_path):
    from app.rag.loaders import load_document

    md = tmp_path / "a.md"
    _write_markdown(md, "# 你好")
    docs = load_document(md)
    assert "你好" in docs[0].page_content


def test_load_document_unsupported_format_raises(tmp_path):
    from app.rag.loaders import load_document

    txt = tmp_path / "a.txt"
    txt.write_text("x", encoding="utf-8")
    import pytest

    with pytest.raises(ValueError, match="不支持的文档格式"):
        load_document(txt)
