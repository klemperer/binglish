# binglish：欣赏美景，邂逅知识
自动更换必应Bing每日壁纸，顺便学个单词（AI生成相关图片、名言警句及翻译）
- 必应壁纸来自https://github.com/TimothyYe/bing-wallpaper
- 单词难度：CET-4至GRE随机（排除所谓Bad words，列表来自https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words）
- 更新频率：每3小时刷新一次
- 生成式AI无法保证内容准确性，请自行甄别
- 适用于Windows10及以上版本，1920x1080分辨率。
<img width="1920" height="1080" alt="screenshot" src="https://github.com/user-attachments/assets/b68bd444-9402-4a27-89ef-3d6c721dc19f" />
##编译Build

git clone https://github.com/klemperer/binglish/    
cd binglish    
pyinstaller --onefile --windowed --add-data "binglish.ico;." --hidden-import "pystray._win32" binglish.py
