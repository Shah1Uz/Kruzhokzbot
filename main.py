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

# Uzbek language messages
MESSAGES = {
    'welcome': """👋 Salom, {}!
① Video yoki rasm yuboring.
② Effektni tanlang.
③ Doira tayyor ✔️

Tezkor buyruqlar:
♻️ Botni qayta ishga tushirish: /start
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

Til o'zgartirish funksiyasi ishlab chiqilmoqda..."""
}

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

def process_video_to_kruzhok(input_path, output_path):
    """Convert video to circular kruzhok format using ffmpeg"""
    try:
        # Get video info first
        duration = get_video_duration(input_path)
        
        # Limit duration to 60 seconds for kruzhok
        duration = min(duration, 60.0)
        
        # FFmpeg command to create circular video
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-i', input_path,
            '-t', str(duration),  # Limit duration
            '-vf', (
                'scale=480:480:force_original_aspect_ratio=increase,'  # Scale to 480x480
                'crop=480:480,'  # Crop to square
                'format=yuv420p'  # Set pixel format
            ),
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

def process_photo_to_kruzhok(input_path, output_path):
    """Convert photo to 5-second circular kruzhok"""
    try:
        # FFmpeg command to create 5-second circular video from image
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-loop', '1',    # Loop the input image
            '-i', input_path,
            '-t', '5',       # 5 seconds duration
            '-vf', (
                'scale=480:480:force_original_aspect_ratio=increase,'  # Scale to 480x480
                'crop=480:480,'  # Crop to square
                'format=yuv420p'  # Set pixel format
            ),
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

@bot.message_handler(content_types=['video'])
def handle_video(message):
    """Handle video messages"""
    try:
        # Send processing message
        processing_msg = bot.reply_to(message, MESSAGES['processing'])
        
        # Get file info
        file_info = bot.get_file(message.video.file_id)
        
        # Create temporary files
        input_file = create_temp_file(suffix='.mp4')
        output_file = create_temp_file(suffix='.mp4')
        
        try:
            # Download the video
            downloaded_file = bot.download_file(file_info.file_path)
            with open(input_file, 'wb') as f:
                f.write(downloaded_file)
            
            # Process video to kruzhok
            if process_video_to_kruzhok(input_file, output_file):
                # Send the kruzhok
                with open(output_file, 'rb') as video:
                    bot.send_video_note(
                        message.chat.id,
                        video,
                        duration=min(60, message.video.duration or 10),
                        length=480,  # Circular video diameter
                        reply_to_message_id=message.message_id
                    )
                
                # Delete processing message
                bot.delete_message(message.chat.id, processing_msg.message_id)
                
            else:
                bot.edit_message_text(
                    MESSAGES['error'],
                    message.chat.id,
                    processing_msg.message_id
                )
        
        finally:
            # Clean up temporary files
            cleanup_file(input_file)
            cleanup_file(output_file)
            
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        bot.reply_to(message, MESSAGES['error'])

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Handle photo messages"""
    try:
        # Send processing message
        processing_msg = bot.reply_to(message, MESSAGES['processing'])
        
        # Get the largest photo size
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        
        # Create temporary files
        input_file = create_temp_file(suffix='.jpg')
        output_file = create_temp_file(suffix='.mp4')
        
        try:
            # Download the photo
            downloaded_file = bot.download_file(file_info.file_path)
            with open(input_file, 'wb') as f:
                f.write(downloaded_file)
            
            # Process photo to kruzhok
            if process_photo_to_kruzhok(input_file, output_file):
                # Send the kruzhok
                with open(output_file, 'rb') as video:
                    bot.send_video_note(
                        message.chat.id,
                        video,
                        duration=5,  # 5 seconds for photos
                        length=480,  # Circular video diameter
                        reply_to_message_id=message.message_id
                    )
                
                # Delete processing message
                bot.delete_message(message.chat.id, processing_msg.message_id)
                
            else:
                bot.edit_message_text(
                    MESSAGES['error'],
                    message.chat.id,
                    processing_msg.message_id
                )
        
        finally:
            # Clean up temporary files
            cleanup_file(input_file)
            cleanup_file(output_file)
            
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        bot.reply_to(message, MESSAGES['error'])

@bot.message_handler(content_types=['document', 'audio', 'voice', 'sticker'])
def handle_unsupported(message):
    """Handle unsupported file types"""
    bot.reply_to(message, MESSAGES['unsupported'])

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Handle all text messages"""
    user_name = message.from_user.first_name or "Foydalanuvchi"
    welcome_text = MESSAGES['welcome'].format(user_name)
    bot.reply_to(message, welcome_text)

def main():
    """Main function to start the bot"""
    logger.info("Starting Kruzhok Bot...")
    
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
