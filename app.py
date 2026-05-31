import os
import threading
import telebot
from flask import Flask
import requests

# ========== 配置 ==========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not TOKEN:
    raise ValueError("请在环境变量中设置 TELEGRAM_TOKEN")
if not DEEPSEEK_API_KEY:
    raise ValueError("请在环境变量中设置 DEEPSEEK_API_KEY")

bot = telebot.TeleBot(TOKEN)

# 语言映射（支持的语言）
LANG_MAP = {
    "中文": "Chinese",
    "英文": "English", 
    "日语": "Japanese",
    "韩语": "Korean",
    "法语": "French",
    "德语": "German",
    "西班牙语": "Spanish",
    "俄语": "Russian",
    "葡萄牙语": "Portuguese"
}

# 默认目标语言
DEFAULT_TARGET_LANG = "Chinese"

# 用户语言偏好存储
user_langs = {}

def get_user_lang(user_id):
    """获取用户的目标语言"""
    return user_langs.get(user_id, DEFAULT_TARGET_LANG)

def translate_with_deepseek(text, target_lang):
    """使用 DeepSeek API 翻译文本"""
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建翻译提示词
    prompt = f"""请将以下文本翻译成{target_lang}，只返回翻译结果，不要添加任何解释：

原文：{text}

翻译成{target_lang}："""
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的翻译助手，只返回翻译结果，不添加任何额外内容。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        translated = result["choices"][0]["message"]["content"].strip()
        return translated
    except Exception as e:
        print(f"翻译错误: {e}")
        return f"翻译出错：{e}"

# ========== 命令 ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "🤖 **DeepSeek AI 翻译机器人**\n\n"
        "直接发送任何语言的文字，我会用 AI 精准翻译\n\n"
        "**设置命令：**\n"
        "/setlang 语言 - 切换目标语言\n"
        "/lang - 查看当前语言\n\n"
        "**支持语言：**\n"
        "中文、英文、日语、韩语、法语、德语、西班牙语、俄语、葡萄牙语\n\n"
        "**示例：**\n"
        "/setlang 葡萄牙语\n"
        "然后发送：Hello, how are you?",
        parse_mode='Markdown')

@bot.message_handler(commands=['lang'])
def show_lang(message):
    user_id = message.from_user.id
    current = get_user_lang(user_id)
    bot.reply_to(message, f"🌐 你当前的翻译目标语言是：**{current}**\n\n发送 `/setlang 语言` 来切换", parse_mode='Markdown')

@bot.message_handler(commands=['setlang'])
def set_lang(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, f"请指定语言，例如：`/setlang 葡萄牙语`\n\n支持：{', '.join(LANG_MAP.keys())}", parse_mode='Markdown')
        return
    
    lang_input = parts[1]
    if lang_input in LANG_MAP:
        target = LANG_MAP[lang_input]
        user_langs[message.from_user.id] = target
        bot.reply_to(message, f"✅ 已设置翻译目标语言为：**{lang_input}**")
    else:
        bot.reply_to(message, f"不支持的语言：{lang_input}\n\n支持：{', '.join(LANG_MAP.keys())}")

@bot.message_handler(func=lambda msg: True)
def translate(message):
    try:
        text = message.text
        if not text or text.startswith('/'):
            return
        
        # 发送"正在翻译"提示
        bot.send_chat_action(message.chat.id, 'typing')
        
        target_lang = get_user_lang(message.from_user.id)
        translated = translate_with_deepseek(text, target_lang)
        
        bot.reply_to(message, f"🌐 **{target_lang}翻译：**\n{translated}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"翻译出错：{e}")

# ========== 启动机器人 ==========
def run_bot():
    print("🤖 DeepSeek AI 翻译机器人已启动...")
    print(f"📊 支持的语言：{', '.join(LANG_MAP.keys())}")
    bot.infinity_polling()

# ========== 健康检查服务器 ==========
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

# ========== 主程序 ==========
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 健康检查服务运行在端口 {port}")
    app.run(host="0.0.0.0", port=port)