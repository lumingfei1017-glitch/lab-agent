import token
from tokenize import Decnumber
from app.services import user_service
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import services
from app.common.response import Response
from app.dependencies.auth import get_current_user
from app.schemas.auth import LoginRequest
from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordUpdateRequest, UserResponse, UserUpdateRequest
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
def update_user_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户当前信息"""
    res = user_service.update_user_info(db, current_user, data)
    return Response.success(data=res)


@router.put("/password")
def update_user_info(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户当前信息"""
    res = user_service.update_password(db, current_user, data)
    return Response.success()
