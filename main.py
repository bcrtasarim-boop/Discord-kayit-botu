import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive # Web sunucusunu başlatmak için

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

@bot.tree.command(name="kayıt", description="Kayıt olmak için bilgilerinizi boşluk bırakarak yazın (Örn: Nick İsim Yaş).")
@app_commands.describe(
    bilgiler="Örnek: Raeburn Uğur 18"
)
async def kayit(interaction: discord.Interaction, bilgiler: str):
    if interaction.channel.id != KAYIT_KANAL_ID:
        await interaction.response.send_message(f"Bu komutu sadece <#{KAYIT_KANAL_ID}> kanalında kullanabilirsin.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    parts = bilgiler.split()

    if len(parts) < 3:
        await interaction.followup.send("Eksik bilgi girdiniz! Lütfen `Nick İsim Yaş` formatında tekrar deneyin. Örnek: `/kayıt Raeburn Uğur 18`")
        return
    
    oyun_nicki = parts[0]
    isim = parts[1]
    yas_str = parts[2]

    if not yas_str.isdigit():
        await interaction.followup.send("Yaş olarak geçerli bir sayı girmediniz! Lütfen `Nick İsim Yaş` formatında tekrar deneyin. Örnek: `/kayıt Raeburn Uğur 18`")
        return
    
    if len(oyun_nicki) > 32:
        await interaction.followup.send("Oyun nicki çok uzun! Discord, 32 karakterden uzun takma adlara izin vermiyor.")
        return
        
    yas = int(yas_str)
    
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
            embed.add_field(name="Oyun Nicki", value=f"{oyun_nicki}", inline=True)
            embed.add_field(name="İsim", value=f"{isim}", inline=True)
            embed.add_field(name="Yaş", value=f"{yas}", inline=True)
            embed.set_footer(text=f"Kullanıcı ID: {kullanici.id}")
            await log_kanali.send(embed=embed)
        
        await interaction.followup.send(f"Harika, kaydın başarıyla tamamlandı. Sunucumuza hoş geldin!")

    except Exception as e:
        print(f"Kayıt komutu sırasında bir hata oluştu: {e}")
        await interaction.followup.send("Kayıt sırasında bir hata oluştu. Lütfen bir yetkili ile iletişime geç.")

keep_alive()

try:
    token = os.environ['DISCORD_TOKEN']
    bot.run(token)
except KeyError:
    print("HATA: DISCORD_TOKEN bulunamadı. Lütfen hosting platformunuzun Secrets/Environment Variables bölümüne eklediğinizden emin olun.")
