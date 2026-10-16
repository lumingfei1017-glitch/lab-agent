from contextlib import asynccontextmanager

from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import logging
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.config import UPLOAD_DIR
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.Reservation import Reservation
from app.database import Base, engine
from app.api import api
from app.common.exceptions import (
    BusinessException,
    http_exception_handler,
    business_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)
from app.services import kb_service, reservation_service
import asyncio

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(kb_service.warmup)
    except Exception:
        logger.exception("向量数据库预热失败")

    task = asyncio.create_task(reservation_service.run_expire_scan())

    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)

app.include_router(api)

# 注册自定义异常
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# 全局异常兜底，需放在最后注册
app.add_exception_handler(Exception, global_exception_handler)

# 挂载静态文件访问路径
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行"}
