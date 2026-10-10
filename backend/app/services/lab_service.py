from sqlalchemy.orm import Session

from app.common.exceptions import BuinessException
from app.common.response import PageResponse
from app.models.lab import Lab
from sqlalchemy import exists, or_

from app.schemas.lab import LabCreateResquest, LabResponse, LabUpdateResquest


def get_lab_page_list(db: Session, page: int, page_size: int, keywords: str | None):
    query = db.query(Lab)
    if keywords:
        query = query.filter(
            or_(Lab.name.ilike(f"%{keywords}"), Lab.location.ilike(f"%{keywords}"))
        )
    total = query.count()
    items = (
        query.order_by(Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[LabResponse.model_validate(item) for item in items], total=total
    )


def create_lab(db: Session, data: LabCreateResquest):
    exists = db.query(Lab).filter(Lab.name == data.name).first()
    if exists:
        raise BuinessException(message="实验室名称已经存在")

    lab = Lab(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(db: Session, lab_id: int, data: LabUpdateResquest):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BuinessException(message="实验室不存在")

    payload = data.model_dump(exclude_none=True)  # 更好的写法exclude_unset = True
    if "name" in payload:
        exists = (
            db.query(Lab).filter(Lab.name == payload["name"], Lab.id != lab_id).first()
        )
        if exists:
            raise BuinessException(message="实验室名称已经存在")

    for field, value in payload.items():
        setattr(lab, field, value)

    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(db: Session, lab_id: int):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BuinessException(message="实验室不存在")
    db.delete(lab)
    db.commit()
