import requests
import ctypes
import os
import sys
import time
import threading
import winreg
import webbrowser
from PIL import Image
import exifread
from pystray import MenuItem as item, Icon, Menu
import tkinter as tk
from tkinter import messagebox
import subprocess
import json
from playsound3 import playsound 
import shutil 
from datetime import datetime 
import multiprocessing
import qrcode
from PIL import ImageTk
import random 
import configparser
import re
import hashlib

VERSION = "1.3.0"
RELEASE_JSON_URL = "https://ss.blueforge.org/bing/release.json" 
DOWNLOAD_URL = "https://ss.blueforge.org/bing/binglish.exe" 
IMAGE_URL = f"https://ss.blueforge.org/bing?v={VERSION}"  
MUSIC_JSON_URL = "https://ss.blueforge.org/bing/songoftheday.json" 
REMOTE_REMIND_URL = "https://ss.blueforge.org/remind.json"
HISTORY_URL_BASE = "https://ss.blueforge.org/getHistory"

UPDATE_INTERVAL_SECONDS = 3 * 60 * 60 
APP_NAME = "Binglish"
REG_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
ICON_FILENAME = "binglish.ico"
DOWNLOAD_RETRY_INTERVAL_SECONDS = 30
INTERNET_CHECK_INTERVAL_SECONDS = 60
PROJECT_URL = "https://github.com/klemperer/binglish" 
CONFIG_FILENAME = "binglish.ini"

REST_INTERVAL_SECONDS = 2700     # 默认休息间隔45分钟
IDLE_RESET_SECONDS = 300         # 闲置5分钟重置计时
REST_LOCK_SECONDS = 30           # 默认锁定屏幕30秒
OVERLAY_COLOR = "#2C3E50"        # 默认遮罩颜色

# 休息提示词
REST_QUOTES = [
    ("Even a Ferrari needs a pit stop. You're a Ferrari, right?", "法拉利也需要进站加油。你也是法拉利，对吧？"),
    ("The computer won't run away. Promise.", "电脑不会长腿跑掉的，我保证。"),
    ("Time to blink manually.", "是时候手动眨眨眼了。"),
    ("Your spine called. It wants to be straight for a bit.", "你的脊椎打电话来了，它想稍微直一直。"),
    ("Hydrate or diedrate. Go drink water.", "要么喝水，要么枯萎。去喝水。"),
    ("404: Energy Not Found. Please reboot yourself.", "404：未找到能量。请重启你自己。"),
    ("Step away from the glowing rectangle.", "离那个发光的长方形远一点。"),
    ("You've been sitting longer than a gargoyle.", "你坐得比石像鬼还久。"),
    ("Reality is calling. It's high resolution out there.", "现实在呼唤。外面的分辨率很高的。"),
    ("Give your mouse a break. It's exhausted.", "放过你的鼠标吧，它累坏了。"),
    ("Look at something further than 50cm away. Like a wall.", "看点50厘米以外的东西。比如墙。"),
    ("If you don't rest, your bugs will multiply.", "如果你不休息，你的Bug会繁殖的。"),
    ("Stretch. You don't want to turn into a shrimp.", "伸个懒腰。你不想变成一只虾米吧。"),
    ("Pause game. Life continues.", "游戏暂停。生活继续。"),
    ("Go annoy your cat/dog/colleague for a moment.", "去骚扰一下你的猫/狗/同事吧。"),
    ("Ctrl+Alt+Del your fatigue.", "Ctrl+Alt+Del 强制结束你的疲劳。"),
    ("Loading 'Energy'... Please wait 30 seconds.", "正在加载“能量”... 请等待30秒。"),
    ("A rested brain is a sexy brain.", "休息过的大脑才是性感的大脑。"),
    ("Don't let the pixels hypnotize you.", "别让像素把你催眠了。"),
    ("Nature called. Not the bathroom, actual nature.", "大自然在召唤。不是指厕所，是真的大自然。"),
    ("Your chair misses your absence.", "你的椅子怀念你不在的时候。"),
    ("Refresh your soul, not just the webpage.", "刷新一下灵魂，而不只是网页。"),
    ("Keep calm and take a break.", "保持冷静，休息一下。"),
    ("System Overheat. Cooling required.", "系统过热。需要冷却。"),
    ("Battery Low. Please recharge with coffee or tea.", "电量低。请用咖啡或茶充电。"),
    ("Remember the sun? It's that bright ball in the sky.", "还记得太阳吗？就是天上那个亮球。"),
    ("Typing speed -50% due to fatigue.", "由于疲劳，打字速度 -50%。"),
    ("AFK (Away From Keyboard) for a bit.", "暂时 AFK 一下吧。"),
    ("You are not a robot. Or are you?", "你不是机器人。还是说你是？"),
    ("Your brain has left the chat. Please wait for it to reconnect.", "你的大脑已退出群聊。请等待重连。"),
    ("Error 404: Motivation not found. Reboot required.", "错误 404：未找到动力。需要重启。"),
    ("Stop typing. The keyboard is filing a restraining order.", "别敲了。键盘正在申请针对你的限制令。"),
    ("Go look at a tree. A real one. Not a decision tree.", "去看棵树。真的树。不是决策树。"),
    ("You are simulating a statue perfectly. Now move.", "你模仿雕像模仿得很完美。现在动一下。"),
    ("Your posture resembles a cooked shrimp. Straighten up.", "你的坐姿像只煮熟的虾米。直起来。"),
    ("Even the CPU throttles when it gets too hot. Chill.", "CPU 热了都知道降频。你也冷静下。"),
    ("Your eyes are dry. Blink. Like a human.", "眼睛干了。眨眼。像个人类那样。"),
    ("Warning: User battery is critically low.", "警告：用户电量严重不足。"),
    ("I bet you forgot what the sun looks like.", "我打赌你忘了太阳长什么样了。"),
    ("Clear your cache. And by cache, I mean your head.", "清一下缓存。我是说你的脑子。"),
    ("Ctrl+S your work, Ctrl+Alt+Del your stress.", "Ctrl+S 保存工作，Ctrl+Alt+Del 结束压力。"),
    ("Have you tried turning yourself off and on again?", "你试过把自己关机再重启吗？"),
    ("Your spine is plotting revenge against you.", "你的脊椎正在密谋报复你。"),
    ("The bugs will still be there in 5 minutes.", "Bug 还是那个 Bug，5分钟后它还在那。"),
    ("Don't let the blue light turn you into a zombie.", "别让蓝光把你变成了僵尸。"),
    ("Touch grass. Literally.", "去摸摸草。字面意思。"),
    ("Stand up. Your butt is falling asleep.", "站起来。你的屁股睡着了。"),
    ("System maintenance required: Intake caffeine or water.", "需要系统维护：摄入咖啡因或水。"),
    ("You've been scroll-locked. Unlock yourself.", "你被 Scroll Lock 了。给自己解锁吧。"),
    ("Nature called. It left a voicemail. Go listen.", "大自然来电话了。留了语音信箱。去听听。"),
    ("Taking a break is part of the algorithm.", "休息也是算法的一部分。"),
    ("Don't code a memory leak in your own brain.", "别给自己脑子里写出内存泄漏了。"),
    ("Your lumbar support misses you. Lean back.", "你的腰靠想你了。往后靠靠。"),
    ("A 5-minute break saves 5 hours of debugging.", "休息5分钟，省下5小时改 Bug。"),
    ("Are you waiting for a segmentation fault in your body?", "你在等身体报段错误吗？"),
    ("Esc key is not just on the keyboard.", "Esc 键不只在键盘上。"),
    ("Refresh your perspective, not just the browser.", "刷新一下视野，而不只是浏览器。"),
    ("Gravity check: Can you still stand up?", "重力检查：你还能站起来吗？"),
    ("The internet will survive without you for 5 minutes.", "没你这5分钟，互联网也不会崩。"),
    ("Your screen resolution is high. Your vision is getting low.", "屏幕分辨率挺高。你的视力在走低。"),
    ("Don't be a browser tab that plays music you can't find.", "别做那个找不到在哪放音乐的浏览器标签页。"),
    ("Stretch. Do not evolve into a T-Rex.", "伸展一下。别退化成霸王龙。"),
    ("Close your eyes. Visualize a beach. Or a bed.", "闭眼。想象海滩。或者一张床。"),
    ("Your RAM is full. Garbage collection needed.", "内存满了。需要进行垃圾回收。"),
    ("Step away from the machine, human.", "离开那台机器，人类。"),
    ("Loading fresh air... 0% complete.", "正在加载新鲜空气... 完成度 0%。"),
    ("Ping timeout. Your brain is lagging.", "Ping 超时。你的大脑卡顿了。"),
    ("Look at something 20 feet away for 20 seconds.", "看20英尺外的东西20秒（20-20-20法则）。"),
    ("You are not a robot. Robots don't get back pain.", "你不是机器人。机器人不会腰疼。"),
    ("Don't let your coffee get cold while you stare at code.", "别盯着代码看，把咖啡放凉了。"),
    ("Minimize all windows. Maximize wellness.", "最小化所有窗口。最大化健康。"),
    ("Time for a bio-break. You know what that means.", "生物钟休息时间。你懂我意思。"),
    ("Checking connection to reality... Signal weak.", "正在检查与现实的连接... 信号微弱。"),
    ("Put the mouse down slowly and nobody gets hurt.", "慢慢放下鼠标，没人会受伤。"),
    ("Go annoy a coworker. It's social interaction.", "去打扰个同事。这也算社交。"),
    ("Take a deep breath. Not a shallow one. A deep one.", "深呼吸。不是浅呼吸。是深呼吸。"),
    ("Is your neck made of stone? Rotate it.", "脖子是石头做的吗？转一转。"),
    ("The matrix has you. Jack out for a bit.", "你被矩阵困住了。拔线出来一会儿。"),
    ("Don't doom-scroll. Doom-stretch instead.", "别刷屏了。起来“刷”个懒腰。"),
    ("Your typing speed is dropping. Your typos are rising.", "打字速度在降。错别字在涨。"),
    ("Give your eyes a holiday.", "给眼睛放个假。"),
    ("Remember blinking? It keeps eyes moist. Try it.", "还记得眨眼吗？能保湿。试试看。"),
    ("Go find a window. Look out of it.", "找个窗户。往外看。"),
    ("Hydrate. Your brain is 73% water. Refill it.", "补水。你脑子73%是水。续杯。"),
    ("Status update: User needs a reboot.", "状态更新：用户需要重启。"),
    ("Don't become a legacy system.", "别让自己成了“老旧系统”。"),
    ("Run diagnostic tool: 'Walk_Around_Room.exe'.", "运行诊断工具：'屋里走两步.exe'。"),
    ("There is no dark mode for real life fatigue.", "现实生活的疲劳可没有“深色模式”。"),
    ("Your code is compiling. You should be stretching.", "代码在编译。你应该在拉伸。"),
    ("Disconnect to reconnect.", "断开连接，为了更好地连接。"),
    ("Screen time is up. Real time begins.", "屏幕时间到。现实时间开始。"),
    ("Avoid burnout. It smells like toasted wires.", "避免过劳烧毁。闻起来像烤焦的电线。"),
    ("You have been idle in real life for too long.", "你在现实生活中“挂机”太久了。"),
    ("Go stretch your legs before they forget how to walk.", "去伸伸腿，趁它们还没忘怎么走路。"),
    ("Alert: Caffeine levels dropping. Cortisol rising.", "警报：咖啡因水平下降。皮质醇上升。"),
    ("Look up. The ceiling is boring, but it's not a screen.", "抬头。天花板很无聊，但它不是屏幕。"),
    ("Shake your hands out. Jazz hands!", "甩甩手。爵士手！"),
    ("Are your shoulders touching your ears? Drop them.", "肩膀缩到耳朵那儿了吗？放下来。"),
    ("Defag your mind.", "对你的大脑进行磁盘碎片整理。"),
    ("Force quit 'Worrying'.", "强制退出“焦虑”进程。"),
    ("Even superheroes take off the cape sometimes.", "超级英雄有时候也得脱下披风。"),
    ("Walk away. The solution will come when you're peeing.", "走开一会。上厕所的时候方案自然就有了。"),
    ("Save your game. Pause your work.", "保存游戏。暂停工作。"),
    ("Low power mode enabled for Human.", "人类低电量模式已启用。"),
    ("Detecting high stress levels. Abort mission immediately.", "检测到高压力水平。立即中止任务。"),
    ("You look like you need a hug. Or a nap.", "你看着像需要一个拥抱。或者一个午觉。"),
    ("Be right back. You, not the computer.", "马上回来（BRB）。是指你，不是电脑。"),
    ("Unlock achievement: 'Stood Up Today'.", "解锁成就：‘今天站起来过’。"),
    ("Don't let the pixels bite.", "别让像素咬你一口。"),
    ("Are you a mushroom? Because you're sitting in the dark.", "你是蘑菇吗？一直坐在黑影里。"),
    ("Give your biological neural network a rest.", "给你的生物神经网络放个假。"),
    ("Overheating warning. Vent heat by walking.", "过热警告。通过散步散热。"),
    ("Remember, you are carbon-based, not silicon-based.", "记住，你是碳基生物，不是硅基生物。"),
    ("Stop slouching. You look like a question mark.", "别驼背。你看着像个问号。"),
    ("Go make some tea. The ritual is healing.", "去泡杯茶。这个仪式很治愈。"),
    ("Close tab: 'Stress'. Open tab: 'Peace'.", "关闭标签页：‘压力’。打开标签页：‘平静’。"),
    ("Your output quality is degrading. Rest required.", "产出质量在下降。要求休息。"),
    ("Don't ignore the hardware (your body).", "别忽视了硬件（你的身体）。"),
    ("Keep calm and step away from the keyboard.", "保持冷静，远离键盘。"),
    ("Life is not a sprint. It's a marathon with snack breaks.", "生活不是冲刺。是有零食时间的马拉松。"),
    ("Go get some Vitamin D. The real kind.", "去搞点维他命D。真的那种。"),
    ("Even the internet sleeps... wait, no it doesn't. But you should.", "互联网都睡觉... 呃它不睡。但你应该睡。"),
    ("Reset your uptime.", "重置你的运行时间。"),
    ("Switch off to switch on.", "关机是为了更好地开机。"),
    ("Your focus needs autofocusing.", "你的注意力需要自动对焦了。"),
    ("Don't let your dreams be dreams. But do sleep.", "别让梦想只是梦想。但觉还是要睡的。")
]

bing_word = None 
bing_url = None  
bing_mp3 = None  
bing_copyright = None 
bing_copyright_url = None 
bing_id = None 
bing_music_name = None 
bing_music_url = None  
bing_music_desc = None 
is_music_playing = False 
music_process = None 
music_check_timer = None 

# 全局变量用于休息提醒
is_rest_enabled = False # 是否开启功能
last_activity_time = time.time() # 上次活动时间
last_rest_time = time.time() # 上次休息（或启动）时间
is_overlay_showing = False # 遮罩层是否正在显示
new_version_available = False # 是否存在新版本标志

# 用于持有 pystray 图标对象的引用
root = None
icon = None

# Windows API 结构体定义，用于检测闲置时间
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

# 获取系统空闲时间（秒）
def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    return 0

# 检测当前前台窗口是否全屏
def is_foreground_fullscreen():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
            
        # 获取屏幕分辨率
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        
        # 获取窗口矩形
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        # 判断是否充满屏幕
        if (rect.left <= 0 and rect.top <= 0 and 
            rect.right >= screen_w and rect.bottom >= screen_h):
            # 排除桌面和任务栏的情况（简单的判断类名）
            buffer_len = 255
            class_name = ctypes.create_unicode_buffer(buffer_len)
            user32.GetClassNameW(hwnd, class_name, buffer_len)
            name = class_name.value
            if name in ["Progman", "WorkerW", "Shell_TrayWnd"]:
                return False
            return True
        return False
    except Exception:
        return False

# 打开配置文件
def open_config_file():
    config_path = os.path.join(os.path.dirname(get_executable_path()), CONFIG_FILENAME)
    try:
        # 确保文件存在，如果不存在尝试重新生成
        if not os.path.exists(config_path):
            load_config_and_init()
            
        print(f"[{time.ctime()}] 正在调用系统默认编辑器打开: {config_path}")
        os.startfile(config_path)
    except Exception as e:
        print(f"[{time.ctime()}] 打开配置文件失败: {e}")
        root.after(0, lambda: messagebox.showerror("错误", f"无法打开配置文件: {e}"))

# 初始化并加载配置文件
def load_config_and_init():
    global is_rest_enabled, REST_INTERVAL_SECONDS, IDLE_RESET_SECONDS, REST_LOCK_SECONDS, OVERLAY_COLOR
    
    config_path = os.path.join(os.path.dirname(get_executable_path()), CONFIG_FILENAME)
    
    # 如果文件不存在，创建带有注释的默认文件
    if not os.path.exists(config_path):
        try:
            default_content = """[Settings]
; 是否开启休息提醒 (0:关闭, 1:开启) - 修改此项后，如通过菜单更改会立即生效；如手动更改文件需重启程序
IS_REST_ENABLED = 0

; 休息间隔时间(秒)，默认45分钟 - 修改此项需重启程序以生效
REST_INTERVAL_SECONDS = 2700

; 闲置重置时间(秒)，默认5分钟不动则重置计时 - 修改此项需重启程序以生效
IDLE_RESET_SECONDS = 300

; 强制休息锁定时间(秒) - 修改此项需重启程序以生效
REST_LOCK_SECONDS = 30

; 遮罩层背景颜色 (Hex代码) - 修改此项需重启程序以生效
OVERLAY_COLOR = #2C3E50
"""
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                f.write(default_content)
            print(f"[{time.ctime()}] 已创建默认配置文件: {config_path}")
        except Exception as e:
            print(f"[{time.ctime()}] 创建配置文件失败: {e}")

    # 读取配置
    config = configparser.ConfigParser()
    try:
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8-sig')
            if 'Settings' in config:
                settings = config['Settings']
                # 使用 getboolean 自动处理 0/1/true/false
                is_rest_enabled = settings.getboolean('IS_REST_ENABLED', fallback=False)
                REST_INTERVAL_SECONDS = settings.getint('REST_INTERVAL_SECONDS', fallback=2700)
                IDLE_RESET_SECONDS = settings.getint('IDLE_RESET_SECONDS', fallback=300)
                REST_LOCK_SECONDS = settings.getint('REST_LOCK_SECONDS', fallback=30)
                # 获取字符串，去除可能的引号
                color_val = settings.get('OVERLAY_COLOR', fallback='#2C3E50').strip().strip('"').strip("'")
                if color_val:
                    OVERLAY_COLOR = color_val
                
                print(f"[{time.ctime()}] 配置加载成功:")
                print(f"    Enabled: {is_rest_enabled}")
                print(f"    Interval: {REST_INTERVAL_SECONDS}")
                print(f"    Idle Reset: {IDLE_RESET_SECONDS}")
                print(f"    Lock: {REST_LOCK_SECONDS}")
                print(f"    Color: {OVERLAY_COLOR}")
            else:
                print(f"[{time.ctime()}] 配置文件中未找到 [Settings] 节，使用默认值。")
    except Exception as e:
        print(f"[{time.ctime()}] 加载配置文件出错: {e}，将使用默认值。")

# 保存休息提醒状态到配置文件
def save_rest_enabled_to_config(enabled):
    config_path = os.path.join(os.path.dirname(get_executable_path()), CONFIG_FILENAME)
    try:
        if not os.path.exists(config_path):
            # 如果文件被删了，重新生成
            load_config_and_init()
            return

        with open(config_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # 使用正则替换 IS_REST_ENABLED = ...
        new_val = "1" if enabled else "0"
        pattern = r"(?m)(?i)(^\s*IS_REST_ENABLED\s*=\s*)([^;\r\n]*)"
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, f"\\g<1>{new_val}", content)
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                f.write(new_content)
            print(f"[{time.ctime()}] 配置已更新: IS_REST_ENABLED = {new_val}")
        else:
            print(f"[{time.ctime()}] 保存配置失败: 未在文件中找到 IS_REST_ENABLED 定义。")
            
    except Exception as e:
        print(f"[{time.ctime()}] 保存配置失败: {e}")

# 切换休息提醒功能
def toggle_rest_reminder():
    global is_rest_enabled, last_rest_time, icon
    is_rest_enabled = not is_rest_enabled
    save_rest_enabled_to_config(is_rest_enabled)
    
    if is_rest_enabled:
        last_rest_time = time.time()
        print(f"[{time.ctime()}] 休息提醒已开启。")
    else:
        print(f"[{time.ctime()}] 休息提醒已关闭。")
        
    if icon:
        icon.menu = Menu(*build_menu_items())

# 显示全屏遮罩层 UI
def show_rest_overlay():
    global is_overlay_showing, last_rest_time, bing_word
    if is_overlay_showing:
        return
    
    is_overlay_showing = True
    
    quote_en, quote_cn = "", ""
    quote_en, quote_cn = random.choice(REST_QUOTES)
    
    # 创建 Toplevel 窗口
    overlay = tk.Toplevel(root)
    overlay.title("Time to Rest")
    
    # 全屏、无边框、置顶
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.configure(bg=OVERLAY_COLOR)
    
    # 初始透明度为0，用于淡入效果
    overlay.attributes("-alpha", 0.0)

    # UI 布局
    container = tk.Frame(overlay, bg=OVERLAY_COLOR)
    container.pack(expand=True, fill="both")
    
    # 垂直居中 Frame
    center_frame = tk.Frame(container, bg=OVERLAY_COLOR)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    font_en = ("Helvetica", 32, "bold")
    font_cn = ("Microsoft YaHei", 24)
    font_word_hint = ("Microsoft YaHei", 18, "bold")
    font_btn = ("Microsoft YaHei", 14)
    
    lbl_en = tk.Label(center_frame, text=quote_en, font=font_en, fg="white", bg=OVERLAY_COLOR, wraplength=w-100)
    lbl_en.pack(pady=(0, 20))
    
    lbl_cn = tk.Label(center_frame, text=quote_cn, font=font_cn, fg="#BDC3C7", bg=OVERLAY_COLOR, wraplength=w-100)
    lbl_cn.pack(pady=(0, 40))

    lbl_word = None
    if bing_word:
        hint_templates = [
            f"思考时间：你知道 {bing_word} 的读音、含义和用法吗？",
            f"考考你：{bing_word} 这个词怎么读，是什么意思？",
            f"趁休息回忆一下：{bing_word} 通常在什么语境下使用？",
            f"试着在脑海里造一个包含 {bing_word} 的句子。",
            f"不查字典，你能准确解释 {bing_word} 的含义吗？",
            f"闭上眼尝试拼写一下：{bing_word}。",
            f"小挑战：你能自信地大声读出 {bing_word} 吗？",
            f"灵魂拷问：你真的完全掌握 {bing_word} 了吗？",
            f"想想 {bing_word} 可以在什么场景使用。",
            f"别只顾着发呆，回顾一下 {bing_word} 的中文意思。",
            f"如果让你给别人讲解 {bing_word}，你会怎么说？",
            f"快速问答：{bing_word} 是名词、动词还是形容词？",
            f"今天的重点单词是 {bing_word}，你记住了吗？",
            f"记忆检查：{bing_word} 有没有什么常见的同义词？",
            f"{bing_word} —— 看到它，你脑海里浮现出的第一个画面是什么？",
            f"在休息结束前，请在心里把 {bing_word} 默念三遍。",
            f"假如现在英语考试，{bing_word} 这道题你会做吗？",
            f"嘿，放松眼睛的同时，别忘了复习一下：{bing_word}。"
        ]
        
        word_hint_text = random.choice(hint_templates)
        
        lbl_word = tk.Label(center_frame, text=word_hint_text, font=font_word_hint, 
                            fg="#A9DFBF", bg=OVERLAY_COLOR, wraplength=w-100)
    
    # 按钮变量
    remaining_seconds = REST_LOCK_SECONDS
    btn_text = tk.StringVar()
    btn_text.set(f"我休息好了 ({remaining_seconds}s)")
    
    def on_close(event=None):
        global is_overlay_showing, last_rest_time
        overlay.destroy()
        is_overlay_showing = False
        last_rest_time = time.time()
        
        if icon:
             icon.menu = Menu(*build_menu_items())
    
    btn_ok = tk.Button(center_frame, textvariable=btn_text, font=font_btn, 
                       command=on_close, state="disabled", 
                       bg="#ECF0F1", fg="#2C3E50", 
                       relief="flat", padx=30, pady=10)
    btn_ok.pack()
    
    # 平滑淡入逻辑
    target_alpha = 0.9  # 最终暗度
    animation_duration = 3000 # 持续时间 3000ms
    step_interval = 20 # 刷新间隔 20ms
    alpha_step = target_alpha / (animation_duration / step_interval)

    def fade_in(current_alpha=0):
        if current_alpha < target_alpha:
            new_alpha = current_alpha + alpha_step
            if new_alpha > target_alpha:
                new_alpha = target_alpha
                
            overlay.attributes("-alpha", new_alpha)
            overlay.after(step_interval, fade_in, new_alpha)
        else:
            start_countdown()
            
    # 倒计时逻辑
    def start_countdown():
        nonlocal remaining_seconds
        show_hint_time = REST_LOCK_SECONDS // 2
        if remaining_seconds == show_hint_time and lbl_word:
            lbl_word.pack(pady=(0, 40), before=btn_ok)
        if remaining_seconds > 0:
            remaining_seconds -= 1
            btn_text.set(f"我休息好了 ({remaining_seconds}s)")
            overlay.after(1000, start_countdown)
        else:
            btn_text.set("我休息好了")
            btn_ok.config(state="normal", bg="white", cursor="hand2")
            overlay.bind('<Return>', on_close)
            overlay.focus_force()
    fade_in(0)
    
    overlay.focus_force()

# 历史事件遮罩层 UI
def show_history_overlay(events, date_str):
    global is_overlay_showing

    if is_overlay_showing:
        pass
    
    is_overlay_showing = True

    overlay = tk.Toplevel(root)
    overlay.title("On This Day")
    
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.configure(bg=OVERLAY_COLOR)
    overlay.attributes("-alpha", 0.0)

    main_container = tk.Frame(overlay, bg=OVERLAY_COLOR)
    main_container.pack(expand=True, fill="both", padx=50, pady=50)

    title_font = ("Helvetica", 36, "bold")
    title_text = f"What Happened Today In History ({date_str})"
    lbl_title = tk.Label(main_container, text=title_text, font=title_font, fg="white", bg=OVERLAY_COLOR)
    lbl_title.pack(pady=(20, 20))

    hint_font = ("Microsoft YaHei", 12)
    lbl_hint = tk.Label(main_container, 
                        text="↓ Use mouse wheel to scroll / 使用滚轮查看更多 ↓", 
                        font=hint_font, fg="#7F8C8D", bg=OVERLAY_COLOR)
    lbl_hint.pack(pady=(0, 20))
    
    # 滚动区域容器
    canvas_container = tk.Frame(main_container, bg=OVERLAY_COLOR)
    canvas_container.pack(expand=True, fill="both")

    canvas = tk.Canvas(canvas_container, bg=OVERLAY_COLOR, highlightthickness=0)
    # scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
    
    scrollable_frame = tk.Frame(canvas, bg=OVERLAY_COLOR)

    # 绑定事件以调整 Canvas 滚动区域
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((w//2 - 50), 0, window=scrollable_frame, anchor="n") # 居中
    canvas.pack(side="left", fill="both", expand=True)

    # 填充事件内容
    font_year = ("Helvetica", 20, "bold")
    font_en = ("Helvetica", 18)
    font_cn = ("Microsoft YaHei", 16)
    
    for event in events:
        year = event.get("year", "")
        text_en = event.get("text_en", "")
        text_cn = event.get("text_cn", "")
        
        # 事件容器
        event_frame = tk.Frame(scrollable_frame, bg=OVERLAY_COLOR)
        event_frame.pack(fill="x", pady=15)
        
        # 年份 + 英文 (白色)
        full_en = f"[{year}] {text_en}"
        lbl_en = tk.Label(event_frame, text=full_en, font=font_en, fg="white", bg=OVERLAY_COLOR, wraplength=w-200, justify="left")
        lbl_en.pack(anchor="w")
        
        # 中文 (浅色，例如浅灰 #95A5A6 或 #BDC3C7)
        lbl_cn = tk.Label(event_frame, text=text_cn, font=font_cn, fg="#95A5A6", bg=OVERLAY_COLOR, wraplength=w-200, justify="left")
        lbl_cn.pack(anchor="w", pady=(5, 0))

    # 鼠标滚轮支持
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    overlay.bind("<MouseWheel>", _on_mousewheel) # 确保绑定到顶层

    # 底部关闭按钮
    close_frame = tk.Frame(overlay, bg=OVERLAY_COLOR)
    close_frame.pack(side="bottom", pady=40)
    
    def on_close_history(event=None):
        global is_overlay_showing
        canvas.unbind_all("<MouseWheel>") # 解绑滚轮防止影响其他
        overlay.destroy()
        is_overlay_showing = False

    btn_font = ("Microsoft YaHei", 14)
    btn_close = tk.Button(close_frame, text="我知道了 (Close)", font=btn_font, 
                          command=on_close_history,
                          bg="white", fg="#2C3E50", 
                          relief="flat", padx=30, pady=10, cursor="hand2")
    btn_close.pack()
    
    # 绑定 ESC 键关闭
    overlay.bind('<Escape>', on_close_history)

    # 平滑淡入 (复用逻辑)
    target_alpha = 0.95
    step_interval = 20
    alpha_step = target_alpha / (1000 / step_interval) # 1秒内淡入

    def fade_in_history(current_alpha=0):
        if current_alpha < target_alpha:
            new_alpha = current_alpha + alpha_step
            if new_alpha > target_alpha: new_alpha = target_alpha
            overlay.attributes("-alpha", new_alpha)
            overlay.after(step_interval, fade_in_history, new_alpha)
    
    fade_in_history(0)
    overlay.focus_force()

# 获取历史事件的后台线程函数
def _fetch_history_thread():
    try:
        now = datetime.now()
        # 格式化日期字符串用于标题显示 (例如 Feb. 1)
        date_str = now.strftime("%b. %d")
        
        url = f"{HISTORY_URL_BASE}?mm={now.month}&dd={now.day}"
        print(f"[{time.ctime()}] 正在获取历史上的今天: {url}")
        
        response = requests.get(url, timeout=10)
        
        valid_data = False
        events = []
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    events = data
                    valid_data = True
            except json.JSONDecodeError:
                print(f"[{time.ctime()}] 历史事件数据不是有效的JSON。")
        else:
            print(f"[{time.ctime()}] 获取历史事件失败，状态码: {response.status_code}")

        # 回到主线程更新 UI
        if valid_data:
            root.after(0, show_history_overlay, events, date_str)
        else:
            root.after(0, lambda: messagebox.showinfo("On This Day", "暂无相关历史内容。\nNo historical events found for today."))

    except Exception as e:
        print(f"[{time.ctime()}] 获取历史事件时出错: {e}")
        root.after(0, lambda: messagebox.showerror("Error", f"获取内容出错: {e}"))

# 菜单点击回调
def on_this_day_click():
    threading.Thread(target=_fetch_history_thread, daemon=True).start()

# 后台监控线程逻辑
def rest_monitor_loop():
    global last_rest_time, icon
    
    last_menu_update_time = time.time()
    
    while True:
        try:
            time.sleep(5) # 每5秒检查一次
            
            if is_rest_enabled and icon:
                if time.time() - last_menu_update_time > 60:
                    icon.menu = Menu(*build_menu_items())
                    last_menu_update_time = time.time()
            
            # 如果功能未开启，跳过检测逻辑
            if not is_rest_enabled:
                continue
            
            # 检查空闲时间
            idle_time = get_idle_duration()
            
            # 如果闲置超过设定时间（5分钟），视为已休息，重置计时器
            if idle_time > IDLE_RESET_SECONDS:
                if time.time() - last_rest_time > 60: # 避免日志刷屏
                    print(f"[{time.ctime()}] 检测到用户闲置 {idle_time:.1f}s，重置休息计时器。")
                last_rest_time = time.time()
                # 重置时间后，刷新菜单
                if icon:
                    icon.menu = Menu(*build_menu_items())
                continue
            
            # 检查是否到了休息时间
            elapsed = time.time() - last_rest_time
            if elapsed > REST_INTERVAL_SECONDS:
                # 检查是否全屏
                if is_foreground_fullscreen():
                    print(f"[{time.ctime()}] 到了休息时间，但检测到全屏应用，暂缓提醒。")
                    # 暂缓 1 分钟再检测，而不是重置
                elif not is_overlay_showing:
                    print(f"[{time.ctime()}] 触发休息提醒！")
                    # 在主线程中显示UI
                    root.after(0, show_rest_overlay)
                    
        except Exception as e:
            print(f"[{time.ctime()}] 休息监控线程出错: {e}")
            time.sleep(10)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_executable_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(__file__)

def is_startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False

#切换开机启动选项        
def toggle_startup():
    executable_path = get_executable_path()
    if is_startup_enabled():
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, APP_NAME)
            print(f"[{time.ctime()}] 已成功从开机启动项中移除。")
        except Exception as e:
            print(f"[{time.ctime()}] 移除开机启动项失败: {e}")
    else:
        try:
            if executable_path.endswith('.exe'):
                command = f'"{executable_path}"'
            else:
                pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
                command = f'"{pythonw_path}" "{executable_path}"'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            print(f"[{time.ctime()}] 已成功添加到开机启动项。")
        except Exception as e:
            print(f"[{time.ctime()}] 添加开机启动项失败: {e}")

#下载图片
def download_image(image_url, save_path):
    try:
        print(f"[{time.ctime()}] 正在从 {image_url} 下载图片...")
        response = requests.get(image_url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(save_path, 'wb') as f: f.write(response.content)
            print(f"[{time.ctime()}] 图片已成功保存到: {save_path}")
            return True
        else:
            print(f"[{time.ctime()}] 下载失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[{time.ctime()}] 下载时发生错误: {e}")
        return False

#设置墙纸
def set_as_wallpaper(image_path):
    if os.name != 'nt': return False
    try:
        print(f"[{time.ctime()}] 正在设置桌面墙纸...")
        SPI_SETDESKWALLPAPER = 20
        abs_image_path = os.path.abspath(image_path)
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, abs_image_path, 3)
        print(f"[{time.ctime()}] 桌面墙纸设置成功！")
        return True
    except Exception as e:
        print(f"[{time.ctime()}] 设置墙纸时发生错误: {e}")
        return False

#检查互联网连接
def check_internet_connection():
    try:
        requests.get("https://www.bing.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

# 计算文件的 SHA256 哈希值
def calculate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"[{time.ctime()}] 计算文件哈希失败: {e}")
        return None

# 在主线程中显示版权信息弹窗
def show_copyright_info():
    root.after(0, _show_copyright_dialog_thread_safe)

# 实际显示弹窗函数
def _show_copyright_dialog_thread_safe():
    if bing_copyright and bing_copyright_url:
        if messagebox.askyesno("图片信息", f"{bing_copyright}\n\n查看相关信息？"):
            webbrowser.open(bing_copyright_url)
    elif bing_copyright:
        messagebox.showinfo("图片信息", bing_copyright)

# 显示“关于”弹窗
def show_about_dialog():
    root.after(0, _show_about_dialog_thread_safe)

def _show_about_dialog_thread_safe():
    title = "关于 Binglish"
    message = (
        f"Binglish桌面英语 {VERSION}\n"
        f"{PROJECT_URL}\n"
    )
    messagebox.showinfo(title, message)

# 显示“Song of the Day”描述弹窗
def show_music_description_dialog():
    root.after(0, _show_music_description_dialog_thread_safe)

# 实际显示弹窗函数
def _show_music_description_dialog_thread_safe():
    if not bing_music_desc:
        if bing_music_name: 
             messagebox.showinfo(f"歌曲: {bing_music_name}", "没有可用的歌曲描述。")
        return

    try:
        music_window = tk.Toplevel(root)
        music_window.title(f"歌曲: {bing_music_name}")
        music_window.resizable(False, False)
        music_window.attributes("-topmost", True) 

        desc_font = ("TkDefaultFont", 15) 
        button_font = ("TkDefaultFont", 12)

        label_desc = tk.Message(music_window, text=bing_music_desc, width=600, justify="left", font=desc_font)
        label_desc.pack(padx=10, pady=(10, 5)) 

        button_frame = tk.Frame(music_window)
        button_frame.pack(pady=(5, 10), padx=10, fill="x")

        def play_and_close():
            print(f"[{time.ctime()}] 用户从歌曲信息弹窗点击播放。")
            music_window.destroy() 

            global is_music_playing
            if not is_music_playing:
                toggle_music_playback() 

        def cancel_and_close():
            music_window.destroy()

        btn_play = tk.Button(button_frame, text="播放", command=play_and_close, width=10, font=button_font)
        btn_play.pack(side="left", expand=True, fill="x", padx=(5, 5))

        btn_cancel = tk.Button(button_frame, text="取消", command=cancel_and_close, width=10, font=button_font)
        btn_cancel.pack(side="right", expand=True, fill="x", padx=(5, 5))

        music_window.update_idletasks()
        x = root.winfo_screenwidth() // 2 - music_window.winfo_width() // 2
        y = root.winfo_screenheight() // 2 - music_window.winfo_height() // 2
        music_window.geometry(f"+{x}+{y}")
        
        music_window.focus_set()
        music_window.grab_set() 
        music_window.wait_window() 
    
    except Exception as e:
        print(f"[{time.ctime()}] 显示自定义音乐弹窗时发生错误: {e}")
        messagebox.showerror("弹窗错误", f"无法显示歌曲信息弹窗: {e}")

# 在主线程中显示二维码弹窗
def show_share_qr():
    root.after(0, _show_share_qr_thread_safe)

# 实际显示二维码弹窗函数
def _show_share_qr_thread_safe():
    global bing_id
    if not bing_id:
        messagebox.showerror("错误", "未找到图片ID，无法分享。")
        return
    
    share_url = f"https://ss.blueforge.org/bing/s/{bing_id}.htm"
    print(f"[{time.ctime()}] 生成分享二维码: {share_url}")
    
    try:
        qr_window = tk.Toplevel(root)
        qr_window.title("分享此壁纸")
        qr_window.resizable(False, False)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_window.tk_image = ImageTk.PhotoImage(img)
        
        label_image = tk.Label(qr_window, image=qr_window.tk_image)
        label_image.pack(padx=10, pady=10)
        
        label_text = tk.Label(qr_window, text="请使用手机(系统相机、浏览器等)扫一扫以分享")
        label_text.pack(pady=5)
        
        qr_window.update_idletasks()
        x = root.winfo_screenwidth() // 2 - qr_window.winfo_width() // 2
        y = root.winfo_screenheight() // 2 - qr_window.winfo_height() // 2
        qr_window.geometry(f"+{x}+{y}")
        
        qr_window.focus_set() 
        
    except Exception as e:
        print(f"[{time.ctime()}] 生成二维码时发生错误: {e}")
        messagebox.showerror("二维码错误", f"生成二维码时发生错误: {e}")

# 播放歌曲的独立进程任务
def _play_music_task(url):
    try:
        from playsound3 import playsound
        print(f"[{time.ctime()}] 音乐播放进程启动: {url}")
        playsound(url)
        print(f"[{time.ctime()}] 音乐播放进程结束。")
    except Exception as e:
        print(f"[{time.ctime()}] 音乐播放进程中发生错误: {e}")

# 定期检查音乐播放进程的状态
def check_music_status():
    global is_music_playing, music_process, icon, music_check_timer, root

    if is_music_playing and music_process and not music_process.is_alive():
        print(f"[{time.ctime()}] 监测到音乐播放进程已结束。")
        is_music_playing = False
        music_process = None
        
        if icon:
            print(f"[{time.ctime()}] 正在更新右键菜单（音乐播放结束）。")
            icon.menu = Menu(*build_menu_items())
        
        if music_check_timer:
            root.after_cancel(music_check_timer)
            music_check_timer = None

    elif is_music_playing and music_process and music_process.is_alive():
        music_check_timer = root.after(1000, check_music_status) 
    
    else:
        if music_check_timer:
            root.after_cancel(music_check_timer)
            music_check_timer = None

# 切换音乐播放/停止
def toggle_music_playback():
    global is_music_playing, music_process, icon, music_check_timer
    
    if is_music_playing:
        print(f"[{time.ctime()}] 正在停止音乐...")
        if music_process and music_process.is_alive():
            music_process.terminate()
            music_process = None
        is_music_playing = False
        
        if music_check_timer:
            root.after_cancel(music_check_timer)
            music_check_timer = None
            
        print(f"[{time.ctime()}] 音乐已停止。")
    
    elif bing_music_url:
        print(f"[{time.ctime()}] 正在开始播放音乐: {bing_music_url}")
        try:
            if music_process and music_process.is_alive():
                music_process.terminate()
            
            music_process = multiprocessing.Process(target=_play_music_task, args=(bing_music_url,), daemon=True)
            music_process.start()
            is_music_playing = True
            
            if music_check_timer: 
                root.after_cancel(music_check_timer)
            music_check_timer = root.after(1000, check_music_status)
            
            print(f"[{time.ctime()}] 音乐播放进程已启动。")
        except Exception as e:
            print(f"[{time.ctime()}] 启动音乐播放进程失败: {e}")
            is_music_playing = False
            music_process = None
    
    if icon:
        print(f"[{time.ctime()}] 正在更新右键菜单（音乐播放状态）。")
        icon.menu = Menu(*build_menu_items())

# 动态构建菜单项
def build_menu_items():
    menu_items = []

    if bing_url:
        menu_items.append(item(f'查单词 {bing_word}', lambda: webbrowser.open(bing_url)))
    
    if bing_mp3:
        menu_items.append(item(f'读单词 {bing_word}', lambda: threading.Thread(target=play_word_sound, daemon=True).start()))
    
    if bing_url or bing_mp3:
        menu_items.append(Menu.SEPARATOR)

    menu_items.append(item('随机复习', lambda: threading.Thread(target=update_wallpaper_job, args=(True,), daemon=True).start()))
    
    wallpaper_path = os.path.join(os.path.dirname(get_executable_path()), "wallpaper.jpg")
    if os.path.exists(wallpaper_path):
        menu_items.append(item('复制保存', copy_and_save_wallpaper))

    if bing_copyright:
        menu_items.append(item('壁纸信息', show_copyright_info))

    if bing_id:
        menu_items.append(Menu.SEPARATOR)
        menu_items.append(item('分享壁纸', show_share_qr))
    
    rest_label = '提醒休息'
    if is_rest_enabled:
        elapsed = time.time() - last_rest_time
        remaining = max(0, REST_INTERVAL_SECONDS - elapsed)
        mins = int(remaining / 60)
        rest_label = f'提醒休息 (剩余{mins}分)'
    
    menu_items.append(item(rest_label, toggle_rest_reminder, checked=lambda item: is_rest_enabled))

    menu_items.append(Menu.SEPARATOR)
    menu_items.append(item('Today in History', on_this_day_click))
    if bing_music_name and bing_music_url:
        menu_items.append(item('==Song of the Day==', None, enabled=False))
        
        if bing_music_desc:
            menu_items.append(item(f'  {bing_music_name}', show_music_description_dialog))
        else:
            menu_items.append(item(f'  {bing_music_name}', None, enabled=False))
        
        play_stop_text = "停止播放" if is_music_playing else "播放歌曲"
        menu_items.append(item(f'  {play_stop_text}', lambda: toggle_music_playback()))
        
        menu_items.append(Menu.SEPARATOR)
        
    menu_items.append(item('开机运行', toggle_startup, checked=lambda item: is_startup_enabled()))

    update_label = '检查更新'
    if new_version_available:
        update_label = '检查更新 (有新版本)'
    
    if getattr(sys, 'frozen', False):
        menu_items.append(item(update_label, lambda: check_for_updates(icon)))

    menu_items.append(item('设置', open_config_file))
    
    menu_items.append(item('关于', show_about_dialog)) 
    menu_items.append(item('退出', lambda: quit_app(icon)))
    
    return tuple(menu_items)

#更新墙纸任务
def update_wallpaper_job(is_random=False):

    global icon, bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id
    global bing_music_name, bing_music_url, bing_music_desc, is_music_playing, music_process
    
    bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id = None, None, None, None, None, None
    bing_music_name, bing_music_url, bing_music_desc = None, None, None
    
    if music_process and music_process.is_alive():
        music_process.terminate()
        music_process = None
    is_music_playing = False

    if icon:
        print(f"[{time.ctime()}] 正在更新右键菜单（清空状态）。")
        icon.menu = Menu(*build_menu_items())

    base_directory = os.path.dirname(get_executable_path())
    save_filename = "wallpaper.jpg"
    full_save_path = os.path.join(base_directory, save_filename)
    
    try:
        # ctypes.windll.shcore.SetProcessDpiAwareness(2) 
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        dc = user32.GetDC(None)
        width = gdi32.GetDeviceCaps(dc, 8) 
        height = gdi32.GetDeviceCaps(dc, 10)
        user32.ReleaseDC(None, dc)
        dynamic_image_url = f"{IMAGE_URL}&w={width}&h={height}"
    except Exception as e:
        print(f"[{time.ctime()}] 获取屏幕分辨率失败: {e}，将使用默认URL: {IMAGE_URL}")
        dynamic_image_url = IMAGE_URL
    
    if is_random:
        dynamic_image_url += "&random"
        print(f"[{time.ctime()}] 随机复习模式，将使用URL: {dynamic_image_url}")
    else:
        print(f"[{time.ctime()}] 正常循环模式，将使用URL: {dynamic_image_url}")

    try:
        print(f"[{time.ctime()}] 正在从 {MUSIC_JSON_URL} 下载音乐信息...")
        music_response = requests.get(MUSIC_JSON_URL, timeout=10)
        if music_response.status_code == 200:
            music_data = music_response.json()
            bing_music_name = music_data.get("name")
            bing_music_url = music_data.get("url")
            bing_music_desc = music_data.get("description")
            
            if bing_music_name and bing_music_url:
                print(f"[{time.ctime()}] 音乐信息下载成功: {bing_music_name}")
                if bing_music_desc:
                    print(f"    - 音乐描述: {bing_music_desc[:20]}...")
            else:
                print(f"[{time.ctime()}] 音乐JSON格式不正确或缺少name/url。")
                bing_music_name, bing_music_url, bing_music_desc = None, None, None 
        else:
            print(f"[{time.ctime()}] 下载音乐信息失败，状态码: {music_response.status_code}")
            bing_music_name, bing_music_url, bing_music_desc = None, None, None 
    except Exception as e:
        print(f"[{time.ctime()}] 下载音乐信息时发生错误: {e}")
        bing_music_name, bing_music_url, bing_music_desc = None, None, None 

    image_downloaded = download_image(dynamic_image_url, full_save_path)
    if image_downloaded:
        try:
            print(f"[{time.ctime()}] 正在从 {full_save_path} 提取EXIF信息 (使用 exifread)...")
            
            with open(full_save_path, 'rb') as f:
                tags = exifread.process_file(f) 

            if tags:
                bing_word = str(tags.get('Image Artist', '')).strip()
                
                bing_url = str(tags.get('Image ImageDescription', '')).strip()
                
                bing_mp3 = str(tags.get('Image DocumentName', '')).strip()
                
                copyright_info = str(tags.get('Image Copyright', '')).strip()

                if copyright_info:
                    if "||" in copyright_info:
                        parts = copyright_info.split("||", 1)
                        bing_copyright = parts[0].strip()
                        bing_copyright_url = parts[1].strip()
                    else:
                        bing_copyright = copyright_info
                        bing_copyright_url = None
                else:
                    bing_copyright = None
                    bing_copyright_url = None

                bing_id = str(tags.get('Image Software', '')).strip()
                
                print(f"[{time.ctime()}] EXIF信息提取成功:")
                print(f"    - Artist (bing_word): {bing_word}")
                print(f"    - ImageDescription (bing_url): {bing_url}")
                print(f"    - DocumentName (bing_mp3): {bing_mp3}")
                print(f"    - Copyright (bing_copyright): {bing_copyright}")
                print(f"    - Copyright URL (bing_copyright_url): {bing_copyright_url}")
                print(f"    - Software (bing_id): {bing_id}")

            else:
                print(f"[{time.ctime()}] 图片中未找到EXIF信息，清空旧数据。")
                bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id = None, None, None, None, None, None

        except Exception as e:
            print(f"[{time.ctime()}] 提取EXIF信息时发生错误: {e}")
            bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id = None, None, None, None, None, None
        
        if icon:
            print(f"[{time.ctime()}] 正在更新右键菜单...")
            icon.menu = Menu(*build_menu_items())

        if set_as_wallpaper(full_save_path):
            return True 
    
    return False

#定时函数
def run_scheduler(icon):
    print(f"[{time.ctime()}] 程序启动，正在检测网络连接...")
    while not check_internet_connection():
        print(f"[{time.ctime()}] 无网络连接，将在 {INTERNET_CHECK_INTERVAL_SECONDS} 秒后重试...")
        time.sleep(INTERNET_CHECK_INTERVAL_SECONDS)

    print(f"[{time.ctime()}] 已连接到互联网，开始尝试首次壁纸更新...")
    
    threading.Thread(target=check_update_startup_thread, daemon=True).start()

    while not update_wallpaper_job():
        if not icon.visible:
            print(f"[{time.ctime()}] 用户在首次更新完成前退出。")
            return
            
        print(f"[{time.ctime()}] 更新失败，将在 {DOWNLOAD_RETRY_INTERVAL_SECONDS} 秒后重试...")
        time.sleep(DOWNLOAD_RETRY_INTERVAL_SECONDS)

    print(f"[{time.ctime()}] F首次壁纸更新成功。")
    print(f"[{time.ctime()}] 已切换到定时更新模式，每 {UPDATE_INTERVAL_SECONDS / 3600:.1f} 小时更新一次。")

    while icon.visible:
        time.sleep(UPDATE_INTERVAL_SECONDS)
        
        if not icon.visible:
            break
            
        print(f"\n[{time.ctime()}] 时间到，开始执行定时更新。")
        if check_internet_connection():
            update_wallpaper_job()
        else:
            print(f"[{time.ctime()}] 检测到无网络连接，跳过本次更新。")
    print(f"[{time.ctime()}] 定时更新线程已退出。")

# 复制并保存当前壁纸
def copy_and_save_wallpaper():
    try:
        base_directory = os.path.dirname(get_executable_path())
        source_path = os.path.join(base_directory, "wallpaper.jpg")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination_filename = f"{timestamp}.jpg"
        destination_path = os.path.join(base_directory, destination_filename)
        
        shutil.copy(source_path, destination_path)
        print(f"[{time.ctime()}] 壁纸已从 {source_path} 复制到 {destination_path}")
        
        root.after(0, lambda: messagebox.showinfo("操作成功", "壁纸已成功复制至程序所在目录"))
    except FileNotFoundError:
        print(f"[{time.ctime()}] 复制操作失败: wallpaper.jpg 不存在。")
        root.after(0, lambda: messagebox.showerror("操作失败", "未找到 wallpaper.jpg 文件。"))
    except Exception as e:
        print(f"[{time.ctime()}] 复制壁纸时发生错误: {e}")
        root.after(0, lambda: messagebox.showerror("操作失败", f"复制文件时出错: {e}"))

#更新新版本程序
def download_and_update(icon, expected_hash=None):
    new_exe_path = os.path.join(os.path.dirname(get_executable_path()), "bing_new.exe")
    try:
        print(f"[{time.ctime()}] 正在从 {DOWNLOAD_URL} 下载新版本...")
        response = requests.get(DOWNLOAD_URL, stream=True, timeout=60)
        if response.status_code == 200:
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[{time.ctime()}] 新版本已下载到: {new_exe_path}")

            if expected_hash:
                print(f"[{time.ctime()}] 正在校验文件完整性...")
                downloaded_hash = calculate_file_hash(new_exe_path)
                if not downloaded_hash or downloaded_hash.lower() != expected_hash.lower():
                    print(f"[{time.ctime()}] 哈希校验失败！期望: {expected_hash}, 实际: {downloaded_hash}")
                    try:
                        os.remove(new_exe_path)
                        print(f"[{time.ctime()}] 已删除校验失败的文件。")
                    except Exception as e:
                        print(f"[{time.ctime()}] 删除失败文件时出错: {e}")
                    
                    root.after(0, lambda: messagebox.showerror("更新失败", "下载的文件校验失败，可能已损坏或被篡改。"))
                    return # 终止更新流程
                else:
                    print(f"[{time.ctime()}] 哈希校验通过。")
            
            updater_bat_path = os.path.join(os.path.dirname(get_executable_path()), "updater.bat")
            current_exe_path = get_executable_path()
            
            with open(updater_bat_path, 'w') as f:
                f.write(f'''
@echo off
echo Waiting for {APP_NAME} to close...
taskkill /F /IM "{os.path.basename(current_exe_path)}" > nul
timeout /t 2 /nobreak > nul
echo Replacing old version...
del "{current_exe_path}"
rename "{new_exe_path}" "{os.path.basename(current_exe_path)}"
echo Starting new version...
start "" "{current_exe_path}"
echo Cleaning up...
del "%~f0"
''')
            subprocess.Popen(f'"{updater_bat_path}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print(f"[{time.ctime()}] 程序正在退出以进行更新...")
            root.after(100, quit_app, icon)
            
        else:
            root.after(0, lambda: messagebox.showerror("下载失败", f"下载新版本失败。状态码: {response.status_code}"))
            print(f"[{time.ctime()}] 下载新版本失败。状态码: {response.status_code}")

    except requests.exceptions.RequestException as e:
        root.after(0, lambda: messagebox.showerror("下载失败", f"下载新版本时发生错误: {e}"))
        print(f"[{time.ctime()}] 下载时发生错误: {e}")

#检查更新提示框
def show_update_dialog(result, icon, silent=False):
    if len(result) == 4:
        status, version_or_error, releasenotes, hash_value = result
    else:
        status, version_or_error, releasenotes = result
        hash_value = None
    
    if silent:
        if status == 'update_available':
            global new_version_available
            new_version_available = True
            print(f"[{time.ctime()}] 静默检测：发现新版本 {version_or_error}")
            
            if icon:
                icon.menu = Menu(*build_menu_items())
        return

    if status == 'update_available':
        message = f"有新版本 ({version_or_error}) 可用。\n\n更新说明:\n{releasenotes}\n\n您想现在更新吗？\n点击确定后程序将在后台更新。"
        if messagebox.askyesno("发现新版本", message):
            threading.Thread(target=download_and_update, args=(icon, hash_value)).start()
    elif status == 'no_update':
        messagebox.showinfo("没有更新", "您使用的已是最新版本。")
    elif status == 'error':
        messagebox.showerror("检查更新失败", f"检查更新时发生错误: {version_or_error}")

#检查更新函数
def perform_network_check(icon, silent=False):
    if not silent:
        print(f"[{time.ctime()}] 正在检查更新...")
        
    try:
        response = requests.get(RELEASE_JSON_URL, timeout=20)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info.get("version")
        releasenotes = release_info.get("releasenotes")
        hash_value = release_info.get("hash")
        
        if not silent:
            print(f"[{time.ctime()}] 当前版本: {VERSION}, 最新版本: {latest_version}")
        
        if latest_version and latest_version != VERSION:
            result = ('update_available', latest_version, releasenotes, hash_value)
        else:
            result = ('no_update', None, None, None)
            
    except requests.exceptions.RequestException as e:
        if not silent:
            print(f"[{time.ctime()}] F检查更新时发生错误: {e}")
        result = ('error', e, None, None)
    except json.JSONDecodeError as e:
        if not silent:
            print(f"[{time.ctime()}] 解析更新信息时发生错误: {e}")
        result = ('error', f"无法解析更新文件: {e}", None, None)
    
    root.after(0, show_update_dialog, result, icon, silent)

#检查更新线程
def check_for_updates(icon):
    threading.Thread(target=perform_network_check, args=(icon, False)).start()

# 启动时静默检查更新线程
def check_update_startup_thread():
    time.sleep(5) 
    perform_network_check(None, silent=True)

#播放单词相关语音
def play_word_sound():
    if bing_mp3:
        try:
            print(f"[{time.ctime()}] 正播放在线音频: {bing_mp3}")
            playsound(bing_mp3)
            print(f"[{time.ctime()}] 音频播放完毕。")
        except Exception as e:
            print(f"[{time.ctime()}] 播放音频时发生错误: {e}")
            root.after(0, lambda: messagebox.showerror("播放失败", f"无法播放在线音频：{e}"))

#退出程序
def quit_app(icon):
    print("正在退出程序...")
    
    # 停止音乐播放进程
    global music_process
    if music_process and music_process.is_alive():
        print("正在停止音乐播放进程...")
        music_process.terminate()
        music_process = None

    if icon:
        icon.stop()
    if root:
        root.destroy()

def main():
    global root, icon, is_rest_enabled
    
    # 添加全局高DPI感知设置，解决屏幕缩放导致遮罩无法覆盖全屏的问题
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) 
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

    root = tk.Tk()
    root.withdraw()

    load_config_and_init()
    print(f"[{time.ctime()}] 休息提醒功能状态: {'开启' if is_rest_enabled else '关闭'}")

    try:
        icon_path = resource_path(ICON_FILENAME)
        image = Image.open(icon_path)
    except FileNotFoundError:
        print(f"错误：找不到图标文件 '{ICON_FILENAME}'。")
        sys.exit(1)
    
    initial_menu_items = build_menu_items()
    icon = Icon(APP_NAME, image, "Binglish桌面英语", menu=Menu(*initial_menu_items))
    
    threading.Thread(target=icon.run, daemon=True).start()

    update_thread = threading.Thread(target=run_scheduler, args=(icon,), daemon=True)
    update_thread.start()

    # 启动休息监控线程
    monitor_thread = threading.Thread(target=rest_monitor_loop, daemon=True)
    monitor_thread.start()
    
    print("程序已启动并在后台运行。请在任务栏右下角查找图标。")
    root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()