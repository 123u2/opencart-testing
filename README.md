# OpenCart 电商系统自动化测试框架

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![pytest](https://img.shields.io/badge/pytest-8.0+-green.svg)](https://pytest.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.16+-brightgreen.svg)](https://selenium.dev)
[![Allure](https://img.shields.io/badge/Allure-2.13+-orange.svg)](https://allurereport.org)
[![Locust](https://img.shields.io/badge/Locust-2.20+-red.svg)](https://locust.io)

> 基于开源电商系统 OpenCart 的全方位自动化测试框架，覆盖**功能测试、接口自动化、Web UI 自动化、性能测试**四大领域。

---

## 📁 项目结构

```
opencart-testing/
├── testcases/                   # 手工测试用例（含设计方法标注）
│   ├── 用户模块测试用例.md        # 24条用例 | 等价类·边界值·判定表·场景法
│   ├── 商品搜索测试用例.md        # 14条用例 | 等价类·边界值·场景法·安全性
│   └── 购物流程测试用例.md        # 24条用例 | 场景法·边界值·数据验证
├── bugs/                        # Bug 报告模板及示例
│   └── 缺陷报告模板.md
├── api_tests/                   # 接口自动化（pytest + requests）
│   ├── test_auth.py             # 认证模块（登录/登出/Token管理）
│   ├── test_product.py          # 商品模块（添加/Schema校验/边界值）
│   ├── test_cart.py             # 购物车模块（CRUD/金额计算）
│   └── test_checkout.py         # 结账流程（多步骤链路 + DB断言）★核心亮点
├── ui_tests/                    # Web UI 自动化（Selenium + Page Object）
│   ├── pages/                   # Page Object 层
│   │   ├── base_page.py         # 基类（等待策略·截图·日志）
│   │   ├── home_page.py         # 首页
│   │   ├── product_page.py      # 商品搜索/详情
│   │   ├── cart_page.py         # 购物车
│   │   └── checkout_page.py     # 结账/登录
│   └── tests/
│       ├── test_e2e_purchase.py # 完整购物流程 E2E ★核心亮点
│       └── test_admin_crud.py   # 后台管理
├── performance/                 # 性能测试（Locust）
│   └── locustfile.py            # 加权任务模拟真实用户行为
├── utils/                       # 工具层
│   ├── api_client.py            # API 客户端（Session·Token·Allure集成）
│   └── db_helper.py             # 数据库助手（直连 MySQL 做数据断言）
├── .github/workflows/
│   └── test.yml                 # CI/CD 流水线（GitHub Actions）
├── config.py                    # 全局配置（多环境切换）
├── pytest.ini                   # pytest 配置
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```

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

### 2. 启动被测系统（OpenCart + MariaDB）

```bash
# 使用 Docker Compose 一键启动（需要先在 opencart 目录下）
cd ../opencart
docker-compose up -d

# 等待启动完成后访问
# 前台: http://localhost:8080
# 后台: http://localhost:8080/admin
# 数据库管理: http://localhost:8081 (Adminer)
```

### 3. 修改配置

编辑 `config.py` 或设置环境变量：

```bash
# Windows
set OPENCART_BASE_URL=http://localhost:8080
set TEST_EMAIL=test@example.com
set TEST_PASSWORD=password

# Mac/Linux
export OPENCART_BASE_URL=http://localhost:8080
export TEST_EMAIL=test@example.com
export TEST_PASSWORD=password
```

### 4. 运行测试

```bash
# ── API 接口自动化 ──
pytest api_tests/ -v                          # 运行全部 API 测试
pytest api_tests/test_checkout.py -v          # 只跑结账流程
pytest api_tests/ -v --alluredir=reports/allure-results  # 生成 Allure 数据

# ── Web UI 自动化 ──
pytest ui_tests/ -v                           # Chrome (默认)
pytest ui_tests/ -v --browser=firefox         # Firefox
pytest ui_tests/ -v --browser=chrome-headless # 无头模式 (CI用)
pytest ui_tests/ -v -m smoke                  # 只跑冒烟测试

# ── 性能测试 ──
cd performance
locust -f locustfile.py                       # 启动 Locust Web UI → http://localhost:8089
locust -f locustfile.py --headless -u 100 -t 5m  # 命令行模式：100并发×5分钟

# ── 查看 Allure 报告 ──
allure serve reports/allure-results
```

---

## 📊 测试概览

| 测试类型 | 框架/工具 | 用例数 | 覆盖范围 |
|----------|----------|--------|---------|
| 手工功能测试 | Markdown/Excel | 62条 | 用户·搜索·购物·下单 |
| API 接口自动化 | pytest + requests + Allure | 20+条 | 认证·商品·购物车·结账 |
| Web UI 自动化 | Selenium + Page Object | 5+条 | 搜索→下单 E2E + 后台 |
| 性能测试 | Locust | 2类用户 | 浏览·搜索·加购·详情 |

### 测试用例设计方法覆盖

| 方法 | 应用示例 | 用例数 |
|------|---------|--------|
| 等价类划分 | 邮箱输入、数量输入、搜索关键词 | 24 |
| 边界值分析 | 购物车数量(0,1,100)、密码长度(3,4,20,21) | 10 |
| 判定表 | 登录组合(用户名×密码×验证码) | 1组(6列) |
| 场景法 | 完整购物流程、密码找回、注册流程 | 21 |
| 探索性 | 登出后退、防滥用 | 3 |

---

## 🎯 核心技术亮点（面试展开讲）

### 1. API 客户端封装 (`utils/api_client.py`)
- `requests.Session()` 自动管理 Cookie，保持登录态
- 登录后 Token 自动注入所有后续请求的 Header
- 统一异常处理 + 请求/响应日志
- Allure 集成：每个请求自动附加到测试报告

### 2. 结账多步骤链路测试 (`api_tests/test_checkout.py`)
- 13步顺序依赖：登录→客户上下文→添加商品→配送地址→配送方式→支付地址→支付方式→确认
- 每步用 `allure.step` 标记，报告中可视化流程
- **数据库断言**：API 返回成功后直连 MySQL 验证订单真实入库
- 异常场景覆盖：空购物车确认、跳过配送地址、下单后购物车清空

### 3. Page Object 模式 (`ui_tests/pages/`)
- `BasePage` 统一等待策略（显式等待）、元素操作、失败截图
- 元素定位与业务逻辑分离 — UI 变更只需改定位器
- 失败自动截图 + Allure 附件

### 4. Locust 性能测试 (`performance/locustfile.py`)
- `@task(权重)` 模拟真实用户行为分布（浏览90% / 下单10%）
- `between(1,3)` 模拟用户思考时间
- 多用户类：`EcommerceUser`(登录) + `GuestUser`(未登录)

---

## 📋 简历项目描述

```
项目名称：OpenCart 电商系统自动化测试框架
项目周期：4周（独立完成）
技术栈：Python + pytest + Selenium + requests + Locust + Allure + Docker + GitHub Actions

项目描述：
基于开源电商系统 OpenCart，从零搭建了一套完整的自动化测试框架，
覆盖功能测试、接口自动化、Web UI 自动化、性能测试四大领域。

主要职责：
1. 独立设计 60+ 条功能测试用例，覆盖等价类、边界值、判定表、场景法等设计方法
2. 基于 pytest + requests 搭建接口自动化框架，封装 API Client 实现 Session/Token
   管理，核心业务（认证、商品、购物车、结账流程）自动化覆盖率 100%
3. 基于 Selenium + Page Object 模式构建 UI 自动化框架，实现失败自动截图、
   Allure 报告集成，覆盖搜索→下单完整用户旅程
4. 使用 Locust 完成性能测试，设计加权 task 模拟真实用户行为，出具性能分析报告
5. 配置 GitHub Actions CI 流水线，实现代码提交自动触发测试

项目成果：
- 自动化用例 25+ 条，核心链路 E2E 执行时间 < 3 分钟
- Allure 可视化测试报告，可追溯每次执行的详细结果
- 框架结构清晰，README 完善，可直接用于团队协作
```

---

## 🎤 面试常见问题 & 回答要点

| 问题 | 回答方向 |
|------|---------|
| "你怎么设计测试用例的？" | 展示 testcases/ 目录中的用例文档，讲等价类/边界值/判定表/场景法的应用实例 |
| "接口自动化框架怎么搭的？" | 打开 api_tests/，讲封装设计（api_client→conftest→test_*.py 三层架构） |
| "Page Object 模式怎么用的？" | 打开 ui_tests/pages/，讲 BasePage 封装了什么、为什么每个页面一个类 |
| "结账流程怎么测的？" | 展示 test_checkout.py，讲多步骤顺序依赖、DB断言、异常场景 |
| "性能测试关注什么？" | 打开 locustfile.py，讲 task 权重设计、并发阶梯、响应时间/错误率/TPS |
| "遇到过什么困难？" | 结账 API 多步骤间 token 传递；元素动态加载需要显式等待；数据隔离 |
| "Allure 报告怎么用？" | 展示 allure.step、allure.attach、报告趋势图 |
| "CI/CD 怎么配的？" | 打开 .github/workflows/test.yml，讲 push 触发→装依赖→跑测试→上传报告 |

---

## 🛠 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.11+ | 全部测试脚本 |
| 测试框架 | pytest 8.0+ | 用例管理、断言、fixture |
| API 测试 | requests 2.31+ | HTTP 请求 |
| UI 测试 | Selenium 4.16+ | 浏览器操控 |
| 驱动管理 | webdriver-manager | 自动下载匹配的 WebDriver |
| 性能测试 | Locust 2.20+ | 负载/压力测试 |
| 测试报告 | Allure 2.13+ | 可视化报告 |
| 数据库 | PyMySQL 1.1+ | 数据断言 |
| CI/CD | GitHub Actions | 自动化流水线 |
| 环境 | Docker Compose | 一键部署被测系统 |

---

## 📝 License

MIT — 仅供学习和求职展示使用。
