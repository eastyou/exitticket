"""render 模块单元测试：分页、卡片内容、裁剪线与转义。"""

from __future__ import annotations

import re
import unittest

from exitticket.model import ExitTicketError, Field, TicketTemplate, get_template
from exitticket.render import render_html


class RenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.template = get_template("321")

    def test_document_basics(self) -> None:
        page = render_html(self.template)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', page)
        self.assertIn('<meta name="viewport"', page)

    def test_a4_portrait(self) -> None:
        page = render_html(self.template)
        self.assertIn("@page { size: A4 portrait; margin: 0; }", page)
        self.assertIn("page-break-after: always", page)

    def test_four_copies_one_sheet(self) -> None:
        page = render_html(self.template, copies=4)
        self.assertEqual(page.count('class="sheet'), 1)
        self.assertEqual(page.count('class="card"'), 4)

    def test_eight_copies_two_sheets(self) -> None:
        page = render_html(self.template, copies=8)
        self.assertEqual(page.count('class="sheet'), 2)
        self.assertEqual(page.count('class="card"'), 8)

    def test_five_copies_two_sheets(self) -> None:
        page = render_html(self.template, copies=5)
        self.assertEqual(page.count('class="sheet'), 2)
        self.assertEqual(page.count('class="card"'), 5)

    def test_each_sheet_has_at_most_four_cards(self) -> None:
        page = render_html(self.template, copies=7)
        sheets = re.findall(r"<section.*?</section>", page, re.S)
        self.assertEqual(len(sheets), 2)
        for sheet in sheets:
            self.assertLessEqual(sheet.count('class="card"'), 4)

    def test_card_numbers_are_continuous(self) -> None:
        page = render_html(self.template, copies=7)
        numbers = [int(item) for item in re.findall(r"编号 (\d+)", page)]
        self.assertEqual(numbers, list(range(1, 8)))

    def test_page_footers(self) -> None:
        page = render_html(self.template, copies=5)
        self.assertIn("第 1 / 2 页", page)
        self.assertIn("第 2 / 2 页", page)
        self.assertIn("共 5 张", page)

    def test_name_and_date_rows(self) -> None:
        page = render_html(self.template, copies=4)
        self.assertEqual(page.count("姓名"), 4)
        self.assertEqual(page.count("日期"), 4)

    def test_title_is_repeated_on_each_card(self) -> None:
        page = render_html(self.template, copies=4, title="数学出门条")
        self.assertEqual(
            page.count('<h2 class="card-title">数学出门条</h2>'), 4
        )

    def test_title_is_escaped(self) -> None:
        page = render_html(self.template, copies=1, title="<课堂>")
        self.assertIn("&lt;课堂&gt;", page)
        self.assertNotIn("<课堂>", page)

    def test_custom_field_is_escaped(self) -> None:
        template = TicketTemplate(
            id="escape",
            name="转义测试",
            summary="检查 <b> 标签是否被转义。",
            fields=(Field(title="我的 <b>收获</b>", lines=1),),
        )
        page = render_html(template, copies=1)
        self.assertIn("&lt;b&gt;收获&lt;/b&gt;", page)
        self.assertNotIn("<b>收获", page)

    def test_template_name_and_summary(self) -> None:
        page = render_html(self.template, copies=1)
        self.assertIn("三二一回顾", page)
        self.assertIn(self.template.summary, page)

    def test_cut_lines_for_four_cards(self) -> None:
        page = render_html(self.template, copies=4)
        self.assertIn("cut-v", page)
        self.assertIn("cut-h", page)
        self.assertIn("dashed", page)

    def test_no_cut_line_for_single_card(self) -> None:
        page = render_html(self.template, copies=1)
        self.assertNotIn('class="sheet cut-v', page)
        self.assertNotIn('class="sheet cut-h', page)

    def test_vertical_cut_for_two_cards(self) -> None:
        page = render_html(self.template, copies=2)
        self.assertIn("cut-v", page)
        self.assertNotIn('class="sheet cut-v cut-h', page)

    def test_both_cuts_for_three_cards(self) -> None:
        page = render_html(self.template, copies=3)
        self.assertIn('class="sheet cut-v cut-h"', page)

    def test_writing_lines_for_321(self) -> None:
        page = render_html(self.template, copies=3)
        self.assertEqual(page.count('<span class="line"></span>'), 18)

    def test_scale_boxes_for_selfcheck(self) -> None:
        page = render_html(get_template("selfcheck"), copies=2)
        self.assertEqual(page.count('<span class="box"></span>'), 8)

    def test_scale_boxes_for_quickquiz(self) -> None:
        page = render_html(get_template("quickquiz"), copies=2)
        self.assertEqual(page.count('<span class="box"></span>'), 10)

    def test_no_external_resources(self) -> None:
        page = render_html(self.template)
        for marker in ("http://", "https://", "<script", "<link", "src="):
            self.assertNotIn(marker, page)

    def test_print_hides_toolbar(self) -> None:
        page = render_html(self.template)
        self.assertIn(".toolbar,", page)
        self.assertIn("display: none", page)

    def test_copies_accepts_numeric_text(self) -> None:
        page = render_html(self.template, copies="6")
        self.assertEqual(page.count('class="card"'), 6)

    def test_repeated_content_is_identical(self) -> None:
        page = render_html(self.template, copies=4)
        self.assertEqual(page.count(self.template.summary), 4)
        self.assertEqual(page.count("我学到的 3 件事"), 4)

    def test_invalid_copies(self) -> None:
        for value in (0, 9, "abc"):
            with self.assertRaises(ExitTicketError):
                render_html(self.template, copies=value)

    def test_invalid_title(self) -> None:
        with self.assertRaises(ExitTicketError):
            render_html(self.template, title=" ")
        with self.assertRaises(ExitTicketError):
            render_html(self.template, title="题" * 41)

    def test_non_template(self) -> None:
        with self.assertRaises(ExitTicketError):
            render_html("321")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
