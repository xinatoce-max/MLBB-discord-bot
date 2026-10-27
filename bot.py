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
RSS_URL = f'https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}'

# Заголовки, чтобы YouTube не блокировал запросы с сервера Render
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

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ЗАПРОСА RSS ---
def get_youtube_feed():
    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return feedparser.parse(response.content)
    except Exception as e:
        print(f"Ошибка при скачивании RSS: {e}")
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
            video_id = latest_video.yt_videoid
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
    await ctx.send("🔄 Принудительно проверяю YouTube-канал через сервер...")
    
    channel = bot.get_channel(YT_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ошибка: Не найден целевой канал с указанным ID!")
        return

    try:
        feed = get_youtube_feed()
        if feed and feed.entries:
            latest_video = feed.entries[0]
            video_id = latest_video.yt_videoid
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
            await ctx.send("✅ Готово! Красивое уведомление успешно отправлено с сервера.")
            last_video_id = video_id
        else:
            await ctx.send("⚠️ Не удалось получить ленту YouTube (сервер временно заблокирован по IP). Попробуйте через минуту.")
    except Exception as e:
        await ctx.send(f"❌ Произошла ошибка: {e}")

bot.run(TOKEN)
