import discord
import os
from flask import Flask
from threading import Thread

# --- Flask Web Sunucusu Kısmı ---
# Bu kısım, Render'ın uygulamayı bir "Web Servisi" olarak görmesi için gerekli.
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discord Bot Kısmı ---
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} olarak Discord\'a bağlandık.')
    print('-----------------------------------------')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('!selam'):
        await message.channel.send('Selam sana da!')
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')

# Botu ve web sunucusunu aynı anda başlatıyoruz.
keep_alive()
client.run(TOKEN)
