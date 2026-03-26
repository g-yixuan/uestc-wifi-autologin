import requests
import time
from datetime import datetime
import os   # 【新增】用来操作文件路径
import sys
import yaml

LOGIN_URL = "http://2.2.2.3/ac_portal/login.php"

def rc4_encrypt(pwd, key):
    # [原来的加密代码不变]
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + ord(key[i % len(key)])) % 256
        S[i], S[j] = S[j], S[i]

    i = j = 0
    res = []
    for char in pwd:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        res.append(f"{ord(char) ^ k:02x}")
    return "".join(res)

def check_network():
    """检测是否能连接外网"""
    try:
        proxies = {"http": None, "https": None}
        response = requests.get(
            "http://www.baidu.com",
            proxies=proxies,
            timeout=5,
            allow_redirects=True
        )
        if response.status_code == 200 and "baidu" in response.text.lower():
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def check_gateway():
    """检测是否连上了校园网 Wi-Fi (网关是否可达)"""
    try:
        # 只请求一下网关IP，看看能不能通。通了说明在学校，不通说明连的是别的网或者没网
        proxies = {"http": None, "https": None}
        requests.get("http://2.2.2.3", proxies=proxies, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def do_login(username, password):
    """伪装浏览器执行动态加密登录"""
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
        "X-Requested-With": "XMLHttpRequest"
    }

    data = {
        "opr": "pwdLogin",
        "userName": username,
        "pwd": encrypted_pwd,
        "auth_tag": current_timestamp,
        "rememberPwd": "1"
    }

    proxies = {"http": None, "https": None}

    try:
        response = requests.post(LOGIN_URL, headers=headers, data=data, proxies=proxies, timeout=5)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送登录请求, 状态码: {response.status_code}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 服务器返回信息: {response.text}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 登录异常: {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    config_file = os.path.join(current_dir, "account_config.yaml")

    # 1. 检查有没有 account_config.yaml，没有就生成带注释的友好模板
    if not os.path.exists(config_file):
        print("⚠️ 未找到配置文件！正在自动生成 account_config.yaml 模板...")

        # YAML 支持注释，我们可以直接把提示写在文件里
        yaml_template = """# 校园网自动登录配置文件
# 请在下方填写你的真实学号和密码（注意：冒号后面必须保留一个空格！）

username: 这里填写你的账号
password: 这里填写你的密码
"""
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(yaml_template)

        print("✅ 已在同目录下生成 [account_config.yaml] 文件！")
        print("👉 请用记事本打开 account_config.yaml，把学号和密码填进去，保存后再重新运行本程序！")
        time.sleep(10)
        sys.exit()

    # 2. 读取 YAML 里的账号密码并进行“防呆”检查
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        MY_USERNAME = str(config.get("username", "")).strip()
        MY_PASSWORD = str(config.get("password", "")).strip()

        # 检查同学是不是直接双击运行，忘了改里面的默认文字
        if MY_USERNAME == "这里填写你的账号" or not MY_USERNAME:
            print("❌ 错误：你还没有在 account_config.yaml 中填写真实的学号和密码！")
            time.sleep(10)
            sys.exit()

    except Exception as e:
        # 捕获 YAML 格式错误
        print("❌ account_config.yaml 格式被破坏了！请检查是不是不小心删掉了冒号或空格。")
        print("💡 解决办法：直接删掉 account_config.yaml 文件，重新运行本程序生成一个全新的模板。")
        time.sleep(10)
        sys.exit()

    print(f"🚀 校园网自动登录守护进程已启动 (当前使用账号: {MY_USERNAME})...")

    # 3. 开始无限循环守护
    while True:
        if not check_network():
            if check_gateway():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 发现校园网，正在自动登录...")
                do_login(MY_USERNAME, MY_PASSWORD)
                time.sleep(8)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💤 未连接校园 Wi-Fi，静默等待中...")
                time.sleep(15)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 网络畅通，一切正常，继续巡逻...")
            time.sleep(30)
