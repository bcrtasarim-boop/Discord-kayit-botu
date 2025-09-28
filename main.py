import os
import sys
import threading
from flask import Flask
import discord
from discord.ext import commands
import asyncio

--- AYARLAR - Sunucu ve Rol ID'lerini kendi sunucuna göre değiştir ---

SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190

----------------------------------------------------------------------
Basit web server (Render için healthcheck)

app = Flask(name)

@app.route("/")
def index():
return "OK"

def run_webserver():
port = int(os.environ.get("PORT", 8080))
# use_reloader=False önemli: Render'da çift başlatmayı önler
app.run(host="0.0.0.0", port=port, use_reloader=False)

Web server'ı ayrı bir thread'te başlat

threading.Thread(target=run_webserver, daemon=True).start()

Discord intents - tüm gerekli intentleri açıyoruz

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
print(f"Bot hazır: {bot.user} (id: {bot.user.id})")
try:
await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
print("Slash komutları senkronize edildi.")
except Exception as e:
print("Komut senkronizasyonu hatası:", e)

/kayıt komutu - DM diyaloğu başlatır

@bot.tree.command(name="kayıt", description="Sunucuya kayıt olmak için kayıt sürecini başlatır.")
async def kayit(interaction: discord.Interaction):
# Komutun doğru kanalda kullanımı kontrolü
try:
if interaction.channel.id != KAYIT_KANAL_ID:
await interaction.response.send_message(f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", ephemeral=True)
return
except Exception:
# Eğer interaction.channel yoksa (nadiren) sessizce dön
return
await interaction.response.send_message("Kayıt işlemi özel mesaj (DM) üzerinden devam edecek. Lütfen DM'lerini kontrol et.", ephemeral=True)
user = interaction.user

try:
    await user.send("Merhaba! Kayıt işlemine başlayalım. Süreç 5 dakika içinde tamamlanmazsa iptal olacaktır.")

    def check(m):
        return m.author == user and isinstance(m.channel, discord.DMChannel)

    # 1) Nick
    await user.send("**1/3** - Lütfen oyundaki takma adını (nick) yaz.")
    msg_nick = await bot.wait_for('message', check=check, timeout=300.0)
    oyun_nicki = msg_nick.content.strip()

    # 2) İsim
    await user.send(f"**2/3** - Harika, nick'in **{oyun_nicki}** olarak alındı. Şimdi de gerçek ismini yazar mısın?")
    msg_isim = await bot.wait_for('message', check=check, timeout=300.0)
    isim = msg_isim.content.strip()

    # 3) Yaş
    await user.send("**3/3** - Çok güzel. Son olarak yaşını yazar mısın?")
    msg_yas = await bot.wait_for('message', check=check, timeout=300.0)
    yas_str = msg_yas.content.strip()

    if not yas_str.isdigit():
        await user.send("Geçerli bir yaş girmedin. Kayıt işlemi iptal edildi. Lütfen baştan başla.")
        return
    yas = int(yas_str)

    await user.send("Tüm bilgileri aldım, sunucudaki ayarlarını yapıyorum...")
    guild = bot.get_guild(SUNUCU_ID)
    if guild is None:
        await user.send("Sunucu bilgisine ulaşılamadı (bot sunucuda olmayabilir). Lütfen yetkililere bildir.")
        return

    member = guild.get_member(user.id)
    if not member:
        await user.send("Sunucuda seni bulamadım. Lütfen sunucuya katıldığından emin ol.")
        return

    yeni_takma_ad = f"{oyun_nicki} - {isim} - {yas}"
    # Discord'un 32 char sınırını UTF-16 bazlı kontrol ile yap
    if (len(yeni_takma_ad.encode("utf-16-le")) // 2) > 32:
        await user.send("Oluşturulan takma ad 32 karakterden uzun. Lütfen daha kısa bilgiler gir.")
        return

    misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
    uye_rolu = guild.get_role(UYE_ROL_ID)

    try:
        if misafir_rolu:
            await member.remove_roles(misafir_rolu)
        if uye_rolu:
            await member.add_roles(uye_rolu)
        await member.edit(nick=yeni_takma_ad)
    except discord.Forbidden:
        await user.send("Botun gerekli yetkileri yok (Manage Roles / Manage Nicknames). Sunucu yetkililerine bildir.")
        return
    except Exception as e:
        await user.send("Roller güncellenirken bir hata oluştu. Yetkililere bildir.")
        print("Üye güncelleme hatası:", e)
        return

    # Log kanalı
    log_kanali = bot.get_channel(LOG_KANAL_ID)
    if log_kanali:
        embed = discord.Embed(title="✅ Yeni Diyalog Kaydı Başarılı", color=0x00ff00)
        embed.set_author(name=f"{user}", icon_url=user.display_avatar.url if user.display_avatar else None)
        embed.add_field(name="Kayıt Olan Kişi", value=user.mention, inline=False)
        embed.add_field(name="Ayarlanan Takma Ad", value=yeni_takma_ad, inline=False)
        embed.set_footer(text=f"Kullanıcı ID: {user.id}")
        await log_kanali.send(embed=embed)

    await user.send("Tebrikler! Kaydın tamamlandı ve sunucudaki yetkilerin güncellendi.")

except asyncio.TimeoutError:
    await user.send("5 dakika içinde cevap vermediğin için kayıt işlemi iptal edildi.")
except discord.Forbidden:
    # Kullanıcı DM kapatmış olabilir
    print("DM gönderilemedi: kullanıcı DM kapalı olabilir.")
except Exception as e:
    print("Kayıt diyaloğunda hata:", e)
    try:
        await user.send("Kayıt sırasında beklenmedik bir hata oluştu. Lütfen sunucu yetkilileri ile iletişime geç.")
    except:
        pass
--- Bot token'i env'den al ve çalıştır ---

token = os.getenv("DISCORD_TOKEN")
if not token:
print("HATA: DISCORD_TOKEN environment variable (env) tanımlı değil. Render/Service ayarlarında ekle.")
sys.exit(1)

try:
bot.run(token)
except Exception as e:
print("Bot çalıştırılırken hata:", e)
sys.exit(1)
