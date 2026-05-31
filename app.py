import os
import threading
import telebot
from flask import Flask
from deep_translator import GoogleTranslator

# ========== 配置 ==========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("请在环境变量中设置 TELEGRAM_TOKEN")

bot = telebot.TeleBot(TOKEN)

# 语言映射
LANG_MAP = {
    "中文": "zh-CN",
    "英文": "en",
    "日语": "ja",
    "韩语": "ko",
    "法语": "fr",
    "德语": "de",
    "西班牙语": "es",
    "俄语": "ru",
    "葡萄牙语": "pt"
}

DEFAULT_TARGET_LANG = "zh-CN"
user_langs = {}

def get_user_lang(user_id):
    return user_langs.get(user_id, DEFAULT_TARGET_LANG)

def translate_with_google(text, target_lang):
    """使用 Google 翻译"""
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        return f"翻译出错：{e}"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "🤖 **翻译机器人**\n\n"
        "直接发送任何语言的文字，自动翻译\n\n"
        "**命令：**\n"
        "/setlang 语言 - 切换目标语言\n"
        "/lang - 查看当前语言\n\n"
        "**支持语言：**\n"
        "中文、英文、日语、韩语、法语、德语、西班牙语、俄语、葡萄牙语",
        parse_mode='Markdown')

@bot.message_handler(commands=['lang'])
def show_lang(message):
    user_id = message.from_user.id
    current = get_user_lang(user_id)
    lang_name = [k for k, v in LANG_MAP.items() if v == current]
    name = lang_name[0] if lang_name else current
    bot.reply_to(message, f"🌐 当前翻译目标语言：**{name}**")

@bot.message_handler(commands=['setlang'])
def set_lang(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"请指定语言：{', '.join(LANG_MAP.keys())}")
        return
    lang_input = parts[1]
    if lang_input in LANG_MAP:
        user_langs[message.from_user.id] = LANG_MAP[lang_input]
        bot.reply_to(message, f"✅ 已设置目标语言为：**{lang_input}**")
    else:
        bot.reply_to(message, f"不支持：{lang_input}\n支持：{', '.join(LANG_MAP.keys())}")

@bot.message_handler(func=lambda msg: True)
def translate(message):
    try:
        text = message.text
        if not text or text.startswith('/'):
            return
        bot.send_chat_action(message.chat.id, 'typing')
        target = get_user_lang(message.from_user.id)
        result = translate_with_google(text, target)
        bot.reply_to(message, f"🌐 **译文：**\n{result}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"翻译出错：{e}")

def run_bot():
    print("🤖 翻译机器人已启动...")
    bot.infinity_polling()

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 健康检查服务运行在端口 {port}")
    app.run(host="0.0.0.0", port=port)