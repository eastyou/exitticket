"""命令行入口单元测试：参数解析、中文报错与退出码。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from exitticket.cli import main
from exitticket.model import TEMPLATES


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = self.root / "课堂出门条.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        """运行 CLI，捕获输出并把 SystemExit 转成退出码。"""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        return code, out.getvalue(), err.getvalue()

    def test_generate(self) -> None:
        code, out, err = self.run_cli(
            ["--template", "321", "-o", str(self.target)]
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(self.target.exists())
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("<title>课堂出门条 · 三二一回顾</title>", page)
        self.assertEqual(page.count('class="card"'), 4)
        self.assertIn("已生成", out)

    def test_all_templates_generate(self) -> None:
        for template in TEMPLATES:
            target = self.root / ("%s.html" % template.id)
            code, _, err = self.run_cli(
                ["--template", template.id, "--copies", "2", "-o", str(target)]
            )
            self.assertEqual(code, 0, err)
            page = target.read_text(encoding="utf-8")
            self.assertEqual(page.count('class="card"'), 2)

    def test_chinese_alias(self) -> None:
        code, _, err = self.run_cli(
            ["--template", "三二一", "--copies", "1", "-o", str(self.target)]
        )
        self.assertEqual(code, 0, err)
        self.assertIn(
            "三二一回顾", self.target.read_text(encoding="utf-8")
        )

    def test_unknown_template(self) -> None:
        code, _, err = self.run_cli(
            ["--template", "不存在的模板", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("未知模板", err)
        self.assertIn("321", err)
        self.assertFalse(self.target.exists())

    def test_copies_out_of_range(self) -> None:
        for value in ("0", "9"):
            code, _, err = self.run_cli(
                ["--template", "321", "--copies", value, "-o", str(self.target)]
            )
            self.assertEqual(code, 2)
            self.assertIn("份数", err)
        self.assertFalse(self.target.exists())

    def test_copies_not_a_number(self) -> None:
        code, _, err = self.run_cli(
            ["--template", "321", "--copies", "abc", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("份数", err)

    def test_title_too_long(self) -> None:
        code, _, err = self.run_cli(
            ["--template", "321", "--title", "题" * 41, "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("标题", err)

    def test_empty_title(self) -> None:
        code, _, err = self.run_cli(
            ["--template", "321", "--title", "  ", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("标题", err)

    def test_write_failure(self) -> None:
        missing = self.root / "missing" / "out.html"
        code, _, err = self.run_cli(
            ["--template", "321", "-o", str(missing)]
        )
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", err)

    def test_two_pages_for_eight_copies(self) -> None:
        code, _, err = self.run_cli(
            ["--template", "oneline", "--copies", "8", "-o", str(self.target)]
        )
        self.assertEqual(code, 0, err)
        page = self.target.read_text(encoding="utf-8")
        self.assertEqual(page.count('class="sheet'), 2)
        self.assertEqual(page.count('class="card"'), 8)

    def test_help(self) -> None:
        code, out, _ = self.run_cli(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("--template", out)

    def test_version(self) -> None:
        code, out, _ = self.run_cli(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("exitticket 0.1.0", out)

    def test_unknown_option(self) -> None:
        code, _, err = self.run_cli(["--bogus"])
        self.assertEqual(code, 2)
        self.assertIn("错误", err)
        self.assertIn("无法识别", err)


if __name__ == "__main__":
    unittest.main()
