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

VERSION = "1.2.0"
RELEASE_JSON_URL = "https://ss.blueforge.org/bing/release.json" # 包含版本号和更新说明的JSON文件URL
DOWNLOAD_URL = "https://ss.blueforge.org/bing/binglish.exe" #最新版本可执行文件
IMAGE_URL = f"https://ss.blueforge.org/bing?v={VERSION}"  #图片URL
MUSIC_JSON_URL = "https://ss.blueforge.org/bing/songoftheday.json" # 每日一歌JSON

UPDATE_INTERVAL_SECONDS = 3 * 60 * 60 #每3小时更新图片
APP_NAME = "Binglish"
REG_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
ICON_FILENAME = "binglish.ico"
DOWNLOAD_RETRY_INTERVAL_SECONDS = 30
INTERNET_CHECK_INTERVAL_SECONDS = 60
PROJECT_URL = "https://github.com/klemperer/binglish" #项目网址

bing_word = None # 单词本身
bing_url = None  # 单词详情页URL
bing_mp3 = None  # 单词发音MP3文件URL
bing_copyright = None # 图片版权文本
bing_copyright_url = None # 图片版权链接
bing_id = None # 图片唯一ID，用于分享
bing_music_name = None # 每日一歌名称
bing_music_url = None  # 每日一歌MP3 URL
bing_music_desc = None # 每日一歌描述
is_music_playing = False # 音乐是否正在播放
music_process = None # 音乐播放进程
music_check_timer = None # 用于存储音乐检查计时器

# 用于持有 pystray 图标对象的引用
root = None
icon = None


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

    menu_items.append(Menu.SEPARATOR)

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

    if getattr(sys, 'frozen', False):
        menu_items.append(item('检查更新', lambda: check_for_updates(icon)))
    
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
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
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
def download_and_update(icon):
    new_exe_path = os.path.join(os.path.dirname(get_executable_path()), "bing_new.exe")
    try:
        print(f"[{time.ctime()}] 正在从 {DOWNLOAD_URL} 下载新版本...")
        response = requests.get(DOWNLOAD_URL, stream=True, timeout=60)
        if response.status_code == 200:
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[{time.ctime()}] 新版本已下载到: {new_exe_path}")
            
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
def show_update_dialog(result, icon):
    status, version_or_error, releasenotes = result
    if status == 'update_available':
        message = f"有新版本 ({version_or_error}) 可用。\n\n更新说明:\n{releasenotes}\n\n您想现在更新吗？\n点击确定后程序将在后台更新。"
        if messagebox.askyesno("发现新版本", message):
            threading.Thread(target=download_and_update, args=(icon,)).start()
    elif status == 'no_update':
        messagebox.showinfo("没有更新", "您使用的已是最新版本。")
    elif status == 'error':
        messagebox.showerror("检查更新失败", f"检查更新时发生错误: {version_or_error}")

#检查更新函数
def perform_network_check(icon):
    print(f"[{time.ctime()}] 正在检查更新...")
    try:
        response = requests.get(RELEASE_JSON_URL, timeout=20)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info.get("version")
        releasenotes = release_info.get("releasenotes")
        
        print(f"[{time.ctime()}] 当前版本: {VERSION}, 最新版本: {latest_version}")
        
        if latest_version and latest_version != VERSION:
            result = ('update_available', latest_version, releasenotes)
        else:
            result = ('no_update', None, None)
            
    except requests.exceptions.RequestException as e:
        print(f"[{time.ctime()}] F检查更新时发生错误: {e}")
        result = ('error', e, None)
    except json.JSONDecodeError as e:
        print(f"[{time.ctime()}] 解析更新信息时发生错误: {e}")
        result = ('error', f"无法解析更新文件: {e}", None)
    
    root.after(0, show_update_dialog, result, icon)

#检查更新线程
def check_for_updates(icon):
    threading.Thread(target=perform_network_check, args=(icon,)).start()

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
    global root, icon
    root = tk.Tk()
    root.withdraw()

    try:
        icon_path = resource_path(ICON_FILENAME)
        image = Image.open(icon_path)
    except FileNotFoundError:
        print(f"错误：找不到图标文件 '{ICON_FILENAME}'。")
        sys.exit(1)
    
    initial_menu = Menu(*build_menu_items())
    icon = Icon(APP_NAME, image, "Binglish桌面英语", menu=initial_menu)
    
    threading.Thread(target=icon.run, daemon=True).start()

    update_thread = threading.Thread(target=run_scheduler, args=(icon,), daemon=True)
    update_thread.start()
    
    print("程序已启动并在后台运行。请在任务栏右下角查找图标。")
    root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()