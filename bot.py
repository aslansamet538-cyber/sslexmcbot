import os
import re
import random
import asyncio
import logging
from threading import Thread
from datetime import timedelta

import discord
from discord.ext import commands
from flask import Flask

# ==============================
# CRAFTDORA AYARLARI
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")
MEMBER_LOG_CHANNEL_ID = 1560361912838004777
ROLE_LOG_CHANNEL_ID = 1370346741181976596
PREFIX = "!"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("craftdora")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

giveaways = {}

# ==============================
# RENDER WEB SUNUCUSU
# ==============================

app = Flask(__name__)

@app.route("/")
def home():
    return "CraftDora Bot aktif! play.craftdora.com", 200

def run_web():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

Thread(target=run_web, daemon=True).start()

# ==============================
# YARDIMCI FONKSİYONLAR
# ==============================

def is_admin(member):
    return (
        isinstance(member, discord.Member)
        and member.guild_permissions.administrator
    )


def parse_duration(value):
    match = re.fullmatch(
        r"(\d+)\s*([smhd])",
        value or "",
        re.IGNORECASE
    )

    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2).lower()

    seconds = amount * {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }[unit]

    if 10 <= seconds <= 30 * 86400:
        return seconds

    return None


def safe_channel_part(value, max_length=20):
    table = str.maketrans({
        "ı": "i", "ğ": "g", "ü": "u",
        "ş": "s", "ö": "o", "ç": "c",
        "İ": "i", "Ğ": "g", "Ü": "u",
        "Ş": "s", "Ö": "o", "Ç": "c"
    })

    value = value.lower().translate(table)
    value = re.sub(r"[^a-z0-9-]", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")

    return value[:max_length] or "destek"


async def send_log(channel_id, embed):
    channel = bot.get_channel(channel_id)

    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            log.exception("Log kanalı alınamadı: %s", channel_id)
            return

    try:
        await channel.send(embed=embed)
    except (AttributeError, discord.Forbidden, discord.HTTPException):
        log.exception("Log gönderilemedi: %s", channel_id)


# ==============================
# BOT HAZIR
# ==============================

@bot.event
async def setup_hook():
    bot.add_view(TicketView())
    bot.add_view(GiveawayView())


@bot.event
async def on_ready():
    log.info("CraftDora aktif: %s", bot.user)

    await bot.change_presence(
        activity=discord.Game(name="play.craftdora.com")
    )


# ==============================
# ÜYE GİRİŞ / ÇIKIŞ LOGU
# ==============================

@bot.event
async def on_member_join(member):
    embed = discord.Embed(
        title="📥 CraftDora | Yeni Üye Katıldı",
        description=(
            f"👤 **Üye:** {member}\n"
            f"🆔 **Kullanıcı ID:** {member.id}\n"
            f"👥 **Üye sayısı:** {member.guild.member_count}\n\n"
            "CraftDora ailesine hoş geldin!"
        ),
        color=discord.Color.green()
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    await send_log(MEMBER_LOG_CHANNEL_ID, embed)

    welcome = discord.Embed(
        title="🌿 CraftDora Dünyasına Hoş Geldin!",
        description=(
            f"Merhaba {member.mention}!\n\n"
            "🌲 **Sunucu:** play.craftdora.com\n"
            "📜 Kuralları okumayı unutma.\n"
            "🎫 Sorun yaşarsan destek talebi açabilirsin.\n\n"
            "Sana iyi oyunlar! ⛏️"
        ),
        color=discord.Color.green()
    )

    try:
        await member.send(embed=welcome)
    except (discord.Forbidden, discord.HTTPException):
        pass


@bot.event
async def on_member_remove(member):
    embed = discord.Embed(
        title="📤 CraftDora | Üye Ayrıldı",
        description=(
            f"👤 **Üye:** {member}\n"
            f"🆔 **Kullanıcı ID:** {member.id}\n"
            f"👥 **Üye sayısı:** {member.guild.member_count}"
        ),
        color=discord.Color.red()
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    await send_log(MEMBER_LOG_CHANNEL_ID, embed)


# ==============================
# ROL LOGU
# ==============================

@bot.event
async def on_member_update(before, after):
    old_roles = {role.id for role in before.roles}
    new_roles = {role.id for role in after.roles}

    if old_roles == new_roles:
        return

    added = [
        role for role in after.roles
        if role.id not in old_roles and role.id != after.guild.id
    ]

    removed = [
        role for role in before.roles
        if role.id not in new_roles and role.id != after.guild.id
    ]

    for role in added:
        embed = discord.Embed(
            title="✨ CraftDora | Rol Eklendi",
            description=f"{after.mention} kullanıcısına rol verildi.",
            color=discord.Color.green()
        )
        embed.add_field(name="Eklenen rol", value=role.name)
        embed.add_field(name="Kullanıcı ID", value=str(after.id))

        await send_log(ROLE_LOG_CHANNEL_ID, embed)

    for role in removed:
        embed = discord.Embed(
            title="➖ CraftDora | Rol Kaldırıldı",
            description=f"{after.mention} kullanıcısından rol kaldırıldı.",
            color=discord.Color.red()
        )
        embed.add_field(name="Kaldırılan rol", value=role.name)
        embed.add_field(name="Kullanıcı ID", value=str(after.id))

        await send_log(ROLE_LOG_CHANNEL_ID, embed)


# ==============================
# ÇEKİLİŞ SİSTEMİ
# ==============================

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Çekilişe Katıl 🎉",
        style=discord.ButtonStyle.success,
        custom_id="craftdora_giveaway_join"
    )
    async def join(self, interaction, button):
        giveaway = giveaways.get(interaction.message.id)

        if giveaway is None:
            await interaction.response.send_message(
                "Bu çekiliş aktif değil veya bot yeniden başlatıldı.",
                ephemeral=True
            )
            return

        if interaction.user.bot:
            await interaction.response.send_message(
                "Botlar çekilişe katılamaz.",
                ephemeral=True
            )
            return

        if interaction.user.id in giveaway["participants"]:
            await interaction.response.send_message(
                "Bu çekilişe zaten katıldın!",
                ephemeral=True
            )
            return

        giveaway["participants"].add(interaction.user.id)

        await interaction.response.send_message(
            "✅ Çekilişe katıldın! Bol şans!",
            ephemeral=True
        )


async def finish_giveaway(message_id):
    giveaway = giveaways.pop(message_id, None)

    if giveaway is None:
        return

    channel = bot.get_channel(giveaway["channel_id"])

    if channel is None:
        try:
            channel = await bot.fetch_channel(giveaway["channel_id"])
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

    participants = list(giveaway["participants"])

    embed = discord.Embed(
        title="🏆 CraftDora | Çekiliş Bitti",
        description=f"🎁 **Ödül:** {giveaway['prize']}",
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )

    if participants:
        winner = random.choice(participants)
        embed.add_field(name="🎉 Kazanan", value=f"<@{winner}>")

        await channel.send(
            content=f"🎉 Tebrikler <@{winner}>! Ödülün: **{giveaway['prize']}**",
            embed=embed
        )
    else:
        embed.add_field(
            name="Sonuç",
            value="Katılımcı olmadığı için kazanan seçilemedi."
        )
        await channel.send(embed=embed)

    try:
        original = await channel.fetch_message(message_id)
        ended_view = discord.ui.View()
        ended_view.add_item(discord.ui.Button(
            label="Çekiliş Sona Erdi",
            style=discord.ButtonStyle.secondary,
            disabled=True
        ))
        await original.edit(view=ended_view)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


# ==============================
# TICKET SİSTEMİ
# ==============================

class TicketModal(discord.ui.Modal, title="CraftDora Destek Talebi"):
    player_name = discord.ui.TextInput(
        label="Minecraft oyuncu adın",
        placeholder="Örnek: CraftDoraOyuncu",
        min_length=1,
        max_length=32,
        required=True
    )

    ticket_issue = discord.ui.TextInput(
        label="Destek konun veya sorunun",
        placeholder="Sorununu açıkla",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=300,
        required=True
    )

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        guild = interaction.guild

        if guild is None:
            await interaction.followup.send(
                "Bu işlem yalnızca sunucuda kullanılabilir.",
                ephemeral=True
            )
            return

        topic = f"craftdora-ticket-owner:{interaction.user.id}"

        existing = next(
            (c for c in guild.text_channels if c.topic == topic),
            None
        )

        if existing:
            await interaction.followup.send(
                f"Zaten açık bir ticket'ın var: {existing.mention}",
                ephemeral=True
            )
            return

        bot_member = guild.me

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),
            bot_member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )
        }

        player = safe_channel_part(str(self.player_name.value), 15)
        issue = safe_channel_part(str(self.ticket_issue.value), 22)

        try:
            channel = await guild.create_text_channel(
                name=f"ticket-{player}-{issue}"[:95],
                topic=topic,
                overwrites=overwrites,
                reason=f"CraftDora ticket: {interaction.user}"
            )

            embed = discord.Embed(
                title="🎫 CraftDora | Destek Talebi",
                description=(
                    f"Merhaba {interaction.user.mention}!\n\n"
                    f"👤 **Minecraft adı:** {self.player_name.value}\n"
                    f"📌 **Sorun:** {self.ticket_issue.value}\n\n"
                    "Yetkililer seninle ilgilenecektir.\n"
                    "Kapatmak için `!kapat` yaz."
                ),
                color=discord.Color.orange()
            )

            await channel.send(
                content=interaction.user.mention,
                embed=embed
            )

            await interaction.followup.send(
                f"✅ Ticket oluşturuldu: {channel.mention}",
                ephemeral=True
            )

        except (discord.Forbidden, discord.HTTPException):
            log.exception("Ticket oluşturulamadı.")

            await interaction.followup.send(
                "Ticket oluşturulamadı. Botun kanal oluşturma iznini kontrol et.",
                ephemeral=True
            )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Destek Talebi Aç 🎫",
        style=discord.ButtonStyle.success,
        custom_id="craftdora_ticket_open"
    )
    async def open_ticket(self, interaction, button):
        await interaction.response.send_modal(TicketModal())


# ==============================
# MESAJLAR VE KOMUTLAR
# ==============================

@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    msg = message.content.lower().strip()

    # Sohbet cevapları
    if msg in {"sa", "s.a", "selam", "selamun aleyküm",
               "selamün aleyküm", "selamun aleykum"}:
        await message.reply(
            "👋 Aleyküm Selam! **CraftDora** dünyasına hoş geldin! 🌿"
        )

    elif "naber" in msg or "nasılsın" in msg or msg == "nbr":
        await message.reply(
            "😊 İyiyim, teşekkür ederim! CraftDora'da keyifler nasıl?"
        )

    elif "iyi geceler" in msg or msg == "ig":
        await message.reply("🌙 Sana da iyi geceler! CraftDora'da görüşürüz!")

    elif "günaydın" in msg or "gunaydin" in msg:
        await message.reply("☀️ Günaydın! CraftDora'da güzel bir gün geçir!")

    elif "iyi akşamlar" in msg or "iyi aksamlar" in msg:
        await message.reply("🌆 Sana da iyi akşamlar!")

    elif msg in {"eyw", "eyvallah"} or "teşekkürler" in msg:
        await message.reply("💚 Rica ederiz! İyi eğlenceler!")

    # Sunucu IP
    if msg in {"!ip", "ip", "sunucu ip"}:
        embed = discord.Embed(
            title="⚔️ CraftDora | Sunucu Bilgileri",
            description=(
                "🌲 **Sunucu adresi:** `play.craftdora.com`\n\n"
                "🛡️ Java: `1.20.1 - 26.3`\n"
                "📱 Mobil: `1.20.1 - 26.3`"
            ),
            color=discord.Color.green()
        )

        await message.reply(embed=embed)

    # Yardım
    elif msg in {"!yardım", "!yardim", "!help"}:
        embed = discord.Embed(
            title="🌲 CraftDora | Komut Listesi",
            description=(
                "`!ip` — Sunucu bilgileri\n"
                "`!yardım` — Komut listesi\n"
                "`!çekiliş 10m 1 Aylık VIP` — Çekiliş oluştur\n"
                "`!destek-kur` — Ticket paneli\n"
                "`!kapat` — Ticket kapat\n"
                "`!kurallar-kur` — Kuralları gönder\n"
                "`!başvuru-kur` — Yetkili başvuru paneli"
            ),
            color=discord.Color.green()
        )

        await message.reply(embed=embed)

    # Kurallar
    elif msg == "!kurallar-kur":
        if not is_admin(message.author):
            await message.reply("❌ Yönetici yetkisi gerekiyor.")
            return

        rules = [
            "Saygılı davranın.",
            "Hakaret, tehdit ve taciz yasaktır.",
            "Hile ve makro kullanımı yasaktır.",
            "Oyun açıklarını kötüye kullanmayın.",
            "Dolandırıcılık yasaktır.",
            "İzinsiz reklam yasaktır.",
            "Spam yapmak yasaktır.",
            "Kişisel bilgileri paylaşmayın.",
            "Yetkili taklidi yapmayın.",
            "Kanalları amacına uygun kullanın.",
            "Sistemleri istismar etmeyin.",
            "Tehdit ve şantaj yasaktır.",
            "Ticket sistemini gereksiz kullanmayın.",
            "Özel yazışmaları izinsiz paylaşmayın.",
            "Yetkili kararlarına saygılı şekilde itiraz edin."
        ]

        description = "\n\n".join(
            f"**{i}.** {rule}" for i, rule in enumerate(rules, 1)
        )

        embed = discord.Embed(
            title="📜 CraftDora | Sunucu Kuralları",
            description=description,
            color=discord.Color.orange()
        )

        await message.channel.send(embed=embed)

    # Ticket paneli
    elif msg == "!destek-kur":
        if not is_admin(message.author):
            await message.reply("❌ Yönetici yetkisi gerekiyor.")
            return

        embed = discord.Embed(
            title="🎫 CraftDora | Destek Merkezi",
            description=(
                "Destek talebi oluşturmak için aşağıdaki butona bas.\n\n"
                "1. Minecraft oyuncu adını gir.\n"
                "2. Sorununu açıkla.\n"
                "3. Sana özel bir kanal oluşturulsun."
            ),
            color=discord.Color.orange()
        )

        await message.channel.send(embed=embed, view=TicketView())

    # Başvuru paneli
    elif msg == "!başvuru-kur":
        if not is_admin(message.author):
            await message.reply("❌ Yönetici yetkisi gerekiyor.")
            return

        embed = discord.Embed(
            title="📝 CraftDora | Yetkili Başvurusu",
            description=(
                "CraftDora ekibine katılmak mı istiyorsun?\n\n"
                "Başvurun için yönetim ekibiyle iletişime geç. "
                "Deneyimini ve neden ekibe katılmak istediğini belirt."
            ),
            color=discord.Color.blue()
        )

        await message.channel.send(embed=embed)

    # Çekiliş oluşturma
    elif msg.startswith("!çekiliş ") or msg.startswith("!cekilis "):
        if not is_admin(message.author):
            await message.reply("❌ Yönetici yetkisi gerekiyor.")
            return

        parts = message.content.split(maxsplit=2)

        if len(parts) < 3:
            await message.reply(
                "Kullanım: `!çekiliş 10m 1 Aylık VIP`"
            )
            return

        duration_text = parts[1]
        prize = parts[2]
        duration = parse_duration(duration_text)

        if duration is None:
            await message.reply(
                "Süre `30s`, `10m`, `2h` veya `1d` şeklinde olmalı. "
                "En az 10 saniye, en fazla 30 gün."
            )
            return

        embed = discord.Embed(
            title="🎁 CRAFTDORA ÇEKİLİŞİ BAŞLADI!",
            description=(
                f"🎁 **Ödül:** {prize}\n"
                f"⏳ **Süre:** {duration_text}\n"
                f"👑 **Düzenleyen:** {message.author.mention}\n\n"
                "Katılmak için aşağıdaki butona bas!"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow() + timedelta(seconds=duration)
        )

        giveaway_message = await message.channel.send(
            embed=embed,
            view=GiveawayView()
        )

        giveaways[giveaway_message.id] = {
            "channel_id": message.channel.id,
            "prize": prize,
            "participants": set()
        }

        async def timer(message_id, seconds):
            await asyncio.sleep(seconds)
            await finish_giveaway(message_id)

        asyncio.create_task(timer(giveaway_message.id, duration))

    # Ticket kapatma
    elif msg in {"!kapat", "!ticket-kapat"}:
        channel = message.channel

        if not isinstance(channel, discord.TextChannel):
            return

        topic = channel.topic or ""

        if not topic.startswith("craftdora-ticket-owner:"):
            await message.reply(
                "Bu komut yalnızca ticket kanalında kullanılabilir."
            )
            return

        try:
            owner_id = int(topic.split(":", 1)[1])
        except (ValueError, IndexError):
            await message.reply("Ticket bilgisi okunamadı.")
            return

        if message.author.id != owner_id and not is_admin(message.author):
            await message.reply(
                "❌ Ticket'ı yalnızca sahibi veya yönetici kapatabilir."
            )
            return

        await message.reply("🔒 Ticket 5 saniye içinde kapatılıyor.")
        await asyncio.sleep(5)

        try:
            await channel.delete(reason="CraftDora ticket kapatıldı.")
        except (discord.Forbidden, discord.HTTPException):
            log.exception("Ticket kapatılamadı.")


# ==============================
# TOKEN KONTROLÜ VE BAŞLATMA
# ==============================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN bulunamadı! Render > Environment bölümüne ekle."
    )

bot.run(TOKEN)
