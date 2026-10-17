from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.database import SessionLocal
from app.models.Reservation import Reservation
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest, ReservationResponse
import asyncio


def get_reservation_page_list(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status: int | None = None,
):
    """查询预约记录"""
    query = db.query(Reservation)
    if current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)

    if status is not None:
        query = query.filter(Reservation.status == status)

    total = query.count()

    # items = (
    #     query.order_by(Reservation.id.desc())
    #     .offset((page - 1) * page_size)
    #     .limit(page_size)
    #     .all()
    # )

    # sql优化
    items = (
        query.options(
            joinedload(Reservation.user),
            joinedload(Reservation.lab),
            joinedload(Reservation.equipment),
        )
        .order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for item in items:
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id else "实验室"
        result.append(res)

    return PageResponse(list=result, total=total)


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    """学生预约取消"""
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if not item:
        raise BusinessException(message="不存在的预约记录")

    if current_user.id != item.user_id:
        raise BusinessException(message="无权限", code=403)

    if item.status != 0:
        raise BusinessException(message="当前状态无法取消")

    item.status = 3
    db.commit()


def audit_reservation(db: Session, reservation_id: int, status: int):
    """管理员审核"""
    if status not in [1, 2]:
        raise BusinessException(message="错误的审核状态")
    item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not item:
        raise BusinessException(message="预约记录不存在")

    if item.status != 0:
        raise BusinessException(message="当前状态不可审核")

    item.status = status
    db.commit()


def create_reservation(db: Session, user_id: int, data: ReservationCreateRequest):
    """创建预约记录（user_id 传纯 int，Agent 工具线程并发时不共享 ORM 对象）"""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    if data.date < current_date:
        raise BusinessException(message="预约日期不能小于当前日期")

    if data.end_time < data.start_time:
        raise BusinessException(message="预约结束时间不能小于开始时间")

    if data.date == current_date and data.start_time < current_time:
        raise BusinessException(message="预约开始时间不能小于当前时间")

    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()

    if not lab:
        raise BusinessException(message="预约实验室不存在")

    if not lab.status:
        raise BusinessException(message="实验室暂时不可用")

    if data.start_time < lab.open_time or data.end_time > lab.close_time:
        raise BusinessException(message="预约时间段不可用")

    if data.equipment_id:
        equipment = (
            db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        )

        if not equipment:
            raise BusinessException(message="实验设备不存在")
        if not equipment.status:
            raise BusinessException(message="实验设备不可用")
        if equipment.lab_id != data.lab_id:
            raise BusinessException(message="该设备不属于所选实验室")

        # 设备按台数并发占用：同一时段被占用的有效预约数不能超过设备总数
        capacity = equipment.quantity or 1
        booked = (
            db.query(func.count(Reservation.id))
            .filter(
                Reservation.equipment_id == data.equipment_id,
                Reservation.date == data.date,
                Reservation.status.in_([0, 1]),
                Reservation.start_time < data.end_time,
                Reservation.end_time > data.start_time,
            )
            .scalar()
        )
        if booked >= capacity:
            raise BusinessException(
                message=f"该设备此时段 {capacity} 台已全部被预约，请选择其他时间或设备"
            )
    else:
        # 预约整个实验室：同一时段只允许一条有效记录
        conflict = (
            db.query(Reservation.id)
            .filter(
                Reservation.lab_id == data.lab_id,
                Reservation.date == data.date,
                Reservation.equipment_id.is_(None),
                Reservation.status.in_([0, 1]),
                Reservation.start_time < data.end_time,
                Reservation.end_time > data.start_time,
            )
            .first()
        )
        if conflict:
            raise BusinessException(message="该时段实验室已被预约")

    reservation_model = Reservation(
        user_id=user_id,
        lab_id=data.lab_id,
        equipment_id=data.equipment_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        remark=data.remark,
        status=0,
    )

    db.add(reservation_model)
    db.commit()


def expire_pending_reservations():
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        now_time = now.strftime("%H:%M")
        items = db.query(Reservation).filter(Reservation.status == 0).all()
        changed = False
        for item in items:
            if item.date < today or (item.date == today and item.end_time <= now_time):
                item.status = 3
                changed = True

        if changed:
            db.commit()

    finally:
        db.close()


async def run_expire_scan():
    while True:
        expire_pending_reservations()
        await asyncio.sleep(60)
