import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive  # Web sunucusunu başlatmak için

# --- AYARLAR BÖLÜMÜ ---
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# --------------------

# Botun çalışması için gerekli Discord ayarları
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot çalıştığında terminalde bir mesaj gösterecek
@bot.event
async def on_ready():
    print(f'{bot.user} olarak Discord\'a başarıyla bağlandım.')
    print("Bot aktif ve komutları bekliyor...")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print(f"{len(synced)} adet komut senkronize edildi.")
    except Exception as e:
        print(f"Komut senkronizasyon hatası: {e}")

# Sunucuya yeni bir üye katıldığında çalışacak olay
@bot.event
async def on_member_join(member):
    if member.guild.id == SUNUCU_ID:
        kayit_kanali = bot.get_channel(KAYIT_KANAL_ID)
        misafir_rolu = member.guild.get_role(MISAFIR_ROL_ID)
        try:
            if misafir_rolu:
                await member.add_roles(misafir_rolu)
            if kayit_kanali:
                await kayit_kanali.send(
                    f"Sunucumuza hoş geldiniz {member.mention}! \nKayıt olmadan sunucunun kanallarını göremezsiniz.\nKayıt olmak için `/kayıt` yazarak ilgili adımları takip etmeniz yeterlidir.\nÖrnek: `/kayıt Slaine - Utku - 31`\nKayıt'ın ardından ilk olarak topluluğumuzun kurallarını okumayı ihmal etmeyin."
                )
        except Exception as e:
            print(f"on_member_join hatası: {e}")

# /kayıt slash komutu
@bot.tree.command(
    name="kayıt",
    description="Kayıt için /kayıt Nick-İsim-Yaş yazıp işlemi tamamlayın. Örnek: /kayıt Slaine-Utku-31",
    guild=discord.Object(id=SUNUCU_ID)
)
@app_commands.describe(
    nick_isim_yas="Kayıt bilgilerinizi Nick-İsim-Yaş şeklinde yazın."
)
async def kayit(interaction: discord.Interaction, nick_isim_yas: str):
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(
            f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        oyun_nicki, isim, yas = nick_isim_yas.split("-")
        yas = int(yas)
    except ValueError:
        await interaction.followup.send(
            "Bilgiler hatalı! Lütfen `/kayıt Nick-İsim-Yaş` şeklinde yazın."
        )
        return

    kullanici = interaction.user
    guild = interaction.guild
    log_kanali = bot.get_channel(LOG_KANAL_ID)
    misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
    uye_rolu = guild.get_role(UYE_ROL_ID)

    try:
        await kullanici.remove_roles(misafir_rolu)
        await kullanici.add_roles(uye_rolu)
        await kullanici.edit(nick=nick_isim_yas)

        if log_kanali:
            avatar_url = kullanici.avatar.url if kullanici.avatar else None
            embed = discord.Embed(title="✅ Yeni Kayıt Başarılı", color=discord.Color.green())
            embed.set_author(name=f"{kullanici.name}", icon_url=avatar_url)
            embed.add_field(name="Kayıt Olan Kişi", value=kullanici.mention, inline=False)
            embed.add_field(name="Oyun Nicki", value=oyun_nicki, inline=True)
            embed.add_field(name="İsim", value=isim, inline=True)
            embed.add_field(name="Yaş", value=yas, inline=True)
            embed.set_footer(text=f"Kullanıcı ID: {kullanici.id}")
            try:
                await log_kanali.send(embed=embed)
            except Exception as e:
                print(f"Log gönderilemedi: {e}")

        await interaction.followup.send(f"Harika, kaydın başarıyla tamamlandı. Sunucumuza hoş geldin!")

    except Exception as e:
        print(f"Kayıt işlemi sırasında hata: {e}")

# --- YENİ EKLENEN MESAJ SİLME KOMUTU ---

@bot.tree.command(
    name="sil",
    description="Kanaldaki belirtilen sayıda mesajı siler (En fazla 100).",
    guild=discord.Object(id=SUNUCU_ID)
)
@app_commands.describe(
    miktar="Silinecek mesaj sayısı (1-100 arası)."
)
@app_commands.checks.has_permissions(manage_messages=True)
async def sil(interaction: discord.Interaction, miktar: app_commands.Range[int, 1, 100]):
    """
    Belirtilen sayıda mesajı siler.
    """
    await interaction.response.defer(ephemeral=True, thinking=True)
    
    try:
        silinen_mesajlar = await interaction.channel.purge(limit=miktar)
        await interaction.followup.send(f"✅ Bu kanaldan başarıyla **{len(silinen_mesajlar)}** adet mesaj silindi.")
        
    except discord.Forbidden:
        await interaction.followup.send("❌ Botun bu kanalda 'Mesajları Yönet' izni bulunmuyor.")
    except Exception as e:
        await interaction.followup.send(f"Bir hata oluştu: {e}")

@sil.error
async def sil_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "Bu komutu kullanmak için 'Mesajları Yönet' yetkisine sahip olmalısın.", 
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Beklenmedik bir hata oluştu: {error}", 
            ephemeral=True
        )

# Web sunucusunu çalıştır
keep_alive()

# Token'ı güvenli şekilde al
try:
    token = os.environ['DISCORD_TOKEN']
    bot.run(token)
except KeyError:
    print("HATA: DISCORD_TOKEN bulunamadı. Lütfen ortam değişkenlerini kontrol edin.")
