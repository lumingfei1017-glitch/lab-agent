import shutil

from fastapi import APIRouter, Depends, File, UploadFile
from app.common.response import Response
from app.common.exceptions import BusinessException
from app.dependencies.auth import get_current_user
from app.models.user import User
from pathlib import Path
import os, time
import uuid
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR
from app.schemas.file import FileResponse

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.post("/upload")
def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """文件上传接口"""
    if not file.filename:
        raise BusinessException(message="文件名不能为空")

    # 原始文件名
    original_name = os.path.basename(file.filename)

    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(message=f"不支持的文件后缀:{ext}")

    if file.size and file.size > MAX_FILE_SIZE:
        raise BusinessException(message=f"文件不能超过{MAX_FILE_SIZE//1024//1024}MB")

    # 设置文件唯一名称
    disk_name = f"{int(time.time() *1000 )}_{uuid.uuid4().hex[:8]}{ext}"

    # 文件存储路径
    save_path = UPLOAD_DIR / disk_name

    # 流式写入
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return Response.success(
        data=FileResponse(
            original_name=original_name,
            disk_name=disk_name,
            size=file.size,
            url=f"/uploads/{disk_name}",
        )
    )
