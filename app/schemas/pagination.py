import math
from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


def make_page(items: list, total: int, skip: int, limit: int) -> dict:
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = math.ceil(total / limit) if limit > 0 and total > 0 else 1
    return {"items": items, "total": total, "page": page, "size": len(items), "pages": pages}
