# 绩效考核系统

一个基于企业微信的现代化绩效考核管理系统，支持自评、上级评估、多级审批等完整的绩效管理流程。

## 项目简介

本系统是一个企业级绩效考核管理平台，通过企业微信集成实现员工身份认证和消息通知，提供完整的绩效考核流程管理功能。

### 核心功能

- **企业微信集成**：OAuth 2.0 身份认证，消息推送通知
- **组织架构同步**：自动同步企业微信的部门和员工信息
- **考核计划管理**：支持月度/季度/年度考核计划创建和管理
- **多维度评估**：自定义评估模板，支持多个考核维度
- **审批流程**：灵活的审批链配置（直属上级 → VP → HR）
- **自评与上级评估**：员工自评 + 上级评估的双向评价机制
- **数据导出**：支持导出考核结果为 Excel 报表
- **移动端优化**：基于 Vant UI 的移动端友好界面

## 技术栈

### 后端
- **框架**：FastAPI (Python 3.13)
- **数据库**：MySQL 5.7+ / SQLAlchemy ORM
- **认证**：企业微信 OAuth 2.0
- **API 文档**：自动生成的 OpenAPI/Swagger 文档

### 前端
- **框架**：Vue 3 + Vite
- **UI 组件**：Vant 4 (移动端组件库)
- **路由**：Vue Router
- **HTTP 客户端**：Axios

### 部署
- **Web 服务器**：Nginx (反向代理 + 静态文件服务)
- **HTTPS**：SSL/TLS 证书支持
- **进程管理**：支持 systemd 或 PM2

## 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+
- MySQL 5.7+
- 企业微信账号（需要管理员权限配置应用）

### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入企业微信凭证和数据库配置

# 初始化数据库
alembic upgrade head

# 启动服务
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 配置企业微信

1. 登录企业微信管理后台
2. 创建自建应用，获取以下信息：
   - `WECOM_CORP_ID`：企业 ID
   - `WECOM_AGENT_ID`：应用 AgentID
   - `WECOM_SECRET`：应用 Secret
3. 配置应用可见范围和回调域名
4. 将凭证填入 `backend/.env` 文件

详细配置步骤请参考项目文档。

## 系统架构

```
┌─────────────┐
│  企业微信    │
│  (OAuth)    │
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│         Nginx (HTTPS)           │
│  ┌──────────┐    ┌───────────┐  │
│  │  前端静态 │    │  API 代理  │  │
│  │  文件服务 │    │  /api/*   │  │
│  └──────────┘    └─────┬─────┘  │
└────────────────────────┼────────┘
                         │
                ┌────────▼────────┐
                │   FastAPI 后端   │
                │  (Python 3.13)  │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │   MySQL 数据库   │
                └─────────────────┘
```

## 主要模块

### 1. 认证模块
- 企业微信 OAuth 2.0 登录
- JWT Token 会话管理
- 权限控制（员工/经理/HR）

### 2. 组织架构模块
- 部门信息同步
- 员工信息同步
- 上下级关系维护

### 3. 考核计划模块
- 考核计划创建
- 评估模板管理
- 考核周期配置

### 4. 评估模块
- 员工自评
- 上级评估
- 多级审批流程
- 评估结果查看

### 5. 数据导出模块
- Excel 报表生成
- 考核数据统计
- 批量导出功能

## 数据库设计

主要数据表：
- `department`：部门信息
- `employee`：员工信息
- `eval_template`：评估模板
- `assessment_plan`：考核计划
- `assessment_record`：考核记录
- `eval_detail`：评估明细
- `approval_log`：审批日志

## API 文档

启动后端服务后，访问以下地址查看 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发指南

### 目录结构

```
.
├── backend/              # 后端代码
│   ├── app/
│   │   ├── models/      # 数据模型
│   │   ├── routers/     # API 路由
│   │   ├── services/    # 业务逻辑
│   │   └── config.py    # 配置管理
│   ├── alembic/         # 数据库迁移
│   └── requirements.txt # Python 依赖
│
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── api/         # API 调用
│   │   ├── router/      # 路由配置
│   │   └── App.vue      # 根组件
│   └── package.json     # Node 依赖
│
└── README.md            # 项目文档
```

### 添加新功能

1. **后端**：在 `backend/app/routers/` 添加新的路由模块
2. **前端**：在 `frontend/src/views/` 添加新的页面组件
3. **数据库**：使用 Alembic 创建迁移脚本

### 代码规范

- Python: 遵循 PEP 8 规范
- JavaScript: 使用 ESLint + Prettier
- 提交信息: 使用语义化提交规范

## 部署说明

### 生产环境部署

1. 构建前端静态文件
2. 配置 Nginx 反向代理
3. 使用 systemd 或 supervisor 管理后端进程
4. 配置 SSL 证书启用 HTTPS
5. 设置定时任务同步组织架构

### 环境变量配置

生产环境需要配置以下环境变量：
- `DATABASE_URL`: 数据库连接字符串
- `WECOM_CORP_ID`: 企业微信企业 ID
- `WECOM_AGENT_ID`: 应用 AgentID
- `WECOM_SECRET`: 应用 Secret
- `APP_SECRET_KEY`: 应用密钥（用于 JWT 签名）
- `APP_BASE_URL`: 应用访问地址

## 安全建议

- ✅ 使用 HTTPS 加密传输
- ✅ 定期更新依赖包
- ✅ 不要将 `.env` 文件提交到版本控制
- ✅ 生产环境使用强密码和密钥
- ✅ 限制数据库访问权限
- ✅ 定期备份数据库

## 常见问题

### 1. 企业微信回调失败
- 检查回调域名是否正确配置
- 确认应用可见范围包含测试用户
- 查看后端日志排查错误

### 2. 组织架构同步失败
- 确认应用有通讯录权限
- 检查企业微信 API 调用限制
- 查看数据库外键约束

### 3. 前端无法访问后端 API
- 检查 Nginx 代理配置
- 确认后端服务正常运行
- 查看浏览器控制台错误信息

## 许可证

本项目采用 MIT 许可证。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系我们。

---

**注意**：本系统需要企业微信环境才能正常运行，请确保已完成企业微信应用配置。
