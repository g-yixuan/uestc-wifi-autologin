import os
import shutil
import sys
import time
import traceback
from datetime import datetime

import requests
import yaml

LOGIN_URL = "http://2.2.2.3/ac_portal/login.php"
CONFIG_FILE_NAME = "account_config.yaml"
EXAMPLE_CONFIG_FILE_NAME = "account_config.example.yaml"
ERROR_LOG_FILE_NAME = "error.log"

# Keep placeholders in escaped form to avoid source encoding issues.
PLACEHOLDER_USERNAME = "\u8fd9\u91cc\u586b\u5199\u4f60\u7684\u8d26\u53f7"
PLACEHOLDER_PASSWORD = "\u8fd9\u91cc\u586b\u5199\u4f60\u7684\u5bc6\u7801"


def get_base_dir():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def default_config_template():
    return """# 校园网自动登录配置文件
# 请在下方填写你的真实账号和密码（注意：冒号后面必须保留一个空格）

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


def wait_before_exit():
    print("\n按任意键退出窗口...")
    paused = False

    # Prefer Windows pause command for double-click launched EXE.
    if os.name == "nt":
        try:
            paused = os.system("pause >nul") == 0
        except Exception:
            paused = False

    if paused:
        return

    try:
        input("按回车键退出...")
    except EOFError:
        # Last-resort fallback when stdin is unavailable.
        time.sleep(15)


def fail_and_exit(base_dir, message, details=""):
    print(f"错误: {message}")
    log_path = write_error_log(base_dir, message, details)
    print(f"详细错误已写入: {log_path}")
    wait_before_exit()
    raise SystemExit(1)


def rc4_encrypt(pwd, key):
    s_box = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s_box[i] + ord(key[i % len(key)])) % 256
        s_box[i], s_box[j] = s_box[j], s_box[i]

    i = j = 0
    result = []
    for char in pwd:
        i = (i + 1) % 256
        j = (j + s_box[i]) % 256
        s_box[i], s_box[j] = s_box[j], s_box[i]
        k = s_box[(s_box[i] + s_box[j]) % 256]
        result.append(f"{ord(char) ^ k:02x}")
    return "".join(result)


def check_network():
    try:
        proxies = {"http": None, "https": None}
        response = requests.get(
            "http://www.baidu.com",
            proxies=proxies,
            timeout=5,
            allow_redirects=True,
        )
        return response.status_code == 200 and "baidu" in response.text.lower()
    except requests.exceptions.RequestException:
        return False


def check_gateway():
    try:
        proxies = {"http": None, "https": None}
        requests.get("http://2.2.2.3", proxies=proxies, timeout=2)
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
        "Origin": "http://2.2.2.3",
        "Referer": "http://2.2.2.3/ac_portal/20210120210326/pc.html?template=20210120210326&tabs=pwd&vlanid=0&url=http://www.msftconnecttest.com%2fredirect",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    data = {
        "opr": "pwdLogin",
        "userName": username,
        "pwd": encrypted_pwd,
        "auth_tag": current_timestamp,
        "rememberPwd": "1",
    }

    proxies = {"http": None, "https": None}
    try:
        response = requests.post(
            LOGIN_URL,
            headers=headers,
            data=data,
            proxies=proxies,
            timeout=5,
        )
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] 发送登录请求，状态码: {response.status_code}"
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 服务端返回: {response.text}")
    except Exception as exc:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 登录异常: {exc}")


def load_credentials(base_dir):
    config_file = os.path.join(base_dir, CONFIG_FILE_NAME)
    example_config_file = os.path.join(base_dir, EXAMPLE_CONFIG_FILE_NAME)

    if not os.path.exists(config_file):
        print("未找到 account_config.yaml，正在初始化配置文件...")
        try:
            if os.path.exists(example_config_file):
                shutil.copyfile(example_config_file, config_file)
                print("已从 account_config.example.yaml 生成 account_config.yaml。")
            else:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(default_config_template())
                print("已自动生成 account_config.yaml。")
            fail_and_exit(
                base_dir,
                "请先编辑 account_config.yaml 填写账号和密码，然后重新运行。",
            )
        except OSError as exc:
            fail_and_exit(base_dir, "生成配置文件失败。", str(exc))

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
    while True:
        if not check_network():
            if check_gateway():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现校园网，正在自动登录...")
                do_login(username, password)
                time.sleep(8)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 未连接校园 Wi-Fi，等待中...")
                time.sleep(15)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 网络正常，继续巡检...")
            time.sleep(30)


def main():
    base_dir = get_base_dir()
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
