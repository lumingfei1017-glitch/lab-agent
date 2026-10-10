import token
from tokenize import Decnumber
from app.services import user_service
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import services
from app.common.response import Response
from app.dependencies.auth import get_current_admin, get_current_user
from app.schemas.auth import LoginRequest
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    PasswordUpdateRequest,
    UserCreateResquest,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.password import verify_password
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/user", tags=["用户信息"])


@router.get("/me")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户登录信息"""
    return Response.success(data=user_service.get_user_info(current_user))


# {
#         "code": 200,
#         "message": "请求成功",
#         "data": UserResponse.model_validate(current_user),
#     }


@router.put("/me")
def update_me_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户当前信息"""
    res = user_service.update_user_info(db, current_user, data)
    return Response.success(data=res)


@router.put("/password")
def update_user_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户当前信息"""
    res = user_service.update_password(db, current_user, data)
    return Response.success()


@router.get("/page")
def get_user_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.get_user_page_list(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post("")
def create_user(
    data: UserCreateResquest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.create_user(db, data)
    return Response.success(data=res)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.updata_user(db, user_id, data)
    return Response.success(data=res)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.delete_user(db, user_id, current_user)
    return Response.success()
