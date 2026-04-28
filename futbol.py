"""
Cumhuriyet Süper Ligi & 2. Lig — Futbol Modülü
Tüm komutlar ve callback'ler burada.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from futbol_db import FutbolDB, TAKTIKLER, BASARILAR, LIG1_LIMIT, LIG2_LIMIT

fdb = FutbolDB()

POZ_EMOJI = {
    "Kaleci":   "🧤",
    "Defans":   "🛡️",
    "Orta Saha":"⚙️",
    "Forvet":   "⚡",
}

LIG1_ADI = "🏆 CUMHURİYET SÜPER LİGİ"
LIG2_ADI = "🥈 CUMHURİYET 2. LİGİ"

TUR_ADLARI = {1: "Tur 1", 2: "Çeyrek Final", 3: "Yarı Final", 4: "Final"}


# ══════════════════════════════════════════════════════════
#  YARDIMCI
# ══════════════════════════════════════════════════════════

async def _gonder(update: Update, metin: str, markup=None, parse_mode="Markdown"):
    if update.callback_query:
        await update.callback_query.edit_message_text(metin, parse_mode=parse_mode, reply_markup=markup)
    else:
        await update.message.reply_text(metin, parse_mode=parse_mode, reply_markup=markup)


def _piyasa_markup(sayfa: int, toplam: int, sayfa_boyut: int = 8) -> InlineKeyboardMarkup:
    nav = []
    if sayfa > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"piyasa_{sayfa-1}"))
    toplam_sayfa = max(1, (toplam + sayfa_boyut - 1) // sayfa_boyut)
    nav.append(InlineKeyboardButton(f"{sayfa+1}/{toplam_sayfa}", callback_data="piyasa_noop"))
    if (sayfa + 1) * sayfa_boyut < toplam:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"piyasa_{sayfa+1}"))
    return InlineKeyboardMarkup([nav, [InlineKeyboardButton("🔄 Yenile", callback_data=f"piyasa_{sayfa}")]])


def _mac_raporu_mesaj(sonuc: dict, kendi_user_id: int) -> str:
    ev = sonuc["ev_takim"]
    dep = sonuc["dep_takim"]
    eg = sonuc["ev_gol"]
    dg = sonuc["dep_gol"]
    if eg > dg:
        emoji = "🟢"
        stext = f"{ev} kazandı!"
    elif dg > eg:
        emoji = "🔵"
        stext = f"{dep} kazandı!"
    else:
        emoji = "🟡"
        stext = "Berabere!"
    metin = (
        f"⚽ *{LIG1_ADI if sonuc.get('lig', 1) == 1 else LIG2_ADI}*\n"
        f"*{sonuc['hafta']}. Hafta Maç Raporu*\n"
        f"{'═'*30}\n"
        f"🏠 *{ev}* {eg} – {dg} *{dep}* ✈️\n"
        f"{'─'*30}\n"
        f"{emoji} {stext}\n"
        f"🎯 Taktik: {sonuc.get('ev_taktik','?')} vs {sonuc.get('dep_taktik','?')}\n"
    )
    if sonuc["ev_gol_atanlar"]:
        metin += f"\n⚽ *{ev}* golleri:\n"
        for g in sonuc["ev_gol_atanlar"]:
            metin += f"  ⚡ {g}\n"
    if sonuc["dep_gol_atanlar"]:
        metin += f"\n⚽ *{dep}* golleri:\n"
        for g in sonuc["dep_gol_atanlar"]:
            metin += f"  ⚡ {g}\n"
    if sonuc.get("olaylar"):
        metin += "\n📋 *Maç Olayları:*\n"
        for o in sonuc["olaylar"]:
            metin += f"  {o}\n"
    odul = 5_000 if (
        (eg > dg and sonuc["ev_takim_user"] == kendi_user_id) or
        (dg > eg and sonuc["dep_takim_user"] == kendi_user_id)
    ) else (2_500 if eg == dg else 1_000)
    metin += f"\n💰 Kazanılan: *+{odul:,}₺*"
    return metin


# ══════════════════════════════════════════════════════════
#  KOMUTLAR
# ══════════════════════════════════════════════════════════

async def cmd_takim_kur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text(
            "⚽ Kullanım: `/takim_kur Takım Adı`", parse_mode="Markdown"
        )
        return
    isim = " ".join(context.args)
    basari, lig_veya_hata, takim_sayisi = fdb.takim_kur(user.id, isim)
    if not basari:
        await update.message.reply_text(f"❌ {lig_veya_hata}")
        return
    lig = lig_veya_hata
    fdb.para_getir(user.id)
    lig_adi = LIG1_ADI if lig == 1 else LIG2_ADI
    limit = LIG1_LIMIT if lig == 1 else LIG2_LIMIT
    fikstur_mesaj = ""
    if takim_sayisi >= limit and not fdb.fikstur_var_mi(lig):
        fdb.fikstur_olustur(lig)
        fikstur_mesaj = (
            f"\n\n🎉 *{limit}. takım tamamlandı!* {lig_adi} fikstürü oluşturuldu! 🎊\n"
            f"Herkes özel mesajından maç sonuçlarını alacak."
        )
    elif fdb.fikstur_var_mi(lig):
        t = fdb.takim_user(user.id)
        if t:
            fdb.fikstur_takim_ekle(t["takim_id"], lig)
        fikstur_mesaj = "\n\n📅 Fikstüre yeni maçlar eklendi! Puanlar korundu."
    await update.message.reply_text(
        f"✅ *{isim}* kuruldu! _{lig_adi}_\n"
        f"💰 Başlangıç bütçen: *100.000₺*\n"
        f"👥 Ligde *{takim_sayisi}/{limit}* takım var.\n"
        f"⚽ Maç için en az 11 oyuncu gerekli (1 Kaleci dahil)."
        f"{fikstur_mesaj}",
        parse_mode="Markdown",
    )


async def cmd_takim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok. `/takim_kur <Ad>` ile kur.", parse_mode="Markdown")
        return
    oyuncular = fdb.takim_oyunculari(takim["takim_id"])
    para = fdb.para_getir(user.id)
    guc = round(fdb.takim_gucu(takim["takim_id"], takim.get("taktik", "4-4-2")), 1)
    sakatlar = fdb.sakatlanan_oyuncular(takim["takim_id"])
    lig_adi = LIG1_ADI if takim["lig"] == 1 else LIG2_ADI
    metin = (
        f"🏟️ *{takim['isim']}*  _{lig_adi}_\n"
        f"{'─'*30}\n"
        f"💰 Bütçe: *{para:,}₺*  |  ⚽ Güç: *{guc}*  |  🎯 Taktik: *{takim.get('taktik','4-4-2')}*\n"
        f"📊 {takim['puan']}P — {takim['galibiyet']}G {takim['beraberlik']}B {takim['maglubiyet']}M — "
        f"{takim['atilan_gol']}:{takim['yenilen_gol']}\n"
        f"👥 Kadro: *{len(oyuncular)}/23*"
    )
    if sakatlar:
        metin += f"  |  🏥 Sakatlar: *{len(sakatlar)}*"
    metin += f"\n{'─'*30}\n"
    if oyuncular:
        sira = {"Kaleci": 0, "Defans": 1, "Orta Saha": 2, "Forvet": 3}
        for o in sorted(oyuncular, key=lambda x: (sira.get(x["pozisyon"], 9), -x["guc"])):
            durum = ""
            if o.get("sakatlik_bitis") and o["sakatlik_bitis"] > __import__("datetime").date.today().isoformat():
                durum = " 🏥"
            elif o.get("satista"):
                durum = f" 🔖{o['satis_fiyati']:,}₺"
            genc = " 🌱" if o.get("genc") else ""
            metin += (
                f"{POZ_EMOJI.get(o['pozisyon'],'⚽')} [{o['oyuncu_id']}] "
                f"*{o['isim']}*{genc} — {o['pozisyon']} | G:{o['guc']}"
                f" | ⚽{o.get('gol',0)} 🅰️{o.get('asist',0)}{durum}\n"
            )
    else:
        metin += "_Kadronuzda henüz oyuncu yok._\n"
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Piyasa", callback_data="piyasa_0"),
        InlineKeyboardButton("🏋️ Antrenman", callback_data="antrenman"),
        InlineKeyboardButton("⚽ Maç", callback_data="mac_oyna"),
    ], [
        InlineKeyboardButton("🎯 Taktik", callback_data="taktik_menu"),
        InlineKeyboardButton("📊 İstatistik", callback_data="istatistik"),
        InlineKeyboardButton("🌱 Altyapı", callback_data="altyapi"),
    ]])
    await _gonder(update, metin, markup=markup)


async def cmd_piyasa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sayfa = 0
    if context.args:
        try:
            sayfa = max(0, int(context.args[0]) - 1)
        except ValueError:
            pass
    await _piyasa_goster(update, sayfa)


async def _piyasa_goster(update: Update, sayfa: int):
    oyuncular, toplam = fdb.piyasa(sayfa)
    if not oyuncular:
        await _gonder(update, "🛒 Piyasada şu an oyuncu yok.")
        return
    metin = f"🛒 *Transfer Piyasası* ({toplam} oyuncu)\n{'─'*32}\n"
    for o in oyuncular:
        durum = "🔓 Serbest" if not o["takim_id"] else "🏟️ Transfer"
        genc = " 🌱" if o.get("genc") else ""
        metin += (
            f"{POZ_EMOJI.get(o['pozisyon'],'⚽')} `[{o['oyuncu_id']}]` "
            f"*{o['isim']}*{genc} — {o['pozisyon']}\n"
            f"   Güç:{o['guc']} | 💰{o['satis_fiyati']:,}₺ | {durum}\n"
        )
    metin += "\n_Satın almak için: `/satin_al <ID>`_"
    await _gonder(update, metin, markup=_piyasa_markup(sayfa, toplam))


async def cmd_satin_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await update.message.reply_text("❌ Önce `/takim_kur` ile takım kur.", parse_mode="Markdown")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Kullanım: `/satin_al <oyuncu_id>`", parse_mode="Markdown")
        return
    basari, mesaj = fdb.satin_al(user.id, takim["takim_id"], int(context.args[0]))
    para = fdb.para_getir(user.id)
    await update.message.reply_text(f"{mesaj}\n💰 Kalan: *{para:,}₺*", parse_mode="Markdown")


async def cmd_sat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await update.message.reply_text("❌ Takımın yok.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Kullanım: `/sat <oyuncu_id> <fiyat>`", parse_mode="Markdown")
        return
    try:
        oid, fiyat = int(context.args[0]), int(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Geçersiz değerler.")
        return
    basari, mesaj = fdb.sat(takim["takim_id"], oid, fiyat)
    await update.message.reply_text(mesaj, parse_mode="Markdown")


async def cmd_sat_iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await update.message.reply_text("❌ Takımın yok.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Kullanım: `/sat_iptal <oyuncu_id>`", parse_mode="Markdown")
        return
    basari, mesaj = fdb.sat_iptal(takim["takim_id"], int(context.args[0]))
    await update.message.reply_text(mesaj, parse_mode="Markdown")


async def cmd_antrenman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok.")
        return
    basari, sonuc = fdb.antrenman_yap(takim["takim_id"])
    if not basari:
        await _gonder(update, f"⚠️ {sonuc}")
        return
    metin = f"🏋️ *Antrenman — {takim['isim']}*\n{'─'*30}\n"
    for o in sonuc:
        genc_tag = " 🌱(+bonus)" if o["genc"] else ""
        metin += f"{POZ_EMOJI.get(o['pozisyon'],'⚽')} *{o['isim']}*{genc_tag} → Güç: +{o['artis']} = **{o['yeni_guc']}**\n"
    metin += "\n_Yarın tekrar antrenman yapabilirsin!_"
    await _gonder(update, metin)


async def cmd_mac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok. `/takim_kur <Ad>` ile kur.", parse_mode="Markdown")
        return
    lig = takim["lig"]
    if not fdb.fikstur_var_mi(lig):
        sayi = fdb.takim_sayisi(lig)
        limit = LIG1_LIMIT if lig == 1 else LIG2_LIMIT
        kalan = limit - sayi
        await _gonder(
            update,
            f"⏳ Fikstür henüz oluşturulmadı.\n"
            f"*{kalan}* takım daha gerekiyor. (Şu an: {sayi}/{limit})",
            parse_mode="Markdown",
        )
        return
    yeterli, neden = fdb.yeterli_kadro_mu(takim["takim_id"])
    if not yeterli:
        await _gonder(update, f"❌ {neden}")
        return
    mac = fdb.sonraki_mac(takim["takim_id"])
    if not mac:
        await _gonder(update, "🎉 Sezon bitti! Tüm maçlarını oynadın.")
        return
    ev_t = fdb.takim_id(mac["ev_takim_id"])
    dep_t = fdb.takim_id(mac["dep_takim_id"])
    ev_guc = round(fdb.takim_gucu(mac["ev_takim_id"]), 1)
    dep_guc = round(fdb.takim_gucu(mac["dep_takim_id"]), 1)
    lig_adi = LIG1_ADI if lig == 1 else LIG2_ADI
    metin = (
        f"⚽ *{lig_adi} — {mac['hafta']}. Hafta*\n"
        f"{'─'*30}\n"
        f"🏠 *{ev_t['isim']}* (Güç:{ev_guc}) 🎯{ev_t.get('taktik','4-4-2')}\n"
        f"✈️ *{dep_t['isim']}* (Güç:{dep_guc}) 🎯{dep_t.get('taktik','4-4-2')}\n\n"
        f"Maçı oynamaya hazır mısın?"
    )
    # Bahis butonu ekle
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚽ MAÇI BAŞLAT!", callback_data=f"mac_bas_{mac['mac_id']}"),
    ], [
        InlineKeyboardButton(f"💰 {ev_t['isim']}'e Bahis", callback_data=f"bahis_{mac['mac_id']}_{mac['ev_takim_id']}"),
        InlineKeyboardButton(f"💰 {dep_t['isim']}'e Bahis", callback_data=f"bahis_{mac['mac_id']}_{mac['dep_takim_id']}"),
    ], [
        InlineKeyboardButton("❌ Vazgeç", callback_data="futbol_iptal"),
    ]])
    await _gonder(update, metin, markup=markup)


async def cmd_lig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lig = 1
    if context.args and context.args[0] == "2":
        lig = 2
    await _lig_goster(update, lig)


async def _lig_goster(update: Update, lig: int):
    takimlar = fdb.tum_takimlar(lig)
    lig_adi = LIG1_ADI if lig == 1 else LIG2_ADI
    diger_lig = 2 if lig == 1 else 1
    if not takimlar:
        await _gonder(update, f"{lig_adi}\n\nHenüz takım yok.")
        return
    metin = f"{lig_adi}\n{'═'*30}\n"
    metin += f"`{'#':<3} {'Takım':<15} {'O':>2} {'G':>2} {'B':>2} {'M':>2} {'AG':>3} {'YG':>3} {'P':>3}`\n"
    metin += f"`{'─'*30}`\n"
    rozetler = ["🥇", "🥈", "🥉"]
    for i, t in enumerate(takimlar):
        rozet = rozetler[i] if i < 3 else f"{i+1:>2}."
        isim = t["isim"][:12]
        metin += (
            f"{rozet} `{isim:<12} {t['mac_sayisi']:>2} {t['galibiyet']:>2} "
            f"{t['beraberlik']:>2} {t['maglubiyet']:>2} {t['atilan_gol']:>3} "
            f"{t['yenilen_gol']:>3} {t['puan']:>3}`\n"
        )
    limit = LIG1_LIMIT if lig == 1 else LIG2_LIMIT
    if not fdb.fikstur_var_mi(lig):
        kalan = limit - len(takimlar)
        metin += f"\n⏳ Lig başlaması için *{kalan}* takım daha gerekli."
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Yenile", callback_data=f"lig_tab_{lig}"),
        InlineKeyboardButton("📅 Fikstür", callback_data=f"fikstur_goster_{lig}"),
        InlineKeyboardButton(f"{'🥈' if lig==1 else '🏆'} {diger_lig}. Lig", callback_data=f"lig_tab_{diger_lig}"),
    ]])
    await _gonder(update, metin, markup=markup)


async def cmd_son_maclar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok.")
        return
    maclar = fdb.son_maclar(takim["takim_id"])
    if not maclar:
        await _gonder(update, "📋 Henüz maç oynamadın.")
        return
    metin = f"📋 *{takim['isim']} — Son 5 Maç*\n{'─'*30}\n"
    for m in maclar:
        kendi = m["ev_takim_id"] == takim["takim_id"]
        kg = m["ev_gol"] if kendi else m["dep_gol"]
        rg = m["dep_gol"] if kendi else m["ev_gol"]
        rakip = m["dep_isim"] if kendi else m["ev_isim"]
        yer = "🏠" if kendi else "✈️"
        sem = "✅" if kg > rg else ("🟡" if kg == rg else "❌")
        metin += f"{sem} {yer} {kg}–{rg} vs *{rakip}* _(Hf.{m['hafta']})_\n"
    await _gonder(update, metin)


async def cmd_fikstur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    lig = takim["lig"] if takim else 1
    hafta = fdb.mevcut_hafta(lig)
    await _fikstur_goster(update, hafta, lig)


async def _fikstur_goster(update: Update, hafta: int, lig: int = 1):
    maclar = fdb.haftalik_fikstur(hafta, lig)
    lig_adi = LIG1_ADI if lig == 1 else LIG2_ADI
    if not maclar:
        await _gonder(update, f"📅 {hafta}. haftada maç yok.")
        return
    metin = f"📅 *{lig_adi}*\n*{hafta}. Hafta*\n{'─'*30}\n"
    for m in maclar:
        if m["oynanmis"]:
            skor = f"*{m['ev_gol']}–{m['dep_gol']}*"
            ikon = "✅"
        else:
            skor = "vs"
            ikon = "⏳"
        metin += f"{ikon} {m['ev_isim']} {skor} {m['dep_isim']}\n"
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️", callback_data=f"fikstur_{max(1,hafta-1)}_{lig}"),
        InlineKeyboardButton(f"Hafta {hafta}", callback_data="noop"),
        InlineKeyboardButton("▶️", callback_data=f"fikstur_{hafta+1}_{lig}"),
    ]])
    await _gonder(update, metin, markup=markup)


async def cmd_cuzdan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    para = fdb.para_getir(user.id)
    takim = fdb.takim_user(user.id)
    tb = f"🏟️ *{takim['isim']}*\n" if takim else "🏟️ Takımın yok.\n"
    await _gonder(
        update,
        f"💰 *Cüzdan — {user.first_name}*\n{'─'*28}\n"
        f"{tb}"
        f"💵 Bakiye: *{para:,}₺*\n\n"
        f"_Galibiyet: +5.000₺ | Beraberlik: +2.500₺ | Mağlubiyet: +1.000₺_",
        parse_mode="Markdown",
    )


async def cmd_spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    odul, toplam = fdb.spin_cevir(user.id)
    if odul is None:
        await _gonder(update, f"🎰 {toplam}")
        return
    await _gonder(
        update,
        f"🎰 *Şans Çarkı*\n{'─'*28}\n"
        f"Çark dönüyor...\n\n"
        f"🎊 *Tebrikler!* {odul[0]} kazandın!\n"
        f"📊 Toplam spin: {toplam}",
        parse_mode="Markdown",
    )


async def cmd_istatistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok.")
        return
    oyuncular = fdb.oyuncu_istatistikleri(takim["takim_id"])
    if not oyuncular:
        await _gonder(update, "📊 Henüz istatistik yok.")
        return
    metin = f"📊 *{takim['isim']} — Oyuncu İstatistikleri*\n{'─'*30}\n"
    for o in oyuncular[:15]:
        g = o.get("gol", 0)
        a = o.get("asist", 0)
        sk = o.get("sari_kart", 0)
        kk = o.get("kirmizi_kart", 0)
        if g == 0 and a == 0:
            continue
        metin += (
            f"{POZ_EMOJI.get(o['pozisyon'],'⚽')} *{o['isim']}*\n"
            f"  ⚽{g} gol  🅰️{a} asist  🟡{sk}  🔴{kk}\n"
        )
    await _gonder(update, metin)


async def cmd_golcular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    golcular = fdb.sezon_golculeri()
    if not golcular:
        await _gonder(update, "⚽ Henüz gol yok.")
        return
    metin = "⚽ *Sezon Golcü Sıralaması*\n{'─'*30}\n"
    for i, g in enumerate(golcular):
        lig_tag = "🏆" if g["lig"] == 1 else "🥈"
        metin += f"{i+1}. {lig_tag} *{g['isim']}* ({g['takim_isim']}) — {g['gol']} gol, {g['asist']} asist\n"
    await _gonder(update, metin)


async def cmd_taktik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok.")
        return
    if context.args:
        taktik = context.args[0]
        if fdb.taktik_sec(takim["takim_id"], taktik):
            h, d, aciklama = TAKTIKLER[taktik]
            await _gonder(update,
                f"✅ Taktik *{taktik}* seçildi!\n_{aciklama}_\n"
                f"Hücum: x{h} | Defans: x{d}", parse_mode="Markdown")
        else:
            await _gonder(update, f"❌ Geçersiz taktik. Seçenekler: {', '.join(TAKTIKLER.keys())}")
        return
    await _taktik_menu_goster(update, takim)


async def _taktik_menu_goster(update: Update, takim: dict):
    mevcut = takim.get("taktik", "4-4-2")
    metin = f"🎯 *Taktik Seçimi — {takim['isim']}*\nMevcut: *{mevcut}*\n{'─'*28}\n"
    for isim, (h, d, acik) in TAKTIKLER.items():
        check = "✅" if isim == mevcut else "  "
        metin += f"{check} *{isim}* — {acik} (Hücum:x{h} Def:x{d})\n"
    satirlar = []
    for isim in TAKTIKLER:
        satirlar.append([InlineKeyboardButton(
            f"{'✅ ' if isim == mevcut else ''}{isim}",
            callback_data=f"taktik_sec_{isim}"
        )])
    await _gonder(update, metin, markup=InlineKeyboardMarkup(satirlar))


async def cmd_altyapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    if not takim:
        await _gonder(update, "❌ Takımın yok.")
        return
    oyuncu, hata = fdb.altyapi_cikart(takim["takim_id"], user.id)
    if hata:
        await _gonder(update, f"❌ {hata}")
        return
    await _gonder(
        update,
        f"🌱 *Altyapı Oyuncusu Bulundu!*\n{'─'*28}\n"
        f"*{oyuncu['isim']}* — {oyuncu['pozisyon']}\n"
        f"Güç: {oyuncu['guc']} | Değer: {oyuncu['deger']:,}₺\n"
        f"_(Gençler antrenmanla daha hızlı gelişir!)_",
        parse_mode="Markdown",
    )


async def cmd_basarilar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    basarilar = fdb.kullanici_basarilari(user.id)
    if not basarilar:
        await _gonder(update, "🏅 Henüz başarı kazanmadın. Oyna ve kazan!")
        return
    metin = f"🏅 *{user.first_name} — Başarılar*\n{'─'*28}\n"
    for b in basarilar:
        kod = b["basari_kodu"]
        if kod in BASARILAR:
            emoji_isim, aciklama = BASARILAR[kod]
            metin += f"🏆 *{emoji_isim}*\n   _{aciklama}_ ({b['tarih']})\n"
    await _gonder(update, metin)


async def cmd_kupa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    takim = fdb.takim_user(user.id)
    mac = fdb.kupa_sonraki_mac(user.id)
    if not mac:
        await _gonder(update,
            "🏅 Cumhuriyet Kupası'nda aktif maçın yok.\n"
            "Admin `/kupa_olustur` komutu ile kupayı başlatabilir."
        )
        return
    ev_t = fdb.takim_id(mac["ev_takim_id"])
    dep_t = fdb.takim_id(mac["dep_takim_id"])
    tur_adi = TUR_ADLARI.get(mac["tur"], f"Tur {mac['tur']}")
    metin = (
        f"🏅 *Cumhuriyet Kupası — {tur_adi}*\n{'─'*30}\n"
        f"🏠 *{ev_t['isim']}*\nvs\n✈️ *{dep_t['isim']}*\n\n"
        f"Kupada sahaya çık!"
    )
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚽ KUPA MAÇINI BAŞLAT!", callback_data=f"kupa_bas_{mac['mac_id']}"),
        InlineKeyboardButton("❌ Vazgeç", callback_data="futbol_iptal"),
    ]])
    await _gonder(update, metin, markup=markup)


async def cmd_kupa_tablo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    maclar = fdb.kupa_tablo()
    if not maclar:
        await _gonder(update, "🏅 Kupa oluşturulmadı.")
        return
    by_tur = {}
    for m in maclar:
        by_tur.setdefault(m["tur"], []).append(m)
    metin = "🏅 *Cumhuriyet Kupası Sonuçları*\n"
    for tur, lst in sorted(by_tur.items()):
        tur_adi = TUR_ADLARI.get(tur, f"Tur {tur}")
        metin += f"\n*— {tur_adi} —*\n"
        for m in lst:
            if m["oynanmis"] and m["dep_isim"]:
                metin += f"  ✅ {m['ev_isim']} {m['ev_gol']}–{m['dep_gol']} {m['dep_isim']}\n"
            elif m["dep_isim"]:
                metin += f"  ⏳ {m['ev_isim']} vs {m['dep_isim']}\n"
    await _gonder(update, metin)


# ══════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ══════════════════════════════════════════════════════════

async def futbol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    data = query.data

    # Piyasa
    if data.startswith("piyasa_"):
        await query.answer()
        if data == "piyasa_noop":
            return True
        await _piyasa_goster(update, int(data.split("_")[1]))
        return True

    # Lig tablosu
    if data.startswith("lig_tab_"):
        await query.answer()
        lig = int(data.split("_")[2])
        await _lig_goster(update, lig)
        return True

    # Antrenman
    if data == "antrenman":
        await query.answer()
        await cmd_antrenman(update, context)
        return True

    # Altyapı
    if data == "altyapi":
        await query.answer()
        await cmd_altyapi(update, context)
        return True

    # Taktik menü
    if data == "taktik_menu":
        await query.answer()
        user = update.effective_user
        takim = fdb.takim_user(user.id)
        if takim:
            await _taktik_menu_goster(update, takim)
        return True

    if data.startswith("taktik_sec_"):
        await query.answer()
        taktik = data.replace("taktik_sec_", "")
        user = update.effective_user
        takim = fdb.takim_user(user.id)
        if takim and fdb.taktik_sec(takim["takim_id"], taktik):
            h, d, aciklama = TAKTIKLER[taktik]
            await query.edit_message_text(
                f"✅ Taktik *{taktik}* seçildi!\n_{aciklama}_\nHücum: x{h} | Defans: x{d}",
                parse_mode="Markdown"
            )
        return True

    # İstatistik
    if data == "istatistik":
        await query.answer()
        await cmd_istatistik(update, context)
        return True

    # Maç oyna
    if data == "mac_oyna":
        await query.answer()
        await cmd_mac(update, context)
        return True

    # Maç başlat
    if data.startswith("mac_bas_"):
        await query.answer("⚽ Maç başlıyor...")
        mac_id = int(data.split("_")[2])
        user = update.effective_user
        takim = fdb.takim_user(user.id)
        if not takim:
            await query.edit_message_text("❌ Takımın yok.")
            return True
        sonuc, hata = fdb.mac_oyna(mac_id, takim["takim_id"])
        if hata:
            await query.edit_message_text(f"⚠️ {hata}")
            return True
        metin = _mac_raporu_mesaj(sonuc, user.id)
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Lig Tablosu", callback_data=f"lig_tab_{sonuc.get('lig',1)}"),
            InlineKeyboardButton("👥 Takımım", callback_data="takim_bilgi"),
        ]])
        await query.edit_message_text(metin, parse_mode="Markdown", reply_markup=markup)
        # Grup bildirimi
        await _grup_bildir_mac(context, sonuc)
        # Rakibe özel bildirim
        rakip_user = sonuc["dep_takim_user"] if sonuc["ev_takim_user"] == user.id else sonuc["ev_takim_user"]
        await _ozel_bildirim(context, rakip_user, sonuc, user.id)
        return True

    # Bahis
    if data.startswith("bahis_"):
        parts = data.split("_")
        mac_id, hedef_id = int(parts[1]), int(parts[2])
        await query.answer()
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("500₺", callback_data=f"bahis_oyna_{mac_id}_{hedef_id}_500"),
            InlineKeyboardButton("1.000₺", callback_data=f"bahis_oyna_{mac_id}_{hedef_id}_1000"),
            InlineKeyboardButton("2.500₺", callback_data=f"bahis_oyna_{mac_id}_{hedef_id}_2500"),
            InlineKeyboardButton("5.000₺", callback_data=f"bahis_oyna_{mac_id}_{hedef_id}_5000"),
        ]])
        t = fdb.takim_id(hedef_id)
        await query.edit_message_text(
            f"💰 *{t['isim']}* kazanacak diye bahis yap!\nKazanırsan 2x ödeme alırsın.\nMiktar seç:",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return True

    if data.startswith("bahis_oyna_"):
        parts = data.split("_")
        mac_id, hedef_id, miktar = int(parts[2]), int(parts[3]), int(parts[4])
        user = update.effective_user
        await query.answer()
        basari, mesaj = fdb.bahis_yap(user.id, mac_id, hedef_id, miktar)
        await query.edit_message_text(mesaj, parse_mode="Markdown")
        return True

    # Kupa maç başlat
    if data.startswith("kupa_bas_"):
        await query.answer("🏅 Kupa maçı başlıyor!")
        mac_id = int(data.split("_")[2])
        user = update.effective_user
        takim = fdb.takim_user(user.id)
        if not takim:
            await query.edit_message_text("❌ Takımın yok.")
            return True
        sonuc, hata = fdb.kupa_mac_oyna(mac_id, takim["takim_id"])
        if hata:
            await query.edit_message_text(f"⚠️ {hata}")
            return True
        tur_adi = TUR_ADLARI.get(sonuc["tur"], f"Tur {sonuc['tur']}")
        uzatma_txt = " (Uzatmalar)" if sonuc.get("uzatma") else ""
        metin = (
            f"🏅 *Cumhuriyet Kupası — {tur_adi}*\n{'═'*30}\n"
            f"🏠 *{sonuc['ev_takim']}* {sonuc['ev_gol']} – {sonuc['dep_gol']} *{sonuc['dep_takim']}* ✈️"
            f"{uzatma_txt}\n"
            f"🏆 *{sonuc['kazanan_isim']}* bir üst tura geçti!\n"
        )
        if sonuc.get("sampiyon"):
            metin += (
                f"\n🎊🎊 *KUPA ŞAMPİYONU: {sonuc['sampiyon']['isim']}!* 🎊🎊\n"
                f"💰 +50.000₺ Şampiyonluk ödülü kazandı!\n🏅 Kupa Şampiyonu rozeti verildi!"
            )
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏅 Kupa Tablosu", callback_data="kupa_tablo"),
            InlineKeyboardButton("👥 Takımım", callback_data="takim_bilgi"),
        ]])
        await query.edit_message_text(metin, parse_mode="Markdown", reply_markup=markup)
        await _grup_bildir_kupa(context, sonuc)
        return True

    if data == "kupa_tablo":
        await query.answer()
        await cmd_kupa_tablo(update, context)
        return True

    # Takım bilgisi
    if data == "takim_bilgi":
        await query.answer()
        await cmd_takim(update, context)
        return True

    # Fikstür
    if data == "fikstur_goster":
        await query.answer()
        user = update.effective_user
        takim = fdb.takim_user(user.id)
        lig = takim["lig"] if takim else 1
        hafta = fdb.mevcut_hafta(lig)
        await _fikstur_goster(update, hafta, lig)
        return True

    if data.startswith("fikstur_goster_"):
        await query.answer()
        lig = int(data.split("_")[2])
        hafta = fdb.mevcut_hafta(lig)
        await _fikstur_goster(update, hafta, lig)
        return True

    if data.startswith("fikstur_"):
        await query.answer()
        parts = data.split("_")
        hafta = int(parts[1])
        lig = int(parts[2]) if len(parts) > 2 else 1
        await _fikstur_goster(update, hafta, lig)
        return True

    # İptal
    if data == "futbol_iptal":
        await query.answer("İptal edildi.")
        await query.edit_message_text("❌ İptal edildi.")
        return True

    return False


# ══════════════════════════════════════════════════════════
#  BİLDİRİM FONKSİYONLARI
# ══════════════════════════════════════════════════════════

async def _ozel_bildirim(context, rakip_user_id: int, sonuc: dict, oynayan_user_id: int):
    """Rakibe özel DM bildirimi gönder"""
    try:
        ev_kazandi = sonuc["ev_gol"] > sonuc["dep_gol"]
        dep_kazandi = sonuc["dep_gol"] > sonuc["ev_gol"]
        rakip_kazandi = (
            (ev_kazandi and sonuc["dep_takim_user"] == oynayan_user_id) or
            (dep_kazandi and sonuc["ev_takim_user"] == oynayan_user_id)
        )
        if rakip_kazandi:
            metin = (
                f"🔔 *Dikkat! Rakibin seni geçti!*\n"
                f"*{sonuc['ev_takim']}* {sonuc['ev_gol']}–{sonuc['dep_gol']} *{sonuc['dep_takim']}*\n"
                f"Lig tablosunda geride kalmamak için maçını oyna! ⚽"
            )
        else:
            metin = (
                f"⚽ *Maç Sonucu*\n"
                f"*{sonuc['ev_takim']}* {sonuc['ev_gol']}–{sonuc['dep_gol']} *{sonuc['dep_takim']}*\n"
                f"_(Hafta {sonuc['hafta']})_"
            )
        await context.bot.send_message(
            chat_id=rakip_user_id,
            text=metin,
            parse_mode="Markdown"
        )
    except Exception:
        pass


async def _grup_bildir_mac(context, sonuc: dict):
    """Kayıtlı gruplara maç sonucu bildir"""
    gruplar = fdb.gruplari_getir()
    if not gruplar:
        return
    metin = (
        f"⚽ *Maç Sonucu — Hafta {sonuc['hafta']}*\n"
        f"*{sonuc['ev_takim']}* {sonuc['ev_gol']} – {sonuc['dep_gol']} *{sonuc['dep_takim']}*\n"
    )
    if sonuc["ev_gol"] > sonuc["dep_gol"]:
        metin += f"🟢 {sonuc['ev_takim']} kazandı!"
    elif sonuc["dep_gol"] > sonuc["ev_gol"]:
        metin += f"🔵 {sonuc['dep_takim']} kazandı!"
    else:
        metin += "🟡 Berabere!"
    for cid in gruplar:
        try:
            await context.bot.send_message(chat_id=cid, text=metin, parse_mode="Markdown")
        except Exception:
            pass


async def _grup_bildir_kupa(context, sonuc: dict):
    gruplar = fdb.gruplari_getir()
    if not gruplar:
        return
    tur_adi = TUR_ADLARI.get(sonuc["tur"], f"Tur {sonuc['tur']}")
    metin = (
        f"🏅 *Cumhuriyet Kupası — {tur_adi}*\n"
        f"*{sonuc['ev_takim']}* {sonuc['ev_gol']}–{sonuc['dep_gol']} *{sonuc['dep_takim']}*\n"
        f"🏆 *{sonuc['kazanan_isim']}* bir üst tura geçti!"
    )
    if sonuc.get("sampiyon"):
        metin += f"\n\n🎊 *KUPA ŞAMPİYONU: {sonuc['sampiyon']['isim']}!* 🎊"
    for cid in gruplar:
        try:
            await context.bot.send_message(chat_id=cid, text=metin, parse_mode="Markdown")
        except Exception:
            pass
