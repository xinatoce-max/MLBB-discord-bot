import os
import discord
from discord.ext import commands, tasks
import feedparser
import requests

# --- НАСТРОЙКИ БОТА ---
TOKEN = os.getenv('TOKEN')

# ID канала в Discord, куда будут отправляться уведомления
YT_CHANNEL_ID = 1562741211981283350        

# Настройки YouTube (канал TurtleLight)
YOUTUBE_CHANNEL_ID = 'UCEjpJz-JIzzaO0KMF8HgAew'

# Используем публичный прокси-агрегатор RSS, чтобы Render не блокировался YouTube
RSS_URL = f'https://nitter.cz/proxy/https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}'
# Или альтернативный вариант RSS-моста:
ALT_RSS_URL = f'https://rsshub.app/youtube/channel/{YOUTUBE_CHANNEL_ID}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
last_video_id = None

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен и готов к работе!')
    check_youtube_channel.start()

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ЗАПРОСА ЧЕРЕЗ ПРОКСИ ---
def get_youtube_feed():
    # Пробуем основной RSS-мост
    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200 and 'entries' in feedparser.parse(response.content):
            feed = feedparser.parse(response.content)
            if feed.entries:
                return feed
    except Exception as e:
        print(f"Ошибка основного RSS: {e}")

    # Если не получилось, пробуем запасной вариант
    try:
        response = requests.get(ALT_RSS_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            if feed.entries:
                return feed
    except Exception as e:
        print(f"Ошибка запасного RSS: {e}")

    return None

# --- МОДУЛЬ: Автоматическая проверка YouTube каждые 10 минут ---
@tasks.loop(minutes=10)
async def check_youtube_channel():
    global last_video_id
    channel = bot.get_channel(YT_CHANNEL_ID)
    if not channel:
        return

    try:
        feed = get_youtube_feed()
        if feed and feed.entries:
            latest_video = feed.entries[0]
            # У разных RSS-форматов поле ID может называться по-разному
            video_id = getattr(latest_video, 'yt_videoid', latest_video.link.split('v=')[-1])
            video_url = latest_video.link
            video_title = latest_video.title
            
            thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
            channel_avatar_url = f"https://unavatar.io/youtube/{YOUTUBE_CHANNEL_ID}"

            if last_video_id != video_id:
                # АНТИСПАМ: Удаляем предыдущее сообщение бота перед отправкой нового
                async for message in channel.history(limit=15):
                    if message.author == bot.user:
                        try:
                            await message.delete()
                        except Exception as e:
                            print(f"Не удалось удалить старое сообщение: {e}")

                embed = discord.Embed(
                    title=video_title,
                    url=video_url,
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
                print(f"Опубликовано новое видео: {video_title}")
                last_video_id = video_id

    except Exception as e:
        print(f"Ошибка при обработке ленты YouTube: {e}")

# --- КОМАНДА ДЛЯ РУЧНОЙ ПРОВЕРКИ ---
@bot.command(name='check_yt')
async def manual_check(ctx):
    global last_video_id
    await ctx.send("🔄 Проверяю YouTube-канал через защищенный прокси...")
    
    channel = bot.get_channel(YT_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ошибка: Не найден целевой канал с указанным ID!")
        return

    try:
        feed = get_youtube_feed()
        if feed and feed.entries:
            latest_video = feed.entries[0]
            video_id = getattr(latest_video, 'yt_videoid', latest_video.link.split('v=')[-1])
            video_url = latest_video.link
            video_title = latest_video.title
            
            thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
            channel_avatar_url = f"https://unavatar.io/youtube/{YOUTUBE_CHANNEL_ID}"

            embed = discord.Embed(
                title=video_title,
                url=video_url,
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
            await ctx.send("✅ Готово! Уведомление успешно доставлено.")
            last_video_id = video_id
        else:
            await ctx.send("⚠️ Не удалось получить данные через прокси. Попробуйте еще раз через минуту.")
    except Exception as e:
        await ctx.send(f"❌ Произошла ошибка: {e}")

bot.run(TOKEN)
