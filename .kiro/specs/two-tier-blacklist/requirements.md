# 需求文档

## 简介

为 Aitbake 烘焙配方管理系统新增「两级黑名单体系」功能。当前系统已有单一黑名单表（blacklist）和订单检查功能，本功能将其升级为两级结构：**系统黑名单**（全局共享，管理员维护）和**用户黑名单**（个人私有，用户自维护）。

用户可将个人黑名单条目申请推送至系统黑名单，经管理员审核通过后合并入全局库，形成网络效应——系统库随社区贡献持续完善，帮助烘焙店铺群体共同应对恶意买家。

订单检查时同时匹配两级黑名单，命中结果标注来源，普通用户无法查看系统黑名单全量数据，仅在命中时可见对应条目。

---

## 词汇表

- **System**：Aitbake 两级黑名单系统整体
- **User**：已登录的普通烘焙店铺用户（`is_admin = false`）
- **Admin**：具有管理员权限的用户（`is_admin = true`）
- **User_Blacklist**：用户个人黑名单，仅创建者可见和操作
- **System_Blacklist**：系统全局黑名单，由管理员维护，对普通用户不可见（仅命中时展示）
- **Blacklist_Entry**：黑名单中的单条记录，包含买家身份信息、风险等级和入黑原因
- **Push_Request**：用户将 User_Blacklist 条目申请推送至 System_Blacklist 的审核申请
- **Order_Screening**：上传订单 Excel 文件，同时匹配两级黑名单的检查流程
- **Match_Result**：订单检查命中的结果，包含来源标注（系统库 / 我的黑名单）
- **Evidence**：推送申请时必须附带的证据，包括订单截图描述或沟通记录文字

---

## 需求

### 需求 1：用户权限分级

**用户故事：** 作为系统管理员，我希望通过 `is_admin` 字段区分管理员和普通用户，以便对不同角色实施差异化的数据访问控制。

#### 验收标准

1. THE System SHALL 在 `users` 表中新增 `is_admin` 布尔字段，默认值为 `false`。
2. WHEN User 访问系统黑名单管理接口，THE System SHALL 返回 403 Forbidden 错误。
3. WHEN Admin 访问系统黑名单管理接口，THE System SHALL 允许访问并返回数据。
4. WHEN User 访问其他用户的 User_Blacklist 数据，THE System SHALL 返回 403 Forbidden 错误。
5. THE System SHALL 在所有需要鉴权的接口中校验 `is_admin` 字段，不依赖前端路由保护作为唯一安全手段。

---

### 需求 2：用户黑名单（个人）

**用户故事：** 作为烘焙店铺用户，我希望创建和管理自己的私人黑名单，以便记录我遇到的恶意买家，且不被其他用户看到。

#### 验收标准

1. THE User_Blacklist SHALL 存储以下字段：KTT名字、微信名字、微信号、下单姓名电话、电话号码列表（JSON）、收货地址1、收货地址2、入黑原因、风险等级（HIGH / MEDIUM / LOW）、创建人 ID、创建时间、更新时间。
2. WHEN User 创建 Blacklist_Entry，THE System SHALL 将该条目的 `owner_id` 设置为当前用户 ID，`blacklist_type` 设置为 `USER`。
3. WHEN User 查询 User_Blacklist 列表，THE System SHALL 仅返回 `owner_id` 等于当前用户 ID 且 `blacklist_type` 为 `USER` 的条目。
4. WHEN User 更新或删除 Blacklist_Entry，THE System SHALL 校验该条目的 `owner_id` 等于当前用户 ID，否则返回 403 Forbidden 错误。
5. THE System SHALL 支持按风险等级过滤和按姓名/电话关键词搜索 User_Blacklist。
6. THE System SHALL 为 User_Blacklist 提供统计接口，返回当前用户各风险等级条目数量及总数。
7. IF User 查询统计数据，THEN THE System SHALL 仅统计该用户自己的 User_Blacklist 条目，不包含 System_Blacklist 数量。

---

### 需求 3：系统黑名单（全局）

**用户故事：** 作为管理员，我希望维护一个全局共享的系统黑名单，以便所有用户在订单检查时都能受益于社区共同积累的恶意买家数据。

#### 验收标准

1. THE System_Blacklist SHALL 存储与 User_Blacklist 相同的字段结构，并额外记录 `source_push_request_id`（来源推送申请 ID，可为空）。
2. WHEN Admin 创建、更新或删除 System_Blacklist 条目，THE System SHALL 执行操作并返回成功响应。
3. WHEN User 请求 System_Blacklist 列表或详情接口，THE System SHALL 返回 403 Forbidden 错误。
4. THE System SHALL 不在任何面向普通用户的接口响应中暴露 System_Blacklist 的总数量。
5. WHEN Admin 查询 System_Blacklist，THE System SHALL 支持按风险等级过滤和按姓名/电话关键词搜索，并返回分页结果。

---

### 需求 4：两级订单检查

**用户故事：** 作为烘焙店铺用户，我希望上传订单文件时同时匹配系统黑名单和我的个人黑名单，并在结果中看到命中来源，以便快速判断风险。

#### 验收标准

1. WHEN User 上传订单 Excel 文件执行 Order_Screening，THE System SHALL 同时在 System_Blacklist 和当前用户的 User_Blacklist 中进行匹配。
2. WHEN Order_Screening 产生 Match_Result，THE System SHALL 在每条命中结果中包含 `source` 字段，值为 `SYSTEM`（来自系统库）或 `USER`（来自我的黑名单）。
3. WHEN 同一订单同时命中 System_Blacklist 和 User_Blacklist，THE System SHALL 返回风险等级更高的命中结果，并在 `source` 字段中标注实际来源。
4. WHEN Order_Screening 命中 System_Blacklist 条目，THE System SHALL 仅在 Match_Result 中展示该条目信息，不允许 User 通过检查结果枚举 System_Blacklist 全量数据。
5. THE System SHALL 保持现有匹配规则不变：电话号码完全一致（HIGH）、姓名严格相等（MEDIUM）。
6. WHEN Order_Screening 完成，THE System SHALL 在保存的检查记录中记录每条命中结果的 `source` 字段。

---

### 需求 5：推送审核流程

**用户故事：** 作为烘焙店铺用户，我希望将我个人黑名单中的条目申请推送到系统黑名单，以便帮助其他用户识别恶意买家。

#### 验收标准

1. WHEN User 发起 Push_Request，THE System SHALL 要求提供 `evidence` 字段（订单截图描述或沟通记录文字，不少于 10 个字符），否则返回 400 Bad Request 错误。
2. WHEN User 发起 Push_Request，THE System SHALL 将申请状态设置为 `PENDING`，并记录申请人 ID、目标 Blacklist_Entry ID 和 Evidence 内容。
3. THE System SHALL 确保同一 Blacklist_Entry 在同一时间只能存在一条状态为 `PENDING` 的 Push_Request，重复提交时返回 409 Conflict 错误。
4. WHEN Admin 审核 Push_Request 并通过，THE System SHALL 将申请状态更新为 `APPROVED`，并将对应 Blacklist_Entry 的数据复制到 System_Blacklist，同时记录 `source_push_request_id`。
5. WHEN Admin 审核 Push_Request 并拒绝，THE System SHALL 将申请状态更新为 `REJECTED`，并记录 `reject_reason` 字段（不可为空）。
6. WHEN User 查询自己提交的 Push_Request 列表，THE System SHALL 返回申请状态（PENDING / APPROVED / REJECTED）和拒绝原因（如有）。
7. WHEN Push_Request 状态为 `APPROVED` 或 `REJECTED`，THE System SHALL 拒绝对该申请的重复审核操作，返回 409 Conflict 错误。

---

### 需求 6：管理员后台

**用户故事：** 作为管理员，我希望有一个独立的后台路由，集中管理系统黑名单、审核推送申请和管理用户，以便高效完成运营工作。

#### 验收标准

1. THE System SHALL 提供独立路由 `/admin`，WHEN User（非管理员）访问该路由，THE System SHALL 在前端重定向至首页，并在后端接口层返回 403 Forbidden 错误。
2. THE System SHALL 在 `/admin` 下提供以下功能模块：系统黑名单管理、推送申请审核、用户管理。
3. WHEN Admin 访问推送申请审核列表，THE System SHALL 支持按状态（PENDING / APPROVED / REJECTED）过滤，并返回分页结果。
4. WHEN Admin 执行用户管理操作（查看用户列表、启用/禁用用户），THE System SHALL 校验操作者具有 `is_admin = true` 权限。
5. THE System SHALL 在管理员后台展示 System_Blacklist 总条目数量统计。

---

### 需求 7：黑名单统计

**用户故事：** 作为烘焙店铺用户，我希望查看自己黑名单的数量统计，以便了解个人黑名单规模，同时不暴露系统黑名单的规模信息。

#### 验收标准

1. WHEN User 请求统计接口，THE System SHALL 返回当前用户 User_Blacklist 的总数及各风险等级（HIGH / MEDIUM / LOW）数量。
2. THE System SHALL 在面向普通用户的统计接口响应中不包含 System_Blacklist 的任何数量信息。
3. WHEN Admin 请求管理员统计接口，THE System SHALL 返回 System_Blacklist 总数、各风险等级数量，以及待审核 Push_Request 数量。
4. WHEN User 的 User_Blacklist 为空，THE System SHALL 返回所有计数字段均为 0 的统计结果，而非错误响应。

---

### 需求 9：通知机制

**用户故事：** 作为烘焙店铺用户，我希望在推送申请被审核后收到通知（邮件 + 站内消息），以便及时了解审核结果；作为管理员，我希望系统自动发送通知，无需手动告知申请人。

#### 验收标准

1. WHEN Admin 审核 Push_Request 并通过，THE System SHALL 通过 163 邮件服务（smtp_user=tangrui_star@163.com）向申请用户的注册邮箱发送审核通过通知邮件，邮件内容包含被推送条目的 KTT 名字和审核结论。
2. WHEN Admin 审核 Push_Request 并拒绝，THE System SHALL 向申请用户的注册邮箱发送审核拒绝通知邮件，邮件内容包含被推送条目的 KTT 名字、拒绝原因。
3. WHEN Admin 审核 Push_Request（通过或拒绝），THE System SHALL 同时在 `notifications` 表中创建一条站内消息，记录接收用户 ID、消息类型（PUSH_APPROVED / PUSH_REJECTED）、关联 Push_Request ID、消息标题、消息内容和已读状态（默认 `false`）。
4. WHEN User 查询站内消息列表，THE System SHALL 返回该用户的所有通知，按创建时间倒序排列，支持分页，并在响应中包含未读消息总数。
5. WHEN User 将某条通知标记为已读，THE System SHALL 将该通知的 `is_read` 字段更新为 `true`，并返回更新后的未读数量。
6. WHEN User 执行「全部标记已读」操作，THE System SHALL 将该用户所有 `is_read = false` 的通知批量更新为 `true`。
7. IF 邮件发送失败，THE System SHALL 记录错误日志，但不影响审核操作本身的成功响应，站内消息仍正常创建。
8. THE System SHALL 不支持用户删除通知，通知记录永久保留。

---

### 需求 8：数据迁移兼容

**用户故事：** 作为系统管理员，我希望现有 `blacklist` 表中的数据能平滑迁移到新的两级结构，以便不丢失历史数据。

#### 验收标准

1. THE System SHALL 提供数据迁移脚本，将现有 `blacklist` 表中 `created_by` 不为空的条目迁移为对应用户的 User_Blacklist 条目。
2. WHEN 迁移脚本执行完成，THE System SHALL 输出迁移成功条目数和失败条目数的统计报告。
3. IF 迁移过程中单条记录发生错误，THEN THE System SHALL 记录错误日志并继续处理其余条目，不中断整体迁移流程。
