const {
  Client,
  GatewayIntentBits,
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ActivityType,
  ChannelType,
  PermissionsBitField,
  ModalBuilder,
  TextInputBuilder,
  TextInputStyle
} = require("discord.js");

const http = require("http");

// ==================================================
// CRAFTDORA AYARLARI
// ==================================================

const TOKEN = process.env.DISCORD_TOKEN;

const MEMBER_LOG_CHANNEL_ID = "1560361912838004777";
const ROLE_LOG_CHANNEL_ID = "1370346741181976596";

const PREFIX = "!";

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers
  ]
});

// Çekilişler bot çalışırken bellekte tutulur.
const giveaways = new Map();

// ==================================================
// RENDER WEB SUNUCUSU
// ==================================================

const webServer = http.createServer((req, res) => {
  res.writeHead(200, {
    "Content-Type": "text/plain; charset=utf-8"
  });
  res.end("CraftDora Bot aktif! play.craftdora.com");
});

webServer.listen(process.env.PORT || 10000, "0.0.0.0", () => {
  console.log("CraftDora web sunucusu başlatıldı.");
});

// ==================================================
// YARDIMCI FONKSİYONLAR
// ==================================================

function isAdmin(member) {
  return Boolean(
    member?.permissions.has(
      PermissionsBitField.Flags.Administrator
    )
  );
}

function parseDuration(input) {
  const match = /^(\d+)\s*([smhd])$/i.exec(input || "");
  if (!match) return null;

  const amount = Number(match[1]);

  const units = {
    s: 1000,
    m: 60000,
    h: 3600000,
    d: 86400000
  };

  const duration = amount * units[match[2].toLowerCase()];

  if (duration < 10000 || duration > 30 * 86400000) {
    return null;
  }

  return duration;
}

function safeChannelPart(text, maxLength = 20) {
  return text
    .toLocaleLowerCase("tr-TR")
    .replace(/ı/g, "i")
    .replace(/ğ/g, "g")
    .replace(/ü/g, "u")
    .replace(/ş/g, "s")
    .replace(/ö/g, "o")
    .replace(/ç/g, "c")
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, maxLength) || "destek";
}

// ==================================================
// BOT HAZIR
// ==================================================

client.once("ready", () => {
  console.log(`CraftDora aktif: ${client.user.tag}`);

  client.user.setActivity("play.craftdora.com", {
    type: ActivityType.Playing
  });
});

// ==================================================
// ÜYE GİRİŞ LOGU
// ==================================================

client.on("guildMemberAdd", async member => {
  const channel = member.guild.channels.cache.get(
    MEMBER_LOG_CHANNEL_ID
  );

  const embed = new EmbedBuilder()
    .setColor("#2ecc71")
    .setTitle("📥 CraftDora | Yeni Üye Katıldı")
    .setDescription(
      `🌿 Sunucumuza yeni bir oyuncu katıldı!\n\n` +
      `👤 **Üye:** ${member.user.tag}\n` +
      `🆔 **Kullanıcı ID:** ${member.id}\n` +
      `👥 **Güncel üye sayısı:** ${member.guild.memberCount}\n\n` +
      `CraftDora ailesine hoş geldin!`
    )
    .setThumbnail(member.user.displayAvatarURL())
    .setFooter({ text: "CraftDora • Üye Kayıt Sistemi" })
    .setTimestamp();

  if (channel?.isTextBased()) {
    try {
      await channel.send({ embeds: [embed] });
    } catch (error) {
      console.error("Giriş logu hatası:", error.message);
    }
  }

  // Özel hoş geldin mesajı
  const welcomeEmbed = new EmbedBuilder()
    .setColor("#2ecc71")
    .setTitle("🌿 CraftDora Dünyasına Hoş Geldin!")
    .setDescription(
      `Merhaba ${member.user.username}!\n\n` +
      `🌲 **Sunucu adresi:** play.craftdora.com\n` +
      `📜 Kuralları okumayı unutma.\n` +
      `🎫 Sorun yaşarsan destek talebi oluşturabilirsin.\n\n` +
      `Sana iyi oyunlar dileriz! ⛏️`
    )
    .setThumbnail(
      member.guild.iconURL({ size: 256 }) ||
      client.user.displayAvatarURL()
    );

  try {
    await member.send({ embeds: [welcomeEmbed] });
  } catch {
    // Üyenin DM kutusu kapalı olabilir.
  }
});

// ==================================================
// ÜYE ÇIKIŞ LOGU
// ==================================================

client.on("guildMemberRemove", async member => {
  const channel = member.guild.channels.cache.get(
    MEMBER_LOG_CHANNEL_ID
  );

  const embed = new EmbedBuilder()
    .setColor("#e74c3c")
    .setTitle("📤 CraftDora | Üye Ayrıldı")
    .setDescription(
      `🍂 Bir oyuncu sunucumuzdan ayrıldı.\n\n` +
      `👤 **Üye:** ${member.user.tag}\n` +
      `🆔 **Kullanıcı ID:** ${member.id}\n` +
      `👥 **Kalan üye sayısı:** ${member.guild.memberCount}\n\n` +
      `CraftDora'da geçirdiği zaman için teşekkür ederiz.`
    )
    .setThumbnail(member.user.displayAvatarURL())
    .setFooter({ text: "CraftDora • Üye Kayıt Sistemi" })
    .setTimestamp();

  if (channel?.isTextBased()) {
    try {
      await channel.send({ embeds: [embed] });
    } catch (error) {
      console.error("Çıkış logu hatası:", error.message);
    }
  }
});

// ==================================================
// ROL EKLEME / KALDIRMA LOGU
// ==================================================

client.on("guildMemberUpdate", async (before, after) => {
  if (before.roles.cache.equals(after.roles.cache)) return;

  const channel = after.guild.channels.cache.get(
    ROLE_LOG_CHANNEL_ID
  );

  if (!channel?.isTextBased()) return;

  const added = after.roles.cache.filter(
    role =>
      !before.roles.cache.has(role.id) &&
      role.id !== after.guild.id
  );

  const removed = before.roles.cache.filter(
    role =>
      !after.roles.cache.has(role.id) &&
      role.id !== after.guild.id
  );

  for (const role of added.values()) {
    const embed = new EmbedBuilder()
      .setColor("#2ecc71")
      .setTitle("✨ CraftDora | Rol Eklendi")
      .setDescription(`${after} kullanıcısına yeni bir rol verildi.`)
      .addFields(
        { name: "Eklenen rol", value: `\`${role.name}\`` },
        { name: "Kullanıcı ID", value: `\`${after.id}\`` }
      )
      .setThumbnail(after.displayAvatarURL())
      .setTimestamp();

    try {
      await channel.send({ embeds: [embed] });
    } catch (error) {
      console.error("Rol logu hatası:", error.message);
    }

    try {
      await after.send(
        `🎉 CraftDora'da sana **${role.name}** rolü verildi!`
      );
    } catch {}
  }

  for (const role of removed.values()) {
    const embed = new EmbedBuilder()
      .setColor("#e74c3c")
      .setTitle("➖ CraftDora | Rol Kaldırıldı")
      .setDescription(`${after} kullanıcısından bir rol kaldırıldı.`)
      .addFields(
        { name: "Kaldırılan rol", value: `\`${role.name}\`` },
        { name: "Kullanıcı ID", value: `\`${after.id}\`` }
      )
      .setThumbnail(after.displayAvatarURL())
      .setTimestamp();

    try {
      await channel.send({ embeds: [embed] });
    } catch (error) {
      console.error("Rol logu hatası:", error.message);
    }

    try {
      await after.send(
        `⚠️ CraftDora'da **${role.name}** rolün kaldırıldı.`
      );
    } catch {}
  }
});

// ==================================================
// ÇEKİLİŞİ BİTİR
// ==================================================

async function finishGiveaway(messageId) {
  const giveaway = giveaways.get(messageId);
  if (!giveaway) return;

  giveaways.delete(messageId);

  try {
    const channel = await client.channels.fetch(giveaway.channelId);
    if (!channel?.isTextBased()) return;

    const participants = [...giveaway.participants];

    const disabledRow = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId(`giveaway_ended_${messageId}`)
        .setLabel("Çekiliş Sona Erdi")
        .setStyle(ButtonStyle.Secondary)
        .setDisabled(true)
    );

    const embed = new EmbedBuilder()
      .setColor("#5865f2")
      .setTitle("🏆 CraftDora | Çekiliş Bitti")
      .setDescription(`🎁 **Ödül:** ${giveaway.prize}`)
      .setTimestamp();

    if (participants.length === 0) {
      embed.addFields({
        name: "Sonuç",
        value: "Katılımcı olmadığı için kazanan seçilemedi."
      });

      await channel.send({ embeds: [embed] });
    } else {
      const winner =
        participants[Math.floor(Math.random() * participants.length)];

      embed.addFields({
        name: "🎉 Kazanan",
        value: `<@${winner}>`
      });

      await channel.send({
        content: `🎉 Tebrikler <@${winner}>! **${giveaway.prize}** kazandın!`,
        embeds: [embed]
      });
    }

    const originalMessage = await channel.messages.fetch(messageId);
    await originalMessage.edit({ components: [disabledRow] });

  } catch (error) {
    console.error("Çekiliş bitiş hatası:", error.message);
  }
}

// ==================================================
// MESAJ VE KOMUT SİSTEMİ
// ==================================================

client.on("messageCreate", async message => {
  if (message.author.bot || !message.guild) return;

  const msg = message.content.toLocaleLowerCase("tr-TR").trim();

  // SELAMLAŞMA
  if (["sa", "s.a", "selam", "selamun aleyküm",
       "selamün aleyküm", "selamun aleykum"].includes(msg)) {
    return message.reply(
      "👋 Aleyküm Selam! **CraftDora** dünyasına hoş geldin! 🌿⛏️"
    );
  }

  if (msg.includes("naber") || msg.includes("nasılsın") || msg === "nbr") {
    return message.reply(
      "😊 İyiyim, çok teşekkür ederim! CraftDora'da keyifler nasıl? 🌲💚"
    );
  }

  if (
    msg.includes("iyiyim sen nasılsın") ||
    msg.includes("bende iyi sen nasılsın") ||
    msg.includes("ben de iyi sen nasılsın")
  ) {
    return message.reply(
      "Harika! İyi olmana sevindim. CraftDora'da keyifli oyunlar! 💚🎒"
    );
  }

  if (msg.includes("iyi geceler") || msg === "ig") {
    return message.reply(
      "Sana da iyi geceler! Yarın CraftDora'da görüşmek üzere! 🌙💤"
    );
  }

  if (msg.includes("günaydın") || msg.includes("gunaydin")) {
    return message.reply("☀️ Günaydın! CraftDora'da güzel bir gün geçir!");
  }

  if (msg.includes("iyi akşamlar") || msg.includes("iyi aksamlar")) {
    return message.reply("🌆 Sana da iyi akşamlar! 💚");
  }

  if (
    msg === "eyw" ||
    msg === "eyvallah" ||
    msg.includes("teşekkürler") ||
    msg.includes("tesekkurler")
  ) {
    return message.reply("💚 Rica ederiz! İyi eğlenceler!");
  }

  // SUNUCU IP
  if (["!ip", "ip", "sunucu ip"].includes(msg)) {
    const embed = new EmbedBuilder()
      .setColor("#2ecc71")
      .setTitle("⚔️ CraftDora | Sunucu Bilgileri")
      .setDescription(
        "🌲 **Sunucu adresi:** `play.craftdora.com`\n\n" +
        "🛡️ **Java sürümleri:** 1.20.1 - 26.3\n" +
        "📱 **Mobil sürümleri:** 1.20.1 - 26.3\n\n" +
        "📌 Bağlantı sorunu yaşarsan destek talebi oluşturabilirsin."
      )
      .setThumbnail(
        message.guild.iconURL({ size: 256 }) ||
        client.user.displayAvatarURL()
      );

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setLabel("CraftDora Web")
        .setStyle(ButtonStyle.Link)
        .setURL("https://craftdora.com")
    );

    return message.reply({ embeds: [embed], components: [row] });
  }

  // YARDIM
  if (["!yardım", "!yardim", "!help"].includes(msg)) {
    const embed = new EmbedBuilder()
      .setColor("#2ecc71")
      .setTitle("🌲 CraftDora | Komut Listesi")
      .setDescription(
        "`!ip` — Sunucu bilgileri\n" +
        "`!yardım` — Komut listesi\n" +
        "`!çekiliş 10m 1 Aylık VIP` — Çekiliş oluştur\n" +
        "`!destek-kur` — Ticket paneli oluştur\n" +
        "`!kapat` — Ticket kanalını kapat\n" +
        "`!kurallar-kur` — Kuralları gönder\n" +
        "`!başvuru-kur` — Yetkili başvuru paneli"
      );

    return message.reply({ embeds: [embed] });
  }

  // 15 MADDELİ KURAL PANELİ
  if (msg === "!kurallar-kur") {
    if (!isAdmin(message.member)) {
      return message.reply("❌ Bu komut için yönetici yetkisi gerekiyor.");
    }

    const embed = new EmbedBuilder()
      .setColor("#ff9f1c")
      .setTitle("📜 CraftDora | Sunucu Kuralları")
      .setDescription(
        "**1. Saygı:** Oyunculara ve yetkililere saygılı davranın.\n\n" +
        "**2. Hakaret:** Tehdit, taciz ve ayrımcı söylemler yasaktır.\n\n" +
        "**3. Hile:** Hile, makro ve haksız avantaj sağlayan yazılımlar yasaktır.\n\n" +
        "**4. Açık kullanımı:** Oyun hatalarını kötüye kullanmayın; yetkililere bildirin.\n\n" +
        "**5. Dolandırıcılık:** Oyuncuları kandırmak ve haksız eşya almak yasaktır.\n\n" +
        "**6. Reklam:** İzinsiz sunucu reklamı yapmak yasaktır.\n\n" +
        "**7. Spam:** Sohbeti gereksiz mesajlarla doldurmayın.\n\n" +
        "**8. Özel bilgiler:** Kişisel bilgilerinizi veya başkasının bilgilerini paylaşmayın.\n\n" +
        "**9. Yetkili taklidi:** Sahte yetkili kimliği kullanmayın.\n\n" +
        "**10. Kanal düzeni:** Kanalları amacına uygun kullanın.\n\n" +
        "**11. Haksız kazanç:** Sistemleri ve ödülleri istismar etmeyin.\n\n" +
        "**12. Tehdit ve şantaj:** Oyunculara baskı kurmak yasaktır.\n\n" +
        "**13. Ticket:** Destek sistemini gereksiz yere meşgul etmeyin.\n\n" +
        "**14. Gizlilik:** Özel yazışmaları izinsiz yaymayın.\n\n" +
        "**15. Yetkili kararları:** İtirazlarınızı destek kanallarından saygılı şekilde iletin.\n\n" +
        "━━━━━━━━━━━━━━━━━━\n" +
        "🌿 Kuralları ihlal edenlere ihlalin durumuna göre işlem uygulanabilir.\n" +
        "**CraftDora'da herkese iyi oyunlar!** ⛏️"
      )
      .setFooter({ text: "CraftDora • Kuralları okuyun" })
      .setTimestamp();

    return message.channel.send({ embeds: [embed] });
  }

  // TICKET PANELİ
  if (msg === "!destek-kur") {
    if (!isAdmin(message.member)) {
      return message.reply("❌ Bu komut için yönetici yetkisi gerekiyor.");
    }

    const embed = new EmbedBuilder()
      .setColor("#ff9f1c")
      .setTitle("🎫 CraftDora | Destek Merkezi")
      .setDescription(
        "Bir sorun, şikâyet veya sorunuz mu var?\n\n" +
        "1. Aşağıdaki butona basın.\n" +
        "2. Minecraft oyuncu adınızı girin.\n" +
        "3. Sorununuzu açıklayın.\n" +
        "4. Size özel bir destek kanalı oluşturulsun.\n\n" +
        "Her üye aynı anda bir açık ticket oluşturabilir."
      )
      .setFooter({ text: "CraftDora Destek Sistemi" });

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId("craftdora_ticket_open")
        .setLabel("Destek Talebi Aç 🎫")
        .setStyle(ButtonStyle.Success)
    );

    return message.channel.send({ embeds: [embed], components: [row] });
  }

  // YETKİLİ BAŞVURU PANELİ
  if (msg === "!başvuru-kur") {
    if (!isAdmin(message.member)) {
      return message.reply("❌ Bu komut için yönetici yetkisi gerekiyor.");
    }

    const embed = new EmbedBuilder()
      .setColor("#3498db")
      .setTitle("📝 CraftDora | Yetkili Başvurusu")
      .setDescription(
        "CraftDora ekibine katılmak mı istiyorsun?\n\n" +
        "Başvuru yapmak için yönetim ekibiyle iletişime geç. " +
        "Başvurunda deneyimini, yaşını ve neden ekibe katılmak istediğini belirt."
      );

    return message.channel.send({ embeds: [embed] });
  }

  // ÇEKİLİŞ: !çekiliş 10m 1 Aylık VIP
  if (msg.startsWith("!çekiliş ") || msg.startsWith("!cekilis ")) {
    if (!isAdmin(message.member)) {
      return message.reply("❌ Bu komut için yönetici yetkisi gerekiyor.");
    }

    const args = message.content.trim().split(/\s+/);
    const durationText = args[1];
    const prize = args.slice(2).join(" ").trim();
    const duration = parseDuration(durationText);

    if (!duration || !prize) {
      return message.reply(
        "❌ Kullanım: `!çekiliş 10m 1 Aylık VIP`\n" +
        "Süre biçimleri: `30s`, `10m`, `2h`, `1d`.\n" +
        "Süre 10 saniye ile 30 gün arasında olmalıdır."
      );
    }

    const embed = new EmbedBuilder()
      .setColor("#f1c40f")
      .setTitle("🎁 CRAFTDORA ÇEKİLİŞİ BAŞLADI!")
      .setDescription(
        `🎁 **Ödül:** ${prize}\n` +
        `⏳ **Süre:** ${durationText}\n` +
        `👑 **Düzenleyen:** ${message.author}\n\n` +
        "Katılmak için aşağıdaki butona bas!"
      )
      .setTimestamp(Date.now() + duration)
      .setFooter({ text: "CraftDora • Bol şans!" });

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId("craftdora_giveaway_join")
        .setLabel("Çekilişe Katıl 🎉")
        .setStyle(ButtonStyle.Success)
    );

    const giveawayMessage = await message.channel.send({
      embeds: [embed],
      components: [row]
    });

    giveaways.set(giveawayMessage.id, {
      channelId: message.channel.id,
      prize,
      participants: new Set()
    });

    setTimeout(() => {
      finishGiveaway(giveawayMessage.id);
    }, duration);

    return;
  }

  // TICKET KAPAT
  if (msg === "!kapat" || msg === "!ticket-kapat") {
    const channel = message.channel;

    if (
      channel.type !== ChannelType.GuildText ||
      !channel.topic?.startsWith("craftdora-ticket-owner:")
    ) {
      return message.reply(
        "Bu komut yalnızca CraftDora ticket kanalında kullanılabilir."
      );
    }

    const ownerId = channel.topic.split(":")[1];

    if (
      message.author.id !== ownerId &&
      !isAdmin(message.member)
    ) {
      return message.reply(
        "❌ Ticketı yalnızca sahibi veya yönetici kapatabilir."
      );
    }

    await message.reply("🔒 Ticket 5 saniye içinde kapatılıyor.");

    setTimeout(() => {
      channel.delete("CraftDora ticket kapatıldı.").catch(console.error);
    }, 5000);
  }
});

// ==================================================
// TÜM BUTON VE FORM ETKİLEŞİMLERİ
// ==================================================

client.on("interactionCreate", async interaction => {
  try {
    // TICKET FORMU GÖNDERİLDİ
    if (
      interaction.isModalSubmit() &&
      interaction.customId === "craftdora_ticket_form"
    ) {
      await interaction.deferReply({ ephemeral: true });

      const playerName = interaction.fields
        .getTextInputValue("player_name").trim();

      const issue = interaction.fields
        .getTextInputValue("ticket_issue").trim();

      const guild = interaction.guild;

      if (!guild) {
        return interaction.editReply(
          "Bu işlem yalnızca sunucuda kullanılabilir."
        );
      }

      const existing = guild.channels.cache.find(channel =>
        channel.type === ChannelType.GuildText &&
        channel.topic === `craftdora-ticket-owner:${interaction.user.id}`
      );

      if (existing) {
        return interaction.editReply(
          `Zaten açık bir destek talebin var: ${existing}`
        );
      }

      const playerPart = safeChannelPart(playerName, 15);
      const issuePart = safeChannelPart(issue, 22);

      const botMember = guild.members.me;

      if (!botMember) {
        return interaction.editReply(
          "Bot sunucu bilgilerine erişemedi. Lütfen tekrar dene."
        );
      }

      const channel = await guild.channels.create({
        name: `ticket-${playerPart}-${issuePart}`.slice(0, 95),
        type: ChannelType.GuildText,
        topic: `craftdora-ticket-owner:${interaction.user.id}`,
        permissionOverwrites: [
          {
            id: guild.roles.everyone.id,
            deny: [PermissionsBitField.Flags.ViewChannel]
          },
          {
            id: interaction.user.id,
            allow: [
              PermissionsBitField.Flags.ViewChannel,
              PermissionsBitField.Flags.SendMessages,
              PermissionsBitField.Flags.ReadMessageHistory,
              PermissionsBitField.Flags.AttachFiles
            ]
          },
          {
            id: botMember.id,
            allow: [
              PermissionsBitField.Flags.ViewChannel,
              PermissionsBitField.Flags.SendMessages,
              PermissionsBitField.Flags.ReadMessageHistory,
              PermissionsBitField.Flags.ManageChannels
            ]
          }
        ],
        reason: `CraftDora destek talebi: ${interaction.user.tag}`
      });

      const ticketEmbed = new EmbedBuilder()
        .setColor("#ff9f1c")
        .setTitle("🎫 CraftDora | Destek Talebi")
        .setDescription(
          `Merhaba ${interaction.user}!\n\n` +
          `👤 **Minecraft oyuncu adı:** ${playerName}\n` +
          `📌 **Destek konusu:** ${issue}\n\n` +
          "Sorununun ayrıntılarını bu kanalda paylaş. " +
          "Yetkililer seninle ilgilenecektir.\n\n" +
          "Talebi kapatmak için `!kapat` yazabilirsin."
        )
        .setFooter({ text: "CraftDora Destek Sistemi" })
        .setTimestamp();

      await channel.send({
        content: `${interaction.user}`,
        embeds: [ticketEmbed]
      });

      return interaction.editReply(
        `✅ Destek talebin oluşturuldu: ${channel}`
      );
    }

    if (!interaction.isButton()) return;

    // TICKET FORMUNU AÇ
    if (interaction.customId === "craftdora_ticket_open") {
      const modal = new ModalBuilder()
        .setCustomId("craftdora_ticket_form")
        .setTitle("CraftDora Destek Talebi");

      const nameInput = new TextInputBuilder()
        .setCustomId("player_name")
        .setLabel("Minecraft oyuncu adın")
        .setPlaceholder("Örnek: CraftDoraOyuncu")
        .setStyle(TextInputStyle.Short)
        .setMinLength(1)
        .setMaxLength(32)
        .setRequired(true);

      const issueInput = new TextInputBuilder()
        .setCustomId("ticket_issue")
        .setLabel("Destek konun veya sorunun")
        .setPlaceholder("Örnek: Hesap sorunu, oyuncu şikâyeti")
        .setStyle(TextInputStyle.Paragraph)
        .setMinLength(5)
        .setMaxLength(300)
        .setRequired(true);

      modal.addComponents(
        new ActionRowBuilder().addComponents(nameInput),
        new ActionRowBuilder().addComponents(issueInput)
      );

      return interaction.showModal(modal);
    }

    // ÇEKİLİŞE KATIL
    if (interaction.customId === "craftdora_giveaway_join") {
      const giveaway = giveaways.get(interaction.message.id);

      if (!giveaway) {
        return interaction.reply({
          content: "Bu çekiliş aktif değil veya sona erdi.",
          ephemeral: true
        });
      }

      if (interaction.user.bot) {
        return interaction.reply({
          content: "Botlar çekilişe katılamaz.",
          ephemeral: true
        });
      }

      if (giveaway.participants.has(interaction.user.id)) {
        return interaction.reply({
          content: "❌ Bu çekilişe zaten katıldın!",
          ephemeral: true
        });
      }

      giveaway.participants.add(interaction.user.id);

      return interaction.reply({
        content: "✅ Çekilişe katıldın! Bol şans! 🎉",
        ephemeral: true
      });
    }

  } catch (error) {
    console.error("Etkileşim hatası:", error);

    if (!interaction.isRepliable()) return;

    try {
      if (interaction.deferred || interaction.replied) {
        await interaction.editReply(
          "❌ İşlem tamamlanamadı. Biraz sonra tekrar dene."
        );
      } else {
        await interaction.reply({
          content: "❌ İşlem tamamlanamadı. Biraz sonra tekrar dene.",
          ephemeral: true
        });
      }
    } catch (replyError) {
      console.error("Hata yanıtı gönderilemedi:", replyError.message);
    }
  }
});

// ==================================================
// HATA KAYITLARI
// ==================================================

process.on("unhandledRejection", error => {
  console.error("İşlenmeyen Promise hatası:", error);
});

process.on("uncaughtException", error => {
  console.error("Beklenmeyen hata:", error);
});

// ==================================================
// BOTU BAŞLAT
// ==================================================

if (!TOKEN) {
  console.error(
    "DISCORD_TOKEN bulunamadı! Render > Environment bölümüne ekle."
  );
  process.exit(1);
}

client.login(TOKEN).catch(error => {
  console.error("Discord giriş hatası:", error);
  process.exit(1);
});
