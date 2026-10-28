import os
import discord
from discord.ext import commands
import requests
import asyncio

# --- НАСТРОЙКИ БОТА ---
TOKEN = os.getenv('TOKEN')

# ID канала в Discord, куда отправлять уведомления
YT_CHANNEL_ID = 1562741211981283350        

# Настройки YouTube (канал TurtleLight)
YOUTUBE_CHANNEL_ID = 'UCEjpJz-JIzzaO0KMF8HgAew'

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
last_video_id = None

# --- ФУНКЦИЯ ПОЛУЧЕНИЯ ПОСЛЕДНЕГО ВИДЕО С YOUTUBE ---
def get_latest_video():
    try:
        url = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}/videos"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            import re
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            title_match = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"\}\]', html)
            
            if match:
                video_id = match.group(1)
                video_title = title_match.group(1) if title_match else "Новое видео на канале!"
                video_title = video_title.encode().decode('unicode-escape', errors='ignore')
                
                return {
                    "id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": video_title
                }
    except Exception as e:
        print(f"Ошибка при получении данных с YouTube: {e}")
    return None

# --- ФОНОВЫЙ ЦИКЛ ПРОВЕРКИ (каждые 1-2 часа) ---
async def youtube_background_checker():
    global last_video_id
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            channel = bot.get_channel(YT_CHANNEL_ID)
            if channel:
                video_data = get_latest_video()
                if video_data:
                    video_id = video_data["id"]
                    
                    if last_video_id != video_id and last_video_id is not None:
                        # АНТИСПАМ: Удаляем предыдущее сообщение бота перед отправкой нового
                        async for message in channel.history(limit=15):
                            if message.author == bot.user:
                                try:
                                    await message.delete()
                                except Exception as e:
                                    print(f"Не удалось удалить старое сообщение: {e}")

                        thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
                        channel_avatar_url = f"https://unavatar.io/youtube/{YOUTUBE_CHANNEL_ID}"

                        embed = discord.Embed(
                            title=video_data["title"],
                            url=video_data["url"],
                            color=discord.Color.red()
                        )
                        
                        embed.set_author(
                            name="TurtleLight выпустил новое видео! 🎬", 
                            icon_url=channel_avatar_url
                        )
                        
                        embed.set_image(url=thumbnail_url)
                        
                        embed.add_field(
                            name="📈 📉 Баффы и нерфы героев",
                            value="Подробная информация расположена на: [mlbbhub.com/patch-notes](https://mlbbhub.com/patch-notes)",
                            inline=False
                        )
                        
                        embed.set_footer(text="YouTube Notification", icon_url=bot.user.avatar.url if bot.user.avatar else None)

                        await channel.send(embed=embed)
                        print(f"Опубликовано новое видео: {video_data['title']}")
                    
                    # Запоминаем текущее видео при первом запуске, чтобы не спамить старыми видео
                    if last_video_id is None:
                        last_video_id = video_id
                        print(f"Инициализация: текущее видео ID {video_id} сохранено без отправки.")

        except Exception as e:
            print(f"Ошибка в фоновом цикле: {e}")

        # Ждем 2 часа перед следующей проверкой (7200 секунд). Можете изменить на 3600 (1 час)
        await asyncio.sleep(7200)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен в режиме фонового воркера!')
    bot.loop.create_task(youtube_background_checker())

# --- КОМАНДА ДЛЯ РУЧНОЙ ПРОВЕРКИ ---
@bot.command(name='check_yt')
async def manual_check(ctx):
    global last_video_id
    await ctx.send("🔄 Принудительно проверяю YouTube-канал...")
    
    channel = bot.get_channel(YT_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ошибка: Не найден целевой канал!")
        return

    video_data = get_latest_video()
    if video_data:
        video_id = video_data["id"]
        thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        channel_avatar_url = f"https://unavatar.io/youtube/{YOUTUBE_CHANNEL_ID}"

        embed = discord.Embed(
            title=video_data["title"],
            url=video_data["url"],
            color=discord.Color.red()
        )
        
        embed.set_author(
            name="TurtleLight выпустил новое видео! 🎬", 
            icon_url=channel_avatar_url
        )
        
        embed.set_image(url=thumbnail_url)
        
        embed.add_field(
            name="📈 📉 Баффы и нерфы героев",
            value="Подробная информация расположена на: [mlbbhub.com/patch-notes](https://mlbbhub.com/patch-notes)",
            inline=False
        )
        
        embed.set_footer(text="YouTube Notification", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await channel.send(embed=embed)
        await ctx.send("✅ Готово! Последнее видео получено.")
        last_video_id = video_id
    else:
        await ctx.send("⚠️ Не удалось подключиться к странице канала. Попробуйте через минуту.")

bot.run(TOKEN)
