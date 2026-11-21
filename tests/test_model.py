"""model 模块单元测试：模板注册、字段校验、参数与分页。"""

from __future__ import annotations

import re
import unittest
from typing import Dict, List

from exitticket.model import (
    DEFAULT_COPIES,
    DEFAULT_TITLE,
    MAX_COPIES,
    MAX_TITLE,
    TEMPLATES,
    ExitTicketError,
    Field,
    TicketTemplate,
    build_registry,
    get_template,
    list_templates,
    normalize_name,
    page_count,
    paginate,
    template_choices,
    validate_copies,
    validate_title,
)

CHINESE = re.compile(r"[\u4e00-\u9fff]")


def make_template(template_id: str = "demo", alias: str = "示例") -> TicketTemplate:
    """构造一个合法模板，供校验用例复用。"""
    return TicketTemplate(
        id=template_id,
        name="示例模板",
        summary="用一句话写下今天的收获。",
        fields=(Field(title="我的收获", lines=2),),
        aliases=(alias,),
    )


class TemplateRegistryTest(unittest.TestCase):
    def test_template_count(self) -> None:
        self.assertEqual(len(TEMPLATES), 5)
        self.assertEqual(len(list_templates()), 5)

    def test_unique_ids(self) -> None:
        ids = [item.id for item in TEMPLATES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_names(self) -> None:
        names = [item.name for item in TEMPLATES]
        self.assertEqual(len(names), len(set(names)))

    def test_every_template_has_chinese_name(self) -> None:
        for template in TEMPLATES:
            self.assertTrue(CHINESE.search(template.name), template.id)

    def test_every_template_has_fields(self) -> None:
        for template in TEMPLATES:
            self.assertGreaterEqual(len(template.fields), 1, template.id)

    def test_every_field_kind_is_known(self) -> None:
        allowed = {"lines", "scale4", "scale5"}
        for template in TEMPLATES:
            for field in template.fields:
                self.assertIn(field.kind, allowed)

    def test_every_field_title_is_chinese(self) -> None:
        for template in TEMPLATES:
            for field in template.fields:
                self.assertTrue(CHINESE.search(field.title), field.title)

    def test_template_321_structure(self) -> None:
        template = get_template("321")
        self.assertEqual([field.lines for field in template.fields], [3, 2, 1])
        self.assertEqual(len(template.fields), 3)
        self.assertTrue(all(field.kind == "lines" for field in template.fields))

    def test_template_oneline_structure(self) -> None:
        template = get_template("oneline")
        self.assertEqual(len(template.fields), 2)
        titles = [field.title for field in template.fields]
        self.assertIn("最重要", titles[0])
        self.assertIn("不太确定", titles[1])

    def test_template_muddiest_structure(self) -> None:
        template = get_template("muddiest")
        titles = " ".join(field.title for field in template.fields)
        self.assertIn("问题", titles)
        self.assertIn("例子", titles)

    def test_template_selfcheck_structure(self) -> None:
        template = get_template("selfcheck")
        self.assertEqual(
            [field.kind for field in template.fields], ["scale4", "lines"]
        )
        self.assertEqual(template.fields[0].lines, 0)

    def test_template_quickquiz_structure(self) -> None:
        template = get_template("quickquiz")
        self.assertEqual(
            [field.kind for field in template.fields],
            ["lines", "lines", "scale5"],
        )
        self.assertEqual(template.fields[-1].lines, 0)

    def test_get_template_by_id(self) -> None:
        for template in TEMPLATES:
            self.assertIs(get_template(template.id), template)

    def test_get_template_by_chinese_alias(self) -> None:
        aliases: Dict[str, str] = {
            "三二一": "321",
            "一句话": "oneline",
            "困惑": "muddiest",
            "自评": "selfcheck",
            "小检测": "quickquiz",
        }
        for alias, expected in aliases.items():
            self.assertEqual(get_template(alias).id, expected)

    def test_get_template_is_case_insensitive(self) -> None:
        self.assertEqual(get_template("OneLine").id, "oneline")
        self.assertEqual(get_template("SELFCHECK").id, "selfcheck")

    def test_get_template_strips_whitespace(self) -> None:
        self.assertEqual(get_template("  muddiest  ").id, "muddiest")
        self.assertEqual(get_template(" 三二一 ").id, "321")

    def test_unknown_template_lists_choices(self) -> None:
        with self.assertRaises(ExitTicketError) as ctx:
            get_template("不存在的模板")
        message = str(ctx.exception)
        self.assertIn("未知模板", message)
        for template in TEMPLATES:
            self.assertIn(template.id, message)
            self.assertIn(template.name, message)

    def test_empty_template_name(self) -> None:
        with self.assertRaises(ExitTicketError) as ctx:
            get_template("   ")
        self.assertIn("可选", str(ctx.exception))

    def test_non_text_template_name(self) -> None:
        with self.assertRaises(ExitTicketError):
            get_template(321)  # type: ignore[arg-type]

    def test_normalize_name(self) -> None:
        self.assertEqual(normalize_name("  OneLine "), "oneline")
        self.assertEqual(normalize_name("三二一"), "三二一")

    def test_template_choices_text(self) -> None:
        text = template_choices()
        for template in TEMPLATES:
            self.assertIn("%s（%s）" % (template.id, template.name), text)

    def test_registry_covers_every_name(self) -> None:
        registry = build_registry(TEMPLATES)
        expected = sum(1 + len(item.aliases) for item in TEMPLATES)
        self.assertEqual(len(registry), expected)
        for template in TEMPLATES:
            self.assertIs(registry[template.id], template)
            for alias in template.aliases:
                self.assertIs(registry[normalize_name(alias)], template)

    def test_duplicate_alias_across_templates(self) -> None:
        first = make_template("first", "同名")
        second = make_template("second", "同名")
        with self.assertRaises(ExitTicketError) as ctx:
            build_registry((first, second))
        self.assertIn("重复", str(ctx.exception))

    def test_build_registry_rejects_non_template(self) -> None:
        with self.assertRaises(ExitTicketError):
            build_registry(("321",))  # type: ignore[arg-type]


class FieldValidationTest(unittest.TestCase):
    def test_default_kind_is_lines(self) -> None:
        self.assertEqual(Field(title="我的收获", lines=2).kind, "lines")

    def test_title_is_stripped(self) -> None:
        self.assertEqual(Field(title="  我的收获  ", lines=2).title, "我的收获")

    def test_empty_title(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="   ", lines=1)

    def test_long_title(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="字" * 31, lines=1)

    def test_lines_must_be_int(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="我的收获", lines=True)  # type: ignore[arg-type]

    def test_lines_must_be_in_range(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="我的收获", lines=9)
        with self.assertRaises(ExitTicketError):
            Field(title="我的收获", lines=-1)

    def test_unknown_kind(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="我的收获", lines=1, kind="slider")

    def test_lines_field_needs_one_line(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="我的收获", lines=0, kind="lines")

    def test_scale_field_rejects_lines(self) -> None:
        with self.assertRaises(ExitTicketError):
            Field(title="理解程度", lines=2, kind="scale4")

    def test_weight(self) -> None:
        self.assertEqual(Field(title="我的收获", lines=3).weight, 3)
        self.assertEqual(
            Field(title="理解程度", lines=0, kind="scale4").weight, 1
        )


class TemplateValidationTest(unittest.TestCase):
    def test_id_must_be_lowercase_slug(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="Demo",
                name="示例",
                summary="说明",
                fields=(Field("我的收获", 1),),
            )

    def test_empty_name(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="  ",
                summary="说明",
                fields=(Field("我的收获", 1),),
            )

    def test_empty_summary(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="示例",
                summary=" ",
                fields=(Field("我的收获", 1),),
            )

    def test_fields_must_not_be_empty(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(id="demo", name="示例", summary="说明", fields=())

    def test_fields_must_be_sequence(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="示例",
                summary="说明",
                fields="我的收获",  # type: ignore[arg-type]
            )

    def test_duplicate_field_titles(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="示例",
                summary="说明",
                fields=(Field("我的收获", 1), Field("我的收获", 2)),
            )

    def test_aliases_must_be_sequence(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="示例",
                summary="说明",
                fields=(Field("我的收获", 1),),
                aliases="示例",  # type: ignore[arg-type]
            )

    def test_empty_alias(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="示例",
                summary="说明",
                fields=(Field("我的收获", 1),),
                aliases=("  ",),
            )

    def test_duplicate_alias_inside_template(self) -> None:
        with self.assertRaises(ExitTicketError):
            TicketTemplate(
                id="demo",
                name="示例",
                summary="说明",
                fields=(Field("我的收获", 1),),
                aliases=("示例", "示例"),
            )

    def test_name_and_summary_are_stripped(self) -> None:
        template = make_template()
        self.assertEqual(template.name, "示例模板")
        self.assertEqual(template.summary, "用一句话写下今天的收获。")


class CopiesTest(unittest.TestCase):
    def test_valid_range(self) -> None:
        for value in (1, DEFAULT_COPIES, MAX_COPIES):
            self.assertEqual(validate_copies(value), value)

    def test_numeric_text(self) -> None:
        self.assertEqual(validate_copies("5"), 5)
        self.assertEqual(validate_copies(" 8 "), 8)

    def test_out_of_range(self) -> None:
        for value in (0, MAX_COPIES + 1, -1):
            with self.assertRaises(ExitTicketError):
                validate_copies(value)

    def test_non_integer_text(self) -> None:
        for value in ("abc", "4.5", ""):
            with self.assertRaises(ExitTicketError):
                validate_copies(value)

    def test_bool_is_rejected(self) -> None:
        with self.assertRaises(ExitTicketError):
            validate_copies(True)  # type: ignore[arg-type]

    def test_other_types_are_rejected(self) -> None:
        with self.assertRaises(ExitTicketError):
            validate_copies(4.0)  # type: ignore[arg-type]
        with self.assertRaises(ExitTicketError):
            validate_copies(None)  # type: ignore[arg-type]


class TitleTest(unittest.TestCase):
    def test_default_title(self) -> None:
        self.assertEqual(validate_title(DEFAULT_TITLE), DEFAULT_TITLE)

    def test_title_is_stripped(self) -> None:
        self.assertEqual(validate_title("  课堂出门条  "), "课堂出门条")

    def test_max_length(self) -> None:
        self.assertEqual(validate_title("题" * MAX_TITLE), "题" * MAX_TITLE)
        with self.assertRaises(ExitTicketError):
            validate_title("题" * (MAX_TITLE + 1))

    def test_empty_title(self) -> None:
        for value in ("", "   "):
            with self.assertRaises(ExitTicketError):
                validate_title(value)

    def test_title_cannot_contain_newline(self) -> None:
        with self.assertRaises(ExitTicketError):
            validate_title("第一行\n第二行")

    def test_non_text_title(self) -> None:
        with self.assertRaises(ExitTicketError):
            validate_title(None)
        with self.assertRaises(ExitTicketError):
            validate_title(123)  # type: ignore[arg-type]


class PaginationTest(unittest.TestCase):
    def test_page_count(self) -> None:
        expected = {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 2}
        for copies, pages in expected.items():
            self.assertEqual(page_count(copies), pages)

    def test_paginate_sizes(self) -> None:
        self.assertEqual([len(page) for page in paginate(8)], [4, 4])
        self.assertEqual([len(page) for page in paginate(5)], [4, 1])
        self.assertEqual([len(page) for page in paginate(1)], [1])

    def test_numbers_are_continuous(self) -> None:
        pages = paginate(8)
        numbers: List[int] = [item for page in pages for item in page]
        self.assertEqual(numbers, list(range(1, 9)))

    def test_each_page_has_at_most_four(self) -> None:
        for copies in range(1, MAX_COPIES + 1):
            for page in paginate(copies):
                self.assertLessEqual(len(page), 4)

    def test_paginate_rejects_invalid(self) -> None:
        with self.assertRaises(ExitTicketError):
            paginate(0)


if __name__ == "__main__":
    unittest.main()
