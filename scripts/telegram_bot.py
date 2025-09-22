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
        response = requests.post(url, data=payload, timeout=10)
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
    
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        return False

    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            response = requests.post(url, files=files, data=data, timeout=20)
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"Error sending Telegram photo: {e}")
        return False

def send_weekly_digest(news_items):
    """
    Expects a list of dicts:
      {
        "title", "summary", "link", "image_path", "created_at", "script"
      }
    """
    if not news_items:
        send_telegram_message("No education news found this week.")
        return

    # Send unified script (from first element)
    try:
        script_content = news_items[0].get("script", "")
        send_telegram_message(f"📰 <b>Weekly Education News Digest</b>\n\n{script_content}")
    except Exception as e:
        print(f"Error sending unified script: {e}")

    # Send each item (image if available)
    for n in news_items:
        title = n.get("title", "")
        summary = n.get("summary", "")
        link = n.get("link", "")
        img = n.get("image_path", None)

        caption = f"<b>{title}</b>\n\n{summary}\n\nRead more: {link}"

        if img:
            path = os.path.join(Config.UPLOAD_FOLDER, img)
            success = send_telegram_photo(path, caption)
            if not success:
                send_telegram_message(caption)
        else:
            send_telegram_message(caption)
