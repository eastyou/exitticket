"""命令行入口：生成 A4 可打印的课堂出门条。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn, Optional, Sequence

from .model import (
    DEFAULT_COPIES,
    DEFAULT_TITLE,
    MAX_COPIES,
    MAX_TITLE,
    MIN_COPIES,
    ExitTicketError,
    get_template,
    template_choices,
    validate_copies,
    validate_title,
)
from .render import render_html


class _ChineseParser(argparse.ArgumentParser):
    """把 argparse 的报错改成中文，并统一以退出码 2 结束。"""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print("错误: %s" % _translate(message), file=sys.stderr)
        raise SystemExit(2)


def _translate(message: str) -> str:
    """翻译 argparse 常见英文报错。"""
    if message.startswith("unrecognized arguments:"):
        return "无法识别的参数：%s" % message.split(":", 1)[1].strip()
    if message.startswith("the following arguments are required:"):
        return "缺少必要参数：%s" % message.split(":", 1)[1].strip()
    if message.endswith("expected one argument"):
        name = message.split(":", 1)[0].replace("argument ", "").strip()
        return "参数 %s 需要一个值" % name
    return message


def build_parser() -> argparse.ArgumentParser:
    parser = _ChineseParser(
        prog="exitticket",
        description="课堂出门条：一条命令生成 A4 可打印、可裁剪的课后反馈卡",
    )
    parser.add_argument(
        "--version", action="version", version="exitticket 0.1.0"
    )
    parser.add_argument(
        "--template",
        default="321",
        help="模板：321 / oneline / muddiest / selfcheck / quickquiz，"
        "也支持中文别名（可选：%s）" % template_choices(),
    )
    parser.add_argument(
        "--copies",
        default=DEFAULT_COPIES,
        help="张数，%d~%d，默认 %d，每页 4 张自动分页"
        % (MIN_COPIES, MAX_COPIES, DEFAULT_COPIES),
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help="卡片标题，1~%d 个字符，默认「%s」" % (MAX_TITLE, DEFAULT_TITLE),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="课堂出门条.html",
        help="输出 HTML 路径，默认 课堂出门条.html",
    )
    return parser


def _validate_output(value: str) -> str:
    """校验输出路径，避免空路径与空字符。"""
    if not isinstance(value, str):
        raise ExitTicketError("输出路径必须是文本")
    target = value.strip()
    if not target:
        raise ExitTicketError("输出路径不能为空")
    if "\x00" in target:
        raise ExitTicketError("输出路径不能包含空字符")
    return target


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        template = get_template(args.template)
        copies = validate_copies(args.copies)
        title = validate_title(args.title)
        output = _validate_output(args.output)
        page = render_html(template, copies=copies, title=title)
    except ExitTicketError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2

    try:
        Path(output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    print(
        "已生成 %s：%s，共 %d 张，每页 4 张"
        % (output, template.name, copies)
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
