import token

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.schemas.auth import LoginRequest
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.password import verify_password
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/user", tags=["用户信息"])


@router.get("/info")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户登录信息"""
    return {
        "code": 200,
        "message": "请求成功",
        "data": UserResponse.model_validate(current_user),
    }
