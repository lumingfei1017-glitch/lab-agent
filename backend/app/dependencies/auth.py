from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """jwt token鉴权"""
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效"
        )
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在"
        )
    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="账号异常，请联系管理员"
        )
    return user
