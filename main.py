import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive # Web sunucusunu başlatmak için
import re  # regex için

# --- AYARLAR BÖLÜMÜ ---
SUNUCU_ID = 1421457543162757122
MISAFIR_ROL_ID = 1421467222357966909
UYE_ROL_ID = 1421467746855682219
KAYIT_KANAL_ID = 1421469878937845780
LOG_KANAL_ID = 1421548807451054190
# --------------------

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} olarak Discord\'a başarıyla bağlandım.')
    print("Kayıt botu aktif ve komutları bekliyor...")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=SUNUCU_ID))
        if synced:
            print(f"{len(synced)} adet komut senkronize edildi: {synced[0].name}")
        else:
            print("Sunucuya özel komut bulunamadı veya senkronize edilemedi.")
    except Exception as e:
        print(f"Komut senkronizasyon hatası: {e}")

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
                    f"Hoş geldin {member.mention}! Lütfen sunucumuza tam erişim için `/kayıt` komutunu kullanarak kayıt ol."
                )
        except Exception as e:
            print(f"on_member_join hatası: {e}")

# Slash komutu: farklı ayırıcıları destekle
@bot.tree.command(
    name="kayıt",
    description="Sunucumuza kayıt olmak için /kayıt yazdıktan sonra OyuniçiNick-İsim-Yaş şeklinde yazıp, işlemi tamamlayın.",
    guild=discord.Object(id=SUNUCU_ID)
)
@app_commands.describe(
    bilgiler="Kayıt bilgilerinizi OyuniçiNick-İsim-Yaş şeklinde yazın."
)
async def kayit(interaction: discord.Interaction, bilgiler: str):
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(
            f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", 
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    # Regex ile ayırıcıları: -, boşluk, _, . kabul et
    parts = [part.strip() for part in re.split(r"[- _\.]", bilgiler) if part.strip()]

    if len(parts) < 3:
        await interaction.followup.send(
            "Bilgiler hatalı! Lütfen `/kayıt Nick-İsim-Yaş` şeklinde yazın."
        )
        return

    oyun_nicki, isim, yas_str = parts[:3]

    try:
        yas = int(yas_str)
    except ValueError:
        await interaction.followup.send("Yaş kısmı sayısal olmalı! Lütfen tekrar deneyin.")
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
            embed.set_author(
                name=f"{kullanici.name}",
                icon_url=kullanici.avatar.url if kullanici.avatar else discord.Embed.Empty
            )
            embed.add_field(name="Kayıt Olan Kişi", value=kullanici.mention, inline=False)
            embed.add_field(name="Oyun Nicki", value=oyun_nicki, inline=True)
            embed.add_field(name="İsim", value=isim, inline=True)
            embed.add_field(name="Yaş", value=yas, inline=True)
            embed.set_footer(text=f"Kullanıcı ID: {kullanici.id}")
            await log_kanali.send(embed=embed)

        await interaction.followup.send(f"Harika, kaydın başarıyla tamamlandı. Sunucumuza hoş geldin!")

    except Exception as e:
        print(f"Kayıt komutu sırasında bir hata oluştu: {e}")
        await interaction.followup.send("Kayıt sırasında bir hata oluştu. Lütfen bir yetkili ile iletişime geç.")

# Web sunucusunu çalıştır
keep_alive()

# Token
try:
    token = os.environ['DISCORD_TOKEN']
    bot.run(token)
except KeyError:
    print("HATA: DISCORD_TOKEN bulunamadı. Lütfen hosting platformunuzun Secrets/Environment Variables bölümüne eklediğinizden emin olun.")
