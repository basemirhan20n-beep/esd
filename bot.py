import logging
import random
import asyncio
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from database import Database
from config import BOT_TOKEN, ADMIN_IDS
from futbol import (
    cmd_takim_kur, cmd_takim, cmd_piyasa, cmd_satin_al,
    cmd_sat, cmd_sat_iptal, cmd_antrenman, cmd_mac,
    cmd_lig, cmd_son_maclar, cmd_fikstur, cmd_cuzdan,
    cmd_spin, cmd_istatistik, cmd_golcular, cmd_taktik,
    cmd_altyapi, cmd_basarilar, cmd_kupa, cmd_kupa_tablo,
    futbol_callback, fdb,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if user.id in ADMIN_IDS:
        return True
    veri = db.kullanici_getir(user.id)
    if veri and veri.get("role") == "Parti Başkanı":
        return True
    try:
        if chat and chat.type in ("group", "supergroup", "channel"):
            uye = await context.bot.get_chat_member(chat.id, user.id)
            if uye.status in ("administrator", "creator"):
                return True
    except Exception:
        pass
    return False


MAKAMLAR = [
    "Parti Başkanı", "Genel Sekreter", "Ekonomi Başkanı",
    "Eğitim Başkanı", "Kooperatif Sorumlusu", "İçişleri Sorumlusu", "Parti Yöneticisi",
]

GOREVLER = {
    "Parti Başkanı": [
        "Parti genel kararını açıkla ve üyeleri bilgilendir.",
        "Kritik bir krizi çöz ve strateji belirle.",
        "Yeni parti stratejisi belirle ve duyur.",
        "Yönetim kurulunu topla ve kararları kayıt altına al.",
    ],
    "Genel Sekreter": [
        "Parti içi düzen raporu hazırla ve sun.",
        "Tüm üyelerin durumunu kontrol et ve belgele.",
        "Bu haftaki toplantıyı organize et.",
        "Arşivleri güncelle ve eksik belgeleri tamamla.",
    ],
    "Ekonomi Başkanı": [
        "Aylık bütçe planı hazırla ve onayla.",
        "Gelir-gider raporu yaz ve sunuma hazırla.",
        "Ekonomik öneri paketi oluştur.",
        "Harcamaları denetle ve tasarruf önerileri sun.",
    ],
    "Eğitim Başkanı": [
        "Parti üyeleri için eğitim planı oluştur.",
        "Üyelere kişisel gelişim önerileri sun.",
        "Eğitim duyurusunu hazırla ve dağıt.",
        "Eğitim materyallerini güncelle ve arşivle.",
    ],
    "Kooperatif Sorumlusu": [
        "Bu dönem için üretim planı hazırla.",
        "Kooperatif faaliyet raporu yaz ve sun.",
        "Gelir artırma önerisi geliştir.",
        "Kooperatif üyelerini denetle ve raporla.",
    ],
    "İçişleri Sorumlusu": [
        "Parti içi güvenlik denetimi gerçekleştir.",
        "Sorunlu durumları tespit et ve raporla.",
        "Disiplin raporu hazırla ve yönetime sun.",
        "Üye şikayetlerini incele ve çözüme kavuştur.",
    ],
    "Parti Yöneticisi": [
        "Üyelere operasyonel destek ver.",
        "Parti içi süreç iyileştirme önerisi sun.",
        "Üyeler arası iletişimi artıracak plan hazırla.",
        "Haftalık yönetim özeti hazırla ve dağıt.",
    ],
}

GOREV_MESAJLARI = {
    "Parti Başkanı": ["🏛️ Başkan genel kararını açıkladı.", "🏛️ Başkan krizi çözüme kavuşturdu."],
    "Genel Sekreter": ["📋 Sekreter düzen raporunu tamamladı.", "📋 Toplantı organize edildi."],
    "Ekonomi Başkanı": ["💰 Bütçe planı açıklandı.", "💰 Gelir-gider raporu sunuldu."],
    "Eğitim Başkanı": ["📚 Yeni eğitim planı devreye alındı.", "📚 Üyelere gelişim programı sunuldu."],
    "Kooperatif Sorumlusu": ["🌾 Üretim planı onaylandı.", "🌾 Kooperatif raporu tamamlandı."],
    "İçişleri Sorumlusu": ["🔒 Güvenlik denetimi tamamlandı.", "🔒 Disiplin raporu hazırlandı."],
    "Parti Yöneticisi": ["⚙️ Üyelere gerekli destek sağlandı.", "⚙️ Süreç iyileştirme önerisi kabul edildi."],
}

SEVIYE_ESLEME = {
    1: 0, 2: 100, 3: 250, 4: 500, 5: 1000,
    6: 2000, 7: 3500, 8: 5500, 9: 8000, 10: 12000,
}


def seviye_hesapla(xp: int) -> int:
    seviye = 1
    for lvl, gerekli in sorted(SEVIYE_ESLEME.items(), reverse=True):
        if xp >= gerekli:
            seviye = lvl
            break
    return seviye


# ─── Başlangıç ─────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    # Grup kaydı
    chat = update.effective_chat
    if chat and chat.type in ("group", "supergroup"):
        fdb.grup_kaydet(chat.id)
    klavye = [
        [
            InlineKeyboardButton("📌 Görev Yap", callback_data="gorev_yap"),
            InlineKeyboardButton("👤 Profil", callback_data="profil"),
        ],
        [
            InlineKeyboardButton("🏛️ Makam", callback_data="makam"),
            InlineKeyboardButton("🏆 Liderler", callback_data="liderler"),
        ],
        [
            InlineKeyboardButton("⚽ Futbol & Lig", callback_data="futbol_menu"),
            InlineKeyboardButton("🎰 Şans Çarkı", callback_data="spin"),
        ],
        [
            InlineKeyboardButton("🏅 Başarılar", callback_data="basarilar"),
        ],
    ]
    await update.message.reply_text(
        f"🏛️ *Parti Yönetim Sistemi'ne Hoş Geldiniz*\n\n"
        f"Sayın {user.first_name}, partimizin güçlü bir üyesisiniz.\n\n"
        f"Günlük görevinizi yaparak XP ve güven kazanın. "
        f"⚽ Futbol ligi, 🎰 şans çarkı ve 🏅 başarı rozetleri sizi bekliyor!\n\n"
        f"_Parti her şeyden önce gelir._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(klavye),
    )


async def grup_kaydet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat and chat.type in ("group", "supergroup"):
        fdb.grup_kaydet(chat.id)
        await update.message.reply_text("✅ Bu grup maç bildirimleri için kayıt edildi!")
    else:
        await update.message.reply_text("⚠️ Bu komut sadece gruplarda kullanılabilir.")


# ─── Profil / Makam / Görev ──────────────────────────────────────────────────

async def profil_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)
    await _profil_goster(update, veri, user.first_name)


async def _profil_goster(update, veri, isim):
    xp = veri["xp"]
    level = seviye_hesapla(xp)
    guven = veri["guven"]
    streak = veri["streak"]
    rol = veri["role"] or "Atanmamış"
    durum = "🟢 Güvenli" if guven >= 75 else ("🟡 Dikkatli" if guven >= 50 else ("🟠 Riskli" if guven >= 30 else "🔴 Kritik"))
    sonraki = SEVIYE_ESLEME.get(level + 1)
    xp_bilgi = f"{xp} XP → Sonraki: {sonraki - xp} XP kaldı" if sonraki else f"{xp} XP (MAX)"
    # Futbol takımı bilgisi
    takim = fdb.takim_user(veri["user_id"])
    takim_bilgi = f"⚽ *Takım:* {takim['isim']} ({takim['puan']} puan)\n" if takim else ""
    # Başarı sayısı
    basari_sayisi = len(fdb.kullanici_basarilari(veri["user_id"]))
    mesaj = (
        f"👤 *{isim} — Profil*\n{'─'*28}\n"
        f"🏛️ *Makam:* {rol}\n"
        f"⭐ *Seviye:* {level}\n"
        f"🔷 *XP:* {xp_bilgi}\n"
        f"🛡️ *Güven:* {guven}/100 — {durum}\n"
        f"🔥 *Seri:* {streak} gün\n"
        f"🏅 *Başarı:* {basari_sayisi} adet\n"
        f"{takim_bilgi}"
    )
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown")


async def makam_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)
    rol = veri["role"]
    guven = veri["guven"]
    if not rol:
        mesaj = "🏛️ *Makam Durumu*\n─────────────\n⚠️ Henüz bir makama atanmadınız."
    else:
        if guven >= 75:
            durum = "🟢 Güvenli Koltuk"
        elif guven >= 50:
            durum = "🟡 Dikkat Gerektiriyor"
        elif guven >= 30:
            durum = "🔴 Riskli Koltuk"
        else:
            durum = "⛔ Kritik — Görevden Alma"
        mesaj = (
            f"🏛️ *Makam Durumu*\n{'─'*20}\n"
            f"📌 *Makam:* {rol}\n"
            f"🛡️ *Güven:* {guven}/100\n"
            f"📊 *Durum:* {durum}\n"
        )
        if guven < 30:
            mesaj += "\n🚨 _Görevden alma oylaması başlatılabilir!_"
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown")


async def gorev_yap_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)
    rol = veri["role"]
    if not rol:
        mesaj = "⚠️ Henüz bir makama atanmadınız."
        if hasattr(update, "message") and update.message:
            await update.message.reply_text(mesaj)
        else:
            await update.callback_query.edit_message_text(mesaj)
        return
    bugun = date.today().isoformat()
    if veri["last_task"] == bugun:
        mesaj = "✅ Bugünkü görevinizi zaten tamamladınız. Yarın tekrar gelin."
        if hasattr(update, "message") and update.message:
            await update.message.reply_text(mesaj)
        else:
            await update.callback_query.edit_message_text(mesaj)
        return
    gorev = random.choice(GOREVLER[rol])
    context.user_data["aktif_gorev"] = gorev
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Görevi Tamamladım", callback_data="gorev_tamamla"),
    ]])
    mesaj = (
        f"📌 *Günlük Göreviniz*\n{'─'*20}\n"
        f"🏛️ *Makam:* {rol}\n\n"
        f"📋 *Görev:*\n_{gorev}_\n\n"
        f"Görevi tamamladıktan sonra butona basın."
    )
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown", reply_markup=markup)
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown", reply_markup=markup)


async def gorev_tamamla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    veri = db.kullanici_getir(user.id)
    if not veri:
        await query.edit_message_text("Kayıt bulunamadı. /start ile başlayın.")
        return
    bugun = date.today().isoformat()
    if veri["last_task"] == bugun:
        await query.edit_message_text("✅ Bu görevi zaten tamamladınız.")
        return
    rol = veri["role"]
    if not rol:
        await query.edit_message_text("⚠️ Makamınız bulunmamaktadır.")
        return
    streak = veri["streak"] + 1
    bonus_xp = streak * 5
    kazanilan_xp = 20 + bonus_xp
    yeni_xp = veri["xp"] + kazanilan_xp
    yeni_guven = min(100, veri["guven"] + 3)
    yeni_level = seviye_hesapla(yeni_xp)
    eski_level = seviye_hesapla(veri["xp"])
    db.kullanici_guncelle(
        user_id=user.id, xp=yeni_xp, level=yeni_level,
        guven=yeni_guven, streak=streak, last_task=bugun,
    )
    mesaj_metni = random.choice(GOREV_MESAJLARI[rol])
    seviye_mesaji = f"\n\n🎉 *SEVİYE ATLADI!* → Seviye {yeni_level}" if yeni_level > eski_level else ""
    mesaj = (
        f"✅ *Görev Tamamlandı*\n{'─'*20}\n"
        f"{mesaj_metni}\n\n"
        f"🔷 *Kazanılan XP:* +{kazanilan_xp} (Baz:20 + Seri:{bonus_xp})\n"
        f"🛡️ *Güven:* {yeni_guven}/100 (+3)\n"
        f"🔥 *Seri:* {streak} gün{seviye_mesaji}"
    )
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("👤 Profilim", callback_data="profil"),
        InlineKeyboardButton("🏛️ Makamım", callback_data="makam"),
    ]])
    await query.edit_message_text(mesaj, parse_mode="Markdown", reply_markup=markup)


async def liderler_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liderler = db.lider_tablosu()
    if not liderler:
        mesaj = "📊 Henüz lider tablosunda kimse yok."
    else:
        satirlar = [f"🏆 *Lider Tablosu — İlk 10*\n{'─'*28}"]
        madalyalar = ["🥇", "🥈", "🥉"]
        for i, (isim, xp, rol, guven) in enumerate(liderler):
            madalya = madalyalar[i] if i < 3 else f"{i+1}."
            rol_kisa = rol or "Atanmamış"
            satirlar.append(f"{madalya} *{isim}* — {xp} XP | {rol_kisa} | G:{guven}")
        mesaj = "\n".join(satirlar)
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown")


# ─── Admin Komutları ─────────────────────────────────────────────────────────

async def rol_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Kullanım: `/rol_ver @kullanıcı Makam Adı`", parse_mode="Markdown")
        return
    hedef_username = args[0].lstrip("@")
    makam = " ".join(args[1:])
    if makam not in MAKAMLAR:
        await update.message.reply_text(f"⚠️ Geçersiz makam.\nMevcut: {', '.join(MAKAMLAR)}")
        return
    hedef = db.kullanici_username_ile_getir(hedef_username)
    if not hedef:
        await update.message.reply_text(f"⚠️ `{hedef_username}` bulunamadı.")
        return
    db.rol_ata(hedef["user_id"], makam)
    await update.message.reply_text(
        f"✅ *{hedef_username}* → *{makam}* görevi verildi.", parse_mode="Markdown"
    )


async def rol_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/rol_al @kullanıcı`", parse_mode="Markdown")
        return
    hedef = db.kullanici_username_ile_getir(context.args[0].lstrip("@"))
    if not hedef:
        await update.message.reply_text("⚠️ Kullanıcı bulunamadı.")
        return
    db.rol_ata(hedef["user_id"], None)
    await update.message.reply_text("✅ Görev alındı.", parse_mode="Markdown")


async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/duyuru Mesaj`", parse_mode="Markdown")
        return
    metin = " ".join(context.args)
    tum = db.tum_kullanicilari_getir()
    basarili = 0
    for uid, _ in tum:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *PARTİ DUYURUSU*\n{'─'*28}\n{metin}",
                parse_mode="Markdown",
            )
            basarili += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Duyuru {basarili} üyeye iletildi.")


async def puan_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Kullanım: `/puan_ver @kullanıcı miktar`", parse_mode="Markdown")
        return
    try:
        miktar = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Miktar sayısal olmalı.")
        return
    hedef = db.kullanici_username_ile_getir(args[0].lstrip("@"))
    if not hedef:
        await update.message.reply_text("⚠️ Kullanıcı bulunamadı.")
        return
    yeni_xp = hedef["xp"] + miktar
    db.kullanici_guncelle(hedef["user_id"], xp=yeni_xp, level=seviye_hesapla(yeni_xp))
    await update.message.reply_text(
        f"✅ {args[0]} → +{miktar} XP. Toplam: {yeni_xp} XP", parse_mode="Markdown"
    )


async def guven_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Kullanım: `/guven_ver @kullanıcı miktar`", parse_mode="Markdown")
        return
    try:
        miktar = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Miktar sayısal olmalı.")
        return
    hedef = db.kullanici_username_ile_getir(args[0].lstrip("@"))
    if not hedef:
        await update.message.reply_text("⚠️ Kullanıcı bulunamadı.")
        return
    yeni_g = max(0, min(100, hedef["guven"] + miktar))
    db.kullanici_guncelle(hedef["user_id"], guven=yeni_g)
    await update.message.reply_text(f"✅ Güven güncellendi → {yeni_g}/100")


async def kupa_olustur_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    basari, mesaj = fdb.kupa_olustur()
    await update.message.reply_text(mesaj if basari else f"❌ {mesaj}")


async def sezon_sifirla_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    lig = 1
    if context.args and context.args[0] == "2":
        lig = 2
    sampiyon = fdb.sezon_sampiyon(lig)
    sayi = fdb.sezon_sifirla(lig)
    lig_adi = "1. Lig" if lig == 1 else "2. Lig"
    mesaj = f"🔄 *{lig_adi} Sezonu Sıfırlandı!*\n{sayi} takımın puanları temizlendi.\n"
    if sampiyon:
        mesaj += f"🥇 Sezon Şampiyonu: *{sampiyon['isim']}* tebrik edildi!\n"
    mesaj += "Yeni sezon için fikstür bekleniyor. (Takım eklenince veya `/fikstur_olustur` ile)"
    await update.message.reply_text(mesaj, parse_mode="Markdown")


async def fikstur_olustur_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔ Yalnızca adminler kullanabilir.")
        return
    lig = 1
    if context.args and context.args[0] == "2":
        lig = 2
    ok = fdb.fikstur_olustur(lig)
    if ok:
        lig_adi = "1. Lig" if lig == 1 else "2. Lig"
        await update.message.reply_text(f"✅ {lig_adi} fikstürü oluşturuldu!")
    else:
        await update.message.reply_text("❌ Yeterli takım yok.")


# ─── Buton Handler ────────────────────────────────────────────────────────────

async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if await futbol_callback(update, context):
        return

    if data == "profil":
        user = update.effective_user
        db.kullanici_ekle(user.id, user.username or user.first_name)
        veri = db.kullanici_getir(user.id)
        await _profil_goster(update, veri, user.first_name)
    elif data == "makam":
        await makam_komutu(update, context)
    elif data == "gorev_yap":
        await gorev_yap_komutu(update, context)
    elif data == "gorev_tamamla":
        await gorev_tamamla(update, context)
    elif data == "liderler":
        await liderler_komutu(update, context)
    elif data == "spin":
        await cmd_spin(update, context)
    elif data == "basarilar":
        user = update.effective_user
        basarilar = fdb.kullanici_basarilari(user.id)
        from futbol_db import BASARILAR
        if not basarilar:
            await query.edit_message_text("🏅 Henüz başarı kazanmadın!")
            return
        metin = f"🏅 *{user.first_name} — Başarılar*\n{'─'*28}\n"
        for b in basarilar:
            kod = b["basari_kodu"]
            if kod in BASARILAR:
                e_isim, acik = BASARILAR[kod]
                metin += f"✨ *{e_isim}*\n  _{acik}_ ({b['tarih']})\n"
        await query.edit_message_text(metin, parse_mode="Markdown")
    elif data == "ana_menu":
        klavye = [
            [
                InlineKeyboardButton("📌 Görev Yap", callback_data="gorev_yap"),
                InlineKeyboardButton("👤 Profil", callback_data="profil"),
            ],
            [
                InlineKeyboardButton("🏛️ Makam", callback_data="makam"),
                InlineKeyboardButton("🏆 Liderler", callback_data="liderler"),
            ],
            [
                InlineKeyboardButton("⚽ Futbol & Lig", callback_data="futbol_menu"),
                InlineKeyboardButton("🎰 Şans Çarkı", callback_data="spin"),
            ],
            [InlineKeyboardButton("🏅 Başarılar", callback_data="basarilar")],
        ]
        await query.edit_message_text(
            "🏛️ *Ana Menü*\nAşağıdan bir seçenek belirleyin:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(klavye),
        )
    elif data == "futbol_menu":
        klavye = [
            [
                InlineKeyboardButton("👥 Takımım", callback_data="takim_bilgi"),
                InlineKeyboardButton("🏆 1. Lig", callback_data="lig_tab_1"),
                InlineKeyboardButton("🥈 2. Lig", callback_data="lig_tab_2"),
            ],
            [
                InlineKeyboardButton("🛒 Transfer", callback_data="piyasa_0"),
                InlineKeyboardButton("⚽ Maç Oyna", callback_data="mac_oyna"),
                InlineKeyboardButton("🏅 Kupa", callback_data="kupa_menu"),
            ],
            [
                InlineKeyboardButton("🏋️ Antrenman", callback_data="antrenman"),
                InlineKeyboardButton("📅 Fikstür", callback_data="fikstur_goster"),
                InlineKeyboardButton("🎯 Taktik", callback_data="taktik_menu"),
            ],
            [
                InlineKeyboardButton("📊 İstatistik", callback_data="istatistik"),
                InlineKeyboardButton("🌱 Altyapı", callback_data="altyapi"),
                InlineKeyboardButton("🎰 Spin", callback_data="spin"),
            ],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="ana_menu")],
        ]
        await query.edit_message_text(
            "⚽ *Futbol Yönetimi*\nNe yapmak istiyorsun?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(klavye),
        )
    elif data == "kupa_menu":
        user = update.effective_user
        mac = fdb.kupa_sonraki_mac(user.id)
        if mac:
            await cmd_kupa(update, context)
        else:
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("🏅 Kupa Tablosu", callback_data="kupa_tablo"),
                InlineKeyboardButton("🔙 Geri", callback_data="futbol_menu"),
            ]])
            await query.edit_message_text(
                "🏅 *Cumhuriyet Kupası*\n\nAktif kupa maçın yok.\n"
                "Admin `/kupa_olustur` ile kupayı başlatabilir.",
                parse_mode="Markdown",
                reply_markup=markup
            )
    elif data == "kupa_tablo":
        await cmd_kupa_tablo(update, context)


# ─── Zamanlanmış Görevler ─────────────────────────────────────────────────────

async def gunluk_ceza_isle(context: ContextTypes.DEFAULT_TYPE):
    tum = db.tum_kullanicilari_getir()
    bugun = date.today().isoformat()
    dun = (date.today() - timedelta(days=1)).isoformat()
    for user_id, _ in tum:
        veri = db.kullanici_getir(user_id)
        if not veri or not veri["role"]:
            continue
        if veri["last_task"] in (bugun, None):
            continue
        if veri["last_task"] == dun:
            continue
        son = veri["last_task"]
        try:
            fark = (date.today() - date.fromisoformat(son)).days if son else 1
        except Exception:
            fark = 1
        ceza = min(5 * fark, 30)
        yeni_guven = max(0, veri["guven"] - ceza)
        db.kullanici_guncelle(user_id, guven=yeni_guven, streak=0)
        try:
            if yeni_guven < 30:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🚨 *Kritik Güven Uyarısı!*\nGüven puanınız {yeni_guven}'e düştü!\nGörevlerinizi aksatmayın!",
                    parse_mode="Markdown",
                )
            elif yeni_guven < 50:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ *Güven Uyarısı*\nGüven puanınız {yeni_guven}'e düştü. Görevinizi yapın!",
                    parse_mode="Markdown",
                )
        except Exception:
            pass


async def gunluk_spin_hatirlatici(context: ContextTypes.DEFAULT_TYPE):
    """Günlük spin hatırlatıcısı"""
    tum = db.tum_kullanicilari_getir()
    bugun = date.today().isoformat()
    for user_id, _ in tum:
        try:
            import sqlite3
            conn = sqlite3.connect("parti.db")
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT son_spin FROM spin_kaydi WHERE user_id=?", (user_id,)).fetchone()
            conn.close()
            if not r or r["son_spin"] != bugun:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎰 *Günlük şans çarkını çevirmedi!*\n`/spin` yazarak çevir ve ödül kazan!",
                    parse_mode="Markdown",
                )
        except Exception:
            pass


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Genel komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profil", profil_komutu))
    app.add_handler(CommandHandler("makam", makam_komutu))
    app.add_handler(CommandHandler("gorev", gorev_yap_komutu))
    app.add_handler(CommandHandler("liderler", liderler_komutu))
    app.add_handler(CommandHandler("rol_ver", rol_ver))
    app.add_handler(CommandHandler("rol_al", rol_al))
    app.add_handler(CommandHandler("duyuru", duyuru))
    app.add_handler(CommandHandler("puan_ver", puan_ver))
    app.add_handler(CommandHandler("guven_ver", guven_ver))
    app.add_handler(CommandHandler("grup_kaydet", grup_kaydet_cmd))

    # Futbol komutları
    app.add_handler(CommandHandler("takim_kur", cmd_takim_kur))
    app.add_handler(CommandHandler("takim", cmd_takim))
    app.add_handler(CommandHandler("piyasa", cmd_piyasa))
    app.add_handler(CommandHandler("satin_al", cmd_satin_al))
    app.add_handler(CommandHandler("sat", cmd_sat))
    app.add_handler(CommandHandler("sat_iptal", cmd_sat_iptal))
    app.add_handler(CommandHandler("antrenman", cmd_antrenman))
    app.add_handler(CommandHandler("mac", cmd_mac))
    app.add_handler(CommandHandler("lig", cmd_lig))
    app.add_handler(CommandHandler("son_maclar", cmd_son_maclar))
    app.add_handler(CommandHandler("fikstur", cmd_fikstur))
    app.add_handler(CommandHandler("cuzdan", cmd_cuzdan))
    app.add_handler(CommandHandler("spin", cmd_spin))
    app.add_handler(CommandHandler("istatistik", cmd_istatistik))
    app.add_handler(CommandHandler("golcular", cmd_golcular))
    app.add_handler(CommandHandler("taktik", cmd_taktik))
    app.add_handler(CommandHandler("altyapi", cmd_altyapi))
    app.add_handler(CommandHandler("basarilar", cmd_basarilar))
    app.add_handler(CommandHandler("kupa", cmd_kupa))
    app.add_handler(CommandHandler("kupa_tablo", cmd_kupa_tablo))

    # Admin komutları
    app.add_handler(CommandHandler("kupa_olustur", kupa_olustur_cmd))
    app.add_handler(CommandHandler("sezon_sifirla", sezon_sifirla_cmd))
    app.add_handler(CommandHandler("fikstur_olustur", fikstur_olustur_cmd))

    app.add_handler(CallbackQueryHandler(buton_handler))

    # Zamanlanmış görevler
    jq = app.job_queue
    jq.run_daily(gunluk_ceza_isle, time=datetime.strptime("23:59", "%H:%M").time(), name="gunluk_ceza")
    jq.run_daily(gunluk_spin_hatirlatici, time=datetime.strptime("09:00", "%H:%M").time(), name="spin_hatirlatici")

    logger.info("✅ Bot başlatılıyor — Cumhuriyet Parti Yönetim Botu v2.0")
    logger.info("Komutlar: /start /takim_kur /mac /spin /kupa /taktik /altyapi /basarilar")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
