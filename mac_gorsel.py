"""
mac_gorsel.py — 2D Üstten Görünüm Maç Görseli
Pillow kullanarak top-down futbol sahası ve maç olayları render eder.
"""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import random
import math
import os

# ─── Renkler ───────────────────────────────────────────────────────────────
C_FIELD       = (34, 139, 34)        # koyu yeşil
C_FIELD_DARK  = (28, 120, 28)        # çizgi arası koyu şerit
C_LINE        = (255, 255, 255)      # çizgiler
C_CENTER      = (255, 255, 255, 120)
C_BALL        = (255, 220, 50)
C_SHADOW      = (0, 0, 0, 80)
C_BLACK       = (0, 0, 0)
C_WHITE       = (255, 255, 255)
C_YELLOW_CARD = (255, 220, 0)
C_RED_CARD    = (220, 30, 30)
C_GOAL_FLASH  = (255, 255, 100, 180)

TAKIM_RENKLER = [
    ((220, 50, 50),   (255,255,255)),   # kırmızı / beyaz
    ((30, 80, 200),   (255,255,255)),   # mavi / beyaz
    ((20, 150, 80),   (255,255,255)),   # yeşil / beyaz
    ((180, 130, 20),  (255,255,255)),   # sarı / beyaz
    ((120, 20, 200),  (255,255,255)),   # mor / beyaz
    ((200, 80, 20),   (255,255,255)),   # turuncu / beyaz
    ((20, 150, 180),  (0, 0, 0)),       # turkuaz / siyah
    ((50, 50, 50),    (255,255,255)),   # siyah / beyaz
    ((200, 20, 120),  (255,255,255)),   # pembe / beyaz
    ((100, 170, 40),  (255,255,255)),   # açık yeşil / beyaz
]

# ─── Boyutlar ──────────────────────────────────────────────────────────────
W, H        = 800, 560
MARGIN      = 40
FIELD_X0    = MARGIN
FIELD_Y0    = MARGIN + 60        # üst skorbord alanı
FIELD_X1    = W - MARGIN
FIELD_Y1    = H - MARGIN - 20
FW          = FIELD_X1 - FIELD_X0
FH          = FIELD_Y1 - FIELD_Y0
CENTER_X    = FIELD_X0 + FW // 2
CENTER_Y    = FIELD_Y0 + FH // 2

# Kale boyutları (saha koordinatları)
KALE_W_ORAN = 0.15   # sahaya göre genişlik
KALE_D_ORAN = 0.04   # derinlik

# ─── Yazı tipi ─────────────────────────────────────────────────────────────
def _font(size: int):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

# ─── Çizgi yardımcıları ─────────────────────────────────────────────────────
def _cx(x_oran: float) -> int:
    return int(FIELD_X0 + x_oran * FW)

def _cy(y_oran: float) -> int:
    return int(FIELD_Y0 + y_oran * FH)


# ─── Saha çiz ───────────────────────────────────────────────────────────────
def _saha_ciz(draw: ImageDraw.Draw):
    # Şeritli zemin
    serit_genislik = FW // 10
    for i in range(10):
        x = FIELD_X0 + i * serit_genislik
        renk = C_FIELD if i % 2 == 0 else C_FIELD_DARK
        draw.rectangle([x, FIELD_Y0, x + serit_genislik, FIELD_Y1], fill=renk)

    # Saha dış çizgisi
    draw.rectangle([FIELD_X0, FIELD_Y0, FIELD_X1, FIELD_Y1], outline=C_LINE, width=3)

    # Orta çizgi
    draw.line([CENTER_X, FIELD_Y0, CENTER_X, FIELD_Y1], fill=C_LINE, width=2)

    # Orta daire
    r = int(FH * 0.12)
    draw.ellipse([CENTER_X - r, CENTER_Y - r, CENTER_X + r, CENTER_Y + r],
                 outline=C_LINE, width=2)
    draw.ellipse([CENTER_X - 4, CENTER_Y - 4, CENTER_X + 4, CENTER_Y + 4],
                 fill=C_LINE)

    # Sol ceza sahası
    cs_w = int(FW * 0.15)
    cs_h = int(FH * 0.45)
    cs_y0 = CENTER_Y - cs_h // 2
    draw.rectangle([FIELD_X0, cs_y0, FIELD_X0 + cs_w, cs_y0 + cs_h],
                   outline=C_LINE, width=2)
    # Sol küçük ceza
    kcs_w = int(FW * 0.06)
    kcs_h = int(FH * 0.22)
    kcs_y0 = CENTER_Y - kcs_h // 2
    draw.rectangle([FIELD_X0, kcs_y0, FIELD_X0 + kcs_w, kcs_y0 + kcs_h],
                   outline=C_LINE, width=2)
    # Sol kale
    kale_h = int(FH * 0.14)
    kale_y0 = CENTER_Y - kale_h // 2
    draw.rectangle([FIELD_X0 - 14, kale_y0, FIELD_X0, kale_y0 + kale_h],
                   outline=C_LINE, width=2, fill=(20, 100, 20))

    # Sağ ceza sahası
    draw.rectangle([FIELD_X1 - cs_w, cs_y0, FIELD_X1, cs_y0 + cs_h],
                   outline=C_LINE, width=2)
    draw.rectangle([FIELD_X1 - kcs_w, kcs_y0, FIELD_X1, kcs_y0 + kcs_h],
                   outline=C_LINE, width=2)
    draw.rectangle([FIELD_X1, kale_y0, FIELD_X1 + 14, kale_y0 + kale_h],
                   outline=C_LINE, width=2, fill=(20, 100, 20))

    # Köşe yayları
    _kose_yay(draw, FIELD_X0, FIELD_Y0, "sol_ust")
    _kose_yay(draw, FIELD_X0, FIELD_Y1, "sol_alt")
    _kose_yay(draw, FIELD_X1, FIELD_Y0, "sag_ust")
    _kose_yay(draw, FIELD_X1, FIELD_Y1, "sag_alt")

    # Penaltı noktaları
    pen_x_sol = FIELD_X0 + int(FW * 0.10)
    pen_x_sag = FIELD_X1 - int(FW * 0.10)
    draw.ellipse([pen_x_sol - 4, CENTER_Y - 4, pen_x_sol + 4, CENTER_Y + 4], fill=C_LINE)
    draw.ellipse([pen_x_sag - 4, CENTER_Y - 4, pen_x_sag + 4, CENTER_Y + 4], fill=C_LINE)


def _kose_yay(draw, x, y, konum):
    r = 20
    if konum == "sol_ust":
        bb = [x - r, y - r, x + r, y + r]
        draw.arc(bb, start=0, end=90, fill=C_LINE, width=2)
    elif konum == "sol_alt":
        bb = [x - r, y - r, x + r, y + r]
        draw.arc(bb, start=270, end=360, fill=C_LINE, width=2)
    elif konum == "sag_ust":
        bb = [x - r, y - r, x + r, y + r]
        draw.arc(bb, start=90, end=180, fill=C_LINE, width=2)
    elif konum == "sag_alt":
        bb = [x - r, y - r, x + r, y + r]
        draw.arc(bb, start=180, end=270, fill=C_LINE, width=2)


# ─── Top çiz ────────────────────────────────────────────────────────────────
def _top_ciz(draw: ImageDraw.Draw, x: int, y: int):
    r = 9
    draw.ellipse([x - r - 2, y - r - 2, x + r + 2, y + r + 2],
                 fill=(0, 0, 0, 120))
    draw.ellipse([x - r, y - r, x + r, y + r], fill=C_BALL, outline=(180, 160, 0), width=2)
    # Pentagon deseni
    draw.line([x - 3, y - 5, x + 3, y - 5], fill=(50, 50, 50), width=2)
    draw.line([x - 6, y + 2, x + 6, y + 2], fill=(50, 50, 50), width=2)


# ─── Oyuncu nokta çiz ───────────────────────────────────────────────────────
def _oyuncu_ciz(draw: ImageDraw.Draw, x: int, y: int,
                renk, yazi_renk, kisaltma: str, font_small):
    r = 14
    # Gölge
    draw.ellipse([x - r + 2, y - r + 2, x + r + 2, y + r + 2],
                 fill=(0, 0, 0, 80))
    # Daire
    draw.ellipse([x - r, y - r, x + r, y + r], fill=renk, outline=C_WHITE, width=2)
    # İsim kısaltması
    draw.text((x, y), kisaltma[:2].upper(), font=font_small,
              fill=yazi_renk, anchor="mm")


# ─── Formasyon pozisyonları ─────────────────────────────────────────────────
def _formasyon_pozisyonlari(taktik: str, sol_mu: bool, oyuncu_sayisi: int):
    """
    Taktike göre sahada oyuncu x/y oranları döndürür.
    sol_mu=True → sol yarı (ev sahibi), False → sağ yarı (deplasman).
    """
    # 4-4-2 default
    FORMASYONLAR = {
        "4-3-3":  [(0.08, 0.5),
                   (0.22, 0.18),(0.22, 0.38),(0.22, 0.62),(0.22, 0.82),
                   (0.38, 0.28),(0.38, 0.5),(0.38, 0.72),
                   (0.52, 0.2),(0.52, 0.5),(0.52, 0.8)],
        "4-4-2":  [(0.08, 0.5),
                   (0.22, 0.18),(0.22, 0.38),(0.22, 0.62),(0.22, 0.82),
                   (0.38, 0.15),(0.38, 0.38),(0.38, 0.62),(0.38, 0.85),
                   (0.52, 0.35),(0.52, 0.65)],
        "5-3-2":  [(0.08, 0.5),
                   (0.2, 0.12),(0.2, 0.3),(0.2, 0.5),(0.2, 0.7),(0.2, 0.88),
                   (0.38, 0.28),(0.38, 0.5),(0.38, 0.72),
                   (0.52, 0.35),(0.52, 0.65)],
        "3-5-2":  [(0.08, 0.5),
                   (0.22, 0.25),(0.22, 0.5),(0.22, 0.75),
                   (0.36, 0.1),(0.36, 0.3),(0.36, 0.5),(0.36, 0.7),(0.36, 0.9),
                   (0.52, 0.35),(0.52, 0.65)],
        "4-2-3-1":[(0.08, 0.5),
                   (0.2, 0.18),(0.2, 0.38),(0.2, 0.62),(0.2, 0.82),
                   (0.32, 0.35),(0.32, 0.65),
                   (0.44, 0.2),(0.44, 0.5),(0.44, 0.8),
                   (0.54, 0.5)],
    }
    pozlar = FORMASYONLAR.get(taktik, FORMASYONLAR["4-4-2"])
    # Oyuncu sayısına göre kırp/tamamla
    while len(pozlar) < min(11, oyuncu_sayisi):
        pozlar.append((random.uniform(0.3, 0.5), random.uniform(0.1, 0.9)))
    pozlar = pozlar[:min(11, oyuncu_sayisi)]

    sonuc = []
    for (xo, yo) in pozlar:
        if sol_mu:
            # Sol yarı: 0..0.47 arası
            gx = _cx(xo * 0.47)
            gy = _cy(yo)
        else:
            # Sağ yarı: 0.53..1.0 arası (ayna)
            gx = _cx(1.0 - xo * 0.47)
            gy = _cy(yo)
        sonuc.append((gx, gy))
    return sonuc


# ─── Skor bandı ─────────────────────────────────────────────────────────────
def _skor_bandi(img: Image.Image, draw: ImageDraw.Draw,
                ev_isim: str, dep_isim: str,
                ev_gol: int, dep_gol: int,
                ev_renk, dep_renk,
                hafta: int, dakika: int = 90):
    font_b = _font(26)
    font_s = _font(16)
    font_sk = _font(38)

    # Arka plan bandı
    band_h = 58
    draw.rectangle([0, 0, W, band_h], fill=(15, 15, 15))

    # Ev takımı
    ev_k = ev_isim[:14]
    draw.rectangle([4, 4, 24, 24], fill=ev_renk[0], outline=C_WHITE, width=1)
    draw.text((30, 10), ev_k, font=font_b, fill=ev_renk[0])

    # Deplasman takımı
    dep_k = dep_isim[:14]
    dep_text_w = draw.textlength(dep_k, font=font_b)
    draw.rectangle([W - 28, 4, W - 8, 24], fill=dep_renk[0], outline=C_WHITE, width=1)
    draw.text((W - 34 - dep_text_w, 10), dep_k, font=font_b, fill=dep_renk[0])

    # Skor ortada
    skor = f"{ev_gol}  –  {dep_gol}"
    sk_w = draw.textlength(skor, font=font_sk)
    draw.text((W // 2 - sk_w // 2, 6), skor, font=font_sk, fill=C_WHITE)

    # Hafta & dakika
    alt = f"Hafta {hafta}  •  {dakika}'"
    aw = draw.textlength(alt, font=font_s)
    draw.text((W // 2 - aw // 2, 42), alt, font=font_s, fill=(180, 180, 180))


# ─── Olay şeridi ─────────────────────────────────────────────────────────────
def _olay_seridi(draw: ImageDraw.Draw, olaylar: list):
    font_s = _font(14)
    y = H - 38
    draw.rectangle([0, y - 4, W, H], fill=(15, 15, 15))
    x = 10
    for olay in olaylar[:7]:
        draw.text((x, y), olay, font=font_s, fill=(220, 220, 180))
        x += draw.textlength(olay, font=font_s) + 24
        if x > W - 60:
            break


# ─── Gol flash ───────────────────────────────────────────────────────────────
def _gol_flash(overlay: Image.Image, draw: ImageDraw.Draw, taraf: str):
    """Gol olan tarafta parlama efekti"""
    if taraf == "ev":
        bbox = [FIELD_X0, FIELD_Y0, CENTER_X, FIELD_Y1]
    else:
        bbox = [CENTER_X, FIELD_Y0, FIELD_X1, FIELD_Y1]
    draw.rectangle(bbox, fill=(255, 255, 100, 60))


# ═══════════════════════════════════════════════════════════════════
#  ANA FONKSİYON
# ═══════════════════════════════════════════════════════════════════

def mac_gorsel_olustur(
    ev_takim: str,
    dep_takim: str,
    ev_gol: int,
    dep_gol: int,
    ev_oyuncular: list,   # [{"isim": ..., "pozisyon": ...}, ...]
    dep_oyuncular: list,
    ev_taktik: str = "4-4-2",
    dep_taktik: str = "4-4-2",
    hafta: int = 1,
    olaylar: list = None,
    ev_gol_atanlar: list = None,
    dep_gol_atanlar: list = None,
) -> BytesIO:
    olaylar = olaylar or []
    ev_gol_atanlar = ev_gol_atanlar or []
    dep_gol_atanlar = dep_gol_atanlar or []

    # Renk ata (takım ismine göre deterministik)
    ev_renk_idx  = hash(ev_takim)  % len(TAKIM_RENKLER)
    dep_renk_idx = (hash(dep_takim) + 3) % len(TAKIM_RENKLER)
    if ev_renk_idx == dep_renk_idx:
        dep_renk_idx = (dep_renk_idx + 1) % len(TAKIM_RENKLER)
    ev_renk  = TAKIM_RENKLER[ev_renk_idx]
    dep_renk = TAKIM_RENKLER[dep_renk_idx]

    img  = Image.new("RGB", (W, H), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    # Saha
    _saha_ciz(draw)

    # Gol efekti
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    if ev_gol > dep_gol:
        _gol_flash(overlay, ov_draw, "ev")
    elif dep_gol > ev_gol:
        _gol_flash(overlay, ov_draw, "dep")
    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(overlay)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Oyuncu pozisyonları
    font_kucuk = _font(11)
    font_orta  = _font(13)

    ev_pozlar  = _formasyon_pozisyonlari(ev_taktik,  True,  len(ev_oyuncular))
    dep_pozlar = _formasyon_pozisyonlari(dep_taktik, False, len(dep_oyuncular))

    for i, (gx, gy) in enumerate(ev_pozlar):
        if i < len(ev_oyuncular):
            o = ev_oyuncular[i]
            kisalt = o["isim"].split()[0][:2].upper()
            _oyuncu_ciz(draw, gx, gy, ev_renk[0], ev_renk[1], kisalt, font_kucuk)
            # isim etiketi
            draw.text((gx, gy + 17), o["isim"].split()[0][:8],
                      font=font_kucuk, fill=C_WHITE, anchor="mt",
                      stroke_width=1, stroke_fill=C_BLACK)

    for i, (gx, gy) in enumerate(dep_pozlar):
        if i < len(dep_oyuncular):
            o = dep_oyuncular[i]
            kisalt = o["isim"].split()[0][:2].upper()
            _oyuncu_ciz(draw, gx, gy, dep_renk[0], dep_renk[1], kisalt, font_kucuk)
            draw.text((gx, gy + 17), o["isim"].split()[0][:8],
                      font=font_kucuk, fill=C_WHITE, anchor="mt",
                      stroke_width=1, stroke_fill=C_BLACK)

    # Top: gol olan kaleye yakın, berabere ortada
    if ev_gol > dep_gol:
        top_x = _cx(0.08)
        top_y = CENTER_Y + random.randint(-20, 20)
    elif dep_gol > ev_gol:
        top_x = _cx(0.92)
        top_y = CENTER_Y + random.randint(-20, 20)
    else:
        top_x = CENTER_X + random.randint(-15, 15)
        top_y = CENTER_Y + random.randint(-15, 15)
    _top_ciz(draw, top_x, top_y)

    # Gol ismi etiketleri (son golcüler)
    font_gol = _font(13)
    for isim in ev_gol_atanlar[-2:]:
        gx = _cx(random.uniform(0.04, 0.12))
        gy = _cy(random.uniform(0.3, 0.7))
        draw.text((gx, gy - 22), f"⚽ {isim.split()[0]}", font=font_gol,
                  fill=C_YELLOW_CARD, anchor="mm",
                  stroke_width=1, stroke_fill=C_BLACK)
    for isim in dep_gol_atanlar[-2:]:
        gx = _cx(random.uniform(0.88, 0.96))
        gy = _cy(random.uniform(0.3, 0.7))
        draw.text((gx, gy - 22), f"⚽ {isim.split()[0]}", font=font_gol,
                  fill=C_YELLOW_CARD, anchor="mm",
                  stroke_width=1, stroke_fill=C_BLACK)

    # Kart ikonları
    for olay in olaylar:
        if "sarı kart" in olay:
            isim = olay.split()[1]
            x = random.randint(FIELD_X0 + 20, FIELD_X1 - 20)
            y = random.randint(FIELD_Y0 + 20, FIELD_Y1 - 20)
            draw.rectangle([x, y - 10, x + 8, y + 2], fill=C_YELLOW_CARD)
        elif "kırmızı" in olay:
            x = random.randint(FIELD_X0 + 20, FIELD_X1 - 20)
            y = random.randint(FIELD_Y0 + 20, FIELD_Y1 - 20)
            draw.rectangle([x, y - 10, x + 8, y + 2], fill=C_RED_CARD)

    # Skor bandı (üst)
    _skor_bandi(img, draw, ev_takim, dep_takim, ev_gol, dep_gol,
                ev_renk, dep_renk, hafta)

    # Olay şeridi (alt)
    tum_olaylar = []
    for g in ev_gol_atanlar:
        tum_olaylar.append(f"⚽{g.split()[0]}")
    for g in dep_gol_atanlar:
        tum_olaylar.append(f"⚽{g.split()[0]}")
    for o in olaylar[:4]:
        tum_olaylar.append(o)
    _olay_seridi(draw, tum_olaylar)

    # Formasyon etiketi
    font_f = _font(13)
    draw.text((_cx(0.12), FIELD_Y1 - 18), f"[{ev_taktik}]",
              font=font_f, fill=(200, 200, 200), anchor="mm")
    draw.text((_cx(0.88), FIELD_Y1 - 18), f"[{dep_taktik}]",
              font=font_f, fill=(200, 200, 200), anchor="mm")

    # BytesIO'ya yaz
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


# ─── Kadro görseli ──────────────────────────────────────────────────────────
def kadro_gorsel_olustur(
    takim_isim: str,
    taktik: str,
    oyuncular: list,
    para: int,
    puan: int,
) -> BytesIO:
    img  = Image.new("RGB", (W, 480), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    _saha_ciz(draw)

    renk_idx = hash(takim_isim) % len(TAKIM_RENKLER)
    renk = TAKIM_RENKLER[renk_idx]

    font_b = _font(22)
    font_s = _font(13)
    font_k = _font(11)

    pozlar = _formasyon_pozisyonlari(taktik, True, len(oyuncular))

    # Tüm oyuncuları sol yarıda göster ama tam saha genişletilmiş
    for i, (gx, gy) in enumerate(pozlar):
        if i >= len(oyuncular):
            break
        o = oyuncular[i]
        kisalt = o["isim"].split()[0][:2].upper()
        renk_k = renk
        _oyuncu_ciz(draw, gx, gy, renk_k[0], renk_k[1], kisalt, font_k)
        draw.text((gx, gy + 17), f"{o['isim'].split()[0][:7]}",
                  font=font_k, fill=C_WHITE, anchor="mt",
                  stroke_width=1, stroke_fill=C_BLACK)
        draw.text((gx, gy + 28), f"G:{o['guc']}",
                  font=font_k, fill=(180, 255, 180), anchor="mt")

    # Üst band
    draw.rectangle([0, 0, W, 50], fill=(15, 15, 15))
    draw.text((W // 2, 8), takim_isim[:20], font=font_b, fill=C_WHITE, anchor="mt")
    draw.text((W // 2, 32), f"Taktik: {taktik}  |  Puan: {puan}  |  Bütçe: {para:,}₺",
              font=font_s, fill=(180, 180, 180), anchor="mt")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
