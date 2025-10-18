# binglish：AI 桌面英语

自动更换必应 Bing 每日壁纸，顺便学个单词（AI 生成相关图片、例句、语音解析等）。
点亮屏幕，欣赏美景，邂逅知识，聚沙成塔。

- 图片 URL：https://ss.blueforge.org/bing
- 壁纸来源：https://github.com/TimothyYe/bing-wallpaper
- 单词难度：CET-4 至 GRE 随机（排除所谓 Bad words，列表来自https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words）
- 更新频率：每 3 小时刷新一次
- 生成式 AI 无法保证内容完全准确
- 适用于 Windows10 及以上版本，1920x1080 分辨率（其他分辨率暂未经测试）
- 国内部分城市因网络问题，可能无法正常下载壁纸
  <img width="1920" height="1080" alt="wallpaper" src="https://github.com/user-attachments/assets/6baf27da-3aea-4e61-a130-0b93aeefd5ed">

## 下载已编译程序

[Github releases](https://github.com/klemperer/binglish/releases/download/latest/binglish.exe) 或者 [备用下载地址](https://ss.blueforge.org/bing/binglish.exe)

## 或 自行打包

```Bash
git clone https://github.com/klemperer/binglish/
cd binglish
pip install -r requirements.txt
pip install pyinstaller
bundle.bat
```

## 运行

双击binglish.exe（如自行打包，可在项目下dist目录中找到该文件）即可运行，无需安装。程序运行后将最小化至右侧任务栏中，可在右键菜单中选择开机自动运行。

也可以在命令行中执行以下命令以运行（不推荐，“检查更新”功能不可用）：

```Bash
python binglish.py
```

## 用作ipad锁屏墙纸

在ipad“快捷指令”程序中新建快捷指令（参考https://www.icloud.com/shortcuts/f309786b43b0420f96c59602b8a0361f
，在ipad safari浏览器中打开），在“快捷指令-自动化”中设置特定时间运行上述快捷指令。该功能未充分测试，可能存在部分ipad机型无法显示墙纸全部内容等现象。

## troubleshooting

如果遇到如下问题：

```
D:\Repository\binglish>python binglish.py 

Traceback (most recent call last):

  File "D:\Repository\binglish\binglish.py", line 11, in <module>

    import tkinter as tk

ModuleNotFoundError: No module named 'tkinter'
```

通常情况下是由于没有正确安装 tkinter 导致的。当您安装完整的 Python 解释器时，tkinter 会随之一起安装。但是，如果您使用的是自定义的 Python 版本，或者在安装时选择了最小化安装选项，那么 tkinter 可能没有被包含。
要解决这个问题，您需要单独安装 tkinter。您可以使用以下命令来安装 tkinter：

```Bash
pip install tk
```

如果您使用的是 Windows，并且已经安装了 Python，那么您可能需要以管理员身份运行命令提示符，然后使用以下命令来安装 tkinter：

```Bash
python -m pip install tk
```

安装完成后，您应该能够正常运行 binglish.py 脚本了。
