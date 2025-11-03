import typing
from playwright.async_api import async_playwright
import asyncio
import yaml
import requests
from pathlib import Path

class Network_maintain:
    def __init__(self):
        pass

    async def setting(self):
        with open(str(Path(__file__).parent / "setting.yaml"), 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.username = self.config.get('校园网账号')
        self.password = self.config.get('校园网密码')
        if not self.username or not self.password:
            return False
        self.check_interval = self.config.get('检测间隔', 300)
        self.url = self.config.get("url")
        return True

    async def main_loop(self):
        result = asyncio.run(self.setting())
        if not result:
            print("请先在setting.yaml中配置校园网账号和密码")
        while not result:
            await asyncio.sleep(30)
            result = asyncio.run(self.setting())
        print("网络维护程序已启动...")
        while True:
            check = await self.is_net_ok()
            if not check:
                await self.re_connect()
                await asyncio.sleep(5)  # 等待5秒以确保连接稳定
            await asyncio.sleep(self.check_interval)

    async def re_connect(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(self.url)
            await page.fill('#username', self.username)
            await page.fill('#password', self.password)
            await page.click('#login-account')
            await page.wait_for_timeout(5000)
            await browser.close()
    
    async def is_net_ok(self) -> bool:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto("http://baidu.com/")
                if self.url == page.url:
                    print("检测功能发力中...")
                    await page.fill('#username', self.username)
                    await page.fill('#password', self.password)
                    await page.click('#login-account')
                    await page.wait_for_timeout(5000)
                    await browser.close()
                    return True
                elif page.url == "http://baidu.com/":
                    return True
                elif page.url.startswith("http://172.30.21.100/"):
                    self.url = page.url
                    print(f"检测功能发力中...更新登录地址为{self.url}")
                    await page.fill('#username', self.username)
                    await page.fill('#password', self.password)
                    await page.click('#login-account')
                    await page.wait_for_timeout(5000)
                    await browser.close()
                    return True
        except:
            return False
                
if __name__ == "__main__":
    network_maintain = Network_maintain()
    asyncio.run(network_maintain.main_loop())
