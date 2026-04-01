# -- coding: utf-8 --
"""
Copyright (c) 2024 [Hosea]
Licensed under the MIT License.
See LICENSE file in the project root for full license information.
"""
import os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

ns_random = os.environ.get("NS_RANDOM","false")
cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
# 通过环境变量控制是否使用无头模式，默认为 True（无头模式）
headless = os.environ.get("HEADLESS", "true").lower() == "true"

randomInputStr = ["bd","绑定","帮顶"]

def click_sign_icon(driver):
    """
    直接访问签到板页面并执行签到
    """
    try:
        # 1. 直接跳转到签到页面，省去点击图标的麻烦
        print("直接访问签到板页面...")
        driver.get('https://www.nodeseek.com/board')
        
        # 2. 等待页面加载（Actions 环境建议多等会儿）
        print("等待签到按钮加载...")
        time.sleep(8) 
        
        # 3. 确定签到策略：是“拿稳 5 个鸡腿”还是“试试手气”
        # 注意：这里使用了你脚本开头定义的 ns_random 变量
        use_random = os.environ.get("NS_RANDOM", "false").lower() == "true"
        target_text = "试试手气" if use_random else "鸡腿 x 5"
        
        print(f"当前策略：{target_text}。正在定位按钮...")

        # 4. 根据你提供的 HTML 结构，使用 XPath 精准定位
        # 这里的 XPath 会寻找 class 为 btn 且包含目标文字的 button
        try:
            sign_button = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((
                    By.XPATH, f"//button[contains(@class, 'btn') and contains(text(), '{target_text}')]"
                ))
            )
            
            # 5. 使用 JavaScript 强制点击（物理点击在无头模式下容易偏移）
            driver.execute_script("arguments[0].click();", sign_button)
            print(f"🎉 【成功】已点击“{target_text}”按钮！")
            
            # 额外等待 3 秒确保请求发送成功
            time.sleep(3)
            return True

        except Exception as btn_err:
            # 如果找不到按钮，很可能是今天已经签到过了，按钮消失了
            print("未发现签到按钮，可能今日已签到。")
            return False

    except Exception as e:
        print(f"签到流程出错: {str(e)}")
        return False

def setup_driver_and_cookies():
    """
    初始化浏览器并设置cookie的通用方法
    返回: 设置好cookie的driver实例
    """
    try:
        cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
        headless = os.environ.get("HEADLESS", "true").lower() == "true"
        
        if not cookie:
            print("未找到cookie配置")
            return None
            
        print("开始初始化浏览器...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if headless:
            print("启用无头模式...")
            options.add_argument('--headless')
            # 添加以下参数来绕过 Cloudflare 检测
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            # 设置 User-Agent
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        print("正在启动Chrome...")
        driver = uc.Chrome(options=options, version_main=146)
        
        if headless:
            # 执行 JavaScript 来修改 webdriver 标记
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(1920, 1080)
        
        print("Chrome启动成功")
        
        print("正在设置cookie...")
        driver.get('https://www.nodeseek.com')
        
        # 等待页面加载完成
        time.sleep(5)
        
        for cookie_item in cookie.split(';'):
            try:
                name, value = cookie_item.strip().split('=', 1)
                driver.add_cookie({
                    'name': name, 
                    'value': value, 
                    'domain': '.nodeseek.com',
                    'path': '/'
                })
            except Exception as e:
                print(f"设置cookie出错: {str(e)}")
                continue
        
        print("刷新页面...")
        driver.refresh()
        time.sleep(5)  # 增加等待时间
        
        return driver
        
    except Exception as e:
        print(f"设置浏览器和Cookie时出错: {str(e)}")
        print("详细错误信息:")
        print(traceback.format_exc())
        return None

def nodeseek_comment(driver):
    try:
        total_simulated_count = 0  # 模拟计数器
        replied_urls = set()

        # 定义话术词库
        buy_replies = ["祝早收", "早收", "bd", "帮顶"]
        sell_replies = ["好鸡bd", "好鸡", "帮顶", "绑定", "祝早出"]
        default_replies = ["bd", "帮顶", "绑定"]

        print(f"🧪 [模拟模式] 开始回帖演习，目标：10 个帖子")

        while total_simulated_count < 10:
            print(f"\n--- [模拟] 正在刷新列表 (进度: {total_simulated_count}/10) ---")
            driver.get('https://www.nodeseek.com/categories/trade')
            time.sleep(5)
            
            try:
                posts = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.post-list-item'))
                )
            except:
                print("[模拟] 加载列表失败，尝试刷新...")
                continue

            # --- 筛选逻辑 (保持不变，用于验证准确性) ---
            target_post = None
            for post in posts:
                try:
                    if post.find_elements(By.CSS_SELECTOR, '.pined'): continue
                    
                    title_elem = post.find_element(By.CSS_SELECTOR, '.post-title a')
                    url = title_elem.get_attribute('href')
                    title = title_elem.text
                    
                    if url in replied_urls: continue
                    
                    comment_text = post.find_element(By.CSS_SELECTOR, '.post-comments').text.strip()
                    comment_count = int(comment_text) if comment_text.isdigit() else 0
                    
                    if comment_count <= 5:
                        target_post = {"url": url, "title": title, "comments": comment_count}
                        break 
                except:
                    continue

            if not target_post:
                print("[模拟] 暂时没发现 5 评以内新贴，5 分钟后重扫...")
                time.sleep(300)
                continue

            # --- 匹配逻辑验证 ---
            current_title = target_post["title"]
            if "收" in current_title:
                reply_type = "收贴话术"
                reply_content = random.choice(buy_replies)
            elif "出" in current_title:
                reply_type = "出贴话术"
                reply_content = random.choice(sell_replies)
            else:
                reply_type = "默认话术"
                reply_content = random.choice(default_replies)

            # --- 模拟执行展示 ---
            print("="*50)
            print(f"🔍 [发现符合条件帖子]")
            print(f"   标题: {current_title}")
            print(f"   评论数: {target_post['comments']}")
            print(f"   链接: {target_post['url']}")
            print(f"   匹配类型: {reply_type}")
            print(f"   拟回复内容: 【{reply_content}】")
            print("="*50)

            # 为了验证页面加载是否正常，我们依然可以“假装”点进去看一眼
            try:
                driver.get(target_post["url"])
                time.sleep(3)
                print(f"✅ [页面访问成功] 确认回复框已加载。")
                
                # --- 注意：以下是模拟动作，不会产生真实提交 ---
                print("🚫 [模拟] 跳过真实输入和点击提交按钮的操作...")
                
                total_simulated_count += 1
                replied_urls.add(target_post["url"])

                # --- 模拟休息逻辑 ---
                if total_simulated_count < 10:
                    wait_time = random.randint(10, 20) # 测试时可以缩短休息时间，正式时改回 120-300
                    print(f"⏱️ [模拟休息] 等待 {wait_time} 秒后模拟下一次寻找...")
                    time.sleep(wait_time)
                else:
                    print("\n🎊 [演习结束] 已完成 10 个帖子的模拟测试。")
                    print("💤 [模拟] 进入一小时长休息的心跳日志输出...")
                    for i in range(3): # 演习时只模拟 30 分钟
                        time.sleep(600)
                        print(f"💤 演习长休息中... 已过去 {(i+1)*10} 分钟")
                    return 

            except Exception as e:
                print(f"❌ [模拟出错] 无法访问帖子页面: {e}")
                time.sleep(5)

    except Exception as e:
        print(f"❌ [模拟全局异常]: {e}")

def click_chicken_leg(driver):
    try:
        print("尝试点击加鸡腿按钮...")
        chicken_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="nsk-post"]//div[@title="加鸡腿"][1]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chicken_btn)
        time.sleep(0.5)
        chicken_btn.click()
        print("加鸡腿按钮点击成功")
        
        # 等待确认对话框出现
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-confirm'))
        )
        
        # 检查是否是7天前的帖子
        try:
            error_title = driver.find_element(By.XPATH, "//h3[contains(text(), '该评论创建于7天前')]")
            if error_title:
                print("该帖子超过7天，无法加鸡腿")
                ok_btn = driver.find_element(By.CSS_SELECTOR, '.msc-confirm .msc-ok')
                ok_btn.click()
                return False
        except:
            ok_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.msc-confirm .msc-ok'))
            )
            ok_btn.click()
            print("确认加鸡腿成功")
            
        # 等待确认对话框消失
        WebDriverWait(driver, 5).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-overlay'))
        )
        time.sleep(1)  # 额外等待以确保对话框完全消失
        
        return True
        
    except Exception as e:
        print(f"加鸡腿操作失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始执行NodeSeek自动任务...")
    driver = setup_driver_and_cookies()
    if not driver:
        print("浏览器初始化失败")
        exit(1)
    
    # 建议先签到，确保最重要的奖励拿到
    click_sign_icon(driver)
    
    # 再去执行评论加鸡腿任务
    nodeseek_comment(driver)
    
    print("所有脚本执行完成")
    # while True:
    #     time.sleep(1)

