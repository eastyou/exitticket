"""出门条数据模型：模板、填写区、参数校验与分页。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

MIN_COPIES = 1
MAX_COPIES = 8
DEFAULT_COPIES = 4
PER_PAGE = 4
MIN_TITLE = 1
MAX_TITLE = 40
DEFAULT_TITLE = "课堂出门条"

MIN_FIELDS = 1
MAX_FIELDS = 6
MAX_FIELD_TITLE = 30
MAX_NAME = 20
MAX_SUMMARY = 80
MAX_ALIAS = 20
MAX_LINES = 8

FIELD_KINDS: Tuple[str, ...] = ("lines", "scale4", "scale5")

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_CONTROL_PATTERN = re.compile(r"[\x00-\x1f\x7f]")

CopiesInput = Union[int, str]


class ExitTicketError(ValueError):
    """模板、参数或渲染输入不合法。"""


def _require_text(value: object, label: str, limit: int) -> str:
    """校验并清理一段展示文本。"""
    if not isinstance(value, str):
        raise ExitTicketError("%s必须是文本" % label)
    text = value.strip()
    if not text:
        raise ExitTicketError("%s不能为空" % label)
    if len(text) > limit:
        raise ExitTicketError("%s最多 %d 个字符" % (label, limit))
    if _CONTROL_PATTERN.search(text):
        raise ExitTicketError("%s不能包含换行或控制字符" % label)
    return text


@dataclass(frozen=True)
class Field:
    """卡片上的一个填写区：标题、书写行数、交互类型。"""

    title: str
    lines: int
    kind: str = "lines"

    def __post_init__(self) -> None:
        title = _require_text(self.title, "填写区标题", MAX_FIELD_TITLE)
        if isinstance(self.lines, bool) or not isinstance(self.lines, int):
            raise ExitTicketError("填写区「%s」的行数必须是整数" % title)
        if not 0 <= self.lines <= MAX_LINES:
            raise ExitTicketError(
                "填写区「%s」的行数必须在 0~%d 之间" % (title, MAX_LINES)
            )
        if not isinstance(self.kind, str) or self.kind not in FIELD_KINDS:
            raise ExitTicketError(
                "填写区「%s」的类型必须是 %s 之一"
                % (title, "、".join(FIELD_KINDS))
            )
        if self.kind == "lines" and self.lines < 1:
            raise ExitTicketError("书写区「%s」至少需要 1 行" % title)
        if self.kind != "lines" and self.lines != 0:
            raise ExitTicketError("勾选区「%s」不需要书写行数" % title)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "kind", self.kind.strip())

    @property
    def weight(self) -> int:
        """填写区在卡片中占的高度权重。"""
        return self.lines if self.kind == "lines" else 1


@dataclass(frozen=True)
class TicketTemplate:
    """一种出门条模板：编号、中文名、说明、填写区与别名。"""

    id: str
    name: str
    summary: str
    fields: Tuple[Field, ...]
    aliases: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise ExitTicketError("模板编号必须是文本")
        template_id = self.id.strip()
        if not template_id:
            raise ExitTicketError("模板编号不能为空")
        if not _ID_PATTERN.match(template_id):
            raise ExitTicketError(
                "模板编号只能使用小写字母、数字和短横线：%s" % template_id
            )
        name = _require_text(self.name, "模板名称", MAX_NAME)
        summary = _require_text(self.summary, "模板说明", MAX_SUMMARY)

        if isinstance(self.fields, str) or not isinstance(
            self.fields, (list, tuple)
        ):
            raise ExitTicketError("模板「%s」的填写区必须是序列" % name)
        fields = tuple(self.fields)
        if not MIN_FIELDS <= len(fields) <= MAX_FIELDS:
            raise ExitTicketError(
                "模板「%s」的填写区数量必须在 %d~%d 之间"
                % (name, MIN_FIELDS, MAX_FIELDS)
            )
        seen: Dict[str, None] = {}
        for field in fields:
            if not isinstance(field, Field):
                raise ExitTicketError("模板「%s」的填写区必须是 Field 对象" % name)
            if field.title in seen:
                raise ExitTicketError(
                    "模板「%s」的填写区标题重复：%s" % (name, field.title)
                )
            seen[field.title] = None

        if isinstance(self.aliases, str) or not isinstance(
            self.aliases, (list, tuple)
        ):
            raise ExitTicketError("模板「%s」的别名必须是序列" % name)
        aliases: List[str] = []
        alias_seen: Dict[str, None] = {}
        for alias in self.aliases:
            if not isinstance(alias, str):
                raise ExitTicketError("模板「%s」的别名必须是文本" % name)
            cleaned = alias.strip()
            if not cleaned:
                raise ExitTicketError("模板「%s」的别名不能为空" % name)
            if len(cleaned) > MAX_ALIAS:
                raise ExitTicketError(
                    "模板「%s」的别名最多 %d 个字符" % (name, MAX_ALIAS)
                )
            key = cleaned.lower()
            if key in alias_seen:
                raise ExitTicketError(
                    "模板「%s」的别名重复：%s" % (name, cleaned)
                )
            alias_seen[key] = None
            aliases.append(cleaned)

        object.__setattr__(self, "id", template_id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "fields", fields)
        object.__setattr__(self, "aliases", tuple(aliases))


TEMPLATES: Tuple[TicketTemplate, ...] = (
    TicketTemplate(
        id="321",
        name="三二一回顾",
        summary="写下 3 个收获、2 个疑问、1 个还想知道的事。",
        fields=(
            Field(title="我学到的 3 件事", lines=3, kind="lines"),
            Field(title="我还没弄懂的 2 个问题", lines=2, kind="lines"),
            Field(title="我还想知道的 1 件事", lines=1, kind="lines"),
        ),
        aliases=("三二一", "3-2-1", "三二一回顾"),
    ),
    TicketTemplate(
        id="oneline",
        name="一句话总结",
        summary="用一句话写出今天最重要的一点，再说说还不确定的一点。",
        fields=(
            Field(title="今天最重要的一点", lines=2, kind="lines"),
            Field(title="我还不太确定的一点", lines=2, kind="lines"),
        ),
        aliases=("一句话", "一句话总结", "one-line"),
    ),
    TicketTemplate(
        id="muddiest",
        name="最困惑的地方",
        summary="写下一个最不明白的问题，再举一个例子。",
        fields=(
            Field(title="我最不明白的一个问题", lines=2, kind="lines"),
            Field(title="我能想到的一个例子", lines=2, kind="lines"),
        ),
        aliases=("困惑", "最困惑", "最困惑的地方", "muddiest-point"),
    ),
    TicketTemplate(
        id="selfcheck",
        name="自评量表",
        summary="在 1~4 里选一个数字打勾，再写下理由。",
        fields=(
            Field(
                title="我对今天的课理解到什么程度（1 不太懂，4 全懂）",
                lines=0,
                kind="scale4",
            ),
            Field(title="我这样选的理由", lines=3, kind="lines"),
        ),
        aliases=("自评", "自评量表", "self-check"),
    ),
    TicketTemplate(
        id="quickquiz",
        name="快速检测",
        summary="用两句话回答小问题，再圈出你的信心指数。",
        fields=(
            Field(title="第 1 题：今天学的内容，用一句话说清楚", lines=2),
            Field(title="第 2 题：举一个今天学到的例子", lines=2),
            Field(
                title="我对答案的信心（1 没把握，5 很有把握）",
                lines=0,
                kind="scale5",
            ),
        ),
        aliases=("快速检测", "小检测", "quick-quiz", "测验"),
    ),
)


def normalize_name(value: str) -> str:
    """统一模板名的大小写与首尾空白。"""
    if not isinstance(value, str):
        raise ExitTicketError("模板名称必须是文本")
    return value.strip().lower()


def build_registry(
    templates: Sequence[TicketTemplate],
) -> Dict[str, TicketTemplate]:
    """建立「编号/别名 -> 模板」注册表，并检查别名冲突。"""
    if isinstance(templates, str) or not isinstance(templates, (list, tuple)):
        raise ExitTicketError("模板列表必须是序列")
    registry: Dict[str, TicketTemplate] = {}
    for template in templates:
        if not isinstance(template, TicketTemplate):
            raise ExitTicketError("模板列表中的每一项都必须是 TicketTemplate")
        keys: List[str] = [template.id]
        keys.extend(template.aliases)
        for key in keys:
            normalized = normalize_name(key)
            if not normalized:
                raise ExitTicketError("模板名称不能为空")
            existing = registry.get(normalized)
            if existing is not None and existing is not template:
                raise ExitTicketError("模板名称或别名重复：%s" % key)
            registry[normalized] = template
    if not registry:
        raise ExitTicketError("模板列表不能为空")
    return registry


_REGISTRY: Dict[str, TicketTemplate] = build_registry(TEMPLATES)


def list_templates() -> Tuple[TicketTemplate, ...]:
    """按注册顺序返回全部模板。"""
    return TEMPLATES


def template_choices() -> str:
    """生成「编号（中文名）」形式的中文选项列表。"""
    return "、".join("%s（%s）" % (item.id, item.name) for item in TEMPLATES)


def get_template(name: str) -> TicketTemplate:
    """按编号或别名取模板，未知时给出中文候选列表。"""
    if not isinstance(name, str):
        raise ExitTicketError("模板名称必须是文本")
    key = normalize_name(name)
    if not key:
        raise ExitTicketError("请指定模板，可选：%s" % template_choices())
    template = _REGISTRY.get(key)
    if template is None:
        raise ExitTicketError(
            "未知模板「%s」，可选：%s" % (name.strip(), template_choices())
        )
    return template


def validate_copies(value: CopiesInput) -> int:
    """校验份数：1~8 的整数。"""
    if isinstance(value, bool):
        raise ExitTicketError(
            "份数必须是 %d~%d 的整数" % (MIN_COPIES, MAX_COPIES)
        )
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ExitTicketError(
                "份数必须是 %d~%d 的整数" % (MIN_COPIES, MAX_COPIES)
            )
        try:
            number = int(text, 10)
        except ValueError as exc:
            raise ExitTicketError(
                "份数必须是 %d~%d 的整数" % (MIN_COPIES, MAX_COPIES)
            ) from exc
    else:
        raise ExitTicketError(
            "份数必须是 %d~%d 的整数" % (MIN_COPIES, MAX_COPIES)
        )
    if not MIN_COPIES <= number <= MAX_COPIES:
        raise ExitTicketError(
            "份数必须在 %d~%d 之间，当前是 %d"
            % (MIN_COPIES, MAX_COPIES, number)
        )
    return number


def validate_title(value: Optional[str]) -> str:
    """校验标题：去空白后 1~40 个字符，且不能换行。"""
    if not isinstance(value, str):
        raise ExitTicketError("标题必须是文本")
    title = value.strip()
    if not MIN_TITLE <= len(title) <= MAX_TITLE:
        raise ExitTicketError(
            "标题长度必须在 %d~%d 个字符之间" % (MIN_TITLE, MAX_TITLE)
        )
    if _CONTROL_PATTERN.search(title):
        raise ExitTicketError("标题不能包含换行或控制字符")
    return title


def page_count(copies: CopiesInput) -> int:
    """按每页 4 张计算总页数。"""
    count = validate_copies(copies)
    return (count + PER_PAGE - 1) // PER_PAGE


def paginate(copies: CopiesInput) -> List[List[int]]:
    """把连续编号切分成每页最多 4 张，返回各页的卡片编号。"""
    count = validate_copies(copies)
    numbers = list(range(1, count + 1))
    return [
        numbers[start:start + PER_PAGE]
        for start in range(0, count, PER_PAGE)
    ]
