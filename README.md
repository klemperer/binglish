# Binglish：AI 桌面英语

自动更换必应 Bing 每日壁纸，顺便学个单词（AI 生成相关图片、例句、语音解析、英语小游戏等）。
点亮屏幕，欣赏美景，邂逅知识，聚沙成塔。For Windows & macOS

- 图片 URL：https://ss.blueforge.org/bing
- 壁纸来源：https://github.com/TimothyYe/bing-wallpaper
- 单词难度：CET-4 至 GRE 随机（排除所谓 Bad words，列表来自https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words）
- 更新频率：每 3 小时刷新一次
- 生成式 AI 无法保证内容完全准确
- 适用于 Windows10 及以上版本/macOS 13及以上版本；会按屏幕分辨率请求壁纸（仍建议 1920x1080 优先适配）
- 国内部分城市因网络问题，可能无法正常下载壁纸

<img width="1920" height="1080" alt="1" src="https://github.com/user-attachments/assets/92f5d84a-cc09-4581-9b17-9e113f27d2bc" />

## 快速开始

最短路径：直接用编译好的程序，无需装 Python。

### Windows 用户

1. 打开 [GitHub Releases](https://github.com/klemperer/binglish/releases/latest)，下载 `binglish.exe`
2. 双击运行（可拷到任意英文路径目录）
3. 程序在任务栏托盘；右键菜单可设「开机运行」

也可使用备用地址：[ss.blueforge.org/bing/binglish.exe](https://ss.blueforge.org/bing/binglish.exe)

### macOS 用户

1. 打开 [GitHub Releases](https://github.com/klemperer/binglish/releases/latest)，下载 `binglish-macos.zip` 并解压
2. 将 `binglish.app` 拖入「应用程序」
3. 首次打开若提示无法验证：右键 →「打开」，或执行  
   `xattr -dr com.apple.quarantine /Applications/binglish.app`
4. 图标在菜单栏托盘；右键菜单可设开机运行

> 安装后约每 3 小时自动更换 Bing 壁纸并展示单词。更多打包、源码运行与菜单说明见下文。

## 或 自行打包（Windows）

在任意目录克隆后进入**仓库根目录**（含 `build.bat`、`binglish` 包的目录）：

```PowerShell
git clone https://github.com/klemperer/binglish/
cd binglish
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pyinstaller
.\build.bat
```

打包产物在 `dist\binglish.exe`。

### 源码运行（Windows）

需图形会话。推荐在仓库根目录用 venv 直接跑包入口：

```PowerShell
cd binglish
.\.venv\Scripts\python.exe -m binglish
```

若 Python 找不到包，可显式指定仓库根目录为包路径后再运行：

```PowerShell
cd binglish
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m binglish.app
```

说明：源码运行时托盘菜单通常没有完整的「检查更新」（打包后的 exe 才有）；仍可点「前往 GitHub Releases」。

## 运行（Windows）

双击 `binglish.exe`（自行打包时在项目 `dist` 目录）即可，无需安装。程序运行后最小化至任务栏托盘，可在右键菜单中选择开机自动运行。

命令行源码运行（不推荐，检查更新受限）见上文「源码运行（Windows）」。

## 下载已编译程序（macOS）

[Github Releases](https://github.com/klemperer/binglish/releases/latest) 提供 macOS 构建（通常为 `binglish-macos.zip`，内含 `.app`）。若未公证，首次打开需右键 → 打开，或：

```Bash
xattr -dr com.apple.quarantine /Applications/binglish.app
```

## 或 自行打包（macOS）

**必须在 macOS 本机打包**（不能在 Windows 上交叉打包 Mac 版）。在仓库根目录：

```Bash
git clone https://github.com/klemperer/binglish/
cd binglish
chmod +x build_macos.sh
./build_macos.sh
```

产物为 `dist/binglish.app`（onedir，适合发布）。脚本会：

1. 安装依赖（含 `pyobjc-core`、`pyobjc-framework-Cocoa`）
2. 跑测试（失败则中止打包）
3. 用 PyInstaller 打包，并带上 macOS 托盘子进程所需的 hidden imports

发布到 GitHub Release 前可自行压缩：

```Bash
ditto -c -k --sequesterRsrc --keepParent dist/binglish.app dist/binglish-macos.zip
shasum -a 256 dist/binglish-macos.zip
```

本地自测：

```Bash
open dist/binglish.app
# 或
./dist/binglish.app/Contents/MacOS/binglish
```

CI（`.github/workflows/release.yml`）在打 tag 时使用的 macOS 打包参数与 `build_macos.sh` 对齐（pyobjc + hidden imports + onedir `.app`）。

### 源码运行（macOS）

在仓库根目录：

```Bash
git clone https://github.com/klemperer/binglish/
cd binglish
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pyobjc-core pyobjc-framework-Cocoa
PYTHONPATH="$PWD" ./.venv/bin/python -m binglish
# 等价于
PYTHONPATH="$PWD" ./.venv/bin/python -m binglish.app
```

### macOS 托盘子进程（架构说明）

macOS 上系统托盘（pystray / AppKit）要求在**进程主线程**跑事件循环；若与 Tk 的 `mainloop` 混在同一进程，容易出现 AppKit 与 Python GIL 冲突导致崩溃。

因此 macOS 运行时采用双进程：

| 进程 | 职责 |
|------|------|
| 父进程 | 仅 Tk：对话框、休息/历史覆盖层、小游戏、壁纸与调度 |
| 子进程 | 仅托盘：在 `binglish.ui.tray_proc` 中运行 pystray / AppKit |

托盘菜单点击通过进程间队列通知父进程，再在 Tk 主线程执行。打包时必须把子进程入口及 `pystray._darwin`、PyObjC 等一并打进产物（见 `build_macos.sh` 与 `release.yml`）。

Windows **不**使用该子进程模型：托盘与 Tk 同进程即可，行为与旧版一致。

## 运行（macOS）

运行 `dist/binglish.app`（解压 zip 后可拖到「应用程序」）即可，无需安装。程序运行后图标出现在菜单栏托盘，可在右键菜单中选择开机自动运行。

## 右键菜单说明

- 查单词：跳转至必应词典进一步了解单词相关用法
- 听单词：播放AI生成的单词用法说明（中英双语）
- 看单词：观看影视中包含该单词的部分片段
- 随机复习：随机显示一张往期壁纸（不影响当前壁纸更新循环）
- 复制保存：如果喜欢当前壁纸，点击该选项可复制一份（保存于程序所在目录）
- 壁纸信息：当前壁纸的内容、版权等相关信息
- 分享壁纸：手机扫码，将当前壁纸分享给微信好友、朋友圈等
- 提醒休息：定时提醒休息（在右键菜单启用，默认45分钟，可修改配置）
- Today in History：历史上的今天，精选自WikiMedia
- Binglish Games：英语小游戏（Sentence Master、Wordle、Mini Crossword、Test Your Vocabulary）
- Song of the Day：推荐一首外文歌曲（来源NPR）

## 被Windows Defender等识别为流氓软件

PyInstaller打包的EXE文件常被杀毒软件误报为病毒或流氓软件（通常为Trojan/木马），主要原因是其使用通用的启动加载器（bootloader）和临时文件解压机制，与部分病毒特征相似。Binglish完全开源，不包含任何恶意代码。如被误报为病毒，可将binglish.exe加入白名单，具体步骤参考https://www.honor.com/cn/support/content/zh-cn15810578/。

## 用作ipad锁屏墙纸

在ipad“快捷指令”程序中新建快捷指令（参考https://www.icloud.com/shortcuts/f309786b43b0420f96c59602b8a0361f
，在ipad safari浏览器中打开），在“快捷指令-自动化”中设置特定时间运行上述快捷指令。该功能未充分测试，可能存在部分ipad机型无法显示墙纸全部内容等现象。

## 偶发问题

#### ModuleNotFoundError: No module named 'tkinter'
用 `python -m binglish` 源码运行时可能遇到。tkinter 随 python.org 官方安装包提供，**不能**用 `pip install tk` 安装。请改用完整版 Python（安装时勾选 tcl/tk），或使用已打包的 exe。
#### 壁纸显示不正常（被过度拉伸或压扁）
尝试以下解决方案：桌面点击右键、选择“个性化”、选择“背景”、选择“填充”或“适应”

#### 程序不能正常运行（黑框闪退）
尝试将程序移动至非中文路径的目录下再双击运行。

#### 打包时报 `PermissionError: [WinError 5] 拒绝访问`
PyInstaller 分析依赖时会再启动一个隔离 Python 子进程；若工程路径含**中文或过长**，部分环境会 `CreateProcess` 失败。  
处理：把仓库拷到纯英文短路径再打包，例如：

```bat
robocopy "%cd%" C:\binglish-build /E /XD .git .venv dist build
cd /d C:\binglish-build
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name binglish ^
  --icon assets\binglish.ico --add-data "assets\binglish.ico;." --paths . ^
  --hidden-import pystray._win32 binglish\app.py
```

若仍失败，可将该目录加入杀软排除后重试。
## Star History

<a href="https://www.star-history.com/?repos=klemperer%2Fbinglish&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=klemperer/binglish&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=klemperer/binglish&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=klemperer/binglish&type=date&legend=top-left" />
 </picture>
</a>
