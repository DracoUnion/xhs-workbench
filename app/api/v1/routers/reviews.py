"""审核点路由：列出待处理、执行通过/驳回。"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.services.runs import act_review_point, list_review_points

router = APIRouter(prefix="/review-points", tags=["reviews"])


class ReviewActionBody(BaseModel):
    action: Literal["passed", "rejected"]
    note: str | None = None


@router.get("")
def list_points(
    pending_only: bool = True,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return {"data": list_review_points(db, pending_only=pending_only)}


@router.patch("/{point_id}")
def apply_review(
    point_id: int,
    body: ReviewActionBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    result = act_review_point(db, point_id, body.action, body.note, actor_id=user.id)
    return {"data": result}