import os
import threading
import telebot
from flask import Flask
from deep_translator import GoogleTranslator

# ========== 配置 ==========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    print("⚠️ 警告：未设置 TELEGRAM_TOKEN 环境变量")
    TOKEN = "请替换为你的Token"  # 临时测试用

bot = telebot.TeleBot(TOKEN)

# ========== 命令 ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "🤖 翻译机器人\n\n"
        "直接发送任何语言的文字，我会自动翻译成中文\n\n"
        "支持语言：中文、英文、日文、韩文、法文、德文等")

@bot.message_handler(func=lambda msg: True)
def translate(message):
    try:
        text = message.text
        if not text:
            return
        translator = GoogleTranslator(source='auto', target='zh-CN')
        result = translator.translate(text)
        bot.reply_to(message, f"🌐 {result}")
    except Exception as e:
        bot.reply_to(message, f"翻译出错：{e}")

# ========== 启动机器人 ==========
def run_bot():
    print("🤖 翻译机器人已启动...")
    bot.infinity_polling()

# ========== 健康检查服务器 ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

# ========== 主程序 ==========
if __name__ == '__main__':
    # 启动机器人线程
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # 启动健康检查服务器
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 健康检查服务运行在端口 {port}")
    app.run(host="0.0.0.0", port=port)