from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.config import UPLOAD_DIR
from app.models.user import User
from app.database import Base, engine
from app.api import api
from app.common.exceptions import (
    BuinessException,
    http_excpetion_hadler,
    bussioness_excpetion_hadler,
    global_excpetion_hadler,
    validation_excpetion_hadler,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

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
app.add_exception_handler(BuinessException, bussioness_excpetion_hadler)
app.add_exception_handler(HTTPException, http_excpetion_hadler)
app.add_exception_handler(RequestValidationError, validation_excpetion_hadler)
# 全局异常兜底，需放在最后注册
app.add_exception_handler(Exception, global_excpetion_hadler)

# 挂载静态文件访问路径
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行"}
