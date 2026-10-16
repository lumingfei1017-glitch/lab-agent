# 智能实验室预约系统（lab-agent）

一个前后端分离的实验室预约管理系统，在传统 CRUD 之上接入了 **LangGraph Agent + RAG 知识库**：学生可以用自然语言查询实验室规则、开放实验室与设备，并在复述确认后由 Agent 直接落库提交预约。

- **后端**：FastAPI + SQLAlchemy 2 + MySQL + JWT，Agent 侧为 LangGraph / LangChain + ChromaDB
- **前端**：Vue 3 + Vite + Element Plus + Axios，对话页使用 SSE 流式渲染

---

## 目录结构

```text
lab-agent/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 入口：CORS、异常处理器、静态挂载、lifespan 启动任务
│   │   ├── config.py             # pydantic-settings 读取 .env + 上传目录/白名单常量
│   │   ├── database.py           # engine / SessionLocal / Base（id、create_time、update_time）
│   │   ├── api/                  # 路由层（统一前缀 /api）
│   │   │   ├── auth.py           #   登录、注册
│   │   │   ├── user.py           #   个人信息、改密、用户管理
│   │   │   ├── lab.py            #   实验室增删改查
│   │   │   ├── equipment.py      #   设备增删改查
│   │   │   ├── reservation.py    #   预约创建、列表、取消、审核
│   │   │   ├── files.py          #   文件上传
│   │   │   └── ai.py             #   /ai/chat 与 /ai/chat/stream（SSE）
│   │   ├── services/             # 业务逻辑层
│   │   │   ├── agent_service.py  #   LangGraph 图构建、invoke / astream_events
│   │   │   ├── agent_tools.py    #   Agent 的 5 个 tool（闭包注入 db + current_user）
│   │   │   ├── kb_service.py     #   Chroma 向量库：预热、懒加载 embedding、检索
│   │   │   ├── ai_service.py     #   早期 OpenAI SDK 直连实现（保留备用）
│   │   │   └── *_service.py      #   auth / user / lab / equipment / reservation
│   │   ├── models/               # SQLAlchemy 表模型：users / labs / equipments / reservations
│   │   ├── schemas/              # Pydantic 请求与响应模型
│   │   ├── dependencies/auth.py  # get_current_user（JWT）、get_current_admin（角色）
│   │   ├── common/               # 统一响应体 Response / PageResponse、业务异常
│   │   └── utils/                # jwt 签发解析、bcrypt 密码哈希
│   ├── data/
│   │   ├── kb/*.md               # 知识库原文（预约规则、开放时间、安全规范、设备使用）
│   │   └── chroma/               # Chroma 持久化目录（集合 lab_kb，首次运行自动写入）
│   ├── uploads/                  # 上传文件落盘目录，通过 /uploads 静态访问
│   ├── requirements.txt
│   └── .env                      # 本地配置（不入库，见下文「环境配置」）
└── frontend/
    ├── src/
    │   ├── router/index.js       # 路由 + token 守卫
    │   ├── layouts/Layout.vue    # 侧边栏菜单（按 role 区分管理员/学生入口）
    │   ├── views/                # Home / LabList / Lab / Equipment / LabEquipment /
    │   │                         # MyReservation / AuditReservation / User / Profile /
    │   │                         # Password / Login / Register / AIChat
    │   ├── api/                  # 按模块封装的接口调用
    │   └── utils/                # request.js（axios 拦截器）、auth.js（token）、user.js
    └── vite.config.js            # /api、/uploads 代理到 127.0.0.1:8000
```

---

## 功能模块

### 用户与权限

- 注册默认 `role = student`、`status = 1`；管理员由管理员在「用户管理」中创建/调整。
- 密码使用 bcrypt 哈希存储，登录成功签发 JWT（`user_id` + `exp`，有效期 `JWT_EXPIRE_HOURS`）。
- 请求经 `Authorization: Bearer <token>` 鉴权；写操作与用户管理接口要求 `role == "admin"`。
- 被禁用（`status = 0`）的账号既不能登录，已有 token 也会被拒绝。

| 角色   | 可见菜单                                                            |
| ------ | ------------------------------------------------------------------- |
| 学生   | 系统首页、实验室列表、我的预约、AI 智能助手                         |
| 管理员 | 系统首页、实验室管理、设备列表管理、用户管理、预约审核、AI 智能助手 |

### 实验室与设备

- 实验室：名称唯一，含位置、容纳人数、开放时段（`open_time` / `close_time`）、简介、封面图、开放状态。
- 设备：归属于某个实验室，同一实验室内名称唯一，含型号规格、数量、状态。
- 列表接口支持分页 + 关键字模糊搜索（实验室匹配名称/位置，设备匹配名称，可按 `lab_id` 过滤）。

### 预约

`reservations` 表用 `equipment_id` 是否为空区分**预约实验室**与**预约设备**；状态机：

```text
0 待审核 ──管理员通过──> 1 已通过
   │  ──管理员拒绝──> 2 已拒绝
   └── 用户取消 / 时段过期 ──> 3 已取消
```

创建时的校验：日期不得早于今天、结束时间不得早于开始时间、当天开始时间不得早于当前时间、实验室必须开放且时段落在其开放时间内、设备必须存在且状态正常且确实属于所选实验室。

冲突判定分两种情况：

- **预约实验室**（`equipment_id` 为空）：同一实验室同一天的有效预约（状态 `0/1`）时段不得重叠，整间实验室同一时刻只允许一条记录。
- **预约设备**：按设备 `quantity` 做**并发台数校验**——同一设备同一时段的重叠有效预约数达到 `quantity` 时拒绝，并提示「已全部被预约」。占用数是实时从 `reservations` 聚合算出的，不在 `equipments` 表上冗余存储，因此不会出现字段漂移，也不需要数据迁移。

列表接口对管理员返回全部记录、对学生只返回本人记录，并用 `joinedload` 一次性带出用户/实验室/设备名。

后台任务 `run_expire_scan()` 在应用启动时拉起，每 60 秒把已过结束时间的待审核预约自动置为已取消。

### 文件上传

`POST /api/files/upload`（需登录），单文件上限 100MB，后缀白名单：
`.jpg .jpeg .png .gif .webp .pdf .doc .docx .xls .xlsx .zip`。
落盘为重命名后的 `毫秒时间戳_uuid8位.ext`，返回 `/uploads/<disk_name>` 相对 URL，由 FastAPI `StaticFiles` 挂载对外访问（头像、实验室封面、设备图片走这里）。

### AI 智能助手（Agent + RAG）

Agent 用 LangGraph 搭了一个最小的 agent ⇄ tools 循环图，工具通过闭包绑定当前请求的 `db` 会话与登录用户，因此**工具调用天然带上用户身份和权限**：

| 工具                     | 作用                                                                         |
| ------------------------ | ---------------------------------------------------------------------------- |
| `search_lab_docs`        | 在 Chroma 知识库中语义检索规则/安全/开放时间等资料（同一问题去重，只查一次） |
| `list_open_labs`         | 查询真实存在且状态为开放的实验室                                             |
| `list_lab_equipments`    | 查询指定实验室的设备                                                         |
| `create_lab_reservation` | 真实落库创建预约（提交后进入待审核）                                         |
| `get_today`              | 返回服务器当前日期，用于「明天/后天」这类相对时间换算                        |

防护与约束：单轮对话最多 8 次工具调用（超限直接要求模型基于已有信息作答），`recursion_limit` 限制图循环次数，工具异常被捕获后以 JSON 返回给模型而不是抛出 500。系统提示词强制要求：**提交预约前必须复述实验室/设备、日期、起止时间并取得用户明确「确认」**，缺 `lab_id`/`equipment_id` 时先查再建，不允许编造库中不存在的数据。

RAG 侧：`SentenceTransformerEmbeddingFunction("BAAI/bge-small-zh-v1.5")` + `chromadb.PersistentClient`，集合 `lab_kb` 首次启动时从 `backend/data/kb/*.md` 按文件灌入；检索结果按 `1/(1+distance)` 归一化打分，低于阈值丢弃、最多保留 2 段拼进提示词。embedding 模型用双重检查锁懒加载，并在 `lifespan` 中通过 `asyncio.to_thread(kb_service.warmup)` 预热，避免首请求承担模型加载耗时。

---

## API 一览

所有接口前缀 `/api`，统一响应体 `{ code, message, data }`（`code == 200` 为成功），分页数据为 `{ list, total }`。

| 方法                | 路径                            | 权限   | 说明                                   |
| ------------------- | ------------------------------- | ------ | -------------------------------------- |
| POST                | `/auth/login`                   | 公开   | 登录，返回 token + 用户信息            |
| POST                | `/auth/register`                | 公开   | 注册（固定为学生）                     |
| GET                 | `/user/me`                      | 登录   | 当前用户信息                           |
| PUT                 | `/user/me`                      | 登录   | 修改个人信息                           |
| PUT                 | `/user/password`                | 登录   | 修改密码                               |
| GET                 | `/user/page`                    | 管理员 | 用户分页列表                           |
| POST / PUT / DELETE | `/user`、`/user/{id}`           | 管理员 | 新增 / 修改 / 删除用户                 |
| GET                 | `/lab/list`                     | 登录   | 实验室分页列表（`keywords`、`status`） |
| GET                 | `/lab/{id}`                     | 登录   | 实验室详情                             |
| POST / PUT / DELETE | `/lab`、`/lab/{id}`             | 管理员 | 新增 / 修改 / 删除实验室               |
| GET                 | `/equipment/list`               | 登录   | 设备分页列表（`keywords`、`lab_id`）   |
| POST / PUT / DELETE | `/equipment`、`/equipment/{id}` | 管理员 | 新增 / 修改 / 删除设备                 |
| POST                | `/reservation`                  | 登录   | 创建预约                               |
| GET                 | `/reservation/list`             | 登录   | 预约列表（管理员见全部，学生见本人）   |
| PUT                 | `/reservation/{id}/cancel`      | 登录   | 取消自己的待审核预约                   |
| PUT                 | `/reservation/{id}/audit`       | 管理员 | 审核通过 / 拒绝                        |
| POST                | `/files/upload`                 | 登录   | 文件上传                               |
| POST                | `/ai/chat`                      | 登录   | Agent 对话（一次性返回完整回答）       |
| POST                | `/ai/chat/stream`               | 登录   | Agent 对话（SSE 流式）                 |

### SSE 事件格式

`POST /api/ai/chat/stream` 返回 `text/event-stream`，每帧形如 `data:{"type": "..."}\n\n`：

| `type`       | 附带字段                   | 含义                                |
| ------------ | -------------------------- | ----------------------------------- |
| `status`     | `message`                  | 阶段提示（如「正在思考」）          |
| `tool_start` | `name`、`label`            | 开始调用某个工具                    |
| `tool_end`   | `name`、`label`、`preview` | 工具返回，`preview` 截断到 200 字符 |
| `token`      | `content`                  | 模型输出的增量文本（打字机效果）    |
| `done`       | —                          | 本轮结束                            |
| `error`      | `message`                  | 业务异常或模型调用失败              |

前端 `frontend/src/api/ai.js` 用 `fetch` + `ReadableStream` 手动解析（而非 `EventSource`，因为需要携带 JWT），`AIChat.vue` 把 `token` 增量拼进正文、把 `tool_start/tool_end` 渲染成过程流水，正文经 `marked` 转 HTML 后用 `DOMPurify.sanitize` 过滤。

---

## 环境与依赖

| 层      | 版本要求                                                                                        |
| ------- | ----------------------------------------------------------------------------------------------- |
| Python  | 3.12                                                                                            |
| Node.js | `^22.18.0 \|\| >=24.12.0`                                                                       |
| MySQL   | 5.7+ / 8.x，需 `utf8mb4`                                                                        |
| 其他    | Git；首次运行知识库灌库与 embedding 推理需要下载 `BAAI/bge-small-zh-v1.5`（离线环境请预先缓存） |

后端主要依赖（`backend/requirements.txt`）：`fastapi` `uvicorn` `sqlalchemy` `pymysql` `pydantic-settings` `bcrypt` `PyJWT` `chromadb` `langgraph` `langchain-openai` `langchain-core`。

> 代码还用到但**未列在 requirements.txt 中**的包：`openai`（`ai_service.py`）、`python-multipart`（`UploadFile` 表单解析）、`sentence-transformers`（Chroma 的 embedding 函数）。当前环境已随其他包间接安装，全新环境建议显式补上，否则会分别在对话、上传、知识库初始化时报错。

---

## 快速开始

### 1. 准备数据库

```sql
CREATE DATABASE lab_agent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

表结构由 `Base.metadata.create_all(bind=engine)` 在应用启动时自动创建（仅建表，不会自动变更已存在的表结构）。

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows；Linux/macOS 用 source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # 然后按下表填写真实配置
uvicorn app.main:app --reload     # http://127.0.0.1:8000
```

VS Code 已配置 `Python Debugger: FastAPI` 调试项（`.vscode/launch.json`），可直接 F5 断点调试。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

`vite.config.js` 已把 `/api` 与 `/uploads` 代理到 `http://127.0.0.1:8000`，开发态无需额外配置跨域；`/api` 代理对流式响应关闭了缓冲，保证 SSE 事件实时到达浏览器。

### 4. 初始化管理员

注册接口只能创建学生账号。先注册一个学生，再在数据库里把该用户改为管理员：

```sql
UPDATE users SET role = 'admin' WHERE username = '你的账号';
```

之后即可在「用户管理」中创建其他管理员账号。

---

## 环境配置（`backend/.env`）

| 变量               | 示例                                                 | 说明                                                |
| ------------------ | ---------------------------------------------------- | --------------------------------------------------- |
| `DATABASE_URL`     | `mysql+pymysql://root:密码@127.0.0.1:3306/lab_agent` | SQLAlchemy 连接串                                   |
| `JWT_SECRET_KEY`   | 随机字符串                                           | 生产环境务必更换，建议 32 字节以上随机值            |
| `JWT_EXPIRE_HOURS` | `24`                                                 | token 有效期（小时）                                |
| `JWT_ALGORITHM`    | `HS256`                                              | 签名算法                                            |
| `LLM_API_KEY`      | `sk-...`                                             | 大模型服务密钥                                      |
| `LLM_BASE_URL`     | `https://.../v1`                                     | OpenAI 兼容接口地址                                 |
| `LLM_MODEL`        | 模型名                                               | Agent 使用的模型（`temperature=0`，开启 streaming） |

任何 OpenAI 兼容的模型服务都可以接入（LangChain 侧走 `ChatOpenAI` + `base_url`），模型名以所选服务的文档为准。

> **安全提示**：`.gitignore` 已忽略 `.env`，但仓库历史里存在一份带真实密钥的 `backend/.env`。若该仓库会公开或共享，请轮换其中的数据库密码、`JWT_SECRET_KEY` 与 `LLM_API_KEY`，并把 `backend/.env` 从索引中移除（`git rm --cached backend/.env`）。同理，`backend/data/chroma/` 与 `backend/uploads/` 属于运行产物，也不适合入库；公开前请确认 `data/kb/*.md` 是否允许外泄。

---

## 知识库维护

`backend/data/kb/` 下每个 `.md` 文件是一篇资料（现有：`预约规则.md`、`开放时间.md`、`安全规范.md`、`设备使用.md`），以文件名为 chunk id、整篇为一个向量单元。新增或修改资料后：

```bash
# 删除持久化目录让服务重新灌库
rm -rf backend/data/chroma
```

集合为空时才会重新读取 `kb/` 目录，因此改动原文需要清掉 `data/chroma` 重建。

---

## 构建与代码风格

```bash
cd frontend && npm run build      # 产物在 frontend/dist（已在 .gitignore 中）
cd frontend && npm run preview
cd frontend && npm run format     # Prettier 格式化 src/（.prettierrc.json）
```

前端统一从 `@/` 别名（指向 `src/`）导入；所有请求走 `utils/request.js`，响应拦截器负责弹出 `ElMessage.error` 与 401 自动登出跳转。

---
