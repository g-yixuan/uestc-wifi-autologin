import atexit
import os
import shutil
import sys
import time
import traceback
from datetime import datetime

import requests
import yaml

GATEWAY_BASE_URL = "http://2.2.2.3"
LOGIN_URL = f"{GATEWAY_BASE_URL}/ac_portal/login.php"
NETWORK_CHECK_URL = "http://www.baidu.com"
CONFIG_FILE_NAME = "account_config.yaml"
EXAMPLE_CONFIG_FILE_NAME = "account_config.example.yaml"
ERROR_LOG_FILE_NAME = "error.log"
MUTEX_NAME = "Local\\UESTC_WIFI_AUTOLOGIN_SINGLE_INSTANCE"
PLACEHOLDER_USERNAME = "这里填写你的账号"
PLACEHOLDER_PASSWORD = "这里填写你的密码"

NETWORK_CHECK_TIMEOUT_SECONDS = 2
GATEWAY_CHECK_TIMEOUT_SECONDS = 1
OFFLINE_POLL_INTERVAL_SECONDS = 1
ONLINE_POLL_INTERVAL_SECONDS = 20
POST_LOGIN_WAIT_SECONDS = 8

PROXIES = {"http": None, "https": None}

_MUTEX_HANDLE = None


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def default_config_template():
    return """# 校园网自动登录配置文件
# 请在下方填写你的真实账号和密码（冒号后保留一个空格）

username: 这里填写你的账号
password: 这里填写你的密码
"""


def write_error_log(base_dir, title, details=""):
    log_path = os.path.join(base_dir, ERROR_LOG_FILE_NAME)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {title}\n")
        if details:
            f.write(f"{details}\n")
        f.write("-" * 80 + "\n")
    return log_path


def has_console():
    return (
        sys.stdin is not None
        and sys.stdout is not None
        and hasattr(sys.stdin, "isatty")
        and hasattr(sys.stdout, "isatty")
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    )


def wait_before_exit():
    if not has_console():
        return

    print("\n按任意键退出窗口...")
    try:
        if os.name == "nt":
            os.system("pause >nul")
        else:
            input("按回车退出...")
    except Exception:
        try:
            input("按回车退出...")
        except EOFError:
            pass


def fail_and_exit(base_dir, message, details=""):
    print(f"错误: {message}")
    log_path = write_error_log(base_dir, message, details)
    print(f"详细错误已写入: {log_path}")
    wait_before_exit()
    raise SystemExit(1)


def release_single_instance():
    global _MUTEX_HANDLE
    if _MUTEX_HANDLE is None or os.name != "nt":
        return

    try:
        import ctypes

        ctypes.windll.kernel32.CloseHandle(_MUTEX_HANDLE)
    except Exception:
        pass

    _MUTEX_HANDLE = None


def ensure_single_instance(base_dir):
    global _MUTEX_HANDLE

    if os.name != "nt":
        return

    try:
        import ctypes
    except Exception as exc:
        fail_and_exit(base_dir, "加载互斥锁模块失败。", str(exc))

    ERROR_ALREADY_EXISTS = 183
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        err_code = ctypes.windll.kernel32.GetLastError()
        fail_and_exit(base_dir, "创建单实例互斥锁失败。", f"WinError={err_code}")

    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        ctypes.windll.kernel32.CloseHandle(handle)
        message = "程序已在运行，本次启动已退出。"
        if has_console():
            print(message)
            wait_before_exit()
        else:
            write_error_log(base_dir, message)
        raise SystemExit(0)

    _MUTEX_HANDLE = handle
    atexit.register(release_single_instance)


def rc4_encrypt(password, key):
    s_box = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s_box[i] + ord(key[i % len(key)])) % 256
        s_box[i], s_box[j] = s_box[j], s_box[i]

    i = j = 0
    result = []
    for char in password:
        i = (i + 1) % 256
        j = (j + s_box[i]) % 256
        s_box[i], s_box[j] = s_box[j], s_box[i]
        k = s_box[(s_box[i] + s_box[j]) % 256]
        result.append(f"{ord(char) ^ k:02x}")
    return "".join(result)


def check_network():
    try:
        response = requests.get(
            NETWORK_CHECK_URL,
            proxies=PROXIES,
            timeout=NETWORK_CHECK_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        return response.status_code == 200 and "baidu" in response.text.lower()
    except requests.exceptions.RequestException:
        return False


def check_gateway():
    try:
        requests.get(
            GATEWAY_BASE_URL,
            proxies=PROXIES,
            timeout=GATEWAY_CHECK_TIMEOUT_SECONDS,
        )
        return True
    except requests.exceptions.RequestException:
        return False


def do_login(username, password):
    current_timestamp = str(int(time.time() * 1000))
    encrypted_pwd = rc4_encrypt(password, current_timestamp)

    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": GATEWAY_BASE_URL,
        "Referer": (
            f"{GATEWAY_BASE_URL}/ac_portal/20210120210326/pc.html"
            "?template=20210120210326&tabs=pwd&vlanid=0"
            "&url=http://www.msftconnecttest.com%2fredirect"
        ),
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/146.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }

    data = {
        "opr": "pwdLogin",
        "userName": username,
        "pwd": encrypted_pwd,
        "auth_tag": current_timestamp,
        "rememberPwd": "1",
    }

    try:
        response = requests.post(
            LOGIN_URL,
            headers=headers,
            data=data,
            proxies=PROXIES,
            timeout=5,
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 登录请求状态码: {response.status_code}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 服务端返回: {response.text}")
    except Exception as exc:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 登录异常: {exc}")


def ensure_config_exists(base_dir):
    config_file = os.path.join(base_dir, CONFIG_FILE_NAME)
    example_config_file = os.path.join(base_dir, EXAMPLE_CONFIG_FILE_NAME)

    if os.path.exists(config_file):
        return config_file

    print("未找到 account_config.yaml，正在初始化配置文件...")
    try:
        if os.path.exists(example_config_file):
            shutil.copyfile(example_config_file, config_file)
            print("已从 account_config.example.yaml 生成 account_config.yaml。")
        else:
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(default_config_template())
            print("已自动生成 account_config.yaml。")
    except OSError as exc:
        fail_and_exit(base_dir, "生成配置文件失败。", str(exc))

    fail_and_exit(base_dir, "请先编辑 account_config.yaml 填写账号和密码，然后重新运行。")
    return config_file


def load_credentials(base_dir):
    config_file = ensure_config_exists(base_dir)
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as exc:
        fail_and_exit(base_dir, "读取 account_config.yaml 失败。", str(exc))

    if not isinstance(config, dict):
        fail_and_exit(base_dir, "account_config.yaml 格式错误，必须是 key-value 结构。")

    username = str(config.get("username", "")).strip()
    password = str(config.get("password", "")).strip()
    if username in ("", PLACEHOLDER_USERNAME) or password in ("", PLACEHOLDER_PASSWORD):
        fail_and_exit(base_dir, "account_config.yaml 里账号或密码未正确填写。")

    return username, password


def run_loop(username, password):
    print(f"校园网自动登录守护进程已启动（当前账号: {username}）")
    last_state = None

    while True:
        if not check_gateway():
            if last_state != "offline":
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 未连接校园 Wi-Fi，等待中...")
                last_state = "offline"
            time.sleep(OFFLINE_POLL_INTERVAL_SECONDS)
            continue

        if check_network():
            if last_state != "online":
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 网络正常，继续巡检...")
                last_state = "online"
            time.sleep(ONLINE_POLL_INTERVAL_SECONDS)
            continue

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现校园网，正在自动登录...")
        do_login(username, password)
        last_state = "login"
        time.sleep(POST_LOGIN_WAIT_SECONDS)


def main():
    base_dir = get_base_dir()
    ensure_single_instance(base_dir)
    username, password = load_credentials(base_dir)
    run_loop(username, password)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n已手动停止程序。")
        wait_before_exit()
    except Exception:
        base_dir = get_base_dir()
        tb = traceback.format_exc()
        log_path = write_error_log(base_dir, "未处理异常", tb)
        print("程序发生未处理异常。")
        print(f"详细错误已写入: {log_path}")
        print(tb)
        wait_before_exit()
        raise SystemExit(1)
