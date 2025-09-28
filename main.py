import os
import sys
import threading
from flask import Flask
import discord
from discord.ext import commands
import asyncio

# --- AYARLAR - Sunucu ve Rol ID'lerini kendi sunucuna göre değiştir ---
# Lütfen bu ID'lerin doğru ve sayısal olduğundan emin ol.
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# ----------------------------------------------------------------------

# Basit web server (Render için healthcheck)
# HATA DÜZELTMESİ: Flask(__name__) olmalı, Flask(name) değil. 'name' tanımsız bir değişkendir.
app = Flask(__name__)

@app.route("/")
def index():
    return "OK"

def run_webserver():
    # Render gibi platformlar portu dinamik olarak atar
    port = int(os.environ.get("PORT", 8080))
    # use_reloader=False önemli: Render'da çift başlatmayı önler
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# Web server'ı ayrı bir thread'te başlat
# daemon=True, ana program kapandığında bu thread'in de kapanmasını sağlar.
web_thread = threading.Thread(target=run_webserver, daemon=True)
web_thread.start()

# --- İYİLEŞTİRME: Gerekli intent'leri spesifik olarak belirtiyoruz ---
# .all() yerine sadece ihtiyacımız olanları açmak daha verimlidir.
# Üyeleri ve mesaj içeriklerini okumak için bu yetkiler GEREKLİDİR.
intents = discord.Intents.default()
intents.members = True  # Üye rollerini yönetmek için
intents.message_content = True # DM'den gelen mesajları okumak için

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Bot hazır olduğunda çalışacak fonksiyon."""
    print(f"Bot hazır: {bot.user} (id: {bot.user.id})")
    try:
        # Sadece belirtilen sunucu için komutları senkronize et
        await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print("Slash komutları başarıyla senkronize edildi.")
    except Exception as e:
        print(f"Komut senkronizasyonu sırasında bir hata oluştu: {e}")

@bot.tree.command(name="kayıt", description="Sunucuya kayıt olmak için kayıt sürecini başlatır.")
async def kayit(interaction: discord.Interaction):
    """Kullanıcıya DM üzerinden kayıt sorularını soran slash komutu."""
    # Komutun doğru kanalda kullanıldığını kontrol et
    if interaction.channel_id != KAYIT_KANAL_ID:
        await interaction.response.send_message(
            f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Kayıt işlemi özel mesaj (DM) üzerinden devam edecek. Lütfen DM'lerini kontrol et.",
        ephemeral=True
    )
    user = interaction.user

    try:
        dm_channel = await user.create_dm()
        await dm_channel.send("Merhaba! Kayıt işlemine başlayalım. Süreç 5 dakika içinde tamamlanmazsa iptal olacaktır.")

        def check(m):
            # Mesajın doğru kullanıcıdan ve DM kanalından geldiğini kontrol et
            return m.author == user and m.channel == dm_channel

        # 1) Nick
        await dm_channel.send("**1/3** - Lütfen oyundaki takma adını (nick) yaz.")
        msg_nick = await bot.wait_for('message', check=check, timeout=300.0)
        oyun_nicki = msg_nick.content.strip()

        # 2) İsim
        await dm_channel.send(f"**2/3** - Harika, nick'in **{oyun_nicki}** olarak alındı. Şimdi de gerçek ismini yazar mısın?")
        msg_isim = await bot.wait_for('message', check=check, timeout=300.0)
        isim = msg_isim.content.strip()

        # 3) Yaş
        await dm_channel.send("**3/3** - Çok güzel. Son olarak yaşını yazar mısın?")
        msg_yas = await bot.wait_for('message', check=check, timeout=300.0)
        yas_str = msg_yas.content.strip()

        if not yas_str.isdigit() or int(yas_str) <= 0:
            await dm_channel.send("Geçerli bir yaş girmedin. Kayıt işlemi iptal edildi. Lütfen baştan başla.")
            return
        yas = int(yas_str)

        await dm_channel.send("Tüm bilgileri aldım, sunucudaki ayarlarını yapıyorum...")
        guild = bot.get_guild(SUNUCU_ID)
        if guild is None:
            await dm_channel.send("Sunucu bilgisine ulaşılamadı. Lütfen yetkililere bildir.")
            return

        member = guild.get_member(user.id)
        if not member:
            await dm_channel.send("Sunucuda seni bulamadım. Lütfen sunucuya katıldığından emin ol.")
            return

        yeni_takma_ad = f"{oyun_nicki} - {isim} - {yas}"
        # İYİLEŞTİRME: Discord takma ad sınırı 32 karakterdir. Basit bir len() kontrolü yeterlidir.
        if len(yeni_takma_ad) > 32:
            await dm_channel.send(f"Oluşturulan takma ad (`{yeni_takma_ad}`) 32 karakterden uzun. Lütfen daha kısa bilgiler girerek tekrar dene.")
            return

        misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
        uye_rolu = guild.get_role(UYE_ROL_ID)

        if not misafir_rolu or not uye_rolu:
            await dm_channel.send("Misafir veya Üye rolü sunucuda bulunamadı. Lütfen yetkililere bildir.")
            return

        try:
            # Önce rol ekle, sonra kaldır. Başarısızlık riskini azaltır.
            await member.add_roles(uye_rolu, reason="Kayıt işlemi tamamlandı.")
            await member.remove_roles(misafir_rolu, reason="Kayıt işlemi tamamlandı.")
            await member.edit(nick=yeni_takma_ad, reason="Kayıt işlemi tamamlandı.")
        except discord.Forbidden:
            await dm_channel.send("Botun gerekli yetkileri yok (Rolleri Yönet / Takma Adları Yönet). Sunucu yetkililerine bildir.")
            return
        except Exception as e:
            await dm_channel.send("Roller veya takma ad güncellenirken bir hata oluştu. Yetkililere bildir.")
            print(f"Üye güncelleme hatası: {e}")
            return

        # Log kanalına bildirim gönder
        log_kanali = bot.get_channel(LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="✅ Yeni Kayıt Başarılı", color=discord.Color.green())
            embed.set_author(name=str(user), icon_url=user.display_avatar.url)
            embed.add_field(name="Kayıt Olan Üye", value=user.mention, inline=False)
            embed.add_field(name="Ayarlanan Takma Ad", value=yeni_takma_ad, inline=False)
            embed.set_footer(text=f"Kullanıcı ID: {user.id}")
            await log_kanali.send(embed=embed)

        await dm_channel.send("Tebrikler! Kaydın tamamlandı ve sunucudaki yetkilerin güncellendi.")

    except asyncio.TimeoutError:
        await dm_channel.send("5 dakika içinde cevap vermediğin için kayıt işlemi zaman aşımına uğradı ve iptal edildi.")
    except discord.Forbidden:
        # Kullanıcı DM'lerini kapattıysa veya botu engellediyse bu hata oluşur.
        print(f"DM gönderilemedi: {user.name} (ID: {user.id}) kullanıcısının DM'leri kapalı olabilir.")
    except Exception as e:
        print(f"Kayıt diyaloğunda beklenmedik bir hata oluştu: {e}")
        try:
            await user.send("Kayıt sırasında beklenmedik bir hata oluştu. Lütfen sunucu yetkilileri ile iletişime geç.")
        except discord.Forbidden:
            pass # Zaten DM gönderemiyorsak yapacak bir şey yok.

# --- Bot token'ını ortam değişkeninden al ve çalıştır ---
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("HATA: DISCORD_TOKEN ortam değişkeni (environment variable) tanımlı değil.")
    sys.exit(1)

try:
    bot.run(token)
except discord.errors.LoginFailure:
    print("HATA: Geçersiz bir token girildi. Lütfen DISCORD_TOKEN değerini kontrol et.")
    sys.exit(1)
except Exception as e:
    print(f"Bot çalıştırılırken bir hata oluştu: {e}")
    sys.exit(1)
