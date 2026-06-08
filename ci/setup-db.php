<?php
/**
 * OpenCart 4.x 数据库自动安装脚本（CI 用）
 *
 * 模拟 OpenCart web 安装器流程：
 *   1. 引导 framework 常量 + 自动加载
 *   2. 创建 registry + config + loader + db
 *   3. 调用 install model → database() 创建表 + 导入种子数据 + 管理员
 *
 * 用法: php ci/setup-db.php <opencart_upload_dir>
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

// ═══ 1. 定位 OpenCart upload 目录 ═══
$opencartDir = $argv[1] ?? getcwd();
$opencartDir = realpath($opencartDir);
if (!$opencartDir) {
    fwrite(STDERR, "OpenCart 目录不存在: " . ($argv[1] ?? getcwd()) . "\n");
    exit(1);
}
echo "[setup-db] OpenCart: $opencartDir\n";

// ═══ 2. 定义 install/index.php 所需的全部常量 ═══
define('APPLICATION', 'Install');
define('HTTP_SERVER', 'http://localhost:8080/');

define('DIR_OPENCART',  $opencartDir . '/');
define('DIR_APPLICATION', DIR_OPENCART . 'install/');
define('DIR_SYSTEM',      DIR_OPENCART . 'system/');
define('DIR_EXTENSION',   DIR_OPENCART . 'extension/');
define('DIR_IMAGE',       DIR_OPENCART . 'image/');
define('DIR_STORAGE',     DIR_OPENCART . 'storage/');
define('DIR_LANGUAGE',    DIR_APPLICATION . 'language/');
define('DIR_TEMPLATE',    DIR_APPLICATION . 'view/template/');
define('DIR_CONFIG',      DIR_SYSTEM . 'config/');
define('DIR_CACHE',       DIR_STORAGE . 'cache/');
define('DIR_DOWNLOAD',    DIR_STORAGE . 'download/');
define('DIR_LOGS',        DIR_STORAGE . 'logs/');
define('DIR_SESSION',     DIR_STORAGE . 'session/');
define('DIR_UPLOAD',      DIR_STORAGE . 'upload/');

// ═══ 3. 加载 autoloader ═══
// Composer autoloader（OpenCart 4.x 的 Twig 等依赖需要）
if (is_file(DIR_OPENCART . 'vendor/autoload.php')) {
    require_once DIR_OPENCART . 'vendor/autoload.php';
}
require_once DIR_SYSTEM . 'helper/general.php';  // 提供 oc_token() 等函数
require_once DIR_SYSTEM . 'engine/autoloader.php';
require_once DIR_SYSTEM . 'engine/registry.php';

$autoloader = new \Opencart\System\Engine\Autoloader();
$autoloader->register('Opencart\\' . APPLICATION, DIR_APPLICATION);
$autoloader->register('Opencart\\Extension',          DIR_EXTENSION);
$autoloader->register('Opencart\\System',             DIR_SYSTEM);

// ═══ 4. 构建 registry（模拟 framework.php 的核心服务）════
$registry = new \Opencart\System\Engine\Registry();

// Config
$config = new \Opencart\System\Engine\Config();
$config->addPath(DIR_CONFIG . 'default.php');
$config->addPath(DIR_CONFIG . 'install.php');
$registry->set('config', $config);

// Loader — install model 需要它来加载 helper
// Loader 构造: __construct(\Opencart\System\Engine\Registry $registry)
$load = new \Opencart\System\Engine\Load($registry);
$registry->set('load', $load);

// Event — 有些 model 基类方法可能触发事件
$event = new \Opencart\System\Engine\Event($registry);
$registry->set('event', $event);

// DB — install model 内部会重新创建，但 Loader 中可能需要
$dbConfig = [
    'db_driver'   => getenv('DB_DRIVER')   ?: 'mysqli',
    'db_hostname' => getenv('DB_HOSTNAME') ?: '127.0.0.1',
    'db_username' => getenv('DB_USERNAME') ?: 'root',
    'db_password' => getenv('DB_PASSWORD') ?: 'root',
    'db_database' => getenv('DB_DATABASE') ?: 'opencart',
    'db_port'     => getenv('DB_PORT')     ?: '3306',
    'db_prefix'   => getenv('DB_PREFIX')   ?: 'oc_',
];
$db = new \Opencart\System\Library\DB(
    $dbConfig['db_driver'],
    $dbConfig['db_hostname'],
    $dbConfig['db_username'],
    $dbConfig['db_password'],
    $dbConfig['db_database'],
    $dbConfig['db_port']
);
$registry->set('db', $db);

// ═══ 5. 执行 install model ═══
echo "[setup-db] 加载 install model...\n";
require_once DIR_APPLICATION . 'model/install/install.php';

$model = new \Opencart\Install\Model\Install\Install($registry);

$installData = [
    'db_driver'   => $dbConfig['db_driver'],
    'db_hostname' => $dbConfig['db_hostname'],
    'db_username' => $dbConfig['db_username'],
    'db_password' => $dbConfig['db_password'],
    'db_database' => $dbConfig['db_database'],
    'db_port'     => $dbConfig['db_port'],
    'db_prefix'   => $dbConfig['db_prefix'],
    'username'    => getenv('ADMIN_USERNAME') ?: 'admin',
    'password'    => getenv('ADMIN_PASSWORD') ?: 'admin123',
    'email'       => getenv('ADMIN_EMAIL')    ?: 'admin@example.com',
];

echo "[setup-db] 创建数据库表 + 导入种子数据...\n";
$model->database($installData);

echo "[setup-db] ✓ OpenCart 数据库安装完成\n";
