# 烘焙配方管理系统

一个专为烘焙行业设计的配方管理系统，支持配方版本控制、智能计算、热量统计等功能。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 一键启动

#### 方式1：使用启动脚本
```bash
# 一键启动所有服务
start_all.bat

# 或分别启动
start_backend.bat  # 启动后端
start_frontend.bat # 启动前端

# 停止所有服务
stop_all.bat
```

#### 方式2：手动启动

1. **安装依赖**
```bash
# 后端依赖
install_backend_deps.bat

# 前端依赖
install_frontend_deps.bat
```

2. **启动后端**
```bash
cd backend
python main.py
```

3. **启动前端**
```bash
cd frontend
npm run dev
```

### 环境检查
运行环境检查脚本，确保所有依赖已安装：
```bash
check_environment.bat
```

### 访问系统
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 默认账户
- 用户名：`admin`
- 密码：`Admin@2025`

## 📱 功能特性

### 核心功能
- ✅ 配方管理（CRUD）
- ✅ 自动版本控制
- ✅ 配方计算器（按比例计算原料用量）
- ✅ 热量自动计算
- ✅ 配方历史版本查看
- ✅ 数据导出（JSON格式）
- ✅ 黑名单管理（客户风险管理）
- ✅ 订单检查（Excel批量检查）

### 用户系统
- ✅ 用户注册/登录
- ✅ JWT双token认证
- ✅ 图片验证码（4位数字）
- ✅ 邮箱验证码（6位数字，开发阶段打印到控制台）
- ✅ 密码加密（bcrypt）
- ✅ 多用户数据隔离（每个用户独立店铺）

### 黑名单系统
- ✅ 黑名单CRUD操作
- ✅ 风险等级管理（高/中/低）
- ✅ 自动提取电话号码
- ✅ 支持多个电话号码
- ✅ 搜索和筛选功能

### 订单检查系统
- ✅ Excel文件上传
- ✅ 智能匹配算法（电话/姓名/地址）
- ✅ 检查历史记录
- ✅ 详细匹配报告

### 移动端优化
- ✅ 小程序风格UI设计
- ✅ 底部Tab导航
- ✅ 响应式布局
- ✅ 触摸优化
- ✅ 图标防压扁处理

## 🗄️ 数据库配置

**连接信息：**
- Host: 47.109.97.153
- Port: 3306
- Database: baking_recipe_system
- User: root
- Password: Root@2025!

**数据表：**
- users - 用户表
- shops - 店铺表
- recipes - 配方表
- recipe_versions - 配方版本表
- ingredients - 原料表
- recipe_version_ingredients - 配方原料关联表
- recipe_steps - 制作步骤表
- recipe_categories - 配方分类表
- refresh_tokens - 刷新令牌表
- login_logs - 登录日志表

## 📂 项目结构

```
bakingRecipe/
├── backend/              # 后端（FastAPI）
│   ├── routers/         # API路由
│   ├── models.py        # 数据模型
│   ├── database.py      # 数据库连接
│   ├── auth_utils.py    # 认证工具
│   ├── captcha_utils.py # 验证码工具
│   └── main.py          # 入口文件
├── frontend/            # 前端（Vue 3 + Element Plus）
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 公共组件
│   │   ├── api/        # API接口
│   │   ├── router/     # 路由配置
│   │   └── styles/     # 全局样式
│   └── index.html
├── database/            # 数据库脚本
│   ├── init_database.sql
│   ├── schema.sql
│   └── seed_data.py
└── README.md
```

## 🎨 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM
- PyMySQL - MySQL驱动
- python-jose - JWT处理
- bcrypt - 密码加密
- Pillow - 验证码生成

### 前端
- Vue 3 - 前端框架
- Element Plus - UI组件库
- Vue Router - 路由管理
- Axios - HTTP客户端
- Vite - 构建工具

## 📖 开发文档

### 认证系统
- 图片验证码有效期：5分钟
- 邮箱验证码有效期：5分钟
- Access Token有效期：30分钟
- Refresh Token有效期：7天
- 密码要求：至少8位，包含大小写字母和数字

### API接口
详见：http://localhost:8000/docs

主要接口：
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/captcha` - 获取图片验证码
- `POST /api/auth/send-email-code` - 发送邮箱验证码
- `GET /api/recipes/` - 获取配方列表
- `POST /api/recipes/` - 创建配方
- `GET /api/recipes/{id}` - 获取配方详情
- `PUT /api/recipes/{id}` - 更新配方
- `DELETE /api/recipes/{id}` - 删除配方
- `GET /api/recipes/export/{shop_id}` - 导出配方数据

### 移动端适配
- 断点：768px
- 底部Tab高度：56px
- 顶部Header高度：48px
- 最小触摸目标：44px
- 输入框字体：16px（防止iOS缩放）

## 🐛 已知问题

无

## 📝 更新日志

### v2.1.0 (2026-04-07)
- ✅ 添加黑名单管理系统
- ✅ 添加订单检查功能
- ✅ Dashboard重新设计
- ✅ 优化项目文档结构
- ✅ 添加一键启动脚本

### v2.0.0 (2026-03-29)
- ✅ 完成移动端UI重构（小程序风格）
- ✅ 添加底部Tab导航
- ✅ 优化所有页面的移动端适配
- ✅ 修复验证码显示问题
- ✅ 修复图标压扁问题
- ✅ 导入13个真实配方数据

### v1.0.0 (2026-03-28)
- ✅ 完成基础功能开发
- ✅ 实现用户认证系统
- ✅ 实现配方管理功能
- ✅ 实现配方计算器
- ✅ 实现数据导出功能

## 📞 联系方式

如有问题，请联系开发团队。

## 📄 许可证

MIT License
