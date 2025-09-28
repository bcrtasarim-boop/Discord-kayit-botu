# Gerekli kütüphaneleri içeri aktar
import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive

# --- AYARLAR BÖLÜMÜ ---
# Bu ID'lerin %100 doğru olduğundan emin olmalıyız.
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# --------------------

# Botun temel ayarlarını ve niyetlerini (Intents) belirle
intents = discord.Intents.default()
intents.members = True # Üye bilgilerini alabilmek için bu gerekli
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot çalıştığında ve Discord'a bağlandığında çalışacak olan bölüm
@bot.event
async def on_ready():
    print(f'Bot {bot.user} olarak Discord\'a bağlandı.')
    # Komutları sadece belirtilen sunucuya kaydetmeyi dene
    try:
        await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print(f'Komutlar {SUNUCU_ID} ID\'li sunucuya başarıyla senkronize edildi.')
    except Exception as e:
        print(f"Komut senkronizasyonunda hata oluştu: {e}")

# /kayıt komutunun kendisi
@bot.tree.command(name="kayıt", description="Kayıt olmak için bilgilerinizi boşluk bırakarak yazın.")
@app_commands.describe(bilgiler="Örnek: OyuncuNicki İsim Yaş")
async def kayit(interaction: discord.Interaction, bilgiler: str):
    # Komutun doğru kanalda kullanıldığını kontrol et
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", ephemeral=True)
        return
    
    # Discord'a "işlem yapılıyor" mesajını hemen gönder (3 saniye kuralı için)
    await interaction.response.defer(ephemeral=True)
    
    # Kullanıcının girdiği metni boşluklara göre ayır
    parts = bilgiler.split()
    
    # En az 3 parça bilgi (Nick, İsim, Yaş) var mı diye kontrol et
    if len(parts) < 3:
        await interaction.followup.send("Eksik bilgi girdiniz! Lütfen `Nick İsim Yaş` formatında tekrar deneyin.")
        return
    
    # Bilgileri değişkenlere ata
    oyun_nicki = parts[0]
    isim = " ".join(parts[1:-1]) # İsimde boşluk olabilme ihtimaline karşı
    yas_str = parts[-1] # Yaş her zaman son parçadır

    # Yaş'ın bir sayı olduğundan emin ol
    if not yas_str.isdigit():
        await interaction.followup.send("Yaş olarak geçerli bir sayı girmediniz! Lütfen `Nick İsim Yaş` formatında tekrar deneyin.")
        return
    
    yas = int(yas_str)
    
    # Takma adın 32 karakter limitini aşmadığından emin ol
    if len(oyun_nicki) > 32:
        await interaction.followup.send("Oyun nicki çok uzun! Discord, 32 karakterden uzun takma adlara izin vermiyor.")
        return
    
    # Gerekli sunucu, kanal ve rol bilgilerini al
    guild = interaction.guild
    kullanici = interaction.user
    log_kanali = bot.get_channel(LOG_KANAL_ID)
    misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
    uye_rolu = guild.get_role(UYE_ROL_ID)

    # Ana işlemleri yapmayı dene
    try:
        await kullanici.remove_roles(misafir_rolu)
        await kullanici.add_roles(uye_rolu)
        await kullanici.edit(nick=oyun_nicki)

        # Log kanalına embed mesajı gönder
        embed = discord.Embed(title="✅ Yeni Kayıt Başarılı", color=discord.Color.green())
        embed.set_author(name=f"{kullanici.name}", icon_url=kullanici.avatar.url)
        embed.add_field(name="Kayıt Olan Kişi", value=kullanici.mention, inline=False)
        embed.add_field(name="Oyun Nicki", value=f"{oyun_nicki}", inline=True)
        embed.add_field(name="İsim", value=f"{isim}", inline=True)
        embed.add_field(name="Yaş", value=f"{yas}", inline=True)
        embed.set_footer(text=f"Kullanıcı ID: {kullanici.id}")
        await log_kanali.send(embed=embed)
        
        # Kullanıcıya işlemin başarılı olduğunu bildir
        await interaction.followup.send("Harika, kaydın başarıyla tamamlandı. Sunucumuza hoş geldin!")

    except Exception as e:
        # Bir hata olursa loga yaz ve kullanıcıya bildir
        print(f"Kayıt işlemi sırasında hata oluştu: {e}")
        await interaction.followup.send("Kayıt sırasında bir hata oluştu. Lütfen bir yetkili ile iletişime geç.")

# 7/24 aktif kalmak için web sunucusunu çalıştır
keep_alive()

# Botu çalıştıracak ana bölüm
try:
    token = os.environ['DISCORD_TOKEN']
    if token:
        bot.run(token)
    else:
        print("HATA: DISCORD_TOKEN bulunamadı.")
except Exception as e:
    print(f"Bot çalıştırılırken bir hata oluştu: {e}")
