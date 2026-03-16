# 技术架构文档 — Dropship Import MCP

## 1. 项目定位

**Dropship Import MCP** 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的服务器，为 AI Agent 提供**一件代发商品导入 → 编辑 → 推送到店铺**的完整工作流。

Agent 只需调用 7 个高层工具，即可完成从供应商 URL 到店铺上架的全过程，无需了解底层平台 API 细节。

---

## 2. 目录结构

```
dropship-import-mcp/
├── server.py                     # MCP 服务入口 (stdio transport)
├── dropship_import_mcp/          # 核心包 — 协议层
│   ├── provider.py               # ImportProvider 抽象基类 + 动态加载
│   ├── mock_provider.py          # 离线 Mock Provider（开发/演示）
│   ├── service.py                # ImportFlowService — 工具编排层
│   ├── job_store.py              # 作业持久化 (FileJobStore)
│   ├── push_options.py           # push_options 校验与归一化
│   ├── resolver.py               # 来源 URL 解析
│   └── rules.py                  # 规则引擎（定价/内容/图片）
├── dsers_provider/               # DSers 适配层
│   ├── __init__.py
│   └── provider.py               # PrivateDsersProvider — ImportProvider 实现
├── vendor-dsers/                 # DSers 平台 API 封装库
│   ├── dsers_mcp_base/           # 基础设施：认证、HTTP 客户端、配置
│   │   ├── auth.py
│   │   ├── client.py
│   │   └── config.py
│   ├── dsers_account.py          # 账户与店铺管理
│   ├── dsers_product.py          # 商品导入、推送、状态查询
│   ├── dsers_settings.py         # 运费模板、运输配置
│   ├── dsers_order.py            # 订单管理
│   └── dsers_logistics.py        # 物流追踪
├── smoke_mock.py                 # Mock Provider 冒烟测试
├── smoke_dsers.py                # DSers Provider 冒烟测试
├── SKILL.md                      # AI Agent 使用指南
├── ARCHITECTURE.md               # 本文档
├── .env.example                  # 环境变量模板
├── .gitignore
├── requirements.txt
└── LICENSE
```

---

## 3. 三层架构

```
┌─────────────────────────────────────────────┐
│  MCP Client (Claude / Cursor / Agent)       │
└──────────────────┬──────────────────────────┘
                   │ MCP Protocol (stdio)
┌──────────────────▼──────────────────────────┐
│  server.py + dropship_import_mcp/           │
│  ┌────────────────────────────────────────┐ │
│  │  ImportFlowService (协议编排层)          │ │
│  │  ├─ Rules Engine    规则校验/应用       │ │
│  │  ├─ Push Options    推送参数归一化      │ │
│  │  └─ Job Store       作业状态持久化      │ │
│  └──────────────┬─────────────────────────┘ │
│                 │ ImportProvider ABC         │
│  ┌──────────────▼─────────────────────────┐ │
│  │  dsers_provider/ (适配层)               │ │
│  │  ├─ prepare_candidate()                │ │
│  │  ├─ commit_candidate()                 │ │
│  │  └─ get_rule_capabilities()            │ │
│  └──────────────┬─────────────────────────┘ │
│                 │ vendor library (sys.path)  │
│  ┌──────────────▼─────────────────────────┐ │
│  │  vendor-dsers/ (平台 API 库)            │ │
│  │  ├─ dsers_mcp_base/  基础设施           │ │
│  │  ├─ dsers_product    商品 API           │ │
│  │  ├─ dsers_account    账户 API           │ │
│  │  └─ dsers_settings   配置 API           │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

| 层级 | 目录 | 职责 | 可替换性 |
|------|------|------|----------|
| **协议层** | `dropship_import_mcp/` | 定义 7 个 MCP 工具，编排 prepare → review → push 流程 | 固定 |
| **适配层** | `dsers_provider/` | 实现 `ImportProvider` 接口，转换平台无关请求为平台特定调用 | 可替换为其他平台 |
| **平台库** | `vendor-dsers/` | 封装底层 HTTP API（认证、商品、订单、物流） | 随适配层一同替换 |

---

## 4. 工具流程

### 4.1 完整推送流程

```
Agent                              MCP Server
  │                                    │
  ├─ get_rule_capabilities() ────────► │ 返回支持的规则/店铺/渠道
  │                                    │
  ├─ validate_rules({rules}) ────────► │ 校验规则结构
  │                                    │
  ├─ prepare_import_candidate() ─────► │ 解析 URL → 导入 → 应用规则
  │                                    │ 返回 job_id + draft 预览
  │                                    │
  ├─ get_import_preview(job_id) ─────► │ 查看编辑后的商品草稿
  │                                    │
  ├─ set_product_visibility() ───────► │ (可选) 调整可见性
  │                                    │
  ├─ confirm_push_to_store() ────────► │ 提交推送 → 轮询状态
  │                                    │ 返回 completed / failed
  │                                    │
  └─ get_job_status(job_id) ─────────► │ 查询最终状态
```

### 4.2 工具一览

| 工具名 | 说明 | 必需参数 |
|--------|------|----------|
| `get_rule_capabilities` | 查询当前 Provider 支持的规则族和推送选项 | — |
| `validate_rules` | 校验规则结构，返回归一化后的规则对象 | `rules` |
| `prepare_import_candidate` | 从供应商 URL 导入并生成预览 | `source_url` |
| `get_import_preview` | 查看已准备的作业预览 | `job_id` |
| `set_product_visibility` | 修改可见性 (backend_only / sell_immediately) | `job_id`, `visibility_mode` |
| `confirm_push_to_store` | 确认推送到目标店铺 | `job_id` |
| `get_job_status` | 查询推送状态 | `job_id` |

---

## 5. Provider 扩展机制

### 5.1 ImportProvider 接口

```python
class ImportProvider(ABC):
    name = "abstract"

    async def get_rule_capabilities(self, target_store=None) -> dict: ...
    async def prepare_candidate(self, source_url, source_hint, country) -> dict: ...
    async def commit_candidate(self, provider_state, draft, target_store,
                                visibility_mode, push_options) -> dict: ...
```

### 5.2 新增 Provider

1. 创建 `your_provider/provider.py`，实现 `ImportProvider` 的三个方法
2. 暴露 `build_provider()` 工厂函数
3. 设置环境变量 `IMPORT_PROVIDER_MODULE=your_provider.provider`

### 5.3 Provider 加载机制

`load_provider()` 通过 `IMPORT_PROVIDER_MODULE` 环境变量动态加载指定模块，调用其 `build_provider()` 工厂函数返回实例。默认加载 `dsers_provider.provider`。

---

## 6. DSers 适配层详解

### 6.1 认证流程

```
DSersConfig.from_env() → email/password
        │
DSersClient.__init__() → 尝试从 session_file 恢复
        │
首次/过期 → POST /passport/login → 获取 session_id → 缓存到 session_file
        │
后续请求 → Bearer {session_id} header
```

### 6.2 vendor-dsers 动态加载

`PrivateDsersProvider.__init__()` 将 `vendor-dsers/` 加入 `sys.path`，然后通过 `importlib` 动态加载各业务模块的 `register()` 函数获取 handler。

### 6.3 Shipping Profile 自动附加

推送时自动处理 Shopify Delivery Profile：
1. 先尝试 API 查询 `dsers_get_store_shipping_profile`
2. API 返回空则回退到 `push_options.store_shipping_profile`
3. 均无则发出警告（推送可能因 "shipping profile not found" 失败）

---

## 7. Push Options

| 选项 | 类型 | 说明 |
|------|------|------|
| `publish_to_online_store` | `bool` | 是否发布到在线店铺 |
| `only_push_specifications` | `bool` | 仅推送规格数据 |
| `image_strategy` | `str` | `selected_only` / `all_available` |
| `pricing_rule_behavior` | `str` | `keep_manual` / `apply_store_pricing_rule` |
| `auto_inventory_update` | `bool` | 自动同步库存 |
| `auto_price_update` | `bool` | 自动同步价格 |
| `sales_channels` | `list` | 销售渠道列表 |
| `store_shipping_profile` | `list` | 平台 Delivery Profile 绑定 (fallback) |

---

## 8. 本地开发

### 8.1 环境搭建

```bash
# 克隆仓库
git clone <repo-url> && cd dropship-import-mcp

# 创建虚拟环境
python3 -m venv .venv && source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的凭据
```

### 8.2 冒烟测试

```bash
# Mock Provider（离线，无需凭据）
python smoke_mock.py

# DSers Provider（需要 .env 中的凭据）
python smoke_dsers.py

# 带实际导入的冒烟测试
SAMPLE_IMPORT_URL="https://www.aliexpress.com/item/xxx.html" python smoke_dsers.py
```

### 8.3 作为 MCP 服务器运行

```bash
python server.py
```

在 Cursor 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "dropship-import": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/dropship-import-mcp"
    }
  }
}
```

---

## 9. 安全注意事项

- **`.env` 文件绝不提交到 Git** — 已在 `.gitignore` 中排除
- **Session 缓存文件**（`.session-cache/`、`.session.json`）已在 `.gitignore` 中排除
- 凭据通过环境变量传入，代码中无硬编码
- `vendor-dsers/` 中的 API 调用全部通过 `DSersClient` 统一管理 session

---

## 10. 已知限制 & 迭代计划

| 状态 | 说明 |
|------|------|
| ⚠️ 当前 | 测试环境 API 地址 (`DSERS_ENV=test`) |
| ⚠️ 当前 | `store_shipping_profile` API 在部分环境返回空，需 push_options fallback |
| 🔜 后续 | 切换到生产 API |
| 🔜 后续 | 支持更多平台 Provider（非 DSers） |
| 🔜 后续 | 支持批量导入 |
| 🔜 后续 | 规则引擎增加 tag 编辑支持 |
