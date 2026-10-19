"""只读 SQL 视图：为前端中「后端尚未实现」的页面提供 SELECT 接口。

这些端点仅做查询（不产生任何写操作），返回的 JSON 形状与 frontend/src/types 完全一致，
使桌面端立即可浏览数据库中已存在的表（keywords/notes/products/accounts/...）。
需要真实业务逻辑的动作（采集、评分、生成、转 Skill、试跑等）保持「待接入」。

挂载方式见 server.build_app()：该 router 先并入 app.api.v1.router.api_router，
再由 app.main.create_app() 一并复制到最终 app（保证不被末尾 catch-all 404 遮蔽）。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    Account,
    AccountMetric,
    AgentDef,
    ContentPackage,
    DesignDoc,
    Direction,
    DirectionAccount,
    Keyword,
    Material,
    Note,
    NoteAnalysis,
    Product,
    ProductImage,
    RankingSource,
    RiskConfig,
    Skill,
    Template,
)
from app.models.content import NoteImage
from app.services.runs import list_runs

router = APIRouter(tags=["standalone-readonly"])


# ---------- 序列化辅助 ----------


def _dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _num(value: Any) -> Any:
    """Numeric/Decimal → float|int；避免 JSON 序列化 Decimal 报错。"""
    if value is None:
        return None
    if hasattr(value, "float"):
        return float(value)
    return value


def _paged(db: Session, model, stmt, page: int, page_size: int) -> tuple[list[Any], int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(model.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return rows, total


# ---------- 模型 → dict ----------


def account_to_dict(a: Account, metrics: AccountMetric | None = None) -> dict[str, Any]:
    return {
        "id": a.id,
        "xhs_user_id": a.xhs_user_id,
        "nickname": a.nickname,
        "fans": a.fans,
        "score": _num(a.score),
        "first_seen_board": _dt(a.first_seen_board),
        "board_days": a.board_days,
        "board_types": a.board_types,
        "metrics": metric_to_dict(metrics) if metrics else None,
    }


def metric_to_dict(m: AccountMetric) -> dict[str, Any]:
    return {
        "id": m.id,
        "account_id": m.account_id,
        "trade_score": _num(m.trade_score),
        "conv_score": _num(m.conv_score),
        "read_score": _num(m.read_score),
        "evidence_score": _num(m.evidence_score),
        "trust_bonus": _num(m.trust_bonus),
        "low_fans_bonus": _num(m.low_fans_bonus),
        "total": _num(m.total),
        "breakdown": m.breakdown or {},
    }


def product_to_dict(p: Product, images: list[ProductImage] | None = None) -> dict[str, Any]:
    return {
        "id": p.id,
        "xhs_id": p.xhs_id,
        "account_id": p.account_id,
        "direction_id": p.direction_id,
        "title": p.title,
        "price_cents": p.price_cents,
        "sales": p.sales,
        "spec": p.spec,
        "desc": p.desc,
        "share_link": p.share_link,
        "form": p.form,
        "role": p.role,
        "status": p.status,
        "images": [image_to_dict(i) for i in images] if images else [],
    }


def image_to_dict(i: ProductImage) -> dict[str, Any]:
    return {"id": i.id, "product_id": i.product_id, "url": i.url, "local_path": i.local_path, "seq": i.seq}


def note_image_to_dict(i: NoteImage) -> dict[str, Any]:
    return {"id": i.id, "note_id": i.note_id, "url": i.url, "local_path": i.local_path, "seq": i.seq}


def direction_to_dict(d: Direction) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "category": d.category,
        "form": d.form,
        "status": d.status,
        "evidence": d.evidence,
        "picked_product_id": d.picked_product_id,
    }


def source_to_dict(s: RankingSource) -> dict[str, Any]:
    return {
        "id": s.id,
        "key": s.key,
        "name": s.name,
        "page_max": s.page_max,
        "delay_scope": s.delay_scope,
        "enabled": s.enabled,
    }


def keyword_to_dict(k: Keyword) -> dict[str, Any]:
    return {
        "id": k.id,
        "product_id": k.product_id,
        "word": k.word,
        "is_core": k.is_core,
        "a_to_z": k.a_to_z,
        "collect_comments": k.collect_comments,
        "pages_target": k.pages_target,
        "collected_count": k.collected_count,
    }


def note_to_dict(n: Note) -> dict[str, Any]:
    return {
        "id": n.id,
        "note_id": n.note_id,
        "product_id": n.product_id,
        "keyword_id": n.keyword_id,
        "title": n.title,
        "body": n.body,
        "topics": n.topics or [],
        "author": n.author,
        "interactions": n.interactions or {},
        "media_type": n.media_type,
        "a_to_z_group": n.a_to_z_group,
        "analyzed": n.analyzed,
        "collected_at": _dt(n.collected_at),
    }


def analysis_to_dict(a: NoteAnalysis) -> dict[str, Any]:
    return {
        "id": a.id,
        "note_id": a.note_id,
        "title_formula": a.title_formula,
        "structure": a.structure,
        "hook_type": a.hook_type,
        "cover_rule": a.cover_rule,
        "interaction_feature": a.interaction_feature,
        "detail": a.detail or {},
        "analyzed_at": _dt(a.analyzed_at),
    }


def template_to_dict(t: Template) -> dict[str, Any]:
    return {
        "id": t.id,
        "product_id": t.product_id,
        "cluster_key": t.cluster_key,
        "supported_count": t.supported_count,
        "draft_md": t.draft_md,
        "status": t.status,
        "note_ids": t.note_ids or [],
    }


def skill_to_dict(s: Skill) -> dict[str, Any]:
    return {
        "id": s.id,
        "product_id": s.product_id,
        "name": s.name,
        "md": s.md,
        "files_whitelist": s.files_whitelist or [],
        "rules": s.rules or {},
        "status": s.status,
        "review_policy": s.review_policy,
        "current_version": s.current_version,
    }


def package_to_dict(c: ContentPackage) -> dict[str, Any]:
    return {
        "id": c.id,
        "skill_id": c.skill_id,
        "seq": c.seq,
        "title": c.title,
        "body": c.body,
        "topics": c.topics or [],
        "images": c.images or [],
        "status": c.status,
        "rounds": c.rounds,
    }


def material_to_dict(m: Material) -> dict[str, Any]:
    return {
        "id": m.id,
        "product_id": m.product_id,
        "filename": m.filename,
        "mime": m.mime,
        "local_path": m.local_path,
        "size_bytes": m.size_bytes,
        "parsed_text": m.parsed_text,
        "ingest_status": m.ingest_status,
    }


def design_to_dict(d: DesignDoc) -> dict[str, Any]:
    return {
        "id": d.id,
        "product_id": d.product_id,
        "stage": d.stage,
        "page_list": d.page_list or [],
        "proto_images": d.proto_images or [],
        "repo_url": d.repo_url,
        "build_path": d.build_path,
        "accept_report": d.accept_report or {},
    }


def agent_def_to_dict(a: AgentDef) -> dict[str, Any]:
    return {
        "id": a.id,
        "key": a.key,
        "name": a.name,
        "system_prompt": a.system_prompt,
        "tool_keys": a.tool_keys or [],
        "model": a.model,
        "temperature": _num(a.temperature),
        "timeout_seconds": a.timeout_seconds,
        "is_enabled": a.is_enabled,
    }


def risk_to_dict(r: RiskConfig) -> dict[str, Any]:
    return {
        "id": r.id,
        "scope": r.scope,
        "min_delay_s": r.min_delay_s,
        "max_delay_s": r.max_delay_s,
        "retry_max": r.retry_max,
        "backoff_exp": r.backoff_exp,
        "enabled": r.enabled,
    }


# ---------- 工作台 ----------


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict:
    """与 frontend types.api.DashboardSummary 对齐。"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    accounts_today = db.scalar(
        select(func.count()).select_from(Account).where(Account.created_at >= today_start)
    ) or 0
    products_today = db.scalar(
        select(func.count()).select_from(Product).where(Product.created_at >= today_start)
    ) or 0

    directions: list[dict[str, Any]] = []
    rows = db.scalars(select(Direction).order_by(Direction.id)).all()
    for d in rows:
        accounts = db.scalar(
            select(func.count()).select_from(DirectionAccount).where(DirectionAccount.direction_id == d.id)
        ) or 0
        directions.append(
            {
                "id": d.id,
                "name": d.name,
                "status": d.status,
                "accounts": accounts,
                "price_range": None,  # 由 direction_accounts 汇总，暂不展示
                "max_sales": None,
            }
        )

    runs, _ = list_runs(db, page=1, page_size=6)
    return {
        "data": {
            "date": _dt(datetime.now(timezone.utc)),
            "accounts_today": accounts_today,
            "products_today": products_today,
            "directions": directions,
            "recent_runs": runs,
        }
    }


# ---------- 需求发现 ----------


@router.get("/ranking-sources")
def ranking_sources(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(RankingSource).order_by(RankingSource.id)).all()
    return {"data": [source_to_dict(s) for s in rows]}


@router.get("/accounts")
def list_accounts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Account)
    rows, total = _paged(db, Account, stmt, page, page_size)
    return {"data": [account_to_dict(a) for a in rows], "meta": {"total": total, "page": page, "page_size": page_size}}


@router.get("/accounts/{account_id}")
def account_detail(account_id: int, db: Session = Depends(get_db)) -> dict:
    a = db.get(Account, account_id)
    if a is None:
        return {"data": None}
    m = db.scalar(select(AccountMetric).where(AccountMetric.account_id == account_id))
    return {"data": account_to_dict(a, m)}


@router.get("/products")
def list_products(
    account_id: int | None = None,
    role: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Product)
    if account_id is not None:
        stmt = stmt.where(Product.account_id == account_id)
    if role:
        stmt = stmt.where(Product.role == role)
    rows, total = _paged(db, Product, stmt, page, page_size)
    return {"data": [product_to_dict(p) for p in rows], "meta": {"total": total, "page": page, "page_size": page_size}}


@router.get("/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    p = db.get(Product, product_id)
    if p is None:
        return {"data": None}
    images = db.scalars(select(ProductImage).where(ProductImage.product_id == product_id)).all()
    return {"data": product_to_dict(p, list(images))}


@router.get("/products/{product_id}/images")
def product_images(product_id: int, db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(ProductImage).where(ProductImage.product_id == product_id)).all()
    return {"data": [image_to_dict(i) for i in rows]}


@router.get("/products/{product_id}/materials")
def product_materials(product_id: int, db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Material).where(Material.product_id == product_id)).all()
    return {"data": [material_to_dict(m) for m in rows]}


@router.get("/products/{product_id}/design")
def product_design(product_id: int, db: Session = Depends(get_db)) -> dict:
    d = db.scalar(select(DesignDoc).where(DesignDoc.product_id == product_id))
    return {"data": design_to_dict(d) if d else {}}


@router.get("/directions")
def list_directions(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Direction).order_by(Direction.id)).all()
    return {"data": [direction_to_dict(d) for d in rows]}


# ---------- 内容获客 ----------


@router.get("/keywords")
def list_keywords(product_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    stmt = select(Keyword)
    if product_id is not None:
        stmt = stmt.where(Keyword.product_id == product_id)
    rows = db.scalars(stmt.order_by(Keyword.id)).all()
    return {"data": [keyword_to_dict(k) for k in rows]}


@router.get("/notes")
def list_notes(
    product_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Note)
    if product_id is not None:
        stmt = stmt.where(Note.product_id == product_id)
    rows, total = _paged(db, Note, stmt, page, page_size)
    return {"data": [note_to_dict(n) for n in rows], "meta": {"total": total, "page": page, "page_size": page_size}}


@router.get("/notes/{note_id}")
def note_detail(note_id: int, db: Session = Depends(get_db)) -> dict:
    n = db.get(Note, note_id)
    if n is None:
        return {"data": None}
    images = db.scalars(select(NoteImage).where(NoteImage.note_id == note_id)).all()
    return {"data": {**note_to_dict(n), "images": [note_image_to_dict(i) for i in images]}}


@router.get("/notes/{note_id}/analysis")
def note_analysis(note_id: int, db: Session = Depends(get_db)) -> dict:
    a = db.scalar(select(NoteAnalysis).where(NoteAnalysis.note_id == note_id))
    return {"data": analysis_to_dict(a) if a else {}}


@router.get("/templates")
def list_templates(product_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    stmt = select(Template)
    if product_id is not None:
        stmt = stmt.where(Template.product_id == product_id)
    rows = db.scalars(stmt.order_by(Template.id)).all()
    return {"data": [template_to_dict(t) for t in rows]}


@router.get("/skills")
def list_skills(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Skill).order_by(Skill.id)).all()
    return {"data": [skill_to_dict(s) for s in rows]}


@router.get("/skills/{skill_id}")
def skill_detail(skill_id: int, db: Session = Depends(get_db)) -> dict:
    s = db.get(Skill, skill_id)
    return {"data": skill_to_dict(s) if s else None}


@router.get("/contents")
def list_contents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(ContentPackage)
    rows, total = _paged(db, ContentPackage, stmt, page, page_size)
    return {"data": [package_to_dict(c) for c in rows], "meta": {"total": total, "page": page, "page_size": page_size}}


# ---------- 设置 ----------


@router.get("/agent-defs")
def agent_defs(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(AgentDef).order_by(AgentDef.id)).all()
    return {"data": [agent_def_to_dict(a) for a in rows]}


@router.get("/risk-config")
def risk_config(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(RiskConfig).order_by(RiskConfig.id)).all()
    return {"data": [risk_to_dict(r) for r in rows]}