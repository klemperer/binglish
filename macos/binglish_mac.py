import requests
import os
import sys
import time
import threading
import webbrowser
from PIL import Image
import exifread
from pystray import MenuItem as item, Icon, Menu
import subprocess
import json
import shutil 
from datetime import datetime 
import multiprocessing
import random 
import configparser
import re
import hashlib

import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

VERSION = "1.0.3"
RELEASE_JSON_URL = "https://ss.blueforge.org/bing/release_mac.json" 
DOWNLOAD_URL = "https://ss.blueforge.org/bing/binglish_mac"          
IMAGE_URL = f"https://ss.blueforge.org/bing?os=mac&v={VERSION}"  
MUSIC_JSON_URL = "https://ss.blueforge.org/bing/songoftheday.json" 
USELESS_FACT_URL = "https://ss.blueforge.org/bing/uselessfact.json"
HISTORY_URL_BASE = "https://ss.blueforge.org/getHistory"
GAME_DATA_URL = "https://ss.blueforge.org/bing/games.json"

UPDATE_INTERVAL_SECONDS = 3 * 60 * 60 
APP_NAME = "Binglish"
ICON_FILENAME = "binglish_mac.png" 

DOWNLOAD_RETRY_INTERVAL_SECONDS = 30
INTERNET_CHECK_INTERVAL_SECONDS = 60
PROJECT_URL = "https://github.com/klemperer/binglish" 
CONFIG_FILENAME = "binglish.ini"

REST_INTERVAL_SECONDS = 2700     
IDLE_RESET_SECONDS = 300         
REST_LOCK_SECONDS = 30           
OVERLAY_COLOR = "#2C3E50"        

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

bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id = None, None, None, None, None, None
bing_music_name, bing_music_url, bing_music_desc = None, None, None
is_music_playing = False 
music_process = None 
music_check_timer = None 

is_rest_enabled = False 
last_rest_time = time.time() 
is_overlay_showing = False 
new_version_available = False 
icon = None

# ==========================================
# 🍎 Mac 原生交互增强组件 (替代 messagebox)
# ==========================================
def escape_applescript(text):
    """
    功能：转义文本中的反斜杠和双引号。
    防止在通过 AppleScript 执行系统弹窗时因特殊字符导致脚本崩溃。
    """
    return str(text).replace('\\', '\\\\').replace('"', '\\"')

def mac_alert(title, text, is_error=False):
    """
    功能：调用 macOS 原生的弹窗警告 (AppleScript)。
    替代丑陋且易崩溃的 tkinter.messagebox.showinfo/showerror，用于展示普通信息或错误提示。
    """
    icon_str = "stop" if is_error else "note"
    script = f'display dialog "{escape_applescript(text)}" with title "{escape_applescript(title)}" buttons {{"OK"}} default button "OK" with icon {icon_str}'
    subprocess.run(['osascript', '-e', script])

def mac_askyesno(title, text, yes_text="Yes", no_text="No"):
    """
    功能：调用 macOS 原生的确认弹窗 (AppleScript)。
    替代 tkinter.messagebox.askyesno，让用户进行是/否的选择（如确认更新、确认打开链接），并返回布尔值。
    """
    script = f'button returned of (display dialog "{escape_applescript(text)}" with title "{escape_applescript(title)}" buttons {{"{no_text}", "{yes_text}"}} default button "{yes_text}")'
    try:
        out = subprocess.check_output(['osascript', '-e', script], text=True).strip()
        return out == yes_text
    except:
        return False

# ==========================================
# 🚀 独立进程 UI 渲染模块 (彻底解决线程冲突)
# ==========================================
def proc_share_qr(share_url):
    """
    功能：独立进程中渲染并显示二维码弹窗。
    用户点击分享壁纸时，弹出一个包含专属链接二维码的 Tkinter 窗口，供手机扫码。
    """
    import tkinter as tk
    import qrcode
    from PIL import ImageTk
    qr_window = tk.Tk()
    qr_window.title("分享此壁纸")
    qr_window.resizable(False, False)
    qr_window.attributes("-topmost", True)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(share_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    tk_image = ImageTk.PhotoImage(img)
    tk.Label(qr_window, image=tk_image).pack(padx=10, pady=10)
    tk.Label(qr_window, text="请使用手机扫一扫以分享").pack(pady=5)
    qr_window.geometry(f"+{qr_window.winfo_screenwidth() // 2 - qr_window.winfo_width() // 2}+{qr_window.winfo_screenheight() // 2 - qr_window.winfo_height() // 2}")
    qr_window.focus_force()
    qr_window.mainloop()

def proc_history_overlay(events, date_str, bg_color):
    """
    功能：独立进程中渲染并显示“历史上的今天”全屏遮罩。
    接收网络请求获取的历史事件列表，通过原生全屏 API 和画布滚动条展示中英文历史信息。
    """
    import tkinter as tk
    from tkmacosx import Button as MacButton
    overlay = tk.Tk()
    overlay.title("On This Day")
    w, h = overlay.winfo_screenwidth(), overlay.winfo_screenheight()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.0)
    overlay.configure(bg=bg_color)
    
    main_container = tk.Frame(overlay, bg=bg_color)
    main_container.pack(expand=True, fill="both", padx=50, pady=50)
    tk.Label(main_container, text=f"What Happened Today In History ({date_str})", font=("Helvetica", 42, "bold"), fg="white", bg=bg_color).pack(pady=(20, 30))
    tk.Label(main_container, text="↓ Use mouse wheel to scroll / 使用滚轮查看更多 ↓", font=("Microsoft YaHei", 16), fg="#7F8C8D", bg=bg_color).pack(pady=(0, 30))
    
    canvas_container = tk.Frame(main_container, bg=bg_color)
    canvas_container.pack(expand=True, fill="both")
    canvas = tk.Canvas(canvas_container, bg=bg_color, highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg=bg_color)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((w//2 - 50), 0, window=scrollable_frame, anchor="n")
    canvas.pack(side="left", fill="both", expand=True)
    
    for event in events:
        event_frame = tk.Frame(scrollable_frame, bg=bg_color)
        event_frame.pack(fill="x", pady=20)
        tk.Label(event_frame, text=f"[{event.get('year', '')}] {event.get('text_en', '')}", font=("Helvetica", 22), fg="white", bg=bg_color, wraplength=w-300, justify="left").pack(anchor="w")
        tk.Label(event_frame, text=event.get('text_cn', ''), font=("Microsoft YaHei", 18), fg="#95A5A6", bg=bg_color, wraplength=w-300, justify="left").pack(anchor="w", pady=(8, 0))

    def _on_mousewheel(e): canvas.yview_scroll(int(-1*(e.delta)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    close_frame = tk.Frame(overlay, bg=bg_color)
    close_frame.pack(side="bottom", pady=50)
    MacButton(close_frame, text="我知道了 (Close)", font=("Microsoft YaHei", 18), command=overlay.destroy, bg="white", fg="#2C3E50", borderless=1, padx=40, pady=15).pack()
    overlay.bind('<Escape>', lambda e: overlay.destroy())

    def fade_in(current_alpha=0):
        if current_alpha < 0.85:
            overlay.attributes("-alpha", current_alpha + 0.05)
            overlay.after(20, fade_in, current_alpha + 0.05)
    fade_in(0)
    
    overlay.focus_force()
    overlay.mainloop()

def proc_rest_overlay(quote_en, quote_cn, lock_seconds, bg_color, current_word, fact_url):
    """
    功能：独立进程中渲染强制休息全屏遮罩。
    接管屏幕，展示休息格言、倒计时按钮，并自动请求冷知识与随机生成单词拷问，强制用户暂离屏幕。
    """
    import tkinter as tk
    import time, random, threading, requests
    from tkmacosx import Button as MacButton
    
    overlay = tk.Tk()
    overlay.title("Time to Rest")
    w = overlay.winfo_screenwidth()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.0)
    overlay.configure(bg=bg_color)

    container = tk.Frame(overlay, bg=bg_color)
    container.pack(expand=True, fill="both")
    
    bottom_frame = tk.Frame(container, bg=bg_color)
    bottom_frame.pack(side="bottom", fill="x", pady=(0, 60), padx=50)
    lbl_fact_en = tk.Label(bottom_frame, text="", font=("Helvetica", 18, "italic"), fg="#BDC3C7", bg=bg_color, wraplength=w-200)
    lbl_fact_en.pack(side="top", pady=(0, 10))
    lbl_fact_cn = tk.Label(bottom_frame, text="正在获取冷知识...", font=("Microsoft YaHei", 16), fg="#7F8C8D", bg=bg_color, wraplength=w-200)
    lbl_fact_cn.pack(side="top")

    def fetch_fact():
        try:
            res = requests.get(fact_url, timeout=3)
            if res.status_code == 200:
                data = res.json()
                overlay.after(0, lambda: [lbl_fact_en.config(text=f"Did you know? {data.get('en', '')}"), lbl_fact_cn.config(text=data.get('cn', ''))])
        except: pass
    threading.Thread(target=fetch_fact, daemon=True).start()

    center_frame = tk.Frame(container, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.45, anchor="center")
    
    tk.Label(center_frame, text=quote_en, font=("Helvetica", 42, "bold"), fg="white", bg=bg_color, wraplength=w-100).pack(pady=(0, 30))
    tk.Label(center_frame, text=quote_cn, font=("Microsoft YaHei", 32), fg="#BDC3C7", bg=bg_color, wraplength=w-100).pack(pady=(0, 50))

    lbl_word = None
    if current_word:
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
        lbl_word = tk.Label(center_frame, text=random.choice(hint_templates), font=("Microsoft YaHei", 24, "bold"), fg="#A9DFBF", bg=bg_color, wraplength=w-100)

    btn_text = tk.StringVar(value=f"我休息好了 ({lock_seconds}s)")
    btn_ok = MacButton(center_frame, textvariable=btn_text, font=("Microsoft YaHei", 18), command=overlay.destroy, state="disabled", bg="#5D6D7E", fg="white", borderless=1, padx=40, pady=15)
    btn_ok.pack()

    def start_countdown(sec):
        if sec == lock_seconds // 2 and lbl_word:
            lbl_word.pack(pady=(0, 50), before=btn_ok)
            
        if sec > 0:
            btn_text.set(f"我休息好了 ({sec}s)")
            overlay.after(1000, start_countdown, sec-1)
        else:
            btn_text.set("我休息好了")
            btn_ok.config(state="normal", bg="white", fg="#2C3E50")
            overlay.bind('<Return>', lambda e: overlay.destroy())
            overlay.focus_force()

    def fade_in(current_alpha=0):
        if current_alpha < 0.85:
            overlay.attributes("-alpha", current_alpha + 0.05)
            overlay.after(20, fade_in, current_alpha + 0.05)
        else:
            start_countdown(lock_seconds)
            
    fade_in(0)
    overlay.focus_force()
    overlay.mainloop()

def proc_game_overlay(bg_color, game_data_url):
    """
    功能：独立进程中渲染 Binglish Games 游戏大厅及游戏内容。
    负责游戏数据拉取、游戏界面切换，并包含 Sentence Master, Wordle 和 Mini Crossword 的所有游戏逻辑与判定动画。
    """
    import tkinter as tk
    from tkmacosx import Button as MacButton
    import requests, re, random, os, threading, time
    import subprocess
    
    overlay = tk.Tk()
    overlay.title("Binglish Games")
    overlay.attributes("-fullscreen", True) 
    overlay.attributes("-alpha", 0.0)
    overlay.configure(bg=bg_color)

    game_data = {}
    try:
        res = requests.get(game_data_url, timeout=5)
        if res.status_code == 200: game_data = res.json()
    except: pass
    if not game_data: overlay.destroy(); return

    def play_sound(t):
        try:
            sound_file = '/System/Library/Sounds/Tink.aiff' if t == "click" else '/System/Library/Sounds/Glass.aiff'
            subprocess.Popen(['afplay', sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    game_active = False
    start_time = 0
    timer_var = tk.StringVar(value="Time: 00:00")
    
    def update_timer():
        if game_active:
            elapsed = int(time.time() - start_time)
            timer_var.set(f"Time: {elapsed//60:02d}:{elapsed%60:02d}")
            overlay.after(1000, update_timer)

    lobby_frame = tk.Frame(overlay, bg=bg_color)
    lobby_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Label(lobby_frame, text="Binglish Games", font=("Helvetica", 64, "bold"), fg="#F1C40F", bg=bg_color).pack(pady=(0, 20))
    tk.Label(lobby_frame, text="请选择一个单词游戏开始挑战：", font=("Microsoft YaHei", 22), fg="#BDC3C7", bg=bg_color).pack(pady=(0, 50))
    
    btn_frame = tk.Frame(lobby_frame, bg=bg_color); btn_frame.pack(pady=20)
    game_container = tk.Frame(overlay, bg=bg_color)

    def start_game(game_type):
        nonlocal game_active, start_time
        game_active = True
        start_time = time.time()
        update_timer()
        
        lobby_frame.destroy() 
        game_container.place(relx=0.5, rely=0.55, anchor="center")
        
        timer_lbl = tk.Label(overlay, textvariable=timer_var, font=("Helvetica", 24, "bold"), fg="#BDC3C7", bg=bg_color)
        timer_lbl.place(relx=0.02, rely=0.02, anchor="nw")
        
        result_msg = tk.Label(overlay, text="", font=("Microsoft YaHei", 36, "bold"), bg=bg_color)
        result_msg.place(relx=0.5, rely=0.1, anchor="center")

        if game_type == "shuffle":
            tk.Label(game_container, text="Sentence Master", font=("Helvetica", 48, "bold"), fg="#F1C40F", bg=bg_color).pack(pady=10)
            tk.Label(game_container, text="还原被打乱的句子，点击下方单词填入横线，点击横线上的单词重填。", font=("Microsoft YaHei", 18), fg="#BDC3C7", bg=bg_color).pack(pady=(0, 20))
            
            attempts_var = tk.IntVar(overlay, value=1)
            attempts_lbl = tk.Label(overlay, text="", font=("Helvetica", 28, "bold"), fg="#F1C40F", bg=bg_color)
            attempts_lbl.place(relx=0.80, rely=0.02, anchor="ne") 
            def update_attempts_ui(): attempts_lbl.config(text=f"尝试次数: {attempts_var.get()}")
            update_attempts_ui()

            MacButton(overlay, text="Exit Game (Esc)", font=("Microsoft YaHei", 16), command=overlay.destroy, bg="#E74C3C", fg="white", borderless=1, padx=20, pady=8).place(relx=0.98, rely=0.08, anchor="ne")

            raw_sentence = game_data["shuffle"]["en"]; words_only = re.findall(r"[\w']+", raw_sentence)
            indexed_pool = [{"id": i, "word": w} for i, w in enumerate(words_only)]
            shuffled_pool = indexed_pool[:]; random.shuffle(shuffled_pool)
            tokens = re.findall(r"[\w']+|[^\w\s]", raw_sentence)
            user_order = [None] * len(words_only); slot_btns, pool_btns = [], {}

            def check_win():
                nonlocal game_active
                if None in user_order: return
                
                is_correct = all(user_order[i]["word"].lower() == words_only[i].lower() for i in range(len(words_only)))
                if is_correct:
                    game_active = False; play_sound("submit")
                    for btn in slot_btns: btn.config(bg="#27AE60", state="disabled")
                    for b_id in pool_btns: pool_btns[b_id].config(state="disabled")
                    
                    attempts = attempts_var.get()
                    if attempts == 1: rank_text = "Godlike!"
                    elif attempts <= 2: rank_text = "Impressive!"
                    elif attempts <= 4: rank_text = "Excellent!"
                    elif attempts <= 6: rank_text = "Good Job!"
                    else: rank_text = "Well Done!"
                    
                    result_msg.config(text=f"🎉 {rank_text} 🎉", fg="#2ECC71")
                    tk.Label(game_container, text=f"{game_data['shuffle']['cn']}", font=("Microsoft YaHei", 20), fg="#BDC3C7", bg=bg_color, wraplength=1000).pack(pady=30)
                else:
                    attempts_var.set(attempts_var.get() + 1)
                    update_attempts_ui()

            def on_pool_click(obj):
                if not game_active: return
                for i in range(len(user_order)):
                    if user_order[i] is None:
                        play_sound("click"); user_order[i] = obj; pool_btns[obj["id"]].pack_forget()
                        if obj["word"].lower()==words_only[i].lower():
                            slot_btns[i].config(text=obj["word"], fg="white", bg="#27AE60")
                        else:
                            slot_btns[i].config(text=obj["word"], fg="white", bg=bg_color)
                            attempts_var.set(attempts_var.get() + 1)
                            update_attempts_ui()
                        check_win(); break

            def on_slot_click(idx):
                if not game_active or user_order[idx] is None or user_order[idx]["word"].lower() == words_only[idx].lower(): return 
                play_sound("click"); obj = user_order[idx]; user_order[idx] = None
                slot_btns[idx].config(text="______", fg="#5D6D7E", bg=bg_color)
                pool_btns[obj["id"]].pack(side="left", padx=8, pady=8)

            slots_wrap = tk.Frame(game_container, bg=bg_color); slots_wrap.pack(pady=40)
            current_slots_row = tk.Frame(slots_wrap, bg=bg_color); current_slots_row.pack(pady=10)
            w_idx, row_char = 0, 0
            for t in tokens:
                if row_char > 60:
                    current_slots_row = tk.Frame(slots_wrap, bg=bg_color); current_slots_row.pack(pady=10); row_char = 0
                if re.match(r"[\w']+", t):
                    curr = w_idx
                    btn = MacButton(current_slots_row, text="______", font=("Helvetica", 24), fg="#5D6D7E", bg=bg_color, borderless=1, padx=10, pady=5, command=lambda i=curr: on_slot_click(i))
                    btn.pack(side="left", padx=5); slot_btns.append(btn); w_idx += 1; row_char += 10
                else:
                    tk.Label(current_slots_row, text=t, font=("Helvetica", 28, "bold"), fg="white", bg=bg_color).pack(side="left"); row_char += 2

            pool_wrap = tk.Frame(game_container, bg=bg_color); pool_wrap.pack(pady=30)
            current_pool_row = tk.Frame(pool_wrap, bg=bg_color); current_pool_row.pack(pady=10)
            pool_char = 0
            for obj in shuffled_pool:
                if pool_char > 60:
                    current_pool_row = tk.Frame(pool_wrap, bg=bg_color); current_pool_row.pack(pady=10); pool_char = 0
                b = MacButton(current_pool_row, text=obj["word"], font=("Helvetica", 22), bg="#ECF0F1", fg="#2C3E50", borderless=1, padx=25, pady=12, command=lambda o=obj: on_pool_click(o))
                b.pack(side="left", padx=8, pady=8); pool_btns[obj["id"]] = b; pool_char += len(obj["word"]) + 4

        elif game_type == "wordle":
            rule_f = tk.Frame(overlay, bg=bg_color, width=450)
            rule_f.place(relx=0.05, rely=0.5, anchor="w")
            tk.Label(rule_f, text="Binglish Wordle", font=("Helvetica", 36, "bold"), fg="#F1C40F", bg=bg_color, justify="left").pack(anchor="w", pady=15)
            tk.Label(rule_f, text="规则：\n1. 目标：6次机会猜出5字母单词\n2. 绿色：字母存在且位置正确\n3. 黄色：字母存在但位置错\n4. 灰色：字母不在答案中", font=("Microsoft YaHei", 18), fg="#BDC3C7", bg=bg_color, justify="left").pack(anchor="w")

            MacButton(overlay, text="Exit Game (Esc)", font=("Microsoft YaHei", 16), command=overlay.destroy, bg="#E74C3C", fg="white", borderless=1, padx=20, pady=8).place(relx=0.98, rely=0.08, anchor="ne")
            
            rank_lbl = tk.Label(overlay, text="", font=("Microsoft YaHei", 32, "bold"), fg="#F1C40F", bg=bg_color)
            target = game_data["wordle"]["word"].lower(); t_len = len(target); guesses, cur_guess = [], []
            
            grid_f = tk.Frame(game_container, bg=bg_color); grid_f.pack(pady=10)
            cells = []
            for r in range(6):
                r_c = []
                for c in range(t_len):
                    l = tk.Label(grid_f, text="", font=("Helvetica", 48, "bold"), width=2, height=1, fg="white", bg="#34495E", highlightbackground="#BDC3C7", highlightthickness=2)
                    l.grid(row=r, column=c, padx=8, pady=8); r_c.append(l)
                cells.append(r_c)

            kb_f = tk.Frame(game_container, bg=bg_color); kb_f.pack(pady=30)
            kb_map = {}
            for row in ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]:
                rf = tk.Frame(kb_f, bg=bg_color); rf.pack()
                for char in row:
                    btn = tk.Label(rf, text=char, font=("Helvetica", 22, "bold"), width=3, height=1, fg="white", bg="#5D6D7E", padx=12, pady=12)
                    btn.pack(side="left", padx=4, pady=4); kb_map[char.lower()] = btn

            wordle_def_lbl = tk.Label(game_container, text="", font=("Microsoft YaHei", 20), fg="#A9DFBF", bg=bg_color, wraplength=800)
            wordle_def_lbl.pack(pady=(20, 0))

            def submit():
                nonlocal cur_guess, game_active
                if not game_active or len(cur_guess) < t_len: return
                g_str = "".join(cur_guess).lower()

                def verify_and_continue():
                    nonlocal game_active, cur_guess
                    valid_def = ""
                    try:
                        verify_url = f"https://ss.blueforge.org/valid?q={g_str}"
                        v_res = requests.get(verify_url, timeout=3)
                        if v_res.status_code == 200:
                            valid_def = v_res.text.strip()
                            if not valid_def:
                                result_msg.config(text="Not in word list", fg="#E67E22")
                                overlay.after(2000, lambda: result_msg.config(text="") if game_active else None)
                                return
                        else: raise Exception()
                    except Exception:
                        result_msg.config(text="无法连接验证服务器，请稍后重试", fg="#E74C3C")
                        overlay.after(2000, lambda: result_msg.config(text="") if game_active else None)
                        return

                    wordle_def_lbl.config(text=f"{g_str}: {valid_def}")
                    play_sound("submit")
                    row = len(guesses)
                    res_colors, t_list = [None] * t_len, list(target)

                    for i in range(t_len):
                        if g_str[i] == target[i]: res_colors[i] = "#2ECC71"; t_list[i] = None
                    for i in range(t_len):
                        if res_colors[i] is None:
                            if g_str[i] in t_list: res_colors[i] = "#F1C40F"; t_list[t_list.index(g_str[i])] = None
                            else: res_colors[i] = "#7F8C8D"

                    for i, col in enumerate(res_colors):
                        cells[row][i].config(bg=col, highlightbackground=col)
                        if kb_map[g_str[i]].cget("bg") != "#2ECC71": kb_map[g_str[i]].config(bg=col)

                    guesses.append(g_str)
                    cur_guess = []

                    if g_str == target:
                        game_active = False
                        ranks = ["Lucky you!", "Genius!", "Excellent!", "Impressive!", "Nice work!", "Whew!"]
                        result_msg.config(text="✨ Success! ✨", fg="#2ECC71")
                        rank_lbl.config(text=ranks[row])
                        rank_lbl.place(relx=0.5, rely=0.16, anchor="center")
                    elif len(guesses) >= 6:
                        game_active = False
                        result_msg.config(text=f"Hard Luck! ({target.upper()})", fg="#E74C3C")
                        tk.Label(game_container, text=f"{game_data['wordle']['word']} {game_data['wordle']['desc']}", font=("Microsoft YaHei", 24, "bold"), fg="#F1C40F", bg=bg_color, wraplength=800).pack(pady=30)

                threading.Thread(target=verify_and_continue, daemon=True).start()

            overlay.bind("<Key>", lambda e: (
                (play_sound("click"), cur_guess.pop()) if e.keysym=="BackSpace" and cur_guess and game_active else
                (play_sound("click"), cur_guess.append(e.char.upper())) if len(e.char)==1 and e.char.isalpha() and len(cur_guess)<t_len and game_active else
                submit() if e.keysym=="Return" and game_active else None,
                [cells[len(guesses)][i].config(text=(cur_guess[i] if i<len(cur_guess) else "")) for i in range(t_len)] if len(guesses)<6 and game_active else None
            ))
            
        elif game_type == "crossword":
            game_container.place(relx=0.5, rely=0.50, anchor="center")
            tk.Label(game_container, text="Mini Crossword", font=("Helvetica", 36, "bold"), fg="#F1C40F", bg=bg_color).pack(pady=(20, 5)) 
            tk.Label(game_container, text="在网格中填入正确的字母，使水平和垂直方向的单词都能吻合线索。", font=("Microsoft YaHei", 18), fg="#BDC3C7", bg=bg_color).pack(pady=(0, 40))

            MacButton(overlay, text="退出游戏 (Esc)", font=("Microsoft YaHei", 14), command=overlay.destroy, bg="#E74C3C", fg="white", borderless=1, padx=20, pady=8).place(relx=0.98, rely=0.02, anchor="ne")
            
            hint_btn = MacButton(overlay, text="💡 提示", font=("Microsoft YaHei", 14), command=lambda: give_hint(), bg="#9B59B6", fg="white", borderless=1, padx=20, pady=8)
            hint_btn.place(relx=0.85, rely=0.02, anchor="ne") 

            cw_data = None
            try:
                res = requests.get("https://ss.blueforge.org/dailyCrossword", timeout=5)
                if res.status_code == 200: cw_data = res.json().get("data")
            except Exception: pass
            if not cw_data:
                result_msg.config(text="无法获取字谜数据，请检查网络", fg="#E74C3C")
                return

            cw_main_frame = tk.Frame(game_container, bg=bg_color)
            cw_main_frame.pack(pady=10, fill="both", expand=True)

            left_clues_f = tk.Frame(cw_main_frame, bg=bg_color)
            left_clues_f.pack(side="left", padx=10, fill="y")
            grid_f = tk.Frame(cw_main_frame, bg=bg_color)
            grid_f.pack(side="left", padx=20)
            right_clues_f = tk.Frame(cw_main_frame, bg=bg_color)
            right_clues_f.pack(side="left", padx=10, fill="y")

            hint_display_f = tk.Frame(game_container, bg=bg_color)
            hint_display_f.pack(pady=20)
            
            penalty_lbl = tk.Label(hint_display_f, text="", font=("Microsoft YaHei", 16, "bold"), fg="#E74C3C", bg=bg_color)
            penalty_lbl.pack()
            
            hint_display_lbl = tk.Message(hint_display_f, text="", font=("Microsoft YaHei", 18), fg="#A9DFBF", bg=bg_color, justify="left", width=900)
            hint_display_lbl.pack()

            valid_cells, num_across, num_down, all_words = {}, {}, {}, []
            for direction in ["Across", "Down"]:
                for w in cw_data["clues"][direction]:
                    w["dir"] = direction
                    all_words.append(w)
                    if direction == "Across": num_across[(w['x'], w['y'])] = w['number']
                    else: num_down[(w['x'], w['y'])] = w['number']
                    for i in range(w["length"]):
                        cx = w["x"] + (i if direction == "Across" else 0)
                        cy = w["y"] + (i if direction == "Down" else 0)
                        valid_cells[(cx, cy)] = w["answer"][i]

            # 渲染线索 - 横向
            tk.Label(left_clues_f, text="Across (横向)", font=("Helvetica", 22, "bold"), fg="#3498DB", bg=bg_color).pack(anchor="w", pady=(0, 10))
            for c in cw_data["clues"]["Across"]:
                lbl = tk.Label(left_clues_f, text=f"{c['number']}. {c['clue']}", font=("Microsoft YaHei", 16), fg="white", bg=bg_color, wraplength=450, justify="left", cursor="hand2")
                lbl.pack(anchor="w", pady=3)
                
                def toggle_clue_across(event, cw=c, widget=lbl):
                    en_text = f"{cw['number']}. {cw['clue']}"
                    cn_text = f"{cw['number']}. {cw.get('clue_cn', '暂无翻译')}"
                    
                    if widget.cget("text") == en_text: widget.config(text=cn_text, fg="#F1C40F")
                    else: widget.config(text=en_text, fg="white") 
                
                lbl.bind("<Button-1>", toggle_clue_across)

            # 渲染线索 - 纵向
            tk.Label(right_clues_f, text="Down (纵向)", font=("Helvetica", 22, "bold"), fg="#E74C3C", bg=bg_color).pack(anchor="w", pady=(0, 10))
            for c in cw_data["clues"]["Down"]:
                lbl = tk.Label(right_clues_f, text=f"{c['number']}. {c['clue']}", font=("Microsoft YaHei", 16), fg="white", bg=bg_color, wraplength=450, justify="left", cursor="hand2")
                lbl.pack(anchor="w", pady=3)
                
                def toggle_clue_down(event, cw=c, widget=lbl):
                    en_text = f"{cw['number']}. {cw['clue']}"
                    cn_text = f"{cw['number']}. {cw.get('clue_cn', '暂无翻译')}"
                    
                    if widget.cget("text") == en_text: widget.config(text=cn_text, fg="#F1C40F")
                    else: widget.config(text=en_text, fg="white")
                        
                lbl.bind("<Button-1>", toggle_clue_down)

            entry_widgets = {}
            active_direction = "Across"
            last_focused_cell = None
            hint_count = 0
            hinted_cells = set()
            locked_cells = set()
            completed_word_ids = set()
            
            display_queue = []
            display_timer = None

            def process_display_queue():
                nonlocal display_timer
                if not display_queue:
                    display_timer = None; return
                w = display_queue.pop(0)
                update_info_display(w)
                if display_queue: display_timer = overlay.after(5000, process_display_queue)
                else: display_timer = None

            def queue_display(w):
                nonlocal display_timer
                display_queue.append(w)
                if display_timer is None: process_display_queue()

            def update_info_display(w):
                ans, yb = w["answer"], w.get("yb", "")
                mean, exp = w.get("meaning", ""), w.get("explanation", "")
                
                if exp:
                    exp = re.sub(r'([a-zA-Z0-9\'\"]+)([\u4e00-\u9fa5])', r'\1 \2', exp)
                    exp = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9\'\"]+)', r'\1 \2', exp)
                if mean:
                    mean = re.sub(r'([a-zA-Z0-9\'\"]+)([\u4e00-\u9fa5])', r'\1 \2', mean)
                    mean = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9\'\"]+)', r'\1 \2', mean)

                hint_display_lbl.config(text=f"【单词】{ans}   【音标】{yb}\n【含义】{mean}\n【解析】{exp}")

            def check_word_completion_at(cx, cy):
                newly_completed = []
                for w in all_words:
                    w_id = f"{w['dir']}_{w['number']}"
                    if w_id in completed_word_ids: continue
                        
                    in_word = False
                    for i in range(w["length"]):
                        wx = w["x"] + (i if w["dir"] == "Across" else 0)
                        wy = w["y"] + (i if w["dir"] == "Down" else 0)
                        if wx == cx and wy == cy:
                            in_word = True; break
                    
                    if in_word:
                        current_word_str, cells_in_word = "", []
                        for i in range(w["length"]):
                            wx = w["x"] + (i if w["dir"] == "Across" else 0)
                            wy = w["y"] + (i if w["dir"] == "Down" else 0)
                            cells_in_word.append((wx, wy))
                            current_word_str += entry_widgets[(wx, wy)].get().strip().upper()
                        
                        if current_word_str == w["answer"]:
                            newly_completed.append((w, cells_in_word))
                            completed_word_ids.add(w_id)
                
                if newly_completed:
                    newly_completed.sort(key=lambda item: 0 if item[0]["dir"] == "Across" else 1)
                    
                    for w, cells_in_word in newly_completed:
                        queue_display(w)
                        
                        for (wx, wy) in cells_in_word:
                            if (wx, wy) not in locked_cells:
                                locked_cells.add((wx, wy))
                                e = entry_widgets[(wx, wy)]
                                current_fg = "#9B59B6" if (wx, wy) in hinted_cells else "#2C3E50"
                                e.config(state="readonly", readonlybackground="#ECF0F1", fg=current_fg)

            def check_cw_win(event=None):
                nonlocal game_active
                if not game_active: return
                for (x,y), char in valid_cells.items():
                    if entry_widgets[(x,y)].get().strip().upper() != char:
                        return
                
                game_active = False 
                play_sound("submit")
                
                rank_text = "Keep Trying!"
                if hint_count == 0: rank_text = "Genius!"
                elif hint_count <= 2: rank_text = "Excellent!"
                
                result_msg.config(text=f"✨ {rank_text} ✨", fg="#2ECC71")
                
                for (x, y), w in entry_widgets.items():
                    final_fg = "#8E44AD" if (x,y) in hinted_cells else "#27AE60"
                    w.config(state="disabled", disabledbackground="#D5F5E3", disabledforeground=final_fg)

            def give_hint():
                nonlocal start_time, hint_count
                if not game_active: return
                unsolved = []
                for w in all_words:
                    word_str = "".join([entry_widgets[(w['x']+(i if w['dir']=='Across' else 0), w['y']+(i if w['dir']=='Down' else 0))].get().strip().upper() for i in range(w['length'])])
                    if word_str != w["answer"]: unsolved.append(w)
                
                if unsolved:
                    w = random.choice(unsolved)
                    cells_modified = []
                    for i in range(w["length"]):
                        cx = w["x"] + (i if w["dir"] == "Across" else 0)
                        cy = w["y"] + (i if w["dir"] == "Down" else 0)
                        e = entry_widgets[(cx, cy)]
                        
                        if e.cget("state") == "readonly": e.config(state="normal")
                        e.delete(0, tk.END)
                        e.insert(0, w["answer"][i])
                        e.config(fg="#9B59B6")
                        hinted_cells.add((cx, cy))
                        cells_modified.append((cx, cy))
                    
                    play_sound("click")
                    
                    start_time -= 30
                    hint_count += 1
                    penalty_lbl.config(text=f"⏳ 触发提示，总时间增加30秒！(当前已提示: {hint_count}次)")
                    
                    for cx, cy in cells_modified: check_word_completion_at(cx, cy)
                    check_cw_win()

            for y in range(5):
                for x in range(5):
                    cell_f = tk.Frame(grid_f, width=70, height=70, bg="#2C3E50") 
                    cell_f.grid(row=y, column=x, padx=2, pady=2)
                    cell_f.grid_propagate(False)
                    
                    if (x, y) in valid_cells:
                        e = tk.Entry(cell_f, font=("Helvetica", 28, "bold"), justify="center", fg="#2C3E50", bg="#ECF0F1", relief="flat")
                        e.place(relx=0, rely=0, relwidth=1, relheight=1)
                        entry_widgets[(x, y)] = e
                        
                        if (x, y) in num_across:
                            lbl_a = tk.Label(cell_f, text=str(num_across[(x, y)]), font=("Helvetica", 10, "bold"), fg="#3498DB", bg="#ECF0F1", cursor="xterm")
                            lbl_a.place(x=2, y=0)
                            lbl_a.bind("<Button-1>", lambda event, target=e: target.focus_set())
                        
                        if (x, y) in num_down:
                            lbl_d = tk.Label(cell_f, text=str(num_down[(x, y)]), font=("Helvetica", 10, "bold"), fg="#E74C3C", bg="#ECF0F1", cursor="xterm")
                            lbl_d.place(x=50, y=0) 
                            lbl_d.bind("<Button-1>", lambda event, target=e: target.focus_set())
                        
                        def on_focus(event, cx=x, cy=y):
                            nonlocal last_focused_cell
                            last_focused_cell = (cx, cy)

                        def on_click(event, cx=x, cy=y):
                            nonlocal active_direction, last_focused_cell
                            if last_focused_cell == (cx, cy):
                                active_direction = "Down" if active_direction == "Across" else "Across"

                        e.bind("<FocusIn>", on_focus)
                        e.bind("<Button-1>", on_click)

                        def on_key(event, cx=x, cy=y, widget=e):
                            nonlocal active_direction
                            if not game_active: return

                            if event.keysym in ["Left", "Right", "Up", "Down"]:
                                if event.keysym == "Left": active_direction = "Across"; (cx-1, cy) in entry_widgets and entry_widgets[(cx-1, cy)].focus_set()
                                elif event.keysym == "Right": active_direction = "Across"; (cx+1, cy) in entry_widgets and entry_widgets[(cx+1, cy)].focus_set()
                                elif event.keysym == "Up": active_direction = "Down"; (cx, cy-1) in entry_widgets and entry_widgets[(cx, cy-1)].focus_set()
                                elif event.keysym == "Down": active_direction = "Down"; (cx, cy+1) in entry_widgets and entry_widgets[(cx, cy+1)].focus_set()
                                return

                            if event.keysym == "BackSpace":
                                if widget.cget("state") == "normal": widget.delete(0, tk.END)
                                px, py = (cx - 1, cy) if active_direction == "Across" else (cx, cy - 1)
                                if (px, py) in entry_widgets: entry_widgets[(px, py)].focus_set()
                                return

                            if widget.cget("state") == "readonly":
                                nx, ny = (cx + 1, cy) if active_direction == "Across" else (cx, cy + 1)
                                if (nx, ny) in entry_widgets: entry_widgets[(nx, ny)].focus_set()
                                return

                            val = widget.get().upper()
                            widget.delete(0, tk.END)
                            if val and val.isalpha():
                                char = val[-1]
                                widget.insert(0, char)
                                widget.config(fg="#2C3E50") 
                                
                                if game_active: check_word_completion_at(cx, cy)
                                check_cw_win()
                                
                                nx, ny = (cx + 1, cy) if active_direction == "Across" else (cx, cy + 1)
                                if (nx, ny) in entry_widgets: entry_widgets[(nx, ny)].focus_set()

                        e.bind("<KeyRelease>", on_key)
                    else:
                        tk.Label(cell_f, bg="#1C2833").place(relx=0, rely=0, relwidth=1, relheight=1)
            tip_f = tk.Frame(game_container, bg=bg_color)
            tip_f.pack(side="bottom", pady=(20, 0))
            
            tk.Label(tip_f, 
                     text="💡 小提示：用鼠标点击线索可以切换查看翻译。线索解析由AI生成，仅供参考。", 
                     font=("Microsoft YaHei", 14, "italic"), 
                     fg="#7F8C8D", 
                     bg=bg_color).pack()

    btn_style = {"font": ("Microsoft YaHei", 20, "bold"), "borderless": 1, "padx": 20, "pady": 20}
    MacButton(btn_frame, text="Sentence Master", bg="#3498DB", fg="white", **btn_style, command=lambda: start_game("shuffle")).pack(side="left", padx=15)
    MacButton(btn_frame, text="Binglish Wordle", bg="#2ECC71", fg="white", **btn_style, command=lambda: start_game("wordle")).pack(side="left", padx=15)
    MacButton(btn_frame, text="Mini Crossword", bg="#9B59B6", fg="white", **btn_style, command=lambda: start_game("crossword")).pack(side="left", padx=15)
    
    return_btn = MacButton(lobby_frame, text=" 返回桌面 ", font=("Microsoft YaHei", 18, "bold"), fg="white", bg="#34495E", borderless=1, padx=60, pady=15, command=overlay.destroy)
    return_btn.pack(pady=40)
    
    return_btn.bind("<Enter>", lambda e: return_btn.config(bg="#455A64"))
    return_btn.bind("<Leave>", lambda e: return_btn.config(bg="#34495E"))
    
    overlay.bind('<Escape>', lambda e: overlay.destroy())
    
    def fade_in(current_alpha=0):
        if current_alpha < 0.85:
            overlay.attributes("-alpha", current_alpha + 0.05)
            overlay.after(20, fade_in, current_alpha + 0.05)
    fade_in(0)
    
    overlay.focus_force()
    overlay.mainloop()

# ==========================================
# 🔌 主程序与调度逻辑
# ==========================================

def show_game_overlay():
    """
    功能：拉起游戏遮罩进程。
    防抖判断后，启动独立子进程来渲染并运行游戏，防止堵塞或干扰 pystray 的主系统线程。
    """
    global is_overlay_showing
    if is_overlay_showing: return
    is_overlay_showing = True
    def runner():
        p = multiprocessing.Process(target=proc_game_overlay, args=(OVERLAY_COLOR, GAME_DATA_URL))
        p.start(); p.join()
        global is_overlay_showing; is_overlay_showing = False
    threading.Thread(target=runner, daemon=True).start()

def show_rest_overlay():
    """
    功能：拉起强制休息遮罩进程。
    防抖判断后，随机抽取休息语录，并启动独立子进程来强制霸占全屏。结束后重置休息计时器。
    """
    global is_overlay_showing, last_rest_time
    if is_overlay_showing: return
    is_overlay_showing = True
    quote_en, quote_cn = random.choice(REST_QUOTES)
    def runner():
        p = multiprocessing.Process(target=proc_rest_overlay, args=(quote_en, quote_cn, REST_LOCK_SECONDS, OVERLAY_COLOR, bing_word, USELESS_FACT_URL))
        p.start(); p.join()
        global is_overlay_showing, last_rest_time, icon
        is_overlay_showing = False; last_rest_time = time.time()
        if icon: icon.menu = Menu(*build_menu_items())
    threading.Thread(target=runner, daemon=True).start()

def show_history_overlay(events, date_str):
    """
    功能：拉起历史上的今天遮罩进程。
    接收已处理好的历史数据，防抖判断后，启动独立子进程来展示历史信息。
    """
    global is_overlay_showing
    if is_overlay_showing: return
    is_overlay_showing = True
    def runner():
        p = multiprocessing.Process(target=proc_history_overlay, args=(events, date_str, OVERLAY_COLOR))
        p.start(); p.join()
        global is_overlay_showing; is_overlay_showing = False
    threading.Thread(target=runner, daemon=True).start()

def _fetch_history_thread():
    """
    功能：后台获取历史数据线程。
    根据当前的公历月日，向服务器请求历史大事件，成功后唤起历史界面，失败则调用原生弹窗报错。
    """
    try:
        now = datetime.now()
        date_str = now.strftime("%b. %d")
        url = f"{HISTORY_URL_BASE}?mm={now.month}&dd={now.day}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and isinstance(response.json(), list) and len(response.json()) > 0:
            show_history_overlay(response.json(), date_str)
        else:
            mac_alert("On This Day", "暂无相关历史内容。")
    except Exception as e:
        mac_alert("Error", f"获取内容出错: {e}", True)

def on_this_day_click():
    """
    功能：处理菜单栏中“Today in History”按钮的点击事件。
    拉起并启动请求历史数据的后台线程，避免网络延迟卡死 UI 线程。
    """
    threading.Thread(target=_fetch_history_thread, daemon=True).start()

def get_idle_duration():
    """
    功能：获取系统空闲时长。
    调用 macOS 底层的 IOHIDSystem 接口查询鼠标和键盘的未操作时间，以秒为单位返回。
    """
    try:
        cmd = "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1000000000); exit}'"
        return float(subprocess.check_output(cmd, shell=True).decode().strip())
    except Exception: return 0

def open_config_file():
    """
    功能：打开本地配置文件。
    使用 macOS 的默认文本编辑器（通常是文本编辑）打开应用目录下的 binglish.ini。若不存在则自动初始化。
    """
    config_path = os.path.join(os.path.dirname(get_executable_path()), CONFIG_FILENAME)
    try:
        if not os.path.exists(config_path): load_config_and_init()
        subprocess.call(['open', config_path])
    except Exception as e:
        mac_alert("错误", f"无法打开配置文件: {e}", True)

def load_config_and_init():
    """
    功能：初始化并加载配置文件。
    检查应用目录下是否存在 binglish.ini。若无，则生成带默认值的配置文件；若有，则读取用户设定的间隔、颜色等选项并更新全局变量。
    """
    global is_rest_enabled, REST_INTERVAL_SECONDS, IDLE_RESET_SECONDS, REST_LOCK_SECONDS, OVERLAY_COLOR
    config_path = os.path.join(os.path.dirname(get_executable_path()), CONFIG_FILENAME)
    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w', encoding='utf-8-sig') as f:
                f.write("[Settings]\nIS_REST_ENABLED = 0\nREST_INTERVAL_SECONDS = 2700\nIDLE_RESET_SECONDS = 300\nREST_LOCK_SECONDS = 30\nOVERLAY_COLOR = #2C3E50\n")
        except Exception: pass
    config = configparser.ConfigParser()
    try:
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8-sig')
            if 'Settings' in config:
                settings = config['Settings']
                is_rest_enabled = settings.getboolean('IS_REST_ENABLED', fallback=False)
                REST_INTERVAL_SECONDS = settings.getint('REST_INTERVAL_SECONDS', fallback=2700)
                IDLE_RESET_SECONDS = settings.getint('IDLE_RESET_SECONDS', fallback=300)
                REST_LOCK_SECONDS = settings.getint('REST_LOCK_SECONDS', fallback=30)
                color_val = settings.get('OVERLAY_COLOR', fallback='#2C3E50').strip().strip('"').strip("'")
                if color_val: OVERLAY_COLOR = color_val
    except Exception: pass

def save_rest_enabled_to_config(enabled):
    """
    功能：保存“开启/关闭休息提醒”状态到本地配置。
    当用户在菜单栏点击切换提醒时，使用正则匹配并修改 ini 文件中 IS_REST_ENABLED 的值，实现持久化保存。
    """
    config_path = os.path.join(os.path.dirname(get_executable_path()), CONFIG_FILENAME)
    try:
        if not os.path.exists(config_path): load_config_and_init(); return
        with open(config_path, 'r', encoding='utf-8-sig') as f: content = f.read()
        new_content = re.sub(r"(?m)(?i)(^\s*IS_REST_ENABLED\s*=\s*)([^;\r\n]*)", f"\\g<1>{'1' if enabled else '0'}", content)
        with open(config_path, 'w', encoding='utf-8-sig') as f: f.write(new_content)
    except Exception: pass

def toggle_rest_reminder():
    """
    功能：切换休息提醒的总开关。
    处理菜单项的回调，改变全局启用状态、更新配置文件，并即刻刷新状态栏菜单里的倒计时信息。
    """
    global is_rest_enabled, last_rest_time, icon
    is_rest_enabled = not is_rest_enabled
    save_rest_enabled_to_config(is_rest_enabled)
    if is_rest_enabled: last_rest_time = time.time()
    if icon: icon.menu = Menu(*build_menu_items())

def rest_monitor_loop():
    """
    功能：核心休息监控死循环线程。
    每隔5秒检查一次系统空闲时间。如果空闲时间超过阈值，视为用户已自行休息并重置计时器；如果连续工作时间超过阈值，则强制拉起休息遮罩。定期触发菜单栏数字刷新。
    """
    global last_rest_time, icon
    last_menu_update_time = time.time()
    while True:
        try:
            time.sleep(5) 
            if is_rest_enabled and icon:
                if time.time() - last_menu_update_time > 60:
                    icon.menu = Menu(*build_menu_items())
                    last_menu_update_time = time.time()
            if not is_rest_enabled: continue
            
            idle_time = get_idle_duration()
            if idle_time > IDLE_RESET_SECONDS:
                last_rest_time = time.time()
                if icon: icon.menu = Menu(*build_menu_items())
                continue
            
            if time.time() - last_rest_time > REST_INTERVAL_SECONDS:
                if not is_overlay_showing: show_rest_overlay()
        except Exception: time.sleep(10)

def resource_path(relative_path):
    """
    功能：获取资源的绝对路径。
    适配 PyInstaller 打包环境。如果在冻结状态下运行，则从临时 _MEIPASS 目录读取资源；如果在开发环境下，则直接读取相对路径。
    """
    try: return os.path.join(sys._MEIPASS, relative_path)
    except Exception: return os.path.join(os.path.abspath("."), relative_path)

def get_executable_path():
    """
    功能：获取当前程序的可执行文件路径。
    为后续写入开机启动项或拉取并替换自身（自动更新）做路径准备。
    """
    return sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)

def get_mac_startup_plist_path():
    """
    功能：生成 macOS LaunchAgents 配置文件的路径。
    返回用户目录下的 com.binglish.app.plist 绝对路径，用于管理开机自启行为。
    """
    return os.path.expanduser('~/Library/LaunchAgents/com.binglish.app.plist')

def is_startup_enabled():
    """
    功能：检查开机自启是否已启用。
    判断 LaunchAgents 目录下是否存在对应 plist 文件，以确定菜单栏“开机运行”的勾选状态。
    """
    return os.path.exists(get_mac_startup_plist_path())

def toggle_startup():
    """
    功能：切换开机自启设置。
    若已存在 plist 则删除（取消自启）；若不存在，则创建一个合规的 plist 文件并指向当前可执行文件路径（开启自启）。
    """
    plist_path = get_mac_startup_plist_path()
    if is_startup_enabled():
        try: os.remove(plist_path)
        except Exception: pass
    else:
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.binglish.app</string>
    <key>ProgramArguments</key>
    <array><string>{get_executable_path()}</string></array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
        try:
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)
            with open(plist_path, 'w') as f: f.write(plist_content)
        except Exception: pass

def set_as_wallpaper(image_path):
    """
    功能：设置为 macOS 桌面壁纸。
    每次生成独立文件路径以强迫 macOS 立即刷新桌面。
    """
    import shutil
    import time
    try:
        base_dir = os.path.dirname(os.path.abspath(image_path))
        
        unique_bg = os.path.join(base_dir, f"mac_bg_{int(time.time())}.jpg")
        shutil.copy(image_path, unique_bg)
        
        script = f'tell application "System Events" to set picture of every desktop to "{unique_bg}"'
        subprocess.run(['osascript', '-e', script], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for f in os.listdir(base_dir):
            if f.startswith("mac_bg_") and f.endswith(".jpg") and f != os.path.basename(unique_bg):
                try: os.remove(os.path.join(base_dir, f))
                except: pass
                
        return True
    except Exception: return False

def show_copyright_info():
    """
    功能：展示壁纸版权信息。
    如果在 EXIF 数据中提取到了版权及链接信息，则唤起原生交互框。若用户点击确认，则通过浏览器跳转至图源页面。
    """
    if bing_copyright and bing_copyright_url:
        if mac_askyesno("图片信息", f"{bing_copyright}\n\n查看相关信息？"): webbrowser.open(bing_copyright_url)
    elif bing_copyright: mac_alert("图片信息", bing_copyright)

def show_music_description_dialog():
    """
    功能：展示当前歌曲的文字描述信息。
    通过原生交互框展示歌曲详情，并在弹窗底部提供播放/取消选项，供用户决策。
    """
    if not bing_music_desc: return
    if mac_askyesno(f"歌曲: {bing_music_name}", f"{bing_music_desc}\n\n是否立即播放？", yes_text="播放", no_text="取消"):
        toggle_music_playback()

def show_share_qr():
    """
    功能：唤起分享二维码进程。
    验证有效性后，拉起多进程渲染对应的 URL 二维码供移动端扫码保存壁纸。
    """
    if not bing_id: return
    share_url = f"https://ss.blueforge.org/bing/s/{bing_id}.htm"
    multiprocessing.Process(target=proc_share_qr, args=(share_url,), daemon=True).start()

def _play_music_task(url):
    """
    功能：处理在线流媒体音乐播放。
    在独立的子进程内，通过 playsound3 库阻塞式下载并播放指定的音频链接，避免卡住主系统线程。
    """
    try: from playsound3 import playsound; playsound(url)
    except Exception: pass

def _music_monitor_thread():
    """
    功能：单线程后台监控音乐播放器状态。
    使用单线程 while 轮询，避免频繁创建销毁线程带来的资源浪费。
    """
    global is_music_playing, music_process, icon
    while is_music_playing and music_process:
        if not music_process.is_alive():
            is_music_playing, music_process = False, None
            if icon: icon.menu = Menu(*build_menu_items())
            break
        time.sleep(1.0)

def toggle_music_playback():
    """
    功能：切换每日一曲（Song of the Day）的播放状态。
    """
    global is_music_playing, music_process, icon
    if is_music_playing:
        if music_process and music_process.is_alive(): music_process.terminate(); music_process = None
        is_music_playing = False
    elif bing_music_url:
        try:
            if music_process and music_process.is_alive(): music_process.terminate()
            music_process = multiprocessing.Process(target=_play_music_task, args=(bing_music_url,), daemon=True)
            music_process.start()
            is_music_playing = True
            # 启动单一监控线程，而不是无限套娃 Timer
            threading.Thread(target=_music_monitor_thread, daemon=True).start()
        except Exception: is_music_playing, music_process = False, None
    if icon: icon.menu = Menu(*build_menu_items())

def build_menu_items():
    """
    功能：动态生成 macOS 顶部托盘的级联菜单。
    根据当前是否下载到数据（单词、音频、历史记录、是否需要休息），实时增删、启用/置灰对应的菜单项，并封装对应的点击回调。
    """
    menu_items = []
    if bing_url: menu_items.append(item(f'查单词 {bing_word}', lambda: webbrowser.open(bing_url)))
    if bing_mp3: menu_items.append(item(f'听单词 {bing_word}', lambda: threading.Thread(target=play_word_sound, daemon=True).start()))
    if bing_word: menu_items.append(item(f'看单词 {bing_word}', lambda: webbrowser.open(f"https://www.playphrase.me/#/search?q={bing_word}&language=en")))
    if bing_url or bing_mp3: menu_items.append(Menu.SEPARATOR)

    menu_items.append(item('随机复习', lambda: threading.Thread(target=update_wallpaper_job, args=(True,), daemon=True).start()))
    if os.path.exists(os.path.join(os.path.dirname(get_executable_path()), "wallpaper.jpg")):
        menu_items.append(item('复制保存', copy_and_save_wallpaper))

    if bing_copyright: menu_items.append(item('壁纸信息', show_copyright_info))
    if bing_id: menu_items.append(item('分享壁纸', show_share_qr))
    
    rest_label = f'提醒休息 (剩余{int(max(0, REST_INTERVAL_SECONDS - (time.time() - last_rest_time)) / 60)}分)' if is_rest_enabled else '提醒休息'
    menu_items.append(Menu.SEPARATOR)
    menu_items.append(item(rest_label, toggle_rest_reminder, checked=lambda i: is_rest_enabled))

    menu_items.append(Menu.SEPARATOR)
    menu_items.append(item('Today in History', on_this_day_click))
    menu_items.append(item('Binglish Games', show_game_overlay))
    if bing_music_name and bing_music_url:
        menu_items.append(item('==Song of the Day==', None, enabled=False))
        if bing_music_desc: menu_items.append(item(f'  {bing_music_name}', show_music_description_dialog))
        else: menu_items.append(item(f'  {bing_music_name}', None, enabled=False))
        menu_items.append(item(f'  {"停止播放" if is_music_playing else "播放歌曲"}', lambda: toggle_music_playback()))
        menu_items.append(Menu.SEPARATOR)
        
    menu_items.append(item('开机运行', toggle_startup, checked=lambda i: is_startup_enabled()))
    
    update_label = '检查更新 (有新版本)' if new_version_available else '检查更新'
    if getattr(sys, 'frozen', False):
        menu_items.append(item(update_label, lambda: check_for_updates(icon)))

    menu_items.append(item('设置', open_config_file))
    menu_items.append(item('关于', lambda: mac_alert("关于 Binglish", f"Binglish 桌面英语 (macOS 版) {VERSION}\n{PROJECT_URL}"))) 
    menu_items.append(item('退出', lambda: quit_app(icon)))
    
    return tuple(menu_items)

def update_wallpaper_job(is_random=False):
    """
    功能：核心后台作业——更新壁纸并解析数据。
    发起并处理网络检查、拉取最新的 JSON 每日音频等信息，下载远端壁纸并静默解析其隐藏的 EXIF 自定义标签。解析成功后赋值给各全局状态，并调用 AppleScript 更换系统桌面，最终刷新菜单。
    """
    global icon, bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id
    global bing_music_name, bing_music_url, bing_music_desc, is_music_playing, music_process

    threading.Thread(target=perform_network_check, args=(icon, True), daemon=True).start()
    bing_word, bing_url, bing_mp3, bing_copyright, bing_copyright_url, bing_id = None, None, None, None, None, None
    bing_music_name, bing_music_url, bing_music_desc = None, None, None
    
    if music_process and music_process.is_alive():
        music_process.terminate(); music_process = None
    is_music_playing = False

    if icon: icon.menu = Menu(*build_menu_items())

    full_save_path = os.path.join(os.path.dirname(get_executable_path()), "wallpaper.jpg")
    dynamic_image_url = f"{IMAGE_URL}&random" if is_random else IMAGE_URL

    try:
        music_data = requests.get(MUSIC_JSON_URL, timeout=10).json()
        bing_music_name, bing_music_url, bing_music_desc = music_data.get("name"), music_data.get("url"), music_data.get("description")
    except Exception: pass

    try:
        response = requests.get(dynamic_image_url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(full_save_path, 'wb') as f: f.write(response.content)
            
            try:
                with open(full_save_path, 'rb') as f: tags = exifread.process_file(f) 
                if tags:
                    bing_word = str(tags.get('Image Artist', '')).strip()
                    bing_url = str(tags.get('Image ImageDescription', '')).strip()
                    bing_mp3 = str(tags.get('Image DocumentName', '')).strip()
                    copyright_info = str(tags.get('Image Copyright', '')).strip()
                    if "||" in copyright_info:
                        bing_copyright, bing_copyright_url = copyright_info.split("||", 1)
                    else:
                        bing_copyright, bing_copyright_url = copyright_info, None
                    bing_id = str(tags.get('Image Software', '')).strip()
            except Exception: pass
            
            if icon: icon.menu = Menu(*build_menu_items())
            if set_as_wallpaper(full_save_path): return True 
    except Exception: pass
    return False

def run_scheduler(icon):
    """
    功能：控制整体应用生命周期的调度器死循环。
    处理启动时的网络探测和首次壁纸拉取，并随后切换到阻塞睡眠模型，定时（如3小时）触发壁纸与数据更新作业。
    """
    while True:
        try: requests.get("https://www.bing.com", timeout=5); break
        except requests.ConnectionError: time.sleep(INTERNET_CHECK_INTERVAL_SECONDS)
        
    threading.Thread(target=check_update_startup_thread, daemon=True).start()
    while not update_wallpaper_job():
        if not icon.visible: return
        time.sleep(DOWNLOAD_RETRY_INTERVAL_SECONDS)

    while icon.visible:
        time.sleep(UPDATE_INTERVAL_SECONDS)
        if not icon.visible: break
        try:
            requests.get("https://www.bing.com", timeout=5)
            update_wallpaper_job()
        except Exception: pass

def copy_and_save_wallpaper():
    """
    功能：复制备份当前桌面壁纸。
    将临时下载的单张壁纸（wallpaper.jpg）以当前时间戳重命名并复制备份到程序根目录，避免被下次更新覆盖。
    """
    try:
        base_dir = os.path.dirname(get_executable_path())
        shutil.copy(os.path.join(base_dir, "wallpaper.jpg"), os.path.join(base_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"))
        mac_alert("操作成功", "壁纸已成功复制至程序所在目录")
    except Exception as e: mac_alert("操作失败", f"复制文件时出错: {e}", True)

def download_and_update(icon, expected_hash=None):
    """
    功能：自动下载并部署新版本程序核心文件。
    根据远程二进制文件的 URL 下载最新版包并做 SHA256 哈希完整性校验。校验成功后生成一个临时 bash 脚本 updater.sh，脱离 Python 上下文强制替换自身实体文件，最后重启应用。
    """
    new_exe_path = os.path.join(os.path.dirname(get_executable_path()), "bing_new")
    try:
        response = requests.get(DOWNLOAD_URL, stream=True, timeout=60)
        if response.status_code == 200:
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): f.write(chunk)

            if expected_hash:
                sha256_hash = hashlib.sha256()
                with open(new_exe_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""): sha256_hash.update(byte_block)
                if sha256_hash.hexdigest().lower() != expected_hash.lower():
                    try: os.remove(new_exe_path)
                    except: pass
                    mac_alert("更新失败", "下载的文件校验失败，可能已损坏或被篡改。", True)
                    return
            
            updater_sh_path = os.path.join(os.path.dirname(get_executable_path()), "updater.sh")
            current_exe_path = get_executable_path()
            
            with open(updater_sh_path, 'w') as f:
                f.write(f'#!/bin/bash\nsleep 2\nrm "{current_exe_path}"\nmv "{new_exe_path}" "{current_exe_path}"\nchmod +x "{current_exe_path}"\nopen "{current_exe_path}"\nrm "$0"\n')
            os.chmod(updater_sh_path, 0o755)
            subprocess.Popen([updater_sh_path], start_new_session=True)
            threading.Timer(0.1, lambda: quit_app(icon)).start()
        else:
            mac_alert("下载失败", f"下载新版本失败。状态码: {response.status_code}", True)
    except Exception as e:
        mac_alert("下载失败", f"下载新版本时发生错误: {e}", True)

def show_update_dialog(result, icon, silent=False):
    """
    功能：处理更新探测结果并展示对应弹窗。
    接收网络模块传来的状态元组。如果是静默启动检查，仅后台打标记并点亮菜单；如果是手动检查，则拉起带发布说明的原生确认弹窗并决定是否唤起部署替换程序。
    """
    status, version_or_error, releasenotes = result[0], result[1], result[2]
    hash_value = result[3] if len(result) == 4 else None
    
    if silent:
        if status == 'update_available':
            global new_version_available; new_version_available = True
            if icon: icon.menu = Menu(*build_menu_items())
        return

    if status == 'update_available':
        if mac_askyesno("发现新版本", f"有新版本 ({version_or_error}) 可用。\n\n更新说明:\n{releasenotes}\n\n您想现在更新吗？"):
            threading.Thread(target=download_and_update, args=(icon, hash_value)).start()
    elif status == 'no_update': mac_alert("没有更新", "您使用的已是最新版本。")
    elif status == 'error': mac_alert("检查更新失败", f"发生错误: {version_or_error}", True)

def perform_network_check(icon, silent=False):
    """
    功能：查询云端最新版本信息。
    请求并解析服务器的 release_mac.json，进行版本字符串比对，生成包含了哈希与更新说明的状态元组。
    """
    try:
        release_info = requests.get(RELEASE_JSON_URL, timeout=20).json()
        latest_version = release_info.get("version")
        if latest_version and latest_version != VERSION:
            result = ('update_available', latest_version, release_info.get("releasenotes"), release_info.get("hash"))
        else:
            result = ('no_update', None, None, None)
    except Exception as e: result = ('error', str(e), None, None)
    show_update_dialog(result, icon, silent)

def check_for_updates(icon):
    """
    功能：手动触发更新检查。
    菜单项回调，拉起独立非静默请求线程。
    """
    threading.Thread(target=perform_network_check, args=(icon, False)).start()
    
def check_update_startup_thread():
    """
    功能：延迟启动静默更新探测。
    在主程序启动时延迟5秒执行版本对比，防止卡主程序的加载。
    """
    time.sleep(5); perform_network_check(None, silent=True)

def play_word_sound():
    """
    功能：播放必应单词在线发音。
    利用 playsound3 执行短而快的阻塞播放，调用系统的 afplay 提供原声单词发音。
    """
    if bing_mp3:
        try: from playsound3 import playsound; playsound(bing_mp3)
        except Exception as e: mac_alert("播放失败", f"无法播放在线音频：{e}", True)

def quit_app(icon):
    """
    功能：执行全应用的退出与扫尾清理工作。
    关闭所有多进程残余资源（特别是音乐播放进程），终止 pystray 图标阻塞渲染，释放系统主线程。
    """
    global music_process
    if music_process and music_process.is_alive(): music_process.terminate(); music_process = None
    if icon: icon.stop()

def main():
    """
    功能：应用的主入口函数。
    加载本地配置文件、处理 PyInstaller 的打包资源寻址，初始化 pystray 顶部图标与菜单，拉起核心调度与系统状态监控子线程。它必须占据 macOS 的主线程来安全地运行基于 C 库的原生系统图形托盘。
    """
    global icon, is_rest_enabled
    load_config_and_init()

    try: image = Image.open(resource_path(ICON_FILENAME))
    except FileNotFoundError: sys.exit(1)
    
    icon = Icon(APP_NAME, image, "Binglish", menu=Menu(*build_menu_items()))
    
    threading.Thread(target=run_scheduler, args=(icon,), daemon=True).start()
    threading.Thread(target=rest_monitor_loop, daemon=True).start()
    
    icon.run()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()