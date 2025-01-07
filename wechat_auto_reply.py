from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from openai import OpenAI

class WeChatBot:
    def __init__(self):
        # 获取用户配置
        print("请输入配置信息：")
        self.my_name = input("请输入您的微信名称: ")
        self.target_names = input("请输入需要自动回复的用户名称（多个用逗号分隔）: ").split(',')
        self.target_names = [name.strip() for name in self.target_names]
        print(f"将自动回复以下用户的消息: {', '.join(self.target_names)}")
        
        # 初始化浏览器
        self.driver = webdriver.Chrome()
        self.driver.get("https://wx2.qq.com/?target=t")
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key="",   #在此输入你的api_key；不同的大模型api_key有不同调用方法，请参考对应模型的官方文档
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 等待用户扫码登录
        print("请扫描二维码登录...")
        input("登录成功后按回车继续...")

    def get_last_message(self):
        """获取最新一条消息"""
        try:
            messages = self.driver.find_elements(By.CSS_SELECTOR, ".message")
            if messages:
                last_message = messages[-1]
                # 获取发送者名称
                avatar = last_message.find_element(By.CSS_SELECTOR, ".avatar")
                sender_name = avatar.get_attribute("title")
                
                # 获取消息内容
                message_text = last_message.find_element(By.CSS_SELECTOR, ".js_message_plain").text
                return sender_name, message_text
            return None
        except:
            return None

    def send_message(self, text):
        """发送消息"""
        try:
            # 定位输入框和发送按钮
            input_box = self.driver.find_element(By.ID, "editArea")
            send_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn.btn_send")
            
            # 输入消息并发送
            input_box.clear()
            input_box.send_keys(text)
            send_btn.click()
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def get_ai_response(self, message):
        """调用大模型获取回复"""
        try:
            completion = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {'role': 'system', 'content': 'You are a helpful assistant. 请使用尽量简短的内容回答。'},
                    {'role': 'user', 'content': message}
                ]
            )
            response = completion.choices[0].message.content
            # 根据回复长度设置等待时间，每10个字符等待1秒，最长等待8秒
            wait_time = min(len(response) / 10, 8)
            time.sleep(wait_time)
            return response
        except Exception as e:
            print(f"调用AI接口失败: {e}")
            return "抱歉,我现在无法回复。"

    def run(self):
        """运行主循环"""
        last_message = None
        print("开始监听消息...")
        
        while True:
            try:
                result = self.get_last_message()
                if result:
                    sender_name, current_message = result
                
                    # 如果有新消息，是目标用户发送的，且不是重复消息
                    if (sender_name in self.target_names and 
                        current_message != last_message):
                        print(f"收到新消息 from {sender_name}: {current_message}")
                        
                        # 获取AI回复
                        response = self.get_ai_response(current_message)
                        print(f"AI回复: {response}")
                        
                        # 发送回复
                        if self.send_message(response):
                            last_message = current_message
                    
                time.sleep(2)  # 避免过于频繁的请求
                
            except Exception as e:
                print(f"运行出错: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = WeChatBot()
    bot.run() 