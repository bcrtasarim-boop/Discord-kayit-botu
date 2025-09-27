import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive # Web sunucusunu başlatmak için ekledik

# --- AYARLAR BÖLÜMÜ ---
SUNUCU_ID = 1421457543162757122  # Kendi sunucu ID'nizi girin
MISAFIR_ROL_ID = 1421467222357966909 # "Misafir" rolünün ID'si
UYE_ROL_ID = 1421467746855682219     # "Üye" rolünün ID'si
KAYIT_KANAL_ID = 1421469878937845780  # #kayıt kanalının ID'si
LOG_KANAL_ID = 1421548807451054190    # #kayıt-log kanalının ID'si
# --------------------

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} olarak Discord\'a bağlandım.')
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print(f"{len(synced)} adet komut senkronize edildi: {synced[0].name}")
    except Exception as e:
        print(f"Komut senkronizasyon hatası: {e}")

@bot.tree.command(name="kayıt", description="Sunucuya kayıt olmak için bilgilerinizi girin.", guild=discord.Object(id=SUNUCU_ID))
@app_commands.describe(
    oyun_nicki="Oyun içindeki isminiz (Bu isim sunucu takma adınız olacak)",
    isim="Gerçek isminiz (sadece yetkililer görebilir)",
    yas="Yaşınız (sadece yetkililer görebilir)"
)
async def kayit(interaction: discord.Interaction, oyun_nicki: str, isim: str, yas: int):
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", ephemeral=True)
        return

    kullanici = interaction.user
    guild = interaction.guild
    log_kanali = bot.get_channel(LOG_KANAL_ID)
    misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
    uye_rolu = guild.get_role(UYE_ROL_ID)

    try:
        await kullanici.remove_roles(misafir_rolu)
        await kullanici.add_roles(uye_rolu)
        await kullanici.edit(nick=oyun_nicki)

        if log_kanali:
            embed = discord.Embed(title="✅ Yeni Kayıt Başarılı", color=discord.Color.green())
            embed.set_author(name=f"{kullanici.name}", icon_url=kullanici.avatar.url if kullanici.avatar else discord.Embed.Empty)
            embed.add_field(name="Kayıt Olan Kişi", value=kullanici.mention, inline=False)
            embed.add_field(name="Oyun Nicki", value=oyun_nicki, inline=True)
            embed.add_field(name="İsim", value=isim, inline=True)
            embed.add_field(name="Yaş", value=yas, inline=True)
            embed.set_footer(text=f"Kullanıcı ID: {kullanici.id}")
            await log_kanali.send(embed=embed)
        
        await interaction.response.send_message(f"Harika, kaydın başarıyla tamamlandı!", ephemeral=True)
    except Exception as e:
        print(f"Kayıt komutu hatası: {e}")
        await interaction.response.send_message("Kayıt sırasında bir hata oluştu. Lütfen bir yetkili ile iletişime geç.", ephemeral=True)

# Web sunucusunu (keep_alive) çalıştır
keep_alive()

# Token'ı ortam değişkenlerinden güvenli bir şekilde al
try:
    token = os.environ['DISCORD_TOKEN']
    bot.run(token)
except KeyError:

    print("HATA: DISCORD_TOKEN bulunamadı. Lütfen Render'da Environment Variables'a eklediğinizden emin olun.")
