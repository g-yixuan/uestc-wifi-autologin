UESTC Wi-Fi 自动登录 (Windows 版)

一、给同学的使用方法（不需要安装 Python）
1. 解压你收到的压缩包。
2. 把 account_config.example.yaml 复制一份，重命名为 account_config.yaml。
3. 用记事本打开 account_config.yaml，填写你自己的账号和密码。
4. 双击 uestc-wifi-autologin.exe 运行。

二、注意事项
1. 不要把自己的 account_config.yaml 发给别人（里面有你的密码）。
2. 首次运行建议保持窗口打开，便于查看日志和报错信息。
3. 如果配置填错，可以删掉 account_config.yaml 后重新创建。
4. 程序报错时会停在窗口，并把完整错误写到同目录的 error.log。
5. 程序已启用单实例互斥，重复启动会自动退出。

三、维护者打包命令（在项目根目录执行）
1. 安装依赖（第一次或依赖有变动时）：
   uv sync

2. 打包有框版本（保留控制台窗口）：
   uv run --with pyinstaller pyinstaller --clean --noconfirm --onefile --name uestc-wifi-autologin main.py

3. 打包无框版本（隐藏控制台窗口）：
   uv run --with pyinstaller pyinstaller --clean --noconfirm --onefile --noconsole --name uestc-wifi-autologin-no-console main.py

4. 生成分发包目录（放 4 个文件）：
   release/
   - uestc-wifi-autologin.exe
   - uestc-wifi-autologin-no-console.exe
   - account_config.example.yaml
   - README.txt

   两个 exe 都在 dist/ 目录，复制到 release/ 即可。
