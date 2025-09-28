import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive # Web sunucusunu başlatmak için

# --- AYARLAR BÖLÜMÜ ---
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# --------------------

# Botun temel ayarları ve niyetleri (Intents)
intents = discord.Intents.default()
intents.members = True # Üye bilgilerini alabilmek için
intents.message_content = True # Mesaj içeriklerini okuyabilmek için (DM'de gerekli)
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot çalıştığında ve Discord'a bağlandığında çalışacak olan bölüm
@bot.event
async def on_ready():
    print(f'Bot {bot.user} olarak Discord\'a bağlandı.')
    try:
        await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print(f'Komutlar {SUNUCU_ID} ID\'li sunucuya başarıyla senkronize edildi.')
    except Exception as e:
        print(f"Komut senkronizasyonunda hata oluştu: {e}")

# /kayıt komutunun kendisi - artık bir diyalog başlatıyor
@bot.tree.command(name="kayıt", description="Sunucuya kayıt olmak için kayıt sürecini başlatır.")
async def kayit(interaction: discord.Interaction):
    
    # Komutun doğru kanalda kullanıldığını kontrol et
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", ephemeral=True)
        return
    
    # Kullanıcıya DM'den devam edileceğini bildir
    await interaction.response.send_message("Kayıt işlemi özel mesaj (DM) üzerinden devam edecek. Lütfen DM'lerini kontrol et.", ephemeral=True)
    
    user = interaction.user
    
    # Kullanıcıya özelden mesaj göndererek diyaloğu başlat
    try:
        await user.send("Merhaba! Kayıt işlemine başlayalım. Süreç 5 dakika içinde tamamlanmazsa iptal olacaktır.")
        
        # --- Nick Sorma ---
        await user.send("**1/3** - Lütfen oyundaki takma adını (nick) yaz.")
        
        def check(m):
            # Cevabın doğru kullanıcıdan ve DM'den geldiğini kontrol et
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        msg_nick = await bot.wait_for('message', check=check, timeout=300.0)
        oyun_nicki = msg_nick.content

        # --- İsim Sorma ---
        await user.send(f"**2/3** - Harika, nick'in **{oyun_nicki}** olarak alındı. Şimdi de gerçek ismini yazar mısın?")
        msg_isim = await bot.wait_for('message', check=check, timeout=300.0)
        isim = msg_isim.content

        # --- Yaş Sorma ---
        await user.send(f"**3/3** - Çok güzel. Son olarak yaşını yazar mısın?")
        msg_yas = await bot.wait_for('message', check=check, timeout=300.0)
        yas_str = msg_yas.content

        # Yaşın sayı olduğundan emin ol
        if not yas_str.isdigit():
            await user.send("Geçerli bir yaş girmedin. Kayıt işlemi iptal edildi. Lütfen baştan başla.")
            return
        yas = int(yas_str)

        # --- Bilgileri İşleme ---
        await user.send("Tüm bilgileri aldım, sunucudaki ayarlarını yapıyorum...")

        # Sunucu üzerindeki üye nesnesini bul
        guild = bot.get_guild(SUNUCU_ID)
        member = guild.get_member(user.id)
        
        if not member:
            await user.send("Sunucuda seni bulamadım. Bir hata oluştu.")
            return

        # Yeni takma adı oluştur ve kontrol et
        yeni_takma_ad = f"{oyun_nicki} - {isim} - {yas}"
        if len(yeni_takma_ad) > 32:
            await user.send(f"Oluşturulan takma ad (`{yeni_takma_ad}`) 32 karakterden uzun olduğu için Discord tarafından kabul edilmiyor. Lütfen daha kısa bilgilerle tekrar dene.")
            return
            
        # Rolleri ve takma adı güncelle
        misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
        uye_rolu = guild.get_role(UYE_ROL_ID)
        
        await member.remove_roles(misafir_rolu)
        await member.add_roles(uye_rolu)
        await member.edit(nick=yeni_takma_ad)

        # Log kanalına embed mesajı gönder
        log_kanali = bot.get_channel(LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="✅ Yeni Diyalog Kaydı Başarılı", color=0x00ff00)
            embed.set_author(name=f"{user.name}", icon_url=user.avatar.url if user.avatar else None)
            embed.add_field(name="Kayıt Olan Kişi", value=user.mention, inline=False)
            embed.add_field(name="Ayarlanan Takma Ad", value=yeni_takma_ad, inline=False)
            embed.set_footer(text=f"Kullanıcı ID: {user.id}")
            await log_kanali.send(embed=embed)
            
        await user.send("Tebrikler! Kaydın başarıyla tamamlandı ve sunucudaki yetkilerin güncellendi.")

    except asyncio.TimeoutError:
        await user.send("5 dakika içinde cevap vermediğin için kayıt işlemi zaman aşımına uğradı ve iptal edildi.")
    except Exception as e:
        print(f"Kayıt diyaloğu sırasında bir hata oluştu: {e}")
        await user.send("Kayıt sırasında beklenmedik bir hata oluştu. Lütfen bir yetkili ile iletişime geç.")


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
