# dazuoagent

全屋定制家具(全屋定制)Agent 平台 —— 客户上传平面图,与 LLM 设计助理对话搭方案,在素材库里挑板材 / 五金,自动生成可追溯行项明细的报价单。

```
backend/   FastAPI + SQLAlchemy + LangGraph
frontend/  React + TypeScript + Vite + Tailwind + Zustand
```

---

## 快速上手

```bash
# 后端 (Python 3.11+)
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
python -m dazuoagent.db.seed                 # 写入 10 条示例素材
dazuoagent-api                               # http://127.0.0.1:8000

# 前端
cd frontend
npm install
npm run dev                                  # http://127.0.0.1:5173
```

Swagger 文档在 <http://127.0.0.1:8000/docs>,ReDoc 在 `/redoc`。

详细架构 / 模块边界 / 开发约定见 [`CLAUDE.md`](CLAUDE.md)。Docker 编排见 `docker-compose.yml`,本地双服务启动脚本见 `scripts/dev.{sh,ps1}`。

---

## 配置

复制根目录的 `.env.example` 到 `backend/.env`,然后填入 LLM Key。`.env` 已经在 `.gitignore` 里,不会被提交。

| 字段 | 说明 |
|---|---|
| `LLM_PROVIDER` | `mock` / `openai` / `anthropic` / `deepseek`,默认 `mock` |
| `DEEPSEEK_API_KEY` | DeepSeek V4 Flash 的 API key (`https://api.deepseek.com/v1`) |
| `OPENAI_API_KEY` | OpenAI key,可选 |
| `ANTHROPIC_API_KEY` | Anthropic key,可选 |
| `DATABASE_URL` | 默认 SQLite 在 `data/db/`,生产可换 PostgreSQL |

---

## 进度 (2026-07)

按时间倒序的最新进展:

### ✅ 报价引擎按面板拆解 + 五金行项
- `services/quotation_service.py` 重写,7 种家具类型(衣柜 / 开放式衣帽间 / 橱柜 / 电视柜 / 书柜 / 鞋柜 / 其他)各自的面板展开规则 + 铰链 / 拉手 / 挂衣杆按件自动开行项
- 每件家具每个角色(侧板 / 顶板 / 底板 / 背板 / 门板 / 层板 / 立板)开一行,小计 = 面积 × 单价,可追溯
- 没 seed 该类五金时静默跳过该行,不崩
- 公共 helper `total_panel_area_sqm()` 暴露,供定制报价使用
- 19 个新测覆盖面板展开 / 五金派生 / 重算 / 幂等性 / graceful skip

### ✅ DeepSeek V4 Flash LLM 接入
- `agent/agent.py` 重写:按 `llm_provider` 路由到 openai / anthropic / deepseek / mock
- `agent/langchain_tools.py` 新增:把 `list_materials` / `get_project_rooms` 包成 LangChain `@tool`,JSON 喂给 LLM
- `_extract_tool_calls` 遍历 LangGraph `messages` 历史取工具调用;`_suggested_actions` 跟着调用的工具给出下一步建议
- `core/config.py` 加 `deepseek_api_key` / `deepseek_model="deepseek-v4-flash"` / `deepseek_base_url="https://api.deepseek.com/v1"`
- **顺手修了 `_BACKEND_ROOT` parent-index off-by-one** (之前指向 `backend/src/`,导致 `.env` 读不到)
- 8 个测试覆盖 provider 路由 + 真实 DeepSeek 调用 (`test_real_deepseek_smoke`)

### ✅ Swagger / OpenAPI 中文化
- `main.py` 的 `title` / `description` / `openapi_tags` 全改成中文,加上 5 步工作流说明
- 5 个 router 的 `summary=` / `description=` / `Query(description=)` 全翻译,带"找不到"等错误中文提示
- `tags` 双语 (`"素材库 / materials"`),分组下拉里既能看中文又能瞄英文标识
- Swagger UI 按钮 chrome (`Try it out` 等) 仍是英文 —— 那段在 Swagger UI bundle 里写死,需要本地化构建版本才能替换

### ✅ 预存在 bug 顺手修
- `db/__init__.py` 被截断的 docstring(只有 `"""...` 没有关闭符)
- 4 个 `*Read` schema 的 `created_at: str` 应该接受 `datetime`,加 `@field_serializer` 输出 ISO 字符串 (兼容 JSON wire shape)

### ✅ 开发环境
- 装上 Python 3.12.10 (清华 TUNA 镜像,4 秒下完)
- venv 在 `backend/.venv`,pip 走 TUNA,装齐 fastapi / sqlalchemy 2 / pydantic v2 / langchain 1.3 / langgraph 1.2 / pytest 9 / ruff
- ruff check 全清,ruff format 一致
- pytest 32 个用例全部通过 (报价 19 + 中间 / smoke / LLM 8 + 4 + 1 共 32)

---

## 路线图

下面这些还在 backlog 里,等你点一个我就推:

- **接 LLM**:拿到 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY` 之后,改 `LLM_PROVIDER` 就切到对应模型 (代码已就绪)
- **FloorPlanCanvas**:把上传的平面图渲染出来 + 让用户框选房间尺寸
- **Design3DViewer**:用 react-three-fiber 把家具位置画成 3D 预览
- **报价公式再升级**:9mm 薄背板自动换材质 / 按件拍五金 / 边封线按 linear meter 算
- **Alembic 迁移**:ORM 模型还没有 alembic revision 管理,生产部署前要补

---

## 许可证

项目内部使用,详细条款待定。
