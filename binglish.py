import requests
import ctypes
import os
import sys
import time
import threading
import winreg
import webbrowser
from PIL import Image, ExifTags
from pystray import MenuItem as item, Icon, Menu
import tkinter as tk
from tkinter import messagebox
import subprocess
import json
from playsound3 import playsound 

VERSION = "1.1.1"
RELEASE_JSON_URL = "https://ss.blueforge.org/bing/release.json" # 包含版本号和更新说明的JSON文件URL
DOWNLOAD_URL = "https://ss.blueforge.org/bing/binglish.exe" #最新版本可执行文件
IMAGE_URL = f"https://ss.blueforge.org/bing?v={VERSION}"  #图片URL

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
    menu_items.append(Menu.SEPARATOR)

    menu_items.append(item('开机运行', toggle_startup, checked=lambda item: is_startup_enabled()))

    if getattr(sys, 'frozen', False):
        menu_items.append(item('检查更新', lambda: check_for_updates(icon)))
    
    menu_items.append(item('项目网址', open_project_website))
    menu_items.append(item('退出', lambda: quit_app(icon)))
    
    return tuple(menu_items)

#更新墙纸任务
def update_wallpaper_job(is_random=False): # is_random 参数用于判断是否为随机复习
    global icon
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
    
    # 如果是随机复习，则在URL中添加random参数
    if is_random:
        dynamic_image_url += "&random"
        print(f"[{time.ctime()}] 随机复习模式，将使用URL: {dynamic_image_url}")
    else:
        print(f"[{time.ctime()}] 正常循环模式，将使用URL: {dynamic_image_url}")

    image_downloaded = download_image(dynamic_image_url, full_save_path)
    if image_downloaded:
        global bing_word, bing_url, bing_mp3
        try:
            print(f"[{time.ctime()}] 正在从 {full_save_path} 提取EXIF信息...")
            with Image.open(full_save_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    bing_word = exif_data.get(315, "").strip()
                    bing_url = exif_data.get(270, "").strip()
                    bing_mp3 = exif_data.get(269, "").strip()
                    
                    print(f"[{time.ctime()}] EXIF信息提取成功:")
                    print(f"    - Artist (bing_word): {bing_word}")
                    print(f"    - ImageDescription (bing_url): {bing_url}")
                    print(f"    - DocumentName (bing_mp3): {bing_mp3}")
                else:
                    print(f"[{time.ctime()}] 图片中未找到EXIF信息，清空旧数据。")
                    bing_word, bing_url, bing_mp3 = None, None, None
        except Exception as e:
            print(f"[{time.ctime()}] 提取EXIF信息时发生错误: {e}")
            bing_word, bing_url, bing_mp3 = None, None, None
        
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

    print(f"[{time.ctime()}] 首次壁纸更新成功。")
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

#打开项目网址
def open_project_website():
    try:
        webbrowser.open(PROJECT_URL)
        print(f"[{time.ctime()}] 已调用浏览器打开: {PROJECT_URL}")
    except Exception as e:
        print(f"[{time.ctime()}] 打开项目网址失败: {e}")

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
        message = f"有新版本 ({version_or_error}) 可用。\n\n更新说明:\n{releasenotes}\n\n您想现在更新吗？"
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
        print(f"[{time.ctime()}] 检查更新时发生错误: {e}")
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
            print(f"[{time.ctime()}] 正在播放在线音频: {bing_mp3}")
            playsound(bing_mp3)
            print(f"[{time.ctime()}] 音频播放完毕。")
        except Exception as e:
            print(f"[{time.ctime()}] 播放音频时发生错误: {e}")
            root.after(0, lambda: messagebox.showerror("播放失败", f"无法播放在线音频：{e}"))

#退出程序
def quit_app(icon):
    print("正在退出程序...")
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
    main()