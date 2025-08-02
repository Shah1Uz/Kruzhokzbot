#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import logging
import subprocess
import time
from pathlib import Path
import telebot
from telebot import types
from models import create_tables, save_user_history, get_user_history, get_total_user_kruzhoks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get bot token from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# User state management
user_states = {}
user_media_files = {}

# Effect names mapping
EFFECT_NAMES = {
    1: "Oddiy",
    2: "Zoom", 
    3: "Blur",
    4: "Rang o'zgarishi",
    5: "Aylanish"
}

# Uzbek language messages
MESSAGES = {
    'welcome': """👋 Salom, {}!
① Video yoki rasm yuboring.
② Effektni tanlang.
③ Doira tayyor ✔️

Tezkor buyruqlar:
♻️ Botni qayta ishga tushirish: /start
🗂 Oxirgi videolarni ko'rish: /history
❓ Muallifni yashirish: /hide
🌐 Tilni o'zgartirish: /lang""",
    
    'processing': "⏳ Ishlov berilmoqda...",
    'success': "✅ Tayyor! Sizning doiraviy videongiz:",
    'error': "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
    'unsupported': "❌ Qo'llab-quvvatlanmaydigan fayl turi. Faqat video yoki rasm yuboring.",
    
    'hide_info': """❓ Muallifni yashirish:

Telegram'da kruzhok (doiraviy video) yuborayotganda muallif nomi ko'rinadi. 
Uni yashirish uchun:

1. Videoni tayyor kruzhok sifatida saqlang
2. Uni boshqa suhbatga yo'naltiring
3. Yoki botdan olingan kruzhokni to'g'ridan-to'g'ri ulashing

Eslatma: Bu Telegram'ning xususiyati bo'lib, bot orqali to'liq nazorat qilib bo'lmaydi.""",
    
    'lang_selection': """🌐 Til tanlash:

Hozirda qo'llab-quvvatlanadigan tillar:
🇺🇿 O'zbek tili (joriy)
🇷🇺 Rus tili (tez orada)
🇺🇸 Ingliz tili (tez orada)

Til o'zgartirish funksiyasi ishlab chiqilmoqda...""",
    
    'choose_effect': "🎨 Quyidagi effektlardan birini tanlang:",
    'effect_processing': "🎬 Effekt qo'llanmoqda...",
    'history_header': "🗂 Oxirgi kruzhok videolaringiz:",
    'history_empty': "📭 Hali kruzhok yaratmagansiz. Video yoki rasm yuboring!",
    'history_count': "📊 Jami yaratilgan kruzhoklar: {count} ta"
}

def create_effect_keyboard():
    """Create inline keyboard for effect selection"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Create buttons for each effect
    btn1 = types.InlineKeyboardButton("📹 Oddiy", callback_data="effect_1")
    btn2 = types.InlineKeyboardButton("🔍 Zoom", callback_data="effect_2")
    btn3 = types.InlineKeyboardButton("🌫️ Blur", callback_data="effect_3")
    btn4 = types.InlineKeyboardButton("🌈 Rang", callback_data="effect_4")
    btn5 = types.InlineKeyboardButton("🔄 Aylanish", callback_data="effect_5")
    
    # Add buttons to markup
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    
    return markup

def create_temp_file(suffix=""):
    """Create a temporary file and return its path"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()
    return temp_file.name

def cleanup_file(file_path):
    """Safely delete a file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")

def get_video_duration(input_path):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return duration
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return 10.0  # Default fallback

def process_video_to_kruzhok(input_path, output_path, effect_type=1):
    """Convert video to circular kruzhok format using ffmpeg with effects"""
    try:
        # Get video info first
        duration = get_video_duration(input_path)
        
        # Limit duration to 60 seconds for kruzhok
        duration = min(duration, 60.0)
        
        # Define video filter based on effect type
        if effect_type == 1:  # Oddiy dumaloq video
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        elif effect_type == 2:  # Zoom effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,zoompan=z=\'min(zoom+0.0015,1.5)\':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2),format=yuv420p'
        elif effect_type == 3:  # Blur effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,gblur=sigma=2:steps=1,format=yuv420p'
        elif effect_type == 4:  # Rang o'zgarishi effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,hue=h=sin(2*PI*t)*360:s=1.5,format=yuv420p'
        elif effect_type == 5:  # Aylanish effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,rotate=PI*t/5,format=yuv420p'
        else:
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        
        # FFmpeg command to create circular video with effects
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-i', input_path,
            '-t', str(duration),  # Limit duration
            '-vf', video_filter,
            '-c:v', 'libx264',  # Video codec
            '-c:a', 'aac',      # Audio codec
            '-b:a', '128k',     # Audio bitrate
            '-ar', '44100',     # Audio sample rate
            '-ac', '2',         # Audio channels
            '-preset', 'fast',  # Encoding preset
            '-crf', '23',       # Quality setting
            output_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Video processing completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return False

def process_photo_to_kruzhok(input_path, output_path, effect_type=1):
    """Convert photo to 5-second circular kruzhok with effects"""
    try:
        # Define video filter based on effect type
        if effect_type == 1:  # Oddiy dumaloq video
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        elif effect_type == 2:  # Zoom effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,zoompan=z=\'min(zoom+0.002,1.8)\':d=1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2),format=yuv420p'
        elif effect_type == 3:  # Blur effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,gblur=sigma=3:steps=2,format=yuv420p'
        elif effect_type == 4:  # Rang o'zgarishi effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,hue=h=sin(2*PI*t/3)*180:s=1.3,format=yuv420p'
        elif effect_type == 5:  # Aylanish effekti
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,rotate=PI*t/3,format=yuv420p'
        else:
            video_filter = 'scale=480:480:force_original_aspect_ratio=increase,crop=480:480,format=yuv420p'
        
        # FFmpeg command to create 5-second circular video from image with effects
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-loop', '1',    # Loop the input image
            '-i', input_path,
            '-t', '5',       # 5 seconds duration
            '-vf', video_filter,
            '-c:v', 'libx264',  # Video codec
            '-pix_fmt', 'yuv420p',
            '-r', '25',         # Frame rate
            '-preset', 'fast',  # Encoding preset
            '-crf', '23',       # Quality setting
            output_path
        ]
        
        logger.info(f"Running ffmpeg command for photo: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("Photo processing completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error for photo: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_name = message.from_user.first_name or "Foydalanuvchi"
    welcome_text = MESSAGES['welcome'].format(user_name)
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['hide'])
def send_hide_info(message):
    """Handle /hide command"""
    bot.reply_to(message, MESSAGES['hide_info'])

@bot.message_handler(commands=['lang'])
def send_lang_selection(message):
    """Handle /lang command"""
    bot.reply_to(message, MESSAGES['lang_selection'])

@bot.message_handler(commands=['history'])
def send_history(message):
    """Handle /history command - show user's recent kruzhok videos"""
    try:
        user_id = message.from_user.id
        history = get_user_history(user_id, limit=10)
        total_count = get_total_user_kruzhoks(user_id)
        
        if not history:
            bot.reply_to(message, MESSAGES['history_empty'])
            return
        
        # Send header message
        header_text = f"{MESSAGES['history_header']}\n{MESSAGES['history_count'].format(count=total_count)}"
        bot.reply_to(message, header_text)
        
        # Send each kruzhok from history
        for item in history:
            try:
                # Create caption with effect info
                caption = f"🎨 {item.effect_name} | 📅 {item.created_at.strftime('%d.%m.%Y %H:%M')}"
                
                # Send the kruzhok video_note
                bot.send_video_note(
                    message.chat.id,
                    item.file_id,
                    caption=caption if len(caption) <= 1024 else ""  # Telegram caption limit
                )
            except Exception as e:
                logger.error(f"Error sending history item {item.id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error handling history command: {e}")
        bot.reply_to(message, MESSAGES['error'])

@bot.message_handler(content_types=['video'])
def handle_video(message):
    """Handle video messages"""
    try:
        user_id = message.from_user.id
        
        # Get file info
        file_info = bot.get_file(message.video.file_id)
        
        # Create temporary file
        input_file = create_temp_file(suffix='.mp4')
        
        # Download the video
        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_file, 'wb') as f:
            f.write(downloaded_file)
        
        # Store user media file and set state
        user_media_files[user_id] = {
            'file_path': input_file,
            'media_type': 'video',
            'duration': message.video.duration or 10
        }
        user_states[user_id] = 'choosing_effect'
        
        # Send effect selection menu with inline keyboard
        markup = create_effect_keyboard()
        bot.reply_to(message, MESSAGES['choose_effect'], reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        bot.reply_to(message, MESSAGES['error'])

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Handle photo messages"""
    try:
        user_id = message.from_user.id
        
        # Get the largest photo size
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        
        # Create temporary file
        input_file = create_temp_file(suffix='.jpg')
        
        # Download the photo
        downloaded_file = bot.download_file(file_info.file_path)
        with open(input_file, 'wb') as f:
            f.write(downloaded_file)
        
        # Store user media file and set state
        user_media_files[user_id] = {
            'file_path': input_file,
            'media_type': 'photo',
            'duration': 5
        }
        user_states[user_id] = 'choosing_effect'
        
        # Send effect selection menu with inline keyboard
        markup = create_effect_keyboard()
        bot.reply_to(message, MESSAGES['choose_effect'], reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        bot.reply_to(message, MESSAGES['error'])

@bot.message_handler(content_types=['document', 'audio', 'voice', 'sticker'])
def handle_unsupported(message):
    """Handle unsupported file types"""
    bot.reply_to(message, MESSAGES['unsupported'])

@bot.callback_query_handler(func=lambda call: call.data.startswith('effect_'))
def handle_effect_callback(call):
    """Handle inline button callbacks for effect selection"""
    try:
        user_id = call.from_user.id
        effect_type = int(call.data.split('_')[1])
        
        # Answer callback to remove loading state
        bot.answer_callback_query(call.id)
        
        # Process media with selected effect
        process_media_with_effect_callback(call, effect_type)
        
    except Exception as e:
        logger.error(f"Error handling effect callback: {e}")
        bot.answer_callback_query(call.id, text="❌ Xatolik yuz berdi")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Handle all text messages"""
    # Default welcome message
    user_name = message.from_user.first_name or "Foydalanuvchi"
    welcome_text = MESSAGES['welcome'].format(user_name)
    bot.reply_to(message, welcome_text)

def process_media_with_effect_callback(call, effect_type):
    """Process stored media with selected effect from callback"""
    user_id = call.from_user.id
    
    try:
        if user_id not in user_media_files:
            bot.edit_message_text("❌ Media fayl topilmadi", call.message.chat.id, call.message.message_id)
            return
        
        # Edit message to show processing
        bot.edit_message_text(MESSAGES['effect_processing'], call.message.chat.id, call.message.message_id)
        
        media_info = user_media_files[user_id]
        input_file = media_info['file_path']
        output_file = create_temp_file(suffix='.mp4')
        
        # Process based on media type
        success = False
        if media_info['media_type'] == 'video':
            success = process_video_to_kruzhok(input_file, output_file, effect_type)
        elif media_info['media_type'] == 'photo':
            success = process_photo_to_kruzhok(input_file, output_file, effect_type)
        
        if success:
            # Send the kruzhok
            with open(output_file, 'rb') as video:
                sent_message = bot.send_video_note(
                    call.message.chat.id,
                    video,
                    duration=media_info['duration'],
                    length=480  # Circular video diameter
                )
            
            # Save to history
            effect_name = EFFECT_NAMES.get(effect_type, f"Effekt {effect_type}")
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else None
            
            save_user_history(
                user_id=user_id,
                username=call.from_user.username,
                first_name=call.from_user.first_name,
                file_id=sent_message.video_note.file_id,
                original_media_type=media_info['media_type'],
                effect_type=effect_type,
                effect_name=effect_name,
                file_size=file_size
            )
            
            # Delete processing message
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(
                MESSAGES['error'],
                call.message.chat.id,
                call.message.message_id
            )
        
        # Clean up
        cleanup_file(input_file)
        cleanup_file(output_file)
        
        # Clear user state
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_media_files:
            del user_media_files[user_id]
            
    except Exception as e:
        logger.error(f"Error processing media with effect: {e}")
        bot.edit_message_text("❌ Xatolik yuz berdi", call.message.chat.id, call.message.message_id)
        
        # Clear user state on error
        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_media_files:
            cleanup_file(user_media_files[user_id]['file_path'])
            del user_media_files[user_id]

def main():
    """Main function to start the bot"""
    logger.info("Starting Kruzhok Bot...")
    
    # Initialize database
    try:
        create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg is not available. Please install ffmpeg.")
        return
    
    # Start polling
    try:
        logger.info("Bot is starting to poll...")
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    main()
