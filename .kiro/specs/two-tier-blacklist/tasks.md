# 实现计划：两级黑名单体系

## 概述

将现有单一 `blacklist` 表升级为两级结构（用户黑名单 + 系统黑名单），新增推送审核流程、管理员后台、站内通知 + 邮件通知，并改造订单检查以支持双库匹配和 `source` 字段标注。

技术栈：Python / FastAPI / SQLAlchemy（后端），Vue 3 / Vant（前端），Hypothesis（属性测试）。

---

## 任务

- [x] 1. 数据库变更与迁移脚本
  - [x] 1.1 编写 DDL 迁移脚本 `database/migrate_to_two_tier.py`
    - 在 `users` 表新增 `is_admin BOOLEAN NOT NULL DEFAULT FALSE`
    - 在 `blacklist` 表新增 `blacklist_type ENUM('USER','SYSTEM') NOT NULL DEFAULT 'USER'`、`owner_id VARCHAR(36)`、`source_push_request_id INT`，并添加对应索引
    - 创建 `push_requests` 表（含 `id`、`blacklist_id`、`applicant_id`、`evidence`、`status`、`reject_reason`、`reviewed_by`、`reviewed_at`、`created_at`、`updated_at` 及索引）
    - 创建 `notifications` 表（含 `id`、`user_id`、`type`、`push_request_id`、`title`、`content`、`is_read`、`created_at` 及索引）
    - 支持 `--dry-run` 参数，仅打印将要执行的 SQL 而不实际修改
    - _需求：1.1、2.1、3.1、5.2、9.3、8.1_

  - [x] 1.2 编写数据迁移逻辑（在同一脚本中）
    - `UPDATE blacklist SET blacklist_type='USER', owner_id=created_by WHERE created_by IS NOT NULL`
    - `UPDATE blacklist SET blacklist_type='SYSTEM' WHERE created_by IS NULL`
    - 逐条处理，捕获单条错误并记录日志，不中断整体流程
    - 迁移完成后输出成功条目数和失败条目数统计报告
    - _需求：8.1、8.2、8.3_

- [x] 2. 后端模型与权限中间件
  - [x] 2.1 更新 `backend/models.py`
    - 新增枚举类 `BlacklistType`、`PushRequestStatus`、`NotificationType`
    - `User` 模型新增 `is_admin = Column(Boolean, default=False, nullable=False)`
    - `Blacklist` 模型新增 `blacklist_type`、`owner_id`、`source_push_request_id` 字段
    - 新增 `PushRequest` 模型（含 relationship 到 `Blacklist` 和 `User`）
    - 新增 `Notification` 模型（含 relationship 到 `User` 和 `PushRequest`）
    - _需求：1.1、2.1、3.1、5.2、9.3_

  - [x] 2.2 在 `backend/routers/auth.py` 中新增 `require_admin` 依赖函数
    - `require_admin(current_user=Depends(get_current_user)) -> User`：若 `is_admin=False` 则抛出 `HTTPException(403)`
    - _需求：1.2、1.3、1.5_

  - [ ]* 2.3 为权限中间件编写属性测试（`backend/tests/test_permissions.py`）
    - **属性 1：普通用户无法访问系统黑名单接口**
    - **验证需求：1.2、3.3**
    - **属性 2：管理员可正常访问系统黑名单接口**
    - **验证需求：1.3**

- [x] 3. 用户黑名单 CRUD 接口改造
  - [x] 3.1 改造 `backend/routers/blacklist.py`
    - `POST /api/blacklist`：创建时强制设置 `owner_id=current_user.id`、`blacklist_type=USER`
    - `GET /api/blacklist`：查询时过滤 `owner_id=current_user.id AND blacklist_type=USER`
    - `GET /api/blacklist/statistics`：统计时过滤 `owner_id=current_user.id AND blacklist_type=USER`，不包含系统黑名单数量
    - `PUT /api/blacklist/{id}` / `DELETE /api/blacklist/{id}`：校验 `owner_id == current_user.id`，否则返回 403
    - 支持按 `risk_level` 过滤和按姓名/电话关键词搜索
    - _需求：2.2、2.3、2.4、2.5、2.6、2.7、7.1、7.2、7.4_

  - [ ]* 3.2 为用户黑名单编写属性测试（`backend/tests/test_user_blacklist.py`）
    - **属性 3：用户黑名单数据隔离**
    - **验证需求：1.4、2.3、2.4**
    - **属性 4：创建用户黑名单条目时字段自动赋值**
    - **验证需求：2.2**
    - **属性 5：风险等级过滤正确性**
    - **验证需求：2.5**
    - **属性 6：统计数据仅反映当前用户**
    - **验证需求：2.7、7.1、7.2、7.4**

- [x] 4. 系统黑名单接口（Admin Only）
  - [x] 4.1 新建 `backend/routers/system_blacklist.py`
    - 所有路由使用 `require_admin` 依赖
    - `POST /api/system-blacklist`：创建，`blacklist_type=SYSTEM`，`owner_id=None`
    - `GET /api/system-blacklist`：列表，支持分页、`risk_level` 过滤、关键词搜索
    - `GET /api/system-blacklist/statistics`：返回总数及各风险等级数量
    - `GET /api/system-blacklist/{id}`：详情
    - `PUT /api/system-blacklist/{id}`：更新
    - `DELETE /api/system-blacklist/{id}`：删除
    - _需求：3.1、3.2、3.3、3.4、3.5_

  - [x] 4.2 在 `backend/main.py` 中注册 `system_blacklist` 路由

- [x] 5. 推送申请接口
  - [x] 5.1 新建 `backend/routers/push_requests.py`
    - `POST /api/push-requests`（User）：校验 `evidence` 长度 ≥ 10 字符（否则 400）；检查同一 `blacklist_id` 是否已有 PENDING 申请（否则 409）；创建申请，`status=PENDING`
    - `GET /api/push-requests/my`（User）：返回当前用户提交的申请列表，含状态和拒绝原因
    - `GET /api/push-requests`（Admin）：返回所有申请，支持按 `status` 过滤，分页
    - `POST /api/push-requests/{id}/approve`（Admin）：校验申请状态为 PENDING（否则 409）；将状态更新为 APPROVED；将用户黑名单条目数据复制到系统黑名单，设置 `source_push_request_id`；触发通知（站内消息 + 邮件）
    - `POST /api/push-requests/{id}/reject`（Admin）：校验申请状态为 PENDING（否则 409）；校验 `reject_reason` 不为空（否则 400）；将状态更新为 REJECTED；触发通知（站内消息 + 邮件）
    - _需求：5.1、5.2、5.3、5.4、5.5、5.6、5.7_

  - [x] 5.2 在 `backend/main.py` 中注册 `push_requests` 路由

  - [ ]* 5.3 为推送申请编写属性测试（`backend/tests/test_push_requests.py`）
    - **属性 9：推送申请 evidence 长度校验**
    - **验证需求：5.1**
    - **属性 10：同一条目不允许重复 PENDING 申请**
    - **验证需求：5.3**
    - **属性 11：审核通过后数据复制到系统黑名单**
    - **验证需求：5.4**
    - **属性 12：已审核申请不可重复审核**
    - **验证需求：5.7**

- [x] 6. 通知接口（站内消息 + 邮件）
  - [x] 6.1 在 `backend/email_utils.py` 中新增审核通知邮件函数
    - `send_push_approved_email(to_email, ktt_name) -> tuple[bool, str]`
    - `send_push_rejected_email(to_email, ktt_name, reject_reason) -> tuple[bool, str]`
    - 邮件发送失败时仅记录日志，不抛出异常
    - _需求：9.1、9.2、9.7_

  - [x] 6.2 新建 `backend/routers/notifications.py`
    - `GET /api/notifications`（User）：返回当前用户通知列表，按 `created_at` 倒序，支持分页，响应中包含 `unread_count`
    - `GET /api/notifications/unread-count`（User）：返回未读数量
    - `PUT /api/notifications/{id}/read`（User）：标记单条已读，返回更新后的未读数量
    - `PUT /api/notifications/read-all`（User）：批量将当前用户所有未读通知标记为已读
    - _需求：9.3、9.4、9.5、9.6、9.8_

  - [x] 6.3 在 `backend/main.py` 中注册 `notifications` 路由

  - [ ]* 6.4 为通知接口编写属性测试（`backend/tests/test_notifications.py`）
    - **属性 13：审核操作触发站内通知创建**
    - **验证需求：9.3**
    - **属性 14：通知列表按创建时间倒序**
    - **验证需求：9.4**
    - **属性 15：标记已读后未读数减少**
    - **验证需求：9.5、9.6**

- [x] 7. 管理员后台接口
  - [x] 7.1 新建 `backend/routers/admin.py`
    - 所有路由使用 `require_admin` 依赖
    - `GET /api/admin/statistics`：返回系统黑名单总数、各风险等级数量、待审核 Push_Request 数量
    - `GET /api/admin/users`：返回用户列表（分页）
    - `PUT /api/admin/users/{id}/toggle-active`：启用/禁用用户
    - _需求：6.2、6.3、6.4、7.3_

  - [x] 7.2 在 `backend/main.py` 中注册 `admin` 路由

- [ ] 8. 检查点 —— 后端接口全部就绪
  - 确保所有后端测试通过，ask the user if questions arise.

- [x] 9. 订单检查改造（双库匹配 + source 字段）
  - [x] 9.1 改造 `backend/routers/screening.py` 中的 `check_orders` 接口
    - 同时查询 `blacklist_type=SYSTEM` 的系统黑名单和 `blacklist_type=USER AND owner_id=current_user.id` 的用户黑名单
    - 改造 `match_blacklist` 函数，接受两个列表（系统库、用户库），分别匹配后合并结果
    - 每条命中结果新增 `source` 字段（`SYSTEM` 或 `USER`）
    - 同一订单同时命中两库时，取风险等级更高的结果，`source` 标注实际来源
    - 保持现有匹配规则不变（电话 HIGH、姓名 MEDIUM）
    - _需求：4.1、4.2、4.3、4.4、4.5_

  - [x] 9.2 改造 `save_screening` 接口，确保保存的 `order_data` JSON 中包含 `source` 字段
    - _需求：4.6_

  - [ ]* 9.3 为双库匹配编写属性测试（`backend/tests/test_screening.py`）
    - **属性 7：双库匹配覆盖性**
    - **验证需求：4.1、4.3**
    - **属性 8：命中结果包含合法 source 字段**
    - **验证需求：4.2**

- [x] 10. 前端：黑名单页改造（`BlacklistManage.vue` + `BlacklistEdit.vue`）
  - [x] 10.1 改造 `frontend/src/views/BlacklistManage.vue`
    - 统计卡片数据来源改为用户黑名单统计接口（不含系统黑名单数量）
    - 列表数据改为用户黑名单列表接口（`blacklist_type=USER`）
    - 每条黑名单条目新增「申请推送」按钮，点击跳转至推送申请页
    - _需求：2.3、2.5、2.6、2.7_

  - [x] 10.2 改造 `frontend/src/api/blacklist.js`
    - 确保创建/更新/删除接口调用用户黑名单路由
    - 新增 `pushRequest(data)` 方法（调用 `POST /api/push-requests`）
    - 新增 `getMyPushRequests()` 方法（调用 `GET /api/push-requests/my`）
    - _需求：2.2、5.1、5.6_

- [x] 11. 前端：推送申请页（新建 `PushRequest.vue`）
  - [x] 11.1 新建 `frontend/src/views/PushRequest.vue`
    - 展示待推送的黑名单条目信息（KTT 名字、风险等级、入黑原因）
    - 提供 `evidence` 文本输入框（最少 10 字符，前端校验）
    - 提交后调用 `POST /api/push-requests`，处理 409（已有 PENDING 申请）和 400（evidence 不足）错误提示
    - _需求：5.1、5.2、5.3_

  - [x] 11.2 新建 `frontend/src/views/MyPushRequests.vue`
    - 展示当前用户提交的推送申请列表，含状态标签（PENDING / APPROVED / REJECTED）和拒绝原因
    - _需求：5.6_

- [x] 12. 前端：通知中心（新建 `Notifications.vue`）
  - [x] 12.1 新建 `frontend/src/views/Notifications.vue`
    - 展示站内消息列表，按创建时间倒序，支持分页
    - 顶部展示未读消息数量徽标
    - 支持单条标记已读和「全部标记已读」操作
    - 调用 `GET /api/notifications`、`PUT /api/notifications/{id}/read`、`PUT /api/notifications/read-all`
    - _需求：9.4、9.5、9.6、9.8_

  - [x] 12.2 在 `frontend/src/components/TabBar.vue` 中为通知入口添加未读数量徽标
    - 调用 `GET /api/notifications/unread-count` 获取未读数
    - _需求：9.4_

- [x] 13. 前端：管理员后台页面
  - [x] 13.1 新建 `frontend/src/views/admin/AdminDashboard.vue`
    - 展示系统黑名单总数、各风险等级数量、待审核申请数量（调用 `GET /api/admin/statistics`）
    - 提供导航入口：系统黑名单管理、推送申请审核、用户管理
    - _需求：6.2、6.5、7.3_

  - [x] 13.2 新建 `frontend/src/views/admin/SystemBlacklist.vue`
    - 系统黑名单列表（分页、风险等级过滤、关键词搜索）
    - 支持创建、编辑、删除系统黑名单条目
    - 调用 `/api/system-blacklist` 系列接口
    - _需求：3.2、3.5_

  - [x] 13.3 新建 `frontend/src/views/admin/PushRequestReview.vue`
    - 推送申请列表，支持按状态过滤（PENDING / APPROVED / REJECTED）
    - 每条 PENDING 申请提供「通过」和「拒绝」操作，拒绝时弹窗要求填写 `reject_reason`
    - 调用 `POST /api/push-requests/{id}/approve` 和 `POST /api/push-requests/{id}/reject`
    - _需求：6.3、5.4、5.5_

  - [x] 13.4 新建 `frontend/src/views/admin/UserManagement.vue`
    - 用户列表（分页），支持启用/禁用用户
    - 调用 `GET /api/admin/users` 和 `PUT /api/admin/users/{id}/toggle-active`
    - _需求：6.4_

- [x] 14. 前端：路由守卫更新
  - [x] 14.1 在 `frontend/src/router/index.js` 中新增管理员路由
    - 新增 `/admin`、`/admin/system-blacklist`、`/admin/push-requests`、`/admin/users` 路由，`meta: { requiresAuth: true, requiresAdmin: true }`
    - 新增 `/notifications`、`/push-requests`、`/my-push-requests` 路由，`meta: { requiresAuth: true }`
    - _需求：6.1_

  - [x] 14.2 更新路由守卫逻辑
    - 读取 `localStorage` 中 `user_info.is_admin` 字段
    - WHEN `requiresAdmin=true` 且用户非管理员，重定向至 `/dashboard`
    - _需求：6.1_

- [ ] 15. 检查点 —— 前端页面全部就绪
  - 确保所有前端路由可正常访问，ask the user if questions arise.

- [ ] 16. 属性测试套件（Hypothesis）
  - [ ]* 16.1 完善 `backend/tests/test_permissions.py`（属性 1、2）
    - 使用 `@given(st.booleans())` 生成 `is_admin` 值，验证权限中间件行为
    - `@settings(max_examples=100)`
    - 注释格式：`# Feature: two-tier-blacklist, Property 1: 普通用户无法访问系统黑名单接口`
    - _需求：1.2、1.3_

  - [ ]* 16.2 完善 `backend/tests/test_user_blacklist.py`（属性 3、4、5、6）
    - 属性 3：`@given(st.text(), st.text())` 生成两个不同用户 ID，验证数据隔离
    - 属性 4：`@given(...)` 生成任意合法黑名单数据，验证 `owner_id` 和 `blacklist_type` 自动赋值
    - 属性 5：`@given(st.sampled_from(['HIGH','MEDIUM','LOW']))` 验证过滤结果一致性
    - 属性 6：`@given(st.integers(min_value=0, max_value=50))` 生成随机条目数，验证统计数据准确性
    - `@settings(max_examples=100)`
    - _需求：2.2、2.3、2.4、2.5、2.7_

  - [ ]* 16.3 完善 `backend/tests/test_push_requests.py`（属性 9、10、11、12）
    - 属性 9：`@given(st.text(max_size=9))` 验证短 evidence 返回 400；`@given(st.text(min_size=10))` 验证成功创建
    - 属性 10：`@given(...)` 验证重复 PENDING 申请返回 409
    - 属性 11：`@given(...)` 验证审核通过后系统黑名单中存在对应记录且 `source_push_request_id` 正确
    - 属性 12：`@given(st.sampled_from(['APPROVED','REJECTED']))` 验证已审核申请重复审核返回 409
    - `@settings(max_examples=100)`
    - _需求：5.1、5.3、5.4、5.7_

  - [ ]* 16.4 完善 `backend/tests/test_notifications.py`（属性 13、14、15）
    - 属性 13：`@given(st.booleans())` 生成通过/拒绝操作，验证通知记录创建
    - 属性 14：`@given(st.integers(min_value=1, max_value=20))` 生成 N 条通知，验证倒序排列
    - 属性 15：`@given(st.integers(min_value=1, max_value=10))` 生成未读通知数，验证标记已读后未读数减少
    - `@settings(max_examples=100)`
    - _需求：9.3、9.4、9.5、9.6_

  - [ ]* 16.5 完善 `backend/tests/test_screening.py`（属性 7、8）
    - 属性 7：`@given(...)` 生成系统库和用户库各一条匹配条目，验证双库匹配覆盖性
    - 属性 8：`@given(...)` 验证所有命中结果的 `source` 字段值为 `SYSTEM` 或 `USER`
    - `@settings(max_examples=100)`
    - _需求：4.1、4.2、4.3_

- [x] 17. 最终检查点 —— 确保所有测试通过
  - 确保所有测试通过，ask the user if questions arise.

---

## 备注

- 标有 `*` 的子任务为可选测试任务，可跳过以加快 MVP 交付
- 每个属性测试文件顶部需注明 `# Feature: two-tier-blacklist, Property N: 属性描述`
- 邮件发送失败不阻断审核主流程，仅记录日志
- 管理员不支持批量审核，每条 Push_Request 必须单独操作
- 通知记录永久保留，不支持用户删除
