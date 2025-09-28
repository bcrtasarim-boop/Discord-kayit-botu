import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from keep_alive import keep_alive  # Web sunucusunu başlatmak için

# --- AYARLAR BÖLÜMÜ ---
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# --------------------

# Bot intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} olarak Discord\'a bağlandı.')
    try:
        await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print(f'Komutlar {SUNUCU_ID} ID\'li sunucuya başarıyla senkronize edildi.')
    except Exception as e:
        print(f"Komut senkronizasyonunda hata oluştu: {e}")

@bot.tree.command(name="kayıt", description="Sunucuya kayıt olmak için kayıt sürecini başlatır.")
async def kayit(interaction: discord.Interaction):
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", ephemeral=True)
        return

    await interaction.response.send_message("Kayıt işlemi özel mesaj (DM) üzerinden devam edecek. Lütfen DM'lerini kontrol et.", ephemeral=True)
    user = interaction.user

    try:
        await user.send("Merhaba! Kayıt işlemine başlayalım. Süreç 5 dakika içinde tamamlanmazsa iptal olacaktır.")

        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        # Nick
        await user.send("**1/3** - Lütfen oyundaki takma adını (nick) yaz.")
        msg_nick = await bot.wait_for('message', check=check, timeout=300.0)
        oyun_nicki = msg_nick.content

        # İsim
        await user.send(f"**2/3** - Harika, nick'in **{oyun_nicki}** olarak alındı. Şimdi de gerçek ismini yazar mısın?")
        msg_isim = await bot.wait_for('message', check=check, timeout=300.0)
        isim = msg_isim.content

        # Yaş
        await user.send("**3/3** - Çok güzel. Son olarak yaşını yazar mısın?")
        msg_yas = await bot.wait_for('message', check=check, timeout=300.0)
        yas_str = msg_yas.content

        if not yas_str.isdigit():
            await user.send("Geçerli bir yaş girmedin. Kayıt işlemi iptal edildi. Lütfen baştan başla.")
            return
        yas = int(yas_str)

        await user.send("Tüm bilgileri aldım, sunucudaki ayarlarını yapıyorum...")
        guild = bot.get_guild(SUNUCU_ID)
        member = guild.get_member(user.id)

        if not member:
            await user.send("Sunucuda seni bulamadım. Bir hata oluştu.")
            return

        yeni_takma_ad = f"{oyun_nicki} - {isim} - {yas}"
        if (len(yeni_takma_ad.encode("utf-16-le")) // 2) > 32:
            await user.send(f"Oluşturulan takma ad (`{yeni_takma_ad}`) 32 karakterden uzun. Daha kısa bilgilerle tekrar dene.")
            return

        misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
        uye_rolu = guild.get_role(UYE_ROL_ID)

        try:
            await member.remove_roles(misafir_rolu)
            await member.add_roles(uye_rolu)
            await member.edit(nick=yeni_takma_ad)
        except discord.Forbidden:
            await user.send("Botun roller veya isim değiştirme yetkisi yok. Yetkililere haber ver.")
            return

        log_kanali = bot.get_channel(LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="✅ Yeni Diyalog Kaydı Başarılı", color=0x00ff00)
            embed.set_author(name=f"{user.name}", icon_url=user.avatar.url if user.avatar else None)
            embed.add_field(name="Kayıt Olan Kişi", value=user.mention, inline=False)
            embed.add_field(name="Ayarlanan Takma Ad", value=yeni_takma_ad, inline=False)
            embed.set_footer(text=f"Kullanıcı ID: {user.id}")
            await log_kanali.send(embed=embed)

        await user.send("Tebrikler! Kaydın tamamlandı ve sunucudaki yetkilerin güncellendi.")

    except asyncio.TimeoutError:
        await user.send("5 dakika içinde cevap vermediğin için kayıt işlemi iptal edildi.")
    except discord.Forbidden:
        print("DM gönderilemedi, kullanıcı DM'lerini kapatmış olabilir.")
    except Exception as e:
        print(f"Kayıt diyaloğu sırasında hata: {e}")
        try:
            await user.send("Kayıt sırasında beklenmedik bir hata oluştu. Yetkiliyle iletişime geç.")
        except:
            pass

# Keep Alive
keep_alive()

# Botu çalıştır
bot.run("BURAYA_BOT_TOKENINI_YAZ")
```
