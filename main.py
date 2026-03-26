import requests
import time
from datetime import datetime

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
    MY_USERNAME = "15309644680"
    MY_PASSWORD = "15309644680"

    print("🚀 校园网自动登录守护进程已启动...")

    while True:
        if not check_network():
            # 没外网的时候，先摸一摸网关在不在
            if check_gateway():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 发现校园网，正在自动登录...")
                do_login(MY_USERNAME, MY_PASSWORD)
                time.sleep(8) # 登录后多等一会儿，给路由器放行的时间
            else:
                # 网关也不在，说明根本没连校园 Wi-Fi
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 💤 未连接校园 Wi-Fi，静默等待中...")
                time.sleep(15)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 网络畅通，一切正常，继续巡逻...")
            # 网络畅通，每 30 秒巡逻一次
            time.sleep(30)