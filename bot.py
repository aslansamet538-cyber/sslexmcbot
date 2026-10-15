import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# ==========================================
# 1. RENDER 7/24 AKTİF TUTMA ALTYAPISI
# ==========================================
app = Flask('')
@app.route('/')
def home(): return "🤖 TAHLİYE Bot 7/24 Aktif!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
def keep_alive(): Thread(target=run).start()

# ==========================================
# 2. BOT YAPILANDIRMASI & KANAL SABİTLEME
# ==========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Kanal ID Sabitleri
HEDEF_KANAL_ID = 1371568718542540842
LOG_KANAL_ID = 1370346741181976596

@bot.event
async def on_ready():
    print(f"🤖 {bot.user.name} BAŞARIYLA ÇALIŞTI!")
    await bot.change_presence(activity=discord.Game(name="TAHLİYE | 7/24 Aktif"))

# ==========================================
# 3. YARDIM KOMUTU SİSTEMİ
# ==========================================
@bot.command(name="yardım")
async def yardim_komutu(ctx):
    embed = discord.Embed(
        title="🎫 Destek Bilgilendirmesi",
        description="⚠️ Lütfen Sorununuz İçin **Ticket Oluşturun**.\n\n🔔 Oluşturduğunuz Ticketin İlgilenilmesi İçin Yetkilileri Sabırlı Şekilde Bekleyin.",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Talep Eden: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# ==========================================
# 4. KUSURSUZ ROL LOG & DM SİSTEMİ (ERENSİBOT)
# ==========================================
@bot.event
async def on_member_update(before, after):
    # Sadece rol değişikliklerinde tetiklenmesini sağla (Hata önleyici filtre)
    if before.roles == after.roles:
        return

    log_channel = bot.get_channel(LOG_KANAL_ID)
    
    # Değişen rolleri listeleme algoritması
    added_roles = [role for role in after.roles if role not in before.roles]
    removed_roles = [role for role in before.roles if role not in after.roles]

    # --- [DURUM 1: ROL EKLENDİ] ---
    for role in added_roles:
        # Tek bir temiz ErensiBot tarzı log mesajı
        if log_channel:
            embed_log = discord.Embed(
                title="✨ Rol İşlemleri",
                description=f"🔮 {after.mention} isimli üyeye yeni bir rol eklendi.",
                color=discord.Color.green()
            )
            embed_log.add_field(name=" Yeni Rol", value=f"```+ {role.name}```", inline=False)
            embed_log.add_field(name="🆔 Kullanıcı ID", value=f"`{after.id}`", inline=True)
            embed_log.set_thumbnail(url=after.display_avatar.url)
            embed_log.set_footer(text="TAHLİYE Yönetim Altyapısı")
            await log_channel.send(embed=embed_log)

        # Üyeye Özel Şık Gömülü DM Mesajı
        try:
            embed_dm = discord.Embed(
                title=f"🎉 {after.guild.name} • Yeni Bir Rol Aldın!",
                description=f"Selam {after.mention},\n\nSunucumuzda harika bir gelişme oldu! Sana yepyeni bir rol tanımlandı. Topluluğumuzdaki yerin her geçen gün daha da güçleniyor. ✨",
                color=discord.Color.green()
            )
            embed_dm.add_field(name="👑 Tanımlanan Rol", value=f"↳ **{role.name}**", inline=False)
            embed_dm.set_thumbnail(url=after.guild.icon.url if after.guild.icon else after.display_avatar.url)
            embed_dm.set_footer(text="Keyifli vakit geçirmeni dileriz! - TAHLİYE")
            await after.send(embed=embed_dm)
        except Exception:
            pass  # Kullanıcının DM kutusu kapalıysa kodun çökmesini önler

    # --- [DURUM 2: ROL KALDIRILDI] ---
    for role in removed_roles:
        # Tek bir temiz ErensiBot tarzı log mesajı
        if log_channel:
            embed_log = discord.Embed(
                title="✨ Rol İşlemleri",
                description=f"🔮 {after.mention} isimli üyeden bir rol kaldırıldı.",
                color=discord.Color.red()
            )
            embed_log.add_field(name="❌ Rol Kaldırıldı", value=f"```- {role.name}```", inline=False)
            embed_log.add_field(name="🆔 Kullanıcı ID", value=f"`{after.id}`", inline=True)
            embed_log.set_thumbnail(url=after.display_avatar.url)
            embed_log.set_footer(text="TAHLİYE Yönetim Altyapısı")
            await log_channel.send(embed=embed_log)

        # Üyeye Özel Şık Gömülü DM Mesajı
        try:
            embed_dm_kaldirildi = discord.Embed(
                title=f"⚠️ {after.guild.name} • Bir Rolün Güncellendi",
                description=f"Selam {after.mention},\n\nSunucumuzdaki rollerin güncellendi ve bir rolün üzerinden geri alındı.",
                color=discord.Color.red()
            )
            embed_dm_kaldirildi.add_field(name="📉 Alınan Rol", value=f"↳ ~~{role.name}~~", inline=False)
            embed_dm_kaldirildi.set_thumbnail(url=after.guild.icon.url if after.guild.icon else after.display_avatar.url)
            embed_dm_kaldirildi.set_footer(text="Soruların için yetkililerle iletişime geçebilirsin. - TAHLİYE")
            await after.send(embed=embed_dm_kaldirildi)
        except Exception:
            pass

# ==========================================
# 5. GİRİŞ / DM HOŞ GELDİN SİSTEMİ
# ==========================================
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(HEDEF_KANAL_ID)
    if channel:
        embed_kanal = discord.Embed(
            title="📥 Ailemiz Genişliyor!",
            description=f"Sunucumuza hoş geldin {member.mention}! Seninle birlikte tam **{member.guild.member_count}** kişi olduk. 🎉",
            color=discord.Color.green()
        )
        embed_kanal.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed_kanal)

    try:
        embed_dm = discord.Embed(
            title=f"👑 {member.guild.name} Dünyasına Hoş Geldin!",
            description=f"Selam {member.mention},\n\nSunucumuza katılarak topluluğumuza büyük bir değer kattın! **TAHLİYE Bot** olarak, sunucu içerisindeki konforunu, güvenliğini ve eğlenceni sağlamak adına 7/24 arka planda görevimin başındayım. 😉\n\nSohbet kanallarımızda yerini almayı, topluluk kurallarımızı incelemeyi ve ekibimizle tanışmayı unutma.",
            color=discord.Color.gold()
        )
        embed_dm.add_field(name="📊 Güncel Durumumuz", value=f"Şu an sunucumuzda seninle birlikte **{member.guild.member_count}** seçkin üye bulunuyor.", inline=False)
        embed_dm.set_thumbnail(url=member.guild.icon.url if member.guild.icon else member.display_avatar.url)
        embed_dm.set_footer(text="Unutulmaz anlar geçirmeni dileriz! - TAHLİYE Üst Düzey Yönetim Sistemi")
        await member.send(embed=embed_dm)
    except Exception:
        pass

# ==========================================
# 6. ÇIKIŞ / DM GÜLE GÜLE SİSTEMİ
# ==========================================
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(HEDEF_KANAL_ID)
    if channel:
        embed_kanal = discord.Embed(
            title="📤 Aramızdan Biri Ayrıldı",
            description=f"**{member.name}** sunucudan ayrıldı. Geriye **{member.guild.member_count}** kişi kaldık... 😔",
            color=discord.Color.red()
        )
        embed_kanal.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed_kanal)

    try:
        embed_dm_cikis = discord.Embed(
            title=f"💔 Ayrılık Vakti... Yolun Açık Olsun.",
            description=f"Hoşça kal **{member.name}**,\n\n`{member.guild.name}` sunucumuzdan ayrıldığını fark ettim. Fikir değiştirirsen kapımız her zaman açık!",
            color=discord.Color.dark_red()
        )
        embed_dm_cikis.set_footer(text="Geri dönmek istersen yetkililerden güncel davet linkini isteyebilirsin! - TAHLİYE")
        await member.send(embed=embed_dm_cikis)
    except Exception:
        pass

# ==========================================
# 7. OTOMATİK SELAMLAMA SİSTEMİ
# ==========================================
@bot.event
async def on_message(message):
    if message.author.bot: return
    mesaj = message.content.lower().strip()
    if mesaj in ["sa", "selam", "selamün aleyküm", "selamun aleykum", "s.a"]:
        await message.channel.send(f"Aleyküm Selam, Sunucumuza Hoşgeldin {message.author.mention}! 🌸")
    await bot.process_commands(message)

# ==========================================
# 8. BOTU BAŞLATMA
# ==========================================
keep_alive()
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
