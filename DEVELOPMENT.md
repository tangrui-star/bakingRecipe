# 开发文档

## 认证系统

### 功能特性
- 用户注册/登录
- JWT双token认证机制
- 图片验证码（4位数字，5分钟有效）
- 邮箱验证码（6位数字，5分钟有效）
- 密码加密（bcrypt）
- 登录日志记录

### 密码要求
- 最少8个字符
- 必须包含大写字母
- 必须包含小写字母
- 必须包含数字

### Token机制
- Access Token：30分钟有效期
- Refresh Token：7天有效期
- 自动刷新机制

### 验证码说明
- 图片验证码：用于保护注册和登录接口
- 邮箱验证码：开发阶段打印到后端控制台，生产环境将发送到邮箱

## 前端开发

### 技术栈
- Vue 3 (Composition API)
- Element Plus
- Vue Router
- Axios

### 设计系统

#### 颜色变量
```css
--primary-blue: #3b82f6
--primary-purple: #8b5cf6
--primary-green: #10b981
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--bg-primary: #f8fafc
--bg-card: #ffffff
--border-color: #e5e7eb
```

#### 移动端适配
- 断点：768px
- 底部Tab高度：56px
- 顶部Header高度：48px
- 最小触摸目标：44px
- 输入框字体：16px（防止iOS缩放）

#### 图标处理
所有图标在移动端添加：
```css
.el-icon {
  flex-shrink: 0 !important;
  min-width: 1em;
  min-height: 1em;
}
```

### 页面结构
- Dashboard - 首页（数据统计、快速操作、最近配方）
- RecipeList - 配方列表（筛选、导出）
- RecipeEdit - 配方编辑（创建/更新）
- RecipeCalculator - 配方计算器
- RecipeHistory - 历史版本
- Profile - 个人资料
- Settings - 系统设置
- Login/Register - 登录/注册

### 路由守卫
系统已配置路由守卫，确保：
- 未登录用户只能访问登录/注册页面
- 已登录用户访问登录/注册页面会自动跳转到Dashboard
- 底部TabBar只在登录状态下显示
- 所有需要认证的页面都有 `meta: { requiresAuth: true }` 标记

### API调用
```javascript
// 示例：获取配方列表
const recipes = await api.recipes.list(shopId, categoryId)

// 示例：创建配方
const newRecipe = await api.recipes.create({
  name: '配方名称',
  category_id: 'cat-001',
  base_quantity: 10,
  base_weight: 1000,
  // ...
})
```

## 后端开发

### 技术栈
- FastAPI
- SQLAlchemy
- PyMySQL
- python-jose (JWT)
- bcrypt (密码加密)
- Pillow (验证码生成)

### 数据库模型
主要表：
- users - 用户
- shops - 店铺
- recipes - 配方
- recipe_versions - 配方版本
- ingredients - 原料
- recipe_categories - 分类

### API路由
```python
# 认证路由
/api/auth/register - POST
/api/auth/login - POST
/api/auth/captcha - GET
/api/auth/send-email-code - POST

# 配方路由
/api/recipes/ - GET, POST
/api/recipes/{id} - GET, PUT, DELETE
/api/recipes/{id}/versions - GET
/api/recipes/export/{shop_id} - GET

# 分类路由
/api/categories/ - GET

# 原料路由
/api/ingredients/ - GET
```

### 数据隔离
每个用户有独立的店铺，所有数据通过shop_id隔离：
```python
# 查询时自动过滤
recipes = db.query(Recipe).filter(Recipe.shop_id == user.shop_id).all()
```

## 移动端优化

### 已完成优化
- ✅ 小程序风格UI
- ✅ 底部Tab导航
- ✅ 响应式布局
- ✅ 触摸优化
- ✅ 图标防压扁
- ✅ 验证码显示优化
- ✅ 安全区域适配

### 测试建议
1. 使用Chrome DevTools移动模式
2. 测试不同屏幕尺寸（320px - 768px）
3. 测试触摸交互
4. 测试输入框（防止iOS缩放）
5. 测试底部Tab导航

## 部署说明

### 后端部署
1. 安装依赖：`pip install -r requirements.txt`
2. 配置环境变量（.env文件）
3. 运行：`python main.py`

### 前端部署
1. 安装依赖：`npm install`
2. 构建：`npm run build`
3. 部署dist目录到静态服务器

### 数据库初始化
```bash
# 运行初始化脚本
python database/init_db.py

# 或导入SQL文件
mysql -h 47.109.97.153 -u root -p baking_recipe_system < database/init_database.sql
```

## 常见问题

### Q: 验证码看不到？
A: 检查后端是否正常运行，验证码接口是否返回图片

### Q: 登录后立即退出？
A: 检查token是否正确保存到localStorage

### Q: 移动端图标变形？
A: 已修复，确保使用最新的global.css

### Q: 配方数据看不到？
A: 检查用户是否有关联的店铺，shop_id是否正确

## 黑名单管理系统

### 功能概述
- 管理职业打假人和恶意退货买家信息
- 支持查看、添加、编辑、删除黑名单
- 支持搜索和风险等级筛选
- 自动提取电话号码

### 核心特性

#### 自动电话号码提取
系统会自动从文本中提取中国手机号（1[3-9]\d{9}），并存储到phone_numbers JSON数组中。

#### 唯一标识生成
每个黑名单条目自动生成10位唯一标识（格式：BL + 8位随机字符）。

#### 风险等级
- HIGH（高风险）：红色标签
- MEDIUM（中风险）：橙色标签
- LOW（低风险）：绿色标签

### API接口
- POST /api/blacklist - 创建黑名单
- GET /api/blacklist - 查询列表（支持搜索、筛选、分页）
- GET /api/blacklist/{id} - 获取详情
- PUT /api/blacklist/{id} - 更新黑名单
- DELETE /api/blacklist/{id} - 删除黑名单

## 订单检查系统

### 功能概述
上传订单Excel文件，自动检查订单中是否存在黑名单客户，识别风险订单。

### Excel文件格式
需要包含以下列：
- 姓名（必填）
- 电话（必填）
- 地址（可选）

### 匹配规则
按以下优先级进行匹配：
1. 电话号码匹配（最高优先级）
2. 姓名匹配
3. 地址匹配（需要姓名也匹配）

### API接口
- POST /api/screening/check-orders - 检查订单
- POST /api/screening/save-screening - 保存检查记录
- GET /api/screening/history - 获取历史列表
- GET /api/screening/history/{id} - 获取检查详情
- DELETE /api/screening/history/{id} - 删除检查记录

### 初始化步骤
```bash
# 创建黑名单表
cd database
python init_blacklist_tables.py

# 创建订单检查表
python init_screening_tables.py

# 安装依赖
pip install pandas openpyxl
```

## 开发工具

### 推荐VSCode插件
- Vue Language Features (Volar)
- Python
- ESLint
- Prettier

### 调试工具
- Vue DevTools
- FastAPI自动文档：http://localhost:8000/docs
- 数据库客户端：MySQL Workbench / DBeaver
