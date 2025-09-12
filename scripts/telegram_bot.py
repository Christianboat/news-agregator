import requests
import os
from config import Config

def send_telegram_message(text, chat_id=None, token=None):
    if not chat_id:
        chat_id = Config.TELEGRAM_CHAT_ID
    if not token:
        token = Config.TELEGRAM_BOT_TOKEN
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def send_telegram_photo(image_path, caption="", chat_id=None, token=None):
    if not chat_id:
        chat_id = Config.TELEGRAM_CHAT_ID
    if not token:
        token = Config.TELEGRAM_BOT_TOKEN
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': chat_id, 'caption': caption}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"Error sending Telegram photo: {e}")
        return False

def send_weekly_digest(news_items_with_scripts):
    # Send the script as a message
    if news_items_with_scripts:
        script_content = news_items_with_scripts[0][1]  # Get script from first item
        send_telegram_message(f"📰 <b>Weekly Education News Digest</b>\n\n{script_content}")
        
        # Send each news item with its image
        for news_item, _ in news_items_with_scripts:
            if news_item.image_path:
                image_path = os.path.join(Config.UPLOAD_FOLDER, news_item.image_path)
                caption = f"<b>{news_item.title}</b>\n\n{news_item.summary}\n\nRead more: {news_item.link}"
                send_telegram_photo(image_path, caption)
            else:
                message = f"<b>{news_item.title}</b>\n\n{news_item.summary}\n\nRead more: {news_item.link}"
                send_telegram_message(message)
    else:
        send_telegram_message("No education news found this week.")