"""把出门条模板渲染成 A4 纵向、可裁剪的打印页面。"""

from __future__ import annotations

import html
from typing import List, Optional

from .model import (
    DEFAULT_COPIES,
    DEFAULT_TITLE,
    CopiesInput,
    ExitTicketError,
    Field,
    TicketTemplate,
    paginate,
    validate_copies,
    validate_title,
)

SCALE_SIZES = {"scale4": 4, "scale5": 5}


def _escape(text: str) -> str:
    """转义 HTML 特殊字符，避免标题或模板文字破坏页面结构。"""
    return html.escape(text, quote=True)


def _field_markup(field: Field) -> str:
    """渲染一个填写区：书写横线或 1~N 勾选框。"""
    label = '<p class="field-label">%s</p>' % _escape(field.title)
    if field.kind == "lines":
        body = '<div class="lines">%s</div>' % (
            '<span class="line"></span>' * field.lines
        )
    else:
        total = SCALE_SIZES[field.kind]
        options = "".join(
            '<span class="opt"><span class="box"></span>%d</span>'
            % number
            for number in range(1, total + 1)
        )
        body = '<div class="scale">%s</div>' % options
    return (
        '<div class="field" style="flex:%d 1 0">%s%s</div>'
        % (field.weight, label, body)
    )


def _card_markup(template: TicketTemplate, title: str, number: int) -> str:
    """渲染一张卡片，包含标题、姓名日期行与全部填写区。"""
    fields = "".join(_field_markup(field) for field in template.fields)
    return (
        '<article class="card" aria-label="第 %d 张出门条">'
        '<header class="card-head">'
        '<h2 class="card-title">%s</h2>'
        '<span class="card-no">编号 %d</span>'
        "</header>"
        '<p class="card-tag">%s · 下课前三分钟</p>'
        '<p class="card-summary">%s</p>'
        '<p class="name-row"><span>姓名</span><span class="blank"></span>'
        '<span>日期</span><span class="blank"></span></p>'
        '<div class="fields">%s</div>'
        "</article>"
        % (
            number,
            _escape(title),
            number,
            _escape(template.name),
            _escape(template.summary),
            fields,
        )
    )


def _sheet_markup(
    template: TicketTemplate,
    title: str,
    numbers: List[int],
    page_no: int,
    page_total: int,
    copies: int,
) -> str:
    """渲染一页 A4：最多 4 张卡片、裁剪虚线与页码。"""
    cards = "".join(
        _card_markup(template, title, number) for number in numbers
    )
    classes = ["sheet"]
    if len(numbers) >= 2:
        classes.append("cut-v")
    if len(numbers) >= 3:
        classes.append("cut-h")
    hint = " · 沿虚线剪开" if classes[1:] else ""
    return (
        '<section class="%s" aria-label="第 %d 页">%s'
        '<p class="page-no">第 %d / %d 页 · 共 %d 张%s</p>'
        "</section>"
        % (
            " ".join(classes),
            page_no,
            cards,
            page_no,
            page_total,
            copies,
            hint,
        )
    )


def render_html(
    template: TicketTemplate,
    copies: CopiesInput = DEFAULT_COPIES,
    title: Optional[str] = DEFAULT_TITLE,
) -> str:
    """生成完整自包含 HTML：A4 纵向，每页 4 张，自动分页。"""
    if not isinstance(template, TicketTemplate):
        raise ExitTicketError("template 必须是 TicketTemplate 对象")
    card_copies = validate_copies(copies)
    page_title = validate_title(title)

    pages = paginate(card_copies)
    sheets = "".join(
        _sheet_markup(
            template,
            page_title,
            numbers,
            index,
            len(pages),
            card_copies,
        )
        for index, numbers in enumerate(pages, start=1)
    )
    toolbar = (
        '<header class="toolbar"><h1>%s</h1>'
        "<p>%s · 共 %d 张 · 每页 4 张 · A4 纵向</p></header>"
        % (_escape(page_title), _escape(template.name), card_copies)
    )
    tip = (
        '<p class="tip">按 Ctrl/Cmd + P 打印，纸张选 A4 纵向；'
        "打印后沿每页中间的虚线剪开，每位学生一张。</p>"
    )
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s · %s</title>\n<style>%s</style>\n</head>\n<body>\n"
        "%s\n%s\n<main class=\"pages\">\n%s</main>\n</body>\n</html>\n"
        % (
            _escape(page_title),
            _escape(template.name),
            _STYLE,
            toolbar,
            tip,
            sheets,
        )
    )


_STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 7mm 4mm 10mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC",
      "Heiti SC", "Hiragino Sans GB", sans-serif;
    line-height: 1.5;
    -webkit-text-size-adjust: 100%;
  }
  .toolbar {
    width: 210mm;
    max-width: 100%;
    margin: 0 auto 3mm;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 6px 16px;
    color: #334155;
  }
  .toolbar h1 {
    margin: 0;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 1px;
  }
  .toolbar p { margin: 0; font-size: 12px; color: #64748b; }
  .tip {
    width: 210mm;
    max-width: 100%;
    margin: 0 auto 5mm;
    font-size: 12px;
    line-height: 1.6;
    color: #64748b;
  }
  .pages {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6mm;
  }
  .sheet {
    position: relative;
    width: 55.2632em;
    height: 78.1em;
    font-size: clamp(
      3px,
      calc((100vw - 9mm - 18px) / 55.2632),
      3.8mm
    );
    padding: 2em;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    column-gap: 1.5em;
    row-gap: 1.5em;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    page-break-after: always;
    break-after: page;
    overflow: hidden;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .sheet.cut-v::before,
  .sheet.cut-h::after {
    content: "";
    position: absolute;
    z-index: 0;
    pointer-events: none;
  }
  .sheet.cut-v::before {
    top: 0;
    bottom: 0;
    left: 50%;
    border-left: 0.07em dashed #94a3b8;
  }
  .sheet.cut-h::after {
    left: 0;
    right: 0;
    top: 50%;
    border-top: 0.07em dashed #94a3b8;
  }
  .card {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    padding: 1.1em 1.3em 0.9em;
    border: 0.06em solid #cbd5e1;
    border-radius: 0.5em;
    background: #fff;
    overflow: hidden;
  }
  .card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.6em;
    padding-bottom: 0.4em;
    border-bottom: 0.05em solid #cbd5e1;
  }
  .card-title {
    margin: 0;
    font-size: 1.15em;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: 0.02em;
    overflow-wrap: anywhere;
  }
  .card-no {
    flex: none;
    padding: 0.15em 0.45em;
    border: 0.05em solid #cbd5e1;
    border-radius: 0.4em;
    color: #475569;
    font-size: 0.6em;
    white-space: nowrap;
  }
  .card-tag {
    margin: 0.45em 0 0;
    color: #475569;
    font-size: 0.7em;
  }
  .card-summary {
    margin: 0.15em 0 0;
    color: #64748b;
    font-size: 0.66em;
    line-height: 1.4;
  }
  .name-row {
    display: flex;
    align-items: flex-end;
    gap: 0.4em;
    margin: 0.7em 0 0.45em;
    color: #334155;
    font-size: 0.75em;
  }
  .name-row .blank {
    flex: 1 1 0;
    min-width: 0;
    height: 1.05em;
    border-bottom: 0.05em solid #94a3b8;
  }
  .fields {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
  }
  .field {
    display: flex;
    flex-direction: column;
    min-height: 0;
    padding-bottom: 0.35em;
  }
  .field + .field { padding-top: 0.3em; }
  .field-label {
    margin: 0 0 0.15em;
    color: #0f172a;
    font-size: 0.82em;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }
  .lines {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
  }
  .line {
    flex: 1 1 0;
    min-height: 1.15em;
    border-bottom: 0.04em solid #cbd5e1;
  }
  .scale {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.9em;
    flex: 1 1 auto;
    min-height: 1.6em;
    padding: 0.1em 0;
  }
  .scale .opt {
    display: inline-flex;
    align-items: center;
    gap: 0.28em;
    color: #334155;
    font-size: 0.8em;
  }
  .scale .box {
    display: inline-block;
    width: 0.95em;
    height: 0.95em;
    border: 0.09em solid #64748b;
    border-radius: 0.15em;
  }
  .page-no {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 1.4em;
    margin: 0;
    color: #64748b;
    font-size: 0.6em;
    text-align: center;
  }
  @page { size: A4 portrait; margin: 0; }
  @media screen and (max-width: 480px) {
    body { padding: 5mm 4mm 8mm; }
    .toolbar h1 { font-size: 15px; }
    .tip { font-size: 11px; }
  }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar,
    .tip { display: none; }
    .pages { gap: 0; }
    .sheet {
      margin: 0;
      font-size: 3.8mm;
      box-shadow: none;
    }
    * {
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
  }
"""
