UESTC Wi-Fi 自动登录（用户说明）

【适用对象】
这是给最终用户的说明，不需要安装 Python。

【使用步骤】
1. 解压发布包。
2. 把 account_config.example.yaml 复制一份，重命名为 account_config.yaml。
3. 用记事本打开 account_config.yaml，填写你自己的账号和密码。
4. 选择一个版本运行：
   - uestc-wifi-autologin.exe（有控制台窗口，适合排错）
   - uestc-wifi-autologin-no-console.exe（无窗口后台运行）

【注意事项】
1. 不要把 account_config.yaml 发给别人（里面有你的密码）。
2. 程序是单实例，重复启动会自动退出。
3. 如果出错，请查看同目录 error.log。
4. 如果配置写坏了，删掉 account_config.yaml 后重新运行即可。

【建议】
第一次使用建议先运行有框版，确认正常后再使用无框版。
