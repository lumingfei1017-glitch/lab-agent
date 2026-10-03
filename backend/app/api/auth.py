from email import message
import token

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common.exceptions import BuinessException
from app.common.response import Response
from app.schemas.auth import LoginRequest, LoginResponse
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.password import verify_password
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["权限验证"])


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password):
        raise BuinessException(message="账号或密码错误")

    if not user.status:
        raise BuinessException(message="账号异常请联系管理员")

    token = create_access_token(user_id=user.id)

    return Response.success(
        message="登录成功",
        data=LoginResponse(
            token=token, user=UserResponse.model_validate(user).model_dump()
        ),
    )
