"""exitticket：A4 可打印、可裁剪的课堂出门条。"""

from __future__ import annotations

from .model import (
    DEFAULT_COPIES,
    DEFAULT_TITLE,
    FIELD_KINDS,
    MAX_COPIES,
    MAX_TITLE,
    MIN_COPIES,
    PER_PAGE,
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
from .render import render_html

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_COPIES",
    "DEFAULT_TITLE",
    "FIELD_KINDS",
    "MAX_COPIES",
    "MAX_TITLE",
    "MIN_COPIES",
    "PER_PAGE",
    "TEMPLATES",
    "ExitTicketError",
    "Field",
    "TicketTemplate",
    "build_registry",
    "get_template",
    "list_templates",
    "normalize_name",
    "page_count",
    "paginate",
    "render_html",
    "template_choices",
    "validate_copies",
    "validate_title",
    "__version__",
]
