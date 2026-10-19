"""小红书采集工具：由 Agent 调用时复用 gateway，生命周期由单次工具调用管理。"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.adapters.xhs import XhsGateway
from app.tools.registry import tool


class XhsSearchNotesParams(BaseModel):
    keyword: str = Field(..., min_length=1, description="搜索关键词")


@tool("xhs_search_notes", "使用 xhs-cli 搜索小红书笔记并返回归一化摘要", XhsSearchNotesParams)
def xhs_search_notes(keyword: str) -> dict:
    notes = XhsGateway().search_notes(keyword)
    return {"keyword": keyword, "count": len(notes), "notes": notes}


class XhsNoteDetailParams(BaseModel):
    note_id: str = Field(..., min_length=1, description="小红书笔记 ID")
    xsec_token: str = Field(default="", description="搜索结果携带的 xsec_token")


@tool("xhs_get_note_detail", "使用 xhs-cli 获取单篇小红书笔记详情", XhsNoteDetailParams)
def xhs_get_note_detail(note_id: str, xsec_token: str = "") -> dict:
    return XhsGateway().get_note_detail(note_id, xsec_token)


class XhsUserParams(BaseModel):
    user_id: str = Field(..., min_length=1, description="小红书用户 ID")


@tool("xhs_get_user_info", "使用 xhs-cli 获取小红书用户资料", XhsUserParams)
def xhs_get_user_info(user_id: str) -> dict:
    return XhsGateway().get_user_info(user_id)


@tool("xhs_get_user_posts", "使用 xhs-cli 获取用户发布的笔记", XhsUserParams)
def xhs_get_user_posts(user_id: str) -> dict:
    posts = XhsGateway().get_user_posts(user_id)
    return {"user_id": user_id, "count": len(posts), "posts": posts}


class XhsCommentsParams(BaseModel):
    note_id: str = Field(..., min_length=1, description="小红书笔记 ID")
    xsec_token: str = ""
    max_comments: int = Field(default=50, ge=0, le=500)


@tool("xhs_get_note_comments", "使用 xhs-cli 获取笔记评论", XhsCommentsParams)
def xhs_get_note_comments(note_id: str, xsec_token: str = "", max_comments: int = 50) -> dict:
    comments = XhsGateway().get_note_comments(note_id, xsec_token, max_comments)
    return {"note_id": note_id, "count": len(comments), "comments": comments}