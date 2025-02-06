import os
import requests
import telebot
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Function to send messages via Instagram DM API
def send_instagram_dm(user_id, message):
    url = f"https://graph.facebook.com/v17.0/{user_id}/messages"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
    data = {"recipient": {"id": user_id}, "message": {"text": message}}

    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Telegram command to start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send an Instagram user ID and a message like this:\n\n /send 123456789 Hello!")

# Handle /send command
@bot.message_handler(commands=['send'])
def handle_send(message):
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            bot.reply_to(message, "Usage: /send <instagram_user_id> <message>")
            return
        
        user_id = parts[1]
        msg_text = parts[2]

        response = send_instagram_dm(user_id, msg_text)
        bot.reply_to(message, f"Message sent! Response: {response}")

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Flask Webhook Endpoint for Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Flask Webhook Endpoint for Instagram Messages
@app.route("/webhook", methods=["GET", "POST"])
def instagram_webhook():
    if request.method == "GET":
        # Verify webhook for Meta
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    elif request.method == "POST":
        data = request.json
        print(f"Received Instagram Message: {data}")
        return "OK", 200

# Set webhook for Telegram
def set_telegram_webhook():
    webhook_url = os.getenv("WEBHOOK_URL") + f"/{TOKEN}"
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
    response = requests.get(url)
    print("Telegram Webhook Set:", response.json())

if __name__ == "__main__":
    set_telegram_webhook()
    app.run(host="0.0.0.0", port=5000)
