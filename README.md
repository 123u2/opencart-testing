# OpenCart 电商系统自动化测试框架

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![pytest](https://img.shields.io/badge/pytest-8.0+-green.svg)](https://pytest.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.16+-brightgreen.svg)](https://selenium.dev)
[![Allure](https://img.shields.io/badge/Allure-2.13+-orange.svg)](https://allurereport.org)
[![Locust](https://img.shields.io/badge/Locust-2.20+-red.svg)](https://locust.io)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-blue.svg)](https://github.com)

> 基于开源电商系统 **OpenCart 4.0.2.3** 的全方位自动化测试框架，覆盖**功能测试、接口自动化、Web UI 自动化、性能测试、安全测试**五大领域。适用于求职面试展示或学习参考。

---

## 目录

- [项目结构](#-项目结构)
- [技术架构](#-技术架构)
- [快速开始](#-快速开始)
- [测试类型详解](#-测试类型详解)
- [CI/CD 流水线](#-cicd-流水线)
- [配置说明](#-配置说明)
- [测试报告](#-测试报告)
- [技术栈](#-技术栈)
- [License](#-license)

---

## 📁 项目结构

```
opencart-testing/
├── testcases/                          # 手工测试用例（62条，含设计方法标注）
│   ├── 用户模块测试用例.md                # 注册/登录/注销 | 等价类·边界值·判定表·场景法
│   ├── 商品搜索测试用例.md                # 搜索/筛选/排序 | 等价类·边界值·场景法·安全性
│   └── 购物流程测试用例.md                # 加购/结账/支付 | 场景法·边界值·数据验证
│
├── bugs/                               # Bug 报告模板及示例
│   └── 缺陷报告模板.md                    # 含3个示例 Bug + 严重程度/优先级定义 + 生命周期
│
├── api_tests/                          # 接口自动化测试（pytest + requests + Allure）
│   ├── conftest.py                     # Fixture：API 客户端、DB 连接、购物车清理
│   ├── test_auth.py                    # 认证模块（7条：登录/登出/异常/边界）
│   ├── test_product.py                 # 商品模块（9条：CRUD/Schema 校验/搜索/边界值）
│   ├── test_cart.py                    # 购物车模块（9条：CRUD/数量/优惠券/金额计算）
│   ├── test_checkout.py                # 结账流程（4条：完整下单+DB 断言 ★核心亮点）
│   └── schemas/
│       └── product.json                # 商品 API JSON Schema（契约测试）
│
├── ui_tests/                           # Web UI 自动化测试（Selenium + Page Object）
│   ├── conftest.py                     # Fixture：多浏览器、失败截图、WebDriver 管理
│   ├── pages/                          # Page Object 层
│   │   ├── base_page.py                # 基类：显式等待·截图·日志·JS 降级 click
│   │   ├── home_page.py                # 首页（搜索·导航）
│   │   ├── product_page.py             # 搜索结果页 + 商品详情页
│   │   ├── cart_page.py                # 购物车（CRUD·优惠券·结算入口）
│   │   ├── checkout_page.py            # 结账/登录（6步流程 + 游客模式 ★核心亮点）
│   │   └── admin_page.py               # 后台管理：登录·Dashboard·商品CRUD·订单
│   └── tests/
│       ├── test_e2e_purchase.py        # 完整购物 E2E（4条 ★核心亮点）
│       └── test_admin_crud.py          # 后台测试（7条：登录·商品·订单）
│
├── performance/                        # 性能测试（Locust）
│   └── locustfile.py                   # 3类用户：已认证用户·游客·管理员（加权任务）
│
├── utils/                              # 工具层
│   ├── api_client.py                   # API 客户端：Session·Token·Allure 集成
│   └── db_helper.py                    # 数据库助手：只读查询·封装常用业务查询
│
├── ci/
│   └── setup-db.php                    # CI 数据库安装脚本（PHP）
│
├── .github/workflows/
│   └── test.yml                        # CI/CD 流水线（3 Job：API + UI + Lint）
│
├── config.py                           # 全局配置（多环境切换·API Key·DB·超时）
├── pytest.ini                          # pytest 配置（标记·日志·路径）
├── requirements.txt                    # Python 依赖
└── README.md                           # 本文件
```

---

## 🏗 技术架构

```
┌──────────────────────────────────────────────────────────────┐
│                    被测系统：OpenCart 4.0.2.3                  │
│              PHP 内置服务器 / Docker Compose 部署               │
│                       MariaDB 10.11                           │
└──────────────────────────┬───────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌───────────┐    ┌─────────────────┐    ┌────────────────┐
│ API 测试   │    │   UI 测试        │    │   性能测试      │
│ pytest +  │    │ Selenium + POM  │    │   Locust       │
│ requests  │    │ Page Object     │    │                │
│           │    │                 │    │ 3 类用户模型    │
│ 20+ 条用例 │    │ 11 条用例        │    │ 多权重任务      │
└─────┬─────┘    └───────┬─────────┘    └───────┬────────┘
      │                  │                      │
      └──────────────────┼──────────────────────┘
                         │
              ┌──────────▼──────────┐
              │     工具层           │
              │  api_client.py     │  → Session 管理·Token·Allure
              │  db_helper.py      │  → MySQL 只读查询·数据断言
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │    配置层            │
              │  config.py          │  → 环境变量·多环境切换
              │  pytest.ini         │  → 标记·日志·路径
              └─────────────────────┘
```

### 设计亮点

| 特性 | 说明 |
|------|------|
| **OpenCart 4.x 适配** | API Key 认证（非 email/password）、路由分隔符 `\|`、api_token→OCSESSID cookie |
| **DB 数据断言** | API 测试不仅验证 HTTP 响应，还直连 MySQL 验证数据真实落库 |
| **多步骤场景测试** | 结账 8 步流程用 `allure.step` 标记，报告可逐步骤追溯 |
| **Page Object 模式** | UI 元素定位与业务操作分离，变更只改一处 |
| **契约测试** | JSON Schema 校验 API 响应结构，确保接口向后兼容 |
| **失败自动截图** | UI 测试失败时自动截屏并附加到 Allure 报告 |
| **真实行为模拟** | 性能测试权重设计符合真实电商 85%浏览/15%交易比例 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <this-repo-url>
cd opencart-testing

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动被测系统

#### 方式 A：Docker Compose（推荐本地开发）

```bash
# 在 opencart 目录下启动
cd ../opencart
docker-compose up -d

# 服务地址
# 前台: http://localhost:8080
# 后台: http://localhost:8080/admin
# Adminer: http://localhost:8081
```

#### 方式 B：PHP 内置服务器（CI 模式，无需 Docker）

```bash
# CI 流水线自动完成此步骤，本地可参考 .github/workflows/test.yml
```

### 3. 配置环境变量

```bash
# 必填（可编辑 config.py 或设置环境变量）
export OPENCART_BASE_URL=http://localhost:8080
export API_USERNAME=Default
export API_KEY=<your-api-key>
export DB_HOST=localhost
export DB_PORT=13306
export DB_USER=opencart
export DB_PASSWORD=opencart
export DB_NAME=opencart

# 可选
export TEST_EMAIL=test@example.com
export TEST_PASSWORD=password
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123
```

> **注意**：Docker Compose 默认不暴露 3306 端口，如需 DB 断言需在 `docker-compose.yml` 中为 MariaDB 添加 `ports: "3306:3306"`。

### 4. 运行测试

```bash
# ── API 接口自动化 ──
pytest api_tests/ -v                          # 全部 API 测试
pytest api_tests/test_checkout.py -v          # 只跑结账流程（核心场景）
pytest api_tests/ -v -m smoke                 # 冒烟测试
pytest api_tests/ -v --alluredir=reports/allure-results  # 生成 Allure 数据

# ── Web UI 自动化 ──
pytest ui_tests/ -v                           # Chrome（默认）
pytest ui_tests/ -v --browser=firefox         # Firefox
pytest ui_tests/ -v --browser=chrome-headless # 无头模式（CI）
pytest ui_tests/ -v -m smoke                  # 冒烟测试
pytest ui_tests/ -v -m e2e                    # 仅端到端场景

# ── 性能测试 ──
cd performance
locust -f locustfile.py                       # Web UI → http://localhost:8089
locust -f locustfile.py --headless -u 100 -r 10 -t 5m  # 命令行：100用户×5分钟
```

---

## 📊 测试类型详解

### 1. 手工功能测试（62 条用例）

| 模块 | 文件 | 用例数 | 设计方法覆盖 |
|------|------|--------|-------------|
| 用户模块 | `testcases/用户模块测试用例.md` | 24 | 等价类·边界值·判定表·场景法 |
| 商品搜索 | `testcases/商品搜索测试用例.md` | 14 | 等价类·边界值·场景法·安全性 |
| 购物流程 | `testcases/购物流程测试用例.md` | 24 | 场景法·边界值·数据验证 |

### 2. API 接口自动化（20+ 条用例）

| 测试文件 | 覆盖范围 | 用例数 | 标记 |
|----------|---------|--------|------|
| `test_auth.py` | 登录成功/错误Key/空Key/不存在的用户/登出/重复登录 | 7 | `@pytest.mark.smoke` |
| `test_product.py` | 空购物车/Schema校验/添加商品/边界值/搜索/异常输入 | 9 | `@pytest.mark.smoke` |
| `test_cart.py` | 添加/修改数量/移除/清空/总计/优惠券/金额校验/负数/字符串 | 9 | `@pytest.mark.smoke` |
| `test_checkout.py` | 完整下单+DB断言/空购物车/无配送地址/数据一致性 ★ | 4 | `@pytest.mark.p0` |

**核心链路：结账流程（test_checkout.py）**

```
Step 1: 添加商品     → POST api/sale/cart|add
Step 2: 配送地址     → POST api/sale/shipping_address
Step 3: 获取配送方式 → GET  api/sale/shipping_method
Step 4: 设置配送方式 → POST api/sale/shipping_method|save
Step 5: 支付地址     → POST api/sale/payment_address
Step 6: 获取支付方式 → GET  api/sale/payment_method
Step 7: 设置支付方式 → POST api/sale/payment_method|save
Step 8: 确认订单     → POST api/sale/order|confirm
Step 9: API 断言     → 验证返回 success
Step 10: DB 断言     → SELECT * FROM oc_order ORDER BY order_id DESC LIMIT 1
```

### 3. Web UI 自动化（11 条用例）

| 测试文件 | 覆盖范围 | 用例数 | 标记 |
|----------|---------|--------|------|
| `test_e2e_purchase.py` | 搜索→详情→加购→结账→下单/购物车CRUD/空购物车/无结果搜索 | 4 | `@pytest.mark.smoke @pytest.mark.p0` |
| `test_admin_crud.py` | 管理员登录/错误密码/商品列表/商品搜索/订单列表 | 7 | `@pytest.mark.smoke` |

**Page Object 设计模式**：

```
BasePage
  ├── HomePage          — 首页（搜索·导航）
  ├── SearchResultPage  — 搜索结果页（列表·点击·无结果）
  ├── ProductDetailPage — 商品详情页（查看·加购·数量）
  ├── CartPage          — 购物车（查看·修改·清空·结账入口）
  ├── LoginPage         — 登录页
  ├── CheckoutPage      — 结账页（6步流程·游客/注册双模式）
  ├── AdminLoginPage    — 后台登录
  ├── AdminDashboardPage — 后台仪表盘
  ├── AdminProductListPage — 后台商品列表
  ├── AdminProductFormPage — 后台商品表单
  └── AdminOrderListPage — 后台订单列表
```

### 4. 性能测试（3 类用户模型）

| 用户类 | 模拟角色 | 权重分布 | 典型操作 |
|--------|---------|---------|---------|
| `EcommerceUser` | 已认证电商用户 | 浏览18:交易3 (~85%浏览) | 分类浏览·搜索·详情·加购·下单 |
| `GuestUser` | 未登录访客 | 纯浏览 | 首页·分类·详情·搜索 |
| `AdminUser` | 后台管理员 | 管理操作 | Dashboard·订单列表·商品列表 |

---

## 🔄 CI/CD 流水线

CI 流水线定义在 [test.yml](.github/workflows/test.yml)，包含 3 个 Job：

```
push / PR → ┌──────────────┐
            │ Job 1: API   │  MariaDB → Deploy OpenCart → 安装DB → API测试
            │    Tests     │  → 上传 Allure 结果
            └──────┬───────┘
                   │ (needs)
                   ▼
            ┌──────────────┐
            │ Job 2: UI    │  MariaDB → Deploy OpenCart → Chrome Headless
            │    Tests     │  → 冒烟测试
            └──────┬───────┘
                   │ (parallel)
                   ▼
            ┌──────────────┐
            │ Job 3: Lint  │  ruff check（Python 代码风格）
            └──────────────┘
```

**CI 核心特性**：
- **无需 Docker 镜像**：PHP 内置服务器直接运行 OpenCart
- **自动 DB 安装**：[ci/setup-db.php](ci/setup-db.php) 自动创建表+种子数据+管理员
- **动态测试商品选择**：自动查找无必填选项的商品（避免 option required 错误）
- **API Key 自动配置**：创建 CI 专用 API 用户 + IP 白名单
- **失败诊断**：自动 dump OpenCart 服务器日志辅助排查

---

## ⚙️ 配置说明

### config.py 配置项

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `BASE_URL` | `OPENCART_BASE_URL` | `http://localhost:8080` | OpenCart 地址 |
| `API_USERNAME` | `API_USERNAME` | `Default` | API 用户名（后台创建） |
| `API_KEY` | `API_KEY` | *(内置)* | API Key（OpenCart 4.x 认证） |
| `DEFAULT_PRODUCT_ID` | `DEFAULT_PRODUCT_ID` | `28` | 默认测试商品（无必填选项） |
| `DEFAULT_SECOND_PRODUCT_ID` | `DEFAULT_SECOND_PRODUCT_ID` | `29` | 第二测试商品 |
| `ADMIN_USERNAME` | `ADMIN_USERNAME` | `admin` | 后台管理员账号 |
| `ADMIN_PASSWORD` | `ADMIN_PASSWORD` | `admin123` | 后台管理员密码 |
| `DB_HOST` | `DB_HOST` | `localhost` | 数据库地址 |
| `DB_PORT` | `DB_PORT` | `13306` | 数据库端口 |
| `DB_USER` | `DB_USER` | `opencart` | 数据库用户 |
| `DB_PASSWORD` | `DB_PASSWORD` | `opencart` | 数据库密码 |
| `DB_NAME` | `DB_NAME` | `opencart` | 数据库名 |
| `API_TIMEOUT` | `API_TIMEOUT` | `30` | API 请求超时（秒） |
| `UI_TIMEOUT` | `UI_TIMEOUT` | `10` | UI 等待超时（秒） |

### pytest 自定义标记

| 标记 | 含义 |
|------|------|
| `@pytest.mark.smoke` | 冒烟测试 — 核心功能快速验证 |
| `@pytest.mark.regression` | 回归测试 — 全量功能验证 |
| `@pytest.mark.p0` | P0 优先级 — 阻塞级缺陷（核心链路中断） |
| `@pytest.mark.p1` | P1 优先级 — 严重缺陷（功能不可用） |
| `@pytest.mark.slow` | 耗时较长的测试 |
| `@pytest.mark.e2e` | 端到端流程测试 |
| `@pytest.mark.auth` / `cart` / `checkout` | 模块标记 |

---

## 📈 测试报告

**Allure 报告**：API 和 UI 测试均集成 Allure，请求/响应内容自动附加为附件。

```bash
# 运行测试并生成数据
pytest api_tests/ --alluredir=reports/allure-results
pytest ui_tests/ --alluredir=reports/allure-results

# 查看报告
allure serve reports/allure-results
```

**截图管理**：UI 测试失败时自动截屏，保存到 `reports/screenshots/`。

---

## 🛠 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.11+ | 全部测试脚本 |
| 测试框架 | pytest 8.0+ | 用例管理、断言、fixture |
| API 测试 | requests 2.31+ | HTTP 请求 |
| Schema 校验 | jsonschema 4.20+ | 契约测试 |
| UI 测试 | Selenium 4.16+ | 浏览器操控 |
| 驱动管理 | webdriver-manager 4.0+ | 自动下载匹配的 WebDriver |
| 性能测试 | Locust 2.20+ | 负载/压力测试 |
| 测试报告 | Allure 2.13+ | 可视化报告 |
| 数据库 | PyMySQL 1.1+ | MySQL 查询/数据断言 |
| Mock 数据 | Faker 22.0+ | 生成随机测试数据 |
| 配置管理 | python-dotenv 1.0+ | .env 文件加载 |
| CI/CD | GitHub Actions | 3 Job 自动化流水线 |
| 代码检查 | ruff | Python 代码风格 |
| 被测环境 | Docker Compose / PHP 内置服务器 | 一键部署/零依赖部署 |
| 数据库 | MariaDB 10.11 | 被测系统数据存储 |
| 被测系统 | OpenCart 4.0.2.3 | 开源 PHP 电商系统 |

---

## 📝 License

MIT — 仅供学习和求职展示使用。
