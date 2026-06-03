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
