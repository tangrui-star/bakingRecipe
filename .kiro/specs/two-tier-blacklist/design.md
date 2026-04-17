# 设计文档：两级黑名单体系

## 概述

将现有单一 `blacklist` 表升级为两级结构：**用户黑名单**（个人私有）和**系统黑名单**（全局共享）。新增推送审核流程、管理员后台、通知机制（邮件 + 站内消息）。

技术栈：FastAPI + SQLAlchemy + MySQL（后端），Vue 3 + Element Plus + Vant（前端），163 邮件服务（已有）。

---

## 架构

```mermaid
graph TD
    subgraph 前端 Vue3
        A[黑名单页 /blacklist] --> B[用户黑名单 CRUD]
        A --> C[推送申请]
        D[通知中心 /notifications] --> E[站内消息列表]
        F[管理员后台 /admin] --> G[系统黑名单管理]
        F --> H[推送申请审核]
        F --> I[用户管理]
    end

    subgraph 后端 FastAPI
        J[/api/blacklist] --> K[用户黑名单路由]
        L[/api/system-blacklist] --> M[系统黑名单路由 Admin Only]
        N[/api/push-requests] --> O[推送申请路由]
        P[/api/notifications] --> Q[通知路由]
        R[/api/admin] --> S[管理员路由]
        T[权限中间件] --> K & M & O & Q & S
    end

    subgraph 数据库 MySQL
        U[(blacklist 扩展)]
        V[(push_requests)]
        W[(notifications)]
        X[(users 新增 is_admin)]
    end

    subgraph 外部服务
        Y[163 SMTP 邮件]
    end

    前端 Vue3 --> 后端 FastAPI
    后端 FastAPI --> 数据库 MySQL
    后端 FastAPI --> Y
```

### 关键设计决策

1. **复用现有 `blacklist` 表**：新增 `blacklist_type`（USER/SYSTEM）和 `owner_id` 字段，而非拆分为两张表，降低迁移成本，保持现有查询逻辑兼容。
2. **邮件失败不阻断审核**：邮件发送异步处理（try/except），失败仅记录日志，审核操作本身正常返回。
3. **管理员不支持批量审核**：每条 Push_Request 必须单独审核，接口设计不提供批量端点。
4. **通知只增不删**：`notifications` 表记录永久保留，仅支持标记已读。

---

## 组件与接口

### 权限中间件

```python
# 两个依赖函数，注入到需要鉴权的路由
def get_current_user(...)  -> User          # 已有，验证 JWT
def require_admin(current_user = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(403, "需要管理员权限")
    return current_user
```

### 后端路由模块

| 模块文件 | 前缀 | 说明 |
|---|---|---|
| `routers/blacklist.py`（改造） | `/api/blacklist` | 用户黑名单 CRUD，需登录 |
| `routers/system_blacklist.py`（新增） | `/api/system-blacklist` | 系统黑名单 CRUD，需 Admin |
| `routers/push_requests.py`（新增） | `/api/push-requests` | 推送申请，需登录；审核需 Admin |
| `routers/notifications.py`（新增） | `/api/notifications` | 站内消息，需登录 |
| `routers/admin.py`（新增） | `/api/admin` | 管理员统计、用户管理 |

### 用户黑名单接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/blacklist` | 创建用户黑名单条目 |
| GET | `/api/blacklist` | 列表（分页、过滤、搜索） |
| GET | `/api/blacklist/statistics` | 当前用户统计 |
| GET | `/api/blacklist/{id}` | 详情 |
| PUT | `/api/blacklist/{id}` | 更新（校验 owner） |
| DELETE | `/api/blacklist/{id}` | 删除（校验 owner） |

### 系统黑名单接口（Admin Only）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/system-blacklist` | 创建系统黑名单条目 |
| GET | `/api/system-blacklist` | 列表（分页、过滤、搜索） |
| GET | `/api/system-blacklist/statistics` | 系统黑名单统计 |
| GET | `/api/system-blacklist/{id}` | 详情 |
| PUT | `/api/system-blacklist/{id}` | 更新 |
| DELETE | `/api/system-blacklist/{id}` | 删除 |

### 推送申请接口

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/push-requests` | User | 发起推送申请 |
| GET | `/api/push-requests/my` | User | 查询自己的申请列表 |
| GET | `/api/push-requests` | Admin | 查询所有申请（支持状态过滤） |
| POST | `/api/push-requests/{id}/approve` | Admin | 审核通过（单条） |
| POST | `/api/push-requests/{id}/reject` | Admin | 审核拒绝（单条，需 reject_reason） |

### 通知接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/notifications` | 获取当前用户通知列表（分页） |
| GET | `/api/notifications/unread-count` | 获取未读数量 |
| PUT | `/api/notifications/{id}/read` | 标记单条已读 |
| PUT | `/api/notifications/read-all` | 全部标记已读 |

### 管理员接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/admin/statistics` | 系统黑名单总数、各等级数、待审核数 |
| GET | `/api/admin/users` | 用户列表 |
| PUT | `/api/admin/users/{id}/toggle-active` | 启用/禁用用户 |

---

## 数据模型

### users 表变更

```sql
ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否管理员';
```

### blacklist 表变更

```sql
ALTER TABLE blacklist
  ADD COLUMN blacklist_type ENUM('USER','SYSTEM') NOT NULL DEFAULT 'USER' COMMENT '黑名单类型',
  ADD COLUMN owner_id VARCHAR(36) NULL COMMENT '用户黑名单归属用户ID（SYSTEM类型为NULL）',
  ADD COLUMN source_push_request_id INT NULL COMMENT '来源推送申请ID（仅SYSTEM类型）',
  ADD INDEX idx_blacklist_type (blacklist_type),
  ADD INDEX idx_owner_id (owner_id);
```

> 现有数据迁移：将 `created_by` 不为空的条目设置 `blacklist_type='USER'`，`owner_id=created_by`；其余设置为 `SYSTEM`。

### push_requests 表（新增）

```sql
CREATE TABLE push_requests (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  blacklist_id    INT NOT NULL COMMENT '申请推送的用户黑名单条目ID',
  applicant_id    VARCHAR(36) NOT NULL COMMENT '申请人用户ID',
  evidence        TEXT NOT NULL COMMENT '证据描述（≥10字符）',
  status          ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
  reject_reason   TEXT NULL COMMENT '拒绝原因（REJECTED时必填）',
  reviewed_by     VARCHAR(36) NULL COMMENT '审核管理员ID',
  reviewed_at     DATETIME NULL COMMENT '审核时间',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_blacklist_id (blacklist_id),
  INDEX idx_applicant_id (applicant_id),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推送申请表';
```

### notifications 表（新增）

```sql
CREATE TABLE notifications (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  user_id         VARCHAR(36) NOT NULL COMMENT '接收用户ID',
  type            ENUM('PUSH_APPROVED','PUSH_REJECTED') NOT NULL COMMENT '通知类型',
  push_request_id INT NOT NULL COMMENT '关联推送申请ID',
  title           VARCHAR(200) NOT NULL COMMENT '消息标题',
  content         TEXT NOT NULL COMMENT '消息内容',
  is_read         BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已读',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_is_read (user_id, is_read),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内通知表';
```

### SQLAlchemy 模型变更（models.py）

```python
class BlacklistType(str, enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"

class PushRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class NotificationType(str, enum.Enum):
    PUSH_APPROVED = "PUSH_APPROVED"
    PUSH_REJECTED = "PUSH_REJECTED"

# User 新增字段
is_admin = Column(Boolean, default=False, nullable=False)

# Blacklist 新增字段
blacklist_type = Column(SQLEnum(BlacklistType), default=BlacklistType.USER, nullable=False)
owner_id = Column(String(36), nullable=True)
source_push_request_id = Column(Integer, nullable=True)

class PushRequest(Base):
    __tablename__ = "push_requests"
    id = Column(Integer, primary_key=True)
    blacklist_id = Column(Integer, ForeignKey('blacklist.id'), nullable=False)
    applicant_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    evidence = Column(Text, nullable=False)
    status = Column(SQLEnum(PushRequestStatus), default=PushRequestStatus.PENDING)
    reject_reason = Column(Text, nullable=True)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    blacklist_entry = relationship("Blacklist")
    applicant = relationship("User", foreign_keys=[applicant_id])

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    push_request_id = Column(Integer, ForeignKey('push_requests.id'), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User")
    push_request = relationship("PushRequest")
```

### 订单检查结果变更

`order_screening_details.order_data`（JSON 字段）中新增 `source` 字段（`SYSTEM` / `USER`），无需 DDL 变更。

---

## 正确性属性

*属性（Property）是在系统所有合法执行路径上都应成立的特征或行为——本质上是对系统应做什么的形式化陈述。属性是人类可读规范与机器可验证正确性保证之间的桥梁。*


### 属性 1：普通用户无法访问系统黑名单接口

*对于任意* 普通用户（`is_admin=false`），调用任何系统黑名单管理接口（列表、详情、创建、更新、删除），系统都应返回 403 Forbidden。

**验证需求：1.2、3.3**

---

### 属性 2：管理员可正常访问系统黑名单接口

*对于任意* 管理员用户（`is_admin=true`），调用系统黑名单管理接口，系统应返回 200 并包含数据。

**验证需求：1.3**

---

### 属性 3：用户黑名单数据隔离

*对于任意* 两个不同用户 A 和 B，用户 A 查询黑名单列表时，结果中不应包含任何 `owner_id` 等于用户 B 的条目；用户 A 尝试更新或删除用户 B 的条目时，系统应返回 403。

**验证需求：1.4、2.3、2.4**

---

### 属性 4：创建用户黑名单条目时字段自动赋值

*对于任意* 已登录用户创建的黑名单条目，该条目的 `owner_id` 应等于当前用户 ID，`blacklist_type` 应等于 `USER`。

**验证需求：2.2**

---

### 属性 5：风险等级过滤正确性

*对于任意* 风险等级过滤参数，查询结果中所有条目的 `risk_level` 都应等于该过滤值；按关键词搜索时，所有结果的姓名或电话字段都应包含该关键词。

**验证需求：2.5**

---

### 属性 6：统计数据仅反映当前用户

*对于任意* 用户，其统计接口返回的各风险等级数量之和应等于该用户 `User_Blacklist` 的实际条目总数，且不包含其他用户或系统黑名单的数量。

**验证需求：2.7、7.1、7.2、7.4（边界：空列表时所有计数为 0）**

---

### 属性 7：双库匹配覆盖性

*对于任意* 订单数据，若系统黑名单和用户黑名单中各存在一条匹配条目，则检查结果中应包含两条命中记录（或取最高风险的一条，`source` 字段标注实际来源）。

**验证需求：4.1、4.3**

---

### 属性 8：命中结果包含合法 source 字段

*对于任意* 订单检查命中结果，`source` 字段应存在且值为 `SYSTEM` 或 `USER` 之一。

**验证需求：4.2**

---

### 属性 9：推送申请 evidence 长度校验

*对于任意* 长度小于 10 个字符的 evidence 字符串，发起推送申请应返回 400；长度 ≥ 10 的应成功创建。

**验证需求：5.1**

---

### 属性 10：同一条目不允许重复 PENDING 申请

*对于任意* 已存在 PENDING 状态申请的黑名单条目，再次提交推送申请应返回 409 Conflict。

**验证需求：5.3**

---

### 属性 11：审核通过后数据复制到系统黑名单

*对于任意* 被审核通过的 Push_Request，系统黑名单中应存在一条与原用户黑名单条目数据一致的记录，且该记录的 `source_push_request_id` 等于该申请的 ID。

**验证需求：5.4**

---

### 属性 12：已审核申请不可重复审核

*对于任意* 状态为 APPROVED 或 REJECTED 的 Push_Request，再次执行审核操作应返回 409 Conflict。

**验证需求：5.7**

---

### 属性 13：审核操作触发站内通知创建

*对于任意* 审核操作（通过或拒绝），`notifications` 表中应新增一条记录，`user_id` 等于申请人 ID，`type` 与审核结论对应，`is_read` 默认为 `false`。

**验证需求：9.3**

---

### 属性 14：通知列表按创建时间倒序

*对于任意* 用户的通知列表，返回结果中相邻两条记录的 `created_at` 应满足前者 ≥ 后者（倒序）。

**验证需求：9.4**

---

### 属性 15：标记已读后未读数减少

*对于任意* 用户，将一条未读通知标记为已读后，该通知的 `is_read` 应为 `true`，且未读总数应比操作前减少 1；执行「全部标记已读」后，未读总数应为 0。

**验证需求：9.5、9.6**

---

## 错误处理

| 场景 | HTTP 状态码 | 说明 |
|---|---|---|
| 未登录或 Token 无效 | 401 | 所有需鉴权接口 |
| 普通用户访问 Admin 接口 | 403 | 权限中间件拦截 |
| 用户操作他人黑名单条目 | 403 | owner_id 校验失败 |
| evidence 长度不足 10 字符 | 400 | 推送申请参数校验 |
| 重复提交 PENDING 申请 | 409 | 唯一性约束 |
| 重复审核已完结申请 | 409 | 状态校验 |
| 审核拒绝时 reject_reason 为空 | 400 | 参数校验 |
| 黑名单条目不存在 | 404 | 通用资源不存在 |
| 邮件发送失败 | 不影响主流程 | 记录日志，审核操作正常返回 200 |

---

## 测试策略

### 双轨测试方法

- **单元测试**：验证具体示例、边界条件和错误场景
- **属性测试**：使用 [Hypothesis](https://hypothesis.readthedocs.io/)（Python PBT 库）验证普遍性属性

两者互补，共同保证覆盖率。

### 单元测试重点

- 权限中间件：`require_admin` 对普通用户返回 403
- 邮件失败不阻断审核流程（mock SMTP 抛出异常）
- 数据迁移脚本：迁移后统计报告格式正确
- 边界：空黑名单时统计接口返回全零（对应属性 6 的边界情况）

### 属性测试配置

每个属性测试最少运行 **100 次**迭代（Hypothesis 默认 100，可通过 `@settings(max_examples=100)` 配置）。

每个属性测试必须包含注释标注对应设计属性，格式：

```python
# Feature: two-tier-blacklist, Property {N}: {属性描述}
```

### 属性测试映射

| 设计属性 | 测试函数 | PBT 模式 |
|---|---|---|
| 属性 1 | `test_user_cannot_access_system_blacklist` | 错误条件 |
| 属性 2 | `test_admin_can_access_system_blacklist` | 不变量 |
| 属性 3 | `test_user_blacklist_isolation` | 不变量 |
| 属性 4 | `test_create_sets_owner_and_type` | 不变量 |
| 属性 5 | `test_filter_returns_matching_entries` | 元变形属性 |
| 属性 6 | `test_statistics_only_counts_own_entries` | 模型测试 |
| 属性 7 | `test_dual_library_matching_coverage` | 不变量 |
| 属性 8 | `test_match_result_has_valid_source` | 不变量 |
| 属性 9 | `test_evidence_length_validation` | 错误条件 |
| 属性 10 | `test_duplicate_pending_request_rejected` | 幂等性 |
| 属性 11 | `test_approve_copies_to_system_blacklist` | 往返属性 |
| 属性 12 | `test_reviewed_request_cannot_be_reviewed_again` | 幂等性 |
| 属性 13 | `test_review_creates_notification` | 不变量 |
| 属性 14 | `test_notifications_ordered_by_created_at_desc` | 不变量 |
| 属性 15 | `test_mark_read_decreases_unread_count` | 往返属性 |

### 数据迁移测试

迁移脚本需在测试数据库上验证：
- 迁移后所有原 `created_by` 不为空的条目 `blacklist_type='USER'`，`owner_id=created_by`
- 迁移报告输出成功数和失败数
- 单条记录错误不中断整体流程

---

## 数据迁移方案

迁移脚本路径：`database/migrate_to_two_tier.py`

```
执行步骤：
1. ALTER TABLE users ADD COLUMN is_admin ...
2. ALTER TABLE blacklist ADD COLUMN blacklist_type, owner_id, source_push_request_id
3. UPDATE blacklist SET blacklist_type='USER', owner_id=created_by WHERE created_by IS NOT NULL
4. UPDATE blacklist SET blacklist_type='SYSTEM' WHERE created_by IS NULL
5. CREATE TABLE push_requests
6. CREATE TABLE notifications
7. 输出统计报告
```

迁移脚本支持 `--dry-run` 参数，仅输出将要执行的变更而不实际修改数据库。
