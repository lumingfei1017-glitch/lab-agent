from datetime import datetime
import json

from langchain_core.tools import tool

import logging

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest
from app.services import equipment_service, kb_service, lab_service, reservation_service

logger = logging.getLogger(__name__)


def build_tools(db: Session, current_user: User):

    # 本次 Agent 生命周期内的缓存
    searched_queries = set()
    call_counter = {"count": 0}
    MAX_TOOL_CALLS = 8  # 一轮对话最多调 8 次工具

    def too_many_calls() -> bool:
        call_counter["count"] += 1
        return call_counter["count"] > MAX_TOOL_CALLS

    @tool
    def search_lab_docs(query: str) -> str:
        """根据用户提问检索知识库（同一问题只查一次）"""
        if too_many_calls():
            return "已达工具调用上限，请立即基于已有信息生成最终回答。"

        query_key = (query or "").strip().lower()
        if not query_key:
            return "查询关键词为空，请基于已有信息回答。"

        if query_key in searched_queries:
            return "该问题已检索过，请直接基于前面的检索结果回答，不要重复调用。"

        searched_queries.add(query_key)

        try:
            return kb_service.search(query) or "没有检索到相关资料"
        except Exception as exc:
            logger.exception("search_lab_docs 执行失败")
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_open_labs(keywords: str = "") -> str:
        """查询开放的实验室列表"""
        if too_many_calls():
            return "已达工具调用上限，请立即生成最终回答。"

        try:
            keywords = keywords.strip() or None
            page = lab_service.get_lab_page_list(
                db, page=1, page_size=10, keywords=keywords, status=1
            )
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "location": item.location,
                    "capacity": item.capacity,
                    "open_time": item.open_time,
                    "close_time": item.close_time,
                }
                for item in page.list
            ]
            return json.dumps({"total": page.total, "labs": rows}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("list_open_labs 失败")
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_lab_equipments(lab_id: int, keywords: str = "") -> str:
        """查询某个实验室的设备列表"""

        if too_many_calls():
            return "已达工具调用上限，请立即生成最终回答。"

        try:
            keywords = keywords.strip()
            page = equipment_service.get_equipment_page_list(
                db, page=1, page_size=10, keywords=keywords, lab_id=lab_id
            )

            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "lab_id": item.lab_id,
                    "lab_name": item.lab_name,
                    "spec": item.spec,
                    "quantity": item.quantity,
                    "status": item.status,
                }
                for item in page.list
            ]
            return json.dumps(
                {"total": page.total, "equipment": rows}, ensure_ascii=False
            )
        except Exception as exc:
            logger.exception("list_lab_equipments 失败")
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def create_lab_reservation(
        lab_id: int,
        date: str,
        start_time: str,
        end_time: str,
        equipment_id: int | None = None,
        remark: str | None = None,
    ) -> str:
        """创建预约单预约实验室或设备"""
        if too_many_calls():
            return "已达工具调用上限，请立即生成最终回答。"
        try:
            data = ReservationCreateRequest(
                lab_id=lab_id,
                equipment_id=equipment_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                remark=remark,
            )
            reservation_service.create_reservation(db, current_user, data)
            return json.dumps(
                {
                    "ok": True,
                    "message": "预约已经提交，请等待管理员审核",
                    "lab_id": lab_id,
                    "equipment_id": equipment_id,
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time,
                },
                ensure_ascii=False,
            )
        except BusinessException as exc:
            logger.exception("create_lab_reservation 失败")
            return json.dumps({"ok": False, "error": exc.message}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("create_lab_reservation 失败")
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def get_today() -> str:
        """获取服务器当前的日期 xxxx-xx-xx:2026-01-01"""
        now = datetime.now()
        return now.strftime("%Y-%m-%d")

    return [
        search_lab_docs,
        list_open_labs,
        list_lab_equipments,
        create_lab_reservation,
        get_today,
    ]
