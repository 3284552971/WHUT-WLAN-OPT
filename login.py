# coding:utf-8
import logging
import requests
import base64
import re
import sys
import time
import socket
import subprocess
import psutil
import asyncio
import os
from urllib.parse import urlparse, parse_qs
import yaml

BLUE, END = '\033[1;36m', '\033[0m'

request_url = 'http://172.30.21.100/api/account/login'

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(asctime)s ====> %(message)s')

session = requests.Session()
session.trust_env = False

# Clash相关可执行文件列表
CLASH_EXECUTABLES = [
    'clash-verge.exe',
    'clash.exe',
    'clash-win64.exe',
    'Clash.for.Windows.exe',
    'Clash.Meta.exe',
    'v2rayN.exe'
]

def log_out():
    """注销当前连接"""
    try:
        response = requests.get('http://172.30.21.100/api/account/logout')
        msg = response.json()
        if msg.get('code') == 0:
            logging.info('尝试注销连接，注销成功.')
            time.sleep(10)
    except Exception as e:
        logging.info(f"尝试注销连接，但失败: {e}")

def get_csrf_token():
    """获取CSRF令牌"""
    resp = session.get("http://172.30.21.100/api/csrf-token")
    return resp.json().get("csrf_token")

def check_ping_connection():
    """使用ping检查网络连接"""
    try:
        # Windows下使用ping命令，检查Google和百度
        test_hosts = ['google.com', 'baidu.com']
        
        for host in test_hosts:
            try:
                result = subprocess.run(
                    ['ping', '-n', '4', host], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    logging.info(f"Ping {host} 成功")
                    return True
            except subprocess.TimeoutExpired:
                logging.warning(f"Ping {host} 超时")
                continue
        return False
    except Exception as e:
        logging.error(f"Ping检查失败: {e}")
        return False

def check_request_connection():
    """使用HTTP请求检查网络连接"""
    try:
        # 测试百度和Google连接
        test_urls = [
            'https://www.baidu.com',
            'https://www.google.com'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logging.info(f"HTTP请求 {url} 成功")
                    return True
            except requests.RequestException:
                logging.warning(f"HTTP请求 {url} 失败")
                continue
        return False
    except Exception as e:
        logging.error(f"HTTP连接检查失败: {e}")
        return False

def is_net_ok() -> bool:
    """综合检查网络连接状态"""
    logging.info("开始检查网络连接...")
    
    # 首先尝试ping检查
    ping_ok = check_ping_connection()
    if ping_ok:
        logging.info("Ping检查通过")
        return True
    
    # 然后尝试HTTP请求检查
    http_ok = check_request_connection()
    if http_ok:
        logging.info("HTTP请求检查通过")
        return True
    
    logging.warning("网络连接检查失败")
    return False

def close_clash_processes():
    """关闭所有Clash相关进程"""
    logging.info("正在关闭Clash相关进程...")
    
    closed_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            for clash_exe in CLASH_EXECUTABLES:
                if clash_exe.lower() in proc_name:
                    proc.terminate()
                    proc.wait(timeout=5)
                    closed_processes.append(clash_exe)
                    logging.info(f"已关闭进程: {clash_exe} (PID: {proc.info['pid']})")
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue
    
    if closed_processes:
        logging.info(f"成功关闭 {len(closed_processes)} 个Clash进程")
        time.sleep(2)  # 等待进程完全关闭
    else:
        logging.info("没有发现正在运行的Clash进程")
    
    return closed_processes

def start_clash_process(clash_path):
    """启动Clash进程"""
    if not clash_path or not os.path.exists(clash_path):
        logging.error(f"Clash路径无效: {clash_path}")
        return False
    
    try:
        logging.info(f"正在启动Clash: {clash_path}")
        subprocess.Popen(clash_path)
        time.sleep(3)  # 等待Clash启动
        logging.info("Clash启动成功")
        return True
    except Exception as e:
        logging.error(f"启动Clash失败: {e}")
        return False

def login_request(username, password) -> bool:
    """执行登录请求"""
    logging.info("正在执行校园网登录...")
    
    nasId = get_nas_id()
    logging.info(f'NAS ID: {nasId}')
    
    if nasId == -1:
        logging.error("无法获取NAS ID")
        return False
    
    csrf_token = get_csrf_token()
    
    data = {
        "username": username,
        "password": password,
        "nasId": nasId
    }
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'accept-encoding': 'gzip, deflate',
        'cache-control': 'max-age=0',
        'connection': 'keep-alive',
        'accept-language': 'zh-CN,zh-TW;q=0.8,zh;q=0.6,en;q=0.4,ja;q=0.2',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'x-csrf-token': csrf_token,
    }
    
    try:
        response = session.post(requesr_url, data=data, headers=headers)
        response.encoding = response.apparent_encoding

        if '"authCode":"ok' in response.text:
            logging.info("登录成功!")
            user_ip = get_user_ip(response.text)
            host_ip = get_host_ip()
            logging.info(f"用户IP: {user_ip}")
            logging.info(f"主机IP: {host_ip}")
            return True
        else:
            logging.error(f"登录失败: {response.text}")
            return False
    except Exception as e:
        logging.exception(f"请求错误: {e}")
        return False

def get_host_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def get_user_ip(response_text):
    """从响应中提取用户IP"""
    match_list = re.findall(r'"UserIpv4":"(.*?)"', response_text, re.S)
    if len(match_list) == 0:
        return -1
    return match_list[0]

def get_nas_id():
    """获取NAS ID"""
    try:
        response = session.get('http://www.msftconnecttest.com/redirect', allow_redirects=True)
        login_url = response.url
        parsed_url = urlparse(login_url)
        query_params = parse_qs(parsed_url.query)
        nasid_list = query_params.get("nasId")
        if nasid_list:
            return nasid_list[0]
        return -1
    except Exception as e:
        logging.error(f"获取NAS ID失败: {e}")
        return -1

async def async_sleep(seconds):
    """异步睡眠函数，减少CPU占用"""
    await asyncio.sleep(seconds)

def heading():
    """显示标题"""
    banner = r"""
 _       ____  ____  ________  _       ____    ___    _   __
| |     / / / / / / / /_  __/ | |     / / /   /   |  / | / /
| | /| / / /_/ / / / / / /____| | /| / / /   / /| | /  |/ / 
| |/ |/ / __  / /_/ / / /_____/ |/ |/ / /___/ ___ |/ /|  /  
|__/|__/_/ /_/\____/ /_/      |__/|__/_____/_/  |_/_/ |_/
"""
    print(BLUE + banner + END + '\n')

async def main_loop(username, password, has_clash=False, clash_path=""):
    """主循环：每10分钟检测一次网络连接"""
    check_interval = 600  # 10分钟 = 600秒
    
    while True:
        try:
            logging.info("开始网络连接检查...")
            
            if is_net_ok():
                logging.info("网络连接正常")
            else:
                logging.warning("检测到网络连接异常，开始自动重连...")
                
                # 如果有clash，先关闭
                closed_processes = []
                if has_clash:
                    closed_processes = close_clash_processes()
                
                # 执行登录
                success = login_request(username, password)
                
                if success:
                    logging.info("网络重连成功")
                    # 等待一段时间再重新启动clash
                    if has_clash and closed_processes:
                        logging.info("等待5秒后重新启动Clash...")
                        await async_sleep(5)
                        start_clash_process(clash_path)
                else:
                    logging.error("网络重连失败")
            
            logging.info(f"等待 {check_interval//60} 分钟后进行下次检查...")
            await async_sleep(check_interval)
            
        except KeyboardInterrupt:
            logging.info("接收到中断信号，正在退出...")
            break
        except Exception as e:
            logging.error(f"主循环发生错误: {e}")
            await async_sleep(60)  # 错误时等待1分钟后重试

if __name__ == "__main__":
    heading()
    
    # 配置信息 - 请修改为你的实际信息
    username = settings.get('校园网账号')
    password = settings.get('校园网密码')
    has_clash = settings.get('clash路径') is not None
    clash_path = settings.get('clash路径')

    print(f"校园网自动连接系统启动")
    print(f"用户名: {username}")
    print(f"是否使用Clash: {has_clash}")
    if has_clash:
        print(f"Clash路径: {clash_path}")
    print("按 Ctrl+C 可退出程序")
    
    # 运行主循环
    try:
        asyncio.run(main_loop(username, password, has_clash, clash_path))
    except KeyboardInterrupt:
        logging.info("程序已退出")
