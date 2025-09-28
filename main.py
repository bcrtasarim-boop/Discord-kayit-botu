import os
import discord
from discord.ext import commands
import asyncio

# --- Sunucu ve Rol ID'lerini kendi sunucuna göre değiştir ---
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# ----------------------------------------------------------------------

# --- Discord bot ayarları ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Bot hazır olduğunda çalışacak ---
@bot.event
async def on_ready():
    print(f"Bot hazır: {bot.user} (id: {bot.user.id})")
    try:
        await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        print("Slash komutları başarıyla senkronize edildi.")
    except Exception as e:
        print(f"Komut senkronizasyonu hatası: {e}")

# --- Kayıt Slash komutu ---
@bot.tree.command(name="kayıt", description="Sunucuya kayıt olmak için kayıt sürecini başlatır.")
async def kayit(interaction: discord.Interaction):
    if interaction.channel_id != KAYIT_KANAL_ID:
        await interaction.response.send_message(
            f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Kayıt işlemi DM üzerinden devam edecek. Lütfen DM'lerini kontrol et.",
        ephemeral=True
    )

    user = interaction.user
    try:
        dm_channel = await user.create_dm()
        await dm_channel.send("Merhaba! Kayıt işlemine başlayalım. 5 dakika içinde tamamlanmazsa iptal olacaktır.")

        def check(m):
            return m.author == user and m.channel == dm_channel

        # 1) Nick
        await dm_channel.send("**1/3** - Lütfen oyundaki takma adını yaz.")
        msg_nick = await bot.wait_for('message', check=check, timeout=300.0)
        oyun_nicki = msg_nick.content.strip()

        # 2) İsim
        await dm_channel.send(f"**2/3** - Nick'in **{oyun_nicki}** olarak alındı. Şimdi gerçek ismini yaz.")
        msg_isim = await bot.wait_for('message', check=check, timeout=300.0)
        isim = msg_isim.content.strip()

        # 3) Yaş
        await dm_channel.send("**3/3** - Son olarak yaşını yaz.")
        msg_yas = await bot.wait_for('message', check=check, timeout=300.0)
        yas_str = msg_yas.content.strip()
        if not yas_str.isdigit() or int(yas_str) <= 0:
            await dm_channel.send("Geçerli bir yaş girmedin. Kayıt iptal edildi.")
            return
        yas = int(yas_str)

        await dm_channel.send("Tüm bilgiler alındı, sunucudaki ayarlarını yapıyorum...")

        guild = bot.get_guild(SUNUCU_ID)
        if not guild:
            await dm_channel.send("Sunucu bilgisine ulaşılamadı.")
            return
        member = guild.get_member(user.id)
        if not member:
            await dm_channel.send("Sunucuda seni bulamadım.")
            return

        yeni_takma_ad = f"{oyun_nicki} - {isim} - {yas}"
        if len(yeni_takma_ad) > 32:
            await dm_channel.send(f"Takma ad 32 karakterden uzun: `{yeni_takma_ad}`. Daha kısa bilgiler gir.")
            return

        misafir_rolu = guild.get_role(MISAFIR_ROL_ID)
        uye_rolu = guild.get_role(UYE_ROL_ID)
        if not misafir_rolu or not uye_rolu:
            await dm_channel.send("Rol bulunamadı. Yetkililere bildir.")
            return

        try:
            await member.add_roles(uye_rolu, reason="Kayıt tamamlandı.")
            await member.remove_roles(misafir_rolu, reason="Kayıt tamamlandı.")
            await member.edit(nick=yeni_takma_ad, reason="Kayıt tamamlandı.")
        except discord.Forbidden:
            await dm_channel.send("Bot yetkisi yok. Rolleri/Nick yönetilemiyor.")
            return
        except Exception as e:
            await dm_channel.send("Roller veya takma ad güncellenirken hata oluştu.")
            print(f"Üye güncelleme hatası: {e}")
            return

        log_kanali = bot.get_channel(LOG_KANAL_ID)
        if log_kanali:
            embed = discord.Embed(title="✅ Yeni Kayıt Başarılı", color=discord.Color.green())
            embed.set_author(name=str(user), icon_url=user.display_avatar.url)
            embed.add_field(name="Kayıt Olan Üye", value=user.mention, inline=False)
            embed.add_field(name="Ayarlanan Takma Ad", value=yeni_takma_ad, inline=False)
            embed.set_footer(text=f"Kullanıcı ID: {user.id}")
            await log_kanali.send(embed=embed)

        await dm_channel.send("Tebrikler! Kaydın tamamlandı ve yetkilerin güncellendi.")

    except asyncio.TimeoutError:
        await dm_channel.send("5 dakika içinde cevap vermediğin için kayıt iptal edildi.")
    except discord.Forbidden:
        print(f"DM gönderilemedi: {user.name} (ID: {user.id})")
    except Exception as e:
        print(f"Kayıt diyaloğu hatası: {e}")
        try:
            await user.send("Kayıt sırasında beklenmedik hata oluştu.")
        except discord.Forbidden:
            pass

# --- Bot token ---
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("HATA: DISCORD_TOKEN tanımlı değil.")
    exit(1)

bot.run(token)
