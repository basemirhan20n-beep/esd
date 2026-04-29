import sqlite3
import random
from datetime import date, timedelta
from typing import Optional

DB_PATH = "parti.db"


# ─── Ülkeye göre oyuncu havuzu ─────────────────────────────────────────────
OYUNCU_HAVUZU = {
    "TR": [
        ("Ahmet Yılmaz",65), ("Mehmet Kaya",63), ("Ali Demir",68), ("Murat Şahin",70),
        ("Emre Çelik",66), ("Serkan Koç",64), ("Burak Arslan",72), ("Kemal Kurt",61),
        ("Arda Doğan",75), ("Caner Aydın",67), ("Sinan Polat",69), ("Fatih Güneş",62),
        ("Taner Yıldız",71), ("Okan Öztürk",65), ("Yasin Kılıç",63), ("Levent Çetin",68),
        ("Ercan Balcı",60), ("Tolga Özdemir",74), ("Kadir Kaplan",66), ("Alper Bozkurt",70),
        ("Kerem Güler",73), ("Furkan Duman",65), ("Mert Özer",69), ("Doruk Ateş",67),
        ("Hasan Bulut",62), ("Volkan Karaca",71), ("Barış Demirci",64), ("Selim Işık",66),
        ("Tarık Avcı",68), ("Haluk Sever",63), ("Uğur Aslan",70), ("Savaş Gürbüz",65),
        ("İbrahim Çevik",67), ("Ömer Albayrak",69), ("Orhan Sarı",62), ("Cemal Taş",64),
    ],
    "BR": [
        ("Carlos Silva",74), ("Rodrigo Santos",77), ("Lucas Oliveira",72), ("Felipe Costa",76),
        ("Thiago Pereira",79), ("Gabriel Alves",73), ("Matheus Lima",71), ("Bruno Ferreira",75),
        ("Anderson Souza",78), ("Marcelo Rocha",70), ("Diego Mendes",76), ("Rafael Cruz",74),
        ("Leandro Barbosa",72), ("Vinicius Gomes",80), ("Pedro Nascimento",73), ("Neyton Jr",82),
        ("Roberto Azevedo",69), ("Alexandre Dias",71), ("Eduardo Carvalho",75), ("Gustavo Ribeiro",74),
    ],
    "ES": [
        ("Carlos García",73), ("Sergio López",76), ("Javier Martínez",71), ("Alejandro Rodríguez",75),
        ("Pablo Hernández",79), ("David González",72), ("Andrés Sánchez",74), ("Rubén Pérez",70),
        ("Iker Fernández",77), ("Jorge Romero",73), ("Alberto Torres",71), ("Álvaro Jiménez",76),
        ("Luis Moreno",74), ("Marcos Ruiz",72), ("Iñaki Alonso",78), ("Raúl Vidal",75),
    ],
    "FR": [
        ("Pierre Dupont",73), ("Théo Martin",76), ("Antoine Bernard",74), ("Lucas Simon",72),
        ("Hugo Thomas",79), ("Mathieu Petit",71), ("Romain Laurent",75), ("Julien Blanc",73),
        ("Karim Besson",77), ("Noel Garnier",70), ("Baptiste Faure",74), ("Axel Renard",76),
        ("Éric Morel",72), ("Florian Chevalier",78), ("Cédric Girard",74), ("Dylan Mercier",71),
    ],
    "DE": [
        ("Hans Müller",74), ("Klaus Schmidt",71), ("Lukas Wagner",76), ("Felix Becker",73),
        ("Niklas Hoffman",78), ("Jonas Fischer",72), ("Tobias Schulz",75), ("Moritz Meyer",70),
        ("Leon Weber",79), ("Julian Koch",74), ("Patrick Bauer",73), ("Sebastian Wolf",76),
        ("Maximilian Braun",72), ("Tim Schäfer",77), ("Daniel Zimmermann",75), ("André Krause",71),
    ],
    "AR": [
        ("Diego Torres",75), ("Pablo Romero",78), ("Alejandro Flores",72), ("Nicolás Medina",76),
        ("Rodrigo Castro",80), ("Lucas Vargas",74), ("Matías Ramos",77), ("Ezequiel Morales",73),
        ("Maximiliano Cruz",79), ("Gonzalo Ortiz",75), ("Santiago Díaz",71), ("Facundo Reyes",76),
    ],
    "PT": [
        ("João Silva",76), ("Pedro Santos",74), ("Tiago Costa",78), ("Rui Ferreira",72),
        ("Bruno Pereira",80), ("Fábio Oliveira",75), ("André Carvalho",73), ("Luis Gomes",77),
        ("Cristiano Jr",82), ("Renato Sousa",71), ("Paulo Lopes",74), ("Nuno Rodrigues",76),
    ],
    "EN": [
        ("James Wilson",73), ("Thomas Johnson",71), ("Jack Williams",76), ("Harry Davies",74),
        ("Oliver Brown",78), ("George Smith",72), ("William Jones",75), ("Charlie Taylor",73),
        ("Ethan Anderson",77), ("Mason Clarke",70), ("Lucas Evans",74), ("Noah Roberts",76),
    ],
    "IT": [
        ("Marco Rossi",74), ("Luca Ferrari",77), ("Alessandro Romano",72), ("Matteo Esposito",75),
        ("Lorenzo Bianchi",79), ("Davide Colombo",73), ("Andrea Ricci",76), ("Simone Conti",71),
        ("Filippo Moretti",78), ("Giovanni Marchetti",74), ("Riccardo Barbieri",72), ("Nicola Grasso",76),
    ],
    "NL": [
        ("Daan van der Berg",75), ("Lars de Vries",73), ("Sven Bakker",77), ("Ruben Visser",74),
        ("Joost Meijer",79), ("Niels de Boer",72), ("Tim Jansen",76), ("Bram Peters",73),
        ("Liam Hendriks",78), ("Finn Smit",71),
    ],
    "NG": [
        ("Emeka Okafor",76), ("Chidi Eze",74), ("Tunde Adeyemi",78), ("Segun Osei",73),
        ("Kofi Mensah",80), ("Dele Abiodun",75), ("Ibrahim Diallo",77), ("Moussa Traore",72),
        ("Sadio Keita",79), ("Boubacar Sow",76),
    ],
}

# Tüm havuzdan düz liste
def _tum_havuz():
    sonuc = []
    for ulke, oyuncular in OYUNCU_HAVUZU.items():
        for isim, guc in oyuncular:
            sonuc.append((isim, guc, ulke))
    return sonuc

TUM_OYUNCULAR = _tum_havuz()

POZISYONLAR_AGIRLIKLI = (
    ["Kaleci"] * 2 + ["Defans"] * 5 + ["Orta Saha"] * 5 + ["Forvet"] * 3
)

# Otomatik kadro yapısı: Takım kurulunca verilecek kadro
BASLANGIC_KADRO = [
    ("Kaleci",    1, (55, 72)),    # 1 Kaleci
    ("Kaleci",    1, (50, 65)),    # yedek Kaleci
    ("Defans",    4, (58, 76)),    # 4 Defans
    ("Orta Saha", 4, (58, 76)),    # 4 Orta Saha
    ("Forvet",    3, (60, 78)),    # 3 Forvet
    ("Defans",    1, (52, 68)),    # yedek Defans
    ("Orta Saha", 1, (52, 68)),    # yedek OS
    ("Forvet",    1, (54, 70)),    # yedek Forvet
]  # toplam: 16 oyuncu


def _deger_hesapla(guc: int) -> int:
    """Güce göre gerçekçi piyasa değeri hesapla"""
    if guc >= 85:
        return random.randint(800_000, 2_000_000)
    elif guc >= 78:
        return random.randint(300_000, 800_000)
    elif guc >= 72:
        return random.randint(120_000, 300_000)
    elif guc >= 65:
        return random.randint(50_000, 120_000)
    elif guc >= 58:
        return random.randint(20_000, 50_000)
    else:
        return random.randint(8_000, 20_000)


def rastgele_isim(kullanilmis: set) -> str:
    shuffled = list(TUM_OYUNCULAR)
    random.shuffle(shuffled)
    for isim, _, _ in shuffled:
        if isim not in kullanilmis:
            return isim
    suf = random.randint(2, 99)
    return f"Oyuncu {suf}"

BASLANGIC_PARASI = 500_000   # Otomatik kadro geldiği için daha az para yeter
LIG1_LIMIT = 15
LIG2_LIMIT = 10

TAKTIKLER = {
    "4-3-3":  (1.15, 0.90, "⚡ Agresif hücum"),
    "4-4-2":  (1.00, 1.00, "⚖️ Dengeli"),
    "5-3-2":  (0.88, 1.18, "🛡️ Güçlü defans"),
    "3-5-2":  (1.08, 1.05, "🎯 Orta saha hâkimiyeti"),
    "4-2-3-1":(1.05, 1.05, "🔄 Modern denge"),
}

SPIN_ODULLER = [
    ("💰 2.000₺",  "para",  2000,  30),
    ("💰 5.000₺",  "para",  5000,  25),
    ("💰 10.000₺", "para",  10000, 15),
    ("💰 20.000₺", "para",  20000, 8),
    ("⭐ 50 XP",   "xp",    50,    20),
    ("⭐ 100 XP",  "xp",    100,   12),
    ("🏋️ +3 Güç", "guc",   3,     8),
    ("🍀 500₺",   "para",  500,   40),
    ("💎 50.000₺", "para",  50000, 2),
]

BASARILAR = {
    "ilk_mac":       ("⚽ İlk Adım",        "İlk maçını oynadın!"),
    "5_galibiyet":   ("🏆 Çaylak Koç",      "5 galibiyet aldın!"),
    "10_galibiyet":  ("🔥 Deneyimli Koç",   "10 galibiyet aldın!"),
    "25_galibiyet":  ("👑 Efsane Koç",      "25 galibiyet aldın!"),
    "golcu_10":      ("⚡ Golcü Kral",       "Bir oyuncun 10 gol attı!"),
    "transfer_5":    ("🛒 Transfer Ustası",  "5 oyuncu transfer ettin!"),
    "sezon_sampiyon":("🥇 Şampiyon",        "Sezonu şampiyon bitirdin!"),
    "kupa_sampiyon": ("🏅 Kupa Şampiyonu",  "Cumhuriyet Kupası'nı kazandın!"),
    "spin_5":        ("🎰 Şans Çarkı",      "Çarkı 5 kez çevirdin!"),
    "bahis_kazan":   ("🎲 Bahisçi",         "İlk bahsini kazandın!"),
    "altyapi":       ("🌱 Altyapı Yöneticisi","Altyapıdan ilk oyuncunu çıkardın!"),
    "lig2_sampiyonu":("📈 Yükselen Yıldız", "2. lig şampiyonu oldun!"),
}


# POZ_ULKE export (futbol.py'den import edilir)
POZ_ULKE = {
    "TR": "🇹🇷", "BR": "🇧🇷", "ES": "🇪🇸", "FR": "🇫🇷", "DE": "🇩🇪",
    "AR": "🇦🇷", "PT": "🇵🇹", "EN": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "IT": "🇮🇹", "NL": "🇳🇱", "NG": "🌍",
}


class FutbolDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_tables()
        self._piyasa_doldur()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS futbol_para (
                    user_id INTEGER PRIMARY KEY,
                    para    INTEGER DEFAULT 100000
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS takimlar (
                    takim_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id          INTEGER UNIQUE,
                    isim             TEXT UNIQUE,
                    lig              INTEGER DEFAULT 1,
                    puan             INTEGER DEFAULT 0,
                    galibiyet        INTEGER DEFAULT 0,
                    beraberlik       INTEGER DEFAULT 0,
                    maglubiyet       INTEGER DEFAULT 0,
                    atilan_gol       INTEGER DEFAULT 0,
                    yenilen_gol      INTEGER DEFAULT 0,
                    mac_sayisi       INTEGER DEFAULT 0,
                    son_mac          TEXT,
                    olusturma_tarihi TEXT,
                    taktik           TEXT DEFAULT '4-4-2',
                    sezon            INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS oyuncular (
                    oyuncu_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    takim_id         INTEGER,
                    isim             TEXT,
                    pozisyon         TEXT,
                    guc              INTEGER,
                    deger            INTEGER,
                    antrenman_tarihi TEXT,
                    satista          INTEGER DEFAULT 0,
                    satis_fiyati     INTEGER DEFAULT 0,
                    gol              INTEGER DEFAULT 0,
                    asist            INTEGER DEFAULT 0,
                    sari_kart        INTEGER DEFAULT 0,
                    kirmizi_kart     INTEGER DEFAULT 0,
                    sakatlik_bitis   TEXT DEFAULT NULL,
                    genc             INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fikstur (
                    mac_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    ev_takim_id    INTEGER,
                    dep_takim_id   INTEGER,
                    hafta          INTEGER,
                    lig            INTEGER DEFAULT 1,
                    oynanma_tarihi TEXT,
                    ev_gol         INTEGER,
                    dep_gol        INTEGER,
                    oynanmis       INTEGER DEFAULT 0,
                    sezon          INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spin_kaydi (
                    user_id    INTEGER PRIMARY KEY,
                    son_spin   TEXT,
                    toplam     INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bahisler (
                    bahis_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac_id      INTEGER,
                    user_id     INTEGER,
                    hedef_takim INTEGER,
                    miktar      INTEGER,
                    odendi      INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS basarilar (
                    user_id     INTEGER,
                    basari_kodu TEXT,
                    tarih       TEXT,
                    PRIMARY KEY (user_id, basari_kodu)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kupa_maclar (
                    mac_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    tur            INTEGER,
                    ev_takim_id    INTEGER,
                    dep_takim_id   INTEGER,
                    ev_gol         INTEGER DEFAULT 0,
                    dep_gol        INTEGER DEFAULT 0,
                    oynanmis       INTEGER DEFAULT 0,
                    oynanma_tarihi TEXT,
                    sezon          INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS grup_chatler (
                    chat_id INTEGER PRIMARY KEY
                )
            """)
            conn.commit()

    # ─── Para ──────────────────────────────────────────────────────────────

    def para_getir(self, user_id: int) -> int:
        with self._conn() as conn:
            r = conn.execute("SELECT para FROM futbol_para WHERE user_id=?", (user_id,)).fetchone()
            if not r:
                conn.execute("INSERT INTO futbol_para VALUES (?,?)", (user_id, BASLANGIC_PARASI))
                conn.commit()
                return BASLANGIC_PARASI
            return r["para"]

    def para_guncelle(self, user_id: int, miktar: int):
        self.para_getir(user_id)
        with self._conn() as conn:
            conn.execute("UPDATE futbol_para SET para=para+? WHERE user_id=?", (miktar, user_id))
            conn.commit()

    # ─── Takım ─────────────────────────────────────────────────────────────

    def takim_kur(self, user_id: int, isim: str):
        isim = isim.strip()
        if len(isim) < 2 or len(isim) > 30:
            return False, "Takım adı 2-30 karakter olmalı.", 0
        with self._conn() as conn:
            lig1 = conn.execute("SELECT COUNT(*) FROM takimlar WHERE lig=1").fetchone()[0]
            lig2 = conn.execute("SELECT COUNT(*) FROM takimlar WHERE lig=2").fetchone()[0]
            if lig1 < LIG1_LIMIT:
                lig = 1
            elif lig2 < LIG2_LIMIT:
                lig = 2
            else:
                return False, "Tüm lig kotaları dolu.", 0
            try:
                conn.execute("""
                    INSERT INTO takimlar (user_id, isim, lig, olusturma_tarihi)
                    VALUES (?,?,?,?)
                """, (user_id, isim, lig, date.today().isoformat()))
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "user_id" in str(e):
                    return False, "Zaten bir takımınız var.", 0
                return False, "Bu takım adı zaten kullanılıyor.", 0

            takim_row = conn.execute("SELECT takim_id FROM takimlar WHERE user_id=?", (user_id,)).fetchone()
            takim_id = takim_row["takim_id"]
            takim_sayisi = conn.execute("SELECT COUNT(*) FROM takimlar WHERE lig=?", (lig,)).fetchone()[0]

        # Otomatik başlangıç kadrosu oluştur
        self._otomatik_kadro_olustur(takim_id)
        return True, lig, takim_sayisi

    def _otomatik_kadro_olustur(self, takim_id: int):
        """Takım kurulunca 16 oyuncudan oluşan otomatik kadro ata"""
        kullanilmis = set()
        with self._conn() as conn:
            kullanilmis = {r[0] for r in conn.execute("SELECT isim FROM oyuncular").fetchall()}

        oyuncu_listesi = []
        havuz = list(TUM_OYUNCULAR)
        random.shuffle(havuz)
        havuz_idx = 0

        for (poz, adet, guc_aralik) in BASLANGIC_KADRO:
            for _ in range(adet):
                # Havuzdan uygun güçte oyuncu bul
                bulunan = False
                for attempt in range(len(havuz)):
                    idx = (havuz_idx + attempt) % len(havuz)
                    isim, baz_guc, ulke = havuz[idx]
                    if isim in kullanilmis:
                        continue
                    guc_min, guc_max = guc_aralik
                    guc = max(guc_min, min(guc_max, baz_guc + random.randint(-3, 5)))
                    if guc_min <= guc <= guc_max + 5:
                        kullanilmis.add(isim)
                        havuz_idx = (idx + 1) % len(havuz)
                        deger = _deger_hesapla(guc)
                        oyuncu_listesi.append((takim_id, isim, poz, guc, deger))
                        bulunan = True
                        break
                if not bulunan:
                    # Fallback: rastgele isim + guc_aralik ortası
                    guc_min, guc_max = guc_aralik
                    isim = rastgele_isim(kullanilmis)
                    kullanilmis.add(isim)
                    guc = random.randint(guc_min, guc_max)
                    deger = _deger_hesapla(guc)
                    oyuncu_listesi.append((takim_id, isim, poz, guc, deger))

        with self._conn() as conn:
            for tid, isim, poz, guc, deger in oyuncu_listesi:
                conn.execute("""
                    INSERT INTO oyuncular (takim_id,isim,pozisyon,guc,deger,satista,satis_fiyati)
                    VALUES (?,?,?,?,?,0,?)
                """, (tid, isim, poz, guc, deger, deger))
            conn.commit()

    def takim_user(self, user_id: int) -> Optional[dict]:
        with self._conn() as conn:
            r = conn.execute("SELECT * FROM takimlar WHERE user_id=?", (user_id,)).fetchone()
            return dict(r) if r else None

    def takim_id(self, takim_id: int) -> Optional[dict]:
        with self._conn() as conn:
            r = conn.execute("SELECT * FROM takimlar WHERE takim_id=?", (takim_id,)).fetchone()
            return dict(r) if r else None

    def takim_sayisi(self, lig: int = 1) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM takimlar WHERE lig=?", (lig,)).fetchone()[0]

    def tum_takimlar(self, lig: int = 1) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM takimlar WHERE lig=?
                ORDER BY puan DESC, (atilan_gol-yenilen_gol) DESC, atilan_gol DESC
            """, (lig,)).fetchall()
            return [dict(r) for r in rows]

    def taktik_sec(self, takim_id: int, taktik: str) -> bool:
        if taktik not in TAKTIKLER:
            return False
        with self._conn() as conn:
            conn.execute("UPDATE takimlar SET taktik=? WHERE takim_id=?", (taktik, takim_id))
            conn.commit()
        return True

    # ─── Oyuncular ─────────────────────────────────────────────────────────

    def _piyasa_doldur(self):
        with self._conn() as conn:
            mevcut = conn.execute(
                "SELECT COUNT(*) FROM oyuncular WHERE takim_id IS NULL AND satista=1"
            ).fetchone()[0]
            if mevcut >= 30:
                return
            kullanilmis = {r[0] for r in conn.execute("SELECT isim FROM oyuncular").fetchall()}
            havuz = list(TUM_OYUNCULAR)
            random.shuffle(havuz)
            eklenen = 0
            for isim, baz_guc, ulke in havuz:
                if eklenen >= (40 - mevcut):
                    break
                if isim in kullanilmis:
                    continue
                kullanilmis.add(isim)
                poz = random.choice(POZISYONLAR_AGIRLIKLI)
                guc = max(40, min(90, baz_guc + random.randint(-5, 8)))
                deger = _deger_hesapla(guc)
                conn.execute("""
                    INSERT INTO oyuncular (takim_id,isim,pozisyon,guc,deger,satista,satis_fiyati)
                    VALUES (NULL,?,?,?,?,1,?)
                """, (isim, poz, guc, deger, deger))
                eklenen += 1
            conn.commit()

    def altyapi_cikart(self, takim_id: int, user_id: int):
        """Altyapıdan genç oyuncu çıkar — ücretsiz ama düşük güçlü"""
        with self._conn() as conn:
            kadro = conn.execute(
                "SELECT COUNT(*) FROM oyuncular WHERE takim_id=?", (takim_id,)
            ).fetchone()[0]
            if kadro >= 23:
                return None, "Kadron dolu (maks. 23)."
            kullanilmis = {r[0] for r in conn.execute("SELECT isim FROM oyuncular").fetchall()}
            isim = rastgele_isim(kullanilmis)
            poz = random.choice(POZISYONLAR_AGIRLIKLI)
            guc = random.randint(30, 52)
            deger = _deger_hesapla(guc)
            conn.execute("""
                INSERT INTO oyuncular (takim_id,isim,pozisyon,guc,deger,satista,satis_fiyati,genc)
                VALUES (?,?,?,?,?,0,?,1)
            """, (takim_id, isim, poz, guc, deger, deger))
            conn.commit()
            r = conn.execute(
                "SELECT * FROM oyuncular WHERE takim_id=? ORDER BY oyuncu_id DESC LIMIT 1",
                (takim_id,)
            ).fetchone()
        self.basari_ver(user_id, "altyapi")
        return dict(r), None

    def takim_oyunculari(self, takim_id: int) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM oyuncular WHERE takim_id=? ORDER BY guc DESC", (takim_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def piyasa(self, sayfa: int = 0, sayfa_boyut: int = 8) -> tuple:
        offset = sayfa * sayfa_boyut
        with self._conn() as conn:
            toplam = conn.execute(
                "SELECT COUNT(*) FROM oyuncular WHERE satista=1"
            ).fetchone()[0]
            rows = conn.execute("""
                SELECT * FROM oyuncular WHERE satista=1
                ORDER BY guc DESC LIMIT ? OFFSET ?
            """, (sayfa_boyut, offset)).fetchall()
            return [dict(r) for r in rows], toplam

    def oyuncu_getir(self, oyuncu_id: int) -> Optional[dict]:
        with self._conn() as conn:
            r = conn.execute("SELECT * FROM oyuncular WHERE oyuncu_id=?", (oyuncu_id,)).fetchone()
            return dict(r) if r else None

    def satin_al(self, user_id: int, takim_id: int, oyuncu_id: int):
        oyuncu = self.oyuncu_getir(oyuncu_id)
        if not oyuncu or not oyuncu["satista"]:
            return False, "Oyuncu satışta değil."
        fiyat = oyuncu["satis_fiyati"]
        para = self.para_getir(user_id)
        if para < fiyat:
            return False, f"Yeterli paran yok. Gerekli: {fiyat:,}₺ | Mevcut: {para:,}₺"
        kadro = self.takim_oyunculari(takim_id)
        if len(kadro) >= 23:
            return False, "Kadron dolu (maks. 23 oyuncu)."
        self.para_guncelle(user_id, -fiyat)
        if oyuncu["takim_id"]:
            with self._conn() as conn:
                satici = conn.execute(
                    "SELECT user_id FROM takimlar WHERE takim_id=?", (oyuncu["takim_id"],)
                ).fetchone()
                if satici:
                    self.para_guncelle(satici["user_id"], fiyat)
        with self._conn() as conn:
            conn.execute(
                "UPDATE oyuncular SET takim_id=?,satista=0,satis_fiyati=0 WHERE oyuncu_id=?",
                (takim_id, oyuncu_id)
            )
            conn.commit()
        self._piyasa_doldur()
        # Transfer başarısı kontrolü
        with self._conn() as conn:
            adet = conn.execute(
                "SELECT COUNT(*) FROM oyuncular WHERE takim_id=?", (takim_id,)
            ).fetchone()[0]
        if adet >= 5:
            self.basari_ver(user_id, "transfer_5")
        return True, f"✅ *{oyuncu['isim']}* ({oyuncu['pozisyon']}, Güç:{oyuncu['guc']}) satın alındı! -{fiyat:,}₺"

    def sat(self, takim_id: int, oyuncu_id: int, fiyat: int):
        oyuncu = self.oyuncu_getir(oyuncu_id)
        if not oyuncu or oyuncu["takim_id"] != takim_id:
            return False, "Bu oyuncu senin takımında değil."
        if oyuncu["satista"]:
            return False, "Oyuncu zaten satışta."
        if fiyat < 1_000:
            return False, "Minimum satış fiyatı 1.000₺."
        with self._conn() as conn:
            conn.execute(
                "UPDATE oyuncular SET satista=1,satis_fiyati=? WHERE oyuncu_id=?",
                (fiyat, oyuncu_id)
            )
            conn.commit()
        return True, f"✅ *{oyuncu['isim']}* {fiyat:,}₺ ile piyasaya çıkarıldı."

    def sat_iptal(self, takim_id: int, oyuncu_id: int):
        oyuncu = self.oyuncu_getir(oyuncu_id)
        if not oyuncu or oyuncu["takim_id"] != takim_id:
            return False, "Bu oyuncu senin takımında değil."
        with self._conn() as conn:
            conn.execute(
                "UPDATE oyuncular SET satista=0,satis_fiyati=0 WHERE oyuncu_id=?",
                (oyuncu_id,)
            )
            conn.commit()
        return True, "✅ Satış iptal edildi."

    def oyuncu_istatistikleri(self, takim_id: int) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM oyuncular WHERE takim_id=?
                ORDER BY gol DESC, asist DESC
            """, (takim_id,)).fetchall()
            return [dict(r) for r in rows]

    def sezon_golculeri(self) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT o.isim, o.gol, o.asist, t.isim as takim_isim, t.lig
                FROM oyuncular o
                JOIN takimlar t ON o.takim_id = t.takim_id
                WHERE o.gol > 0
                ORDER BY o.gol DESC, o.asist DESC
                LIMIT 10
            """).fetchall()
            return [dict(r) for r in rows]

    def sakatlanan_oyuncular(self, takim_id: int) -> list:
        bugun = date.today().isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM oyuncular WHERE takim_id=? AND sakatlik_bitis > ?",
                (takim_id, bugun)
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── Antrenman ─────────────────────────────────────────────────────────

    def antrenman_yap(self, takim_id: int):
        bugun = date.today().isoformat()
        oyuncular = self.takim_oyunculari(takim_id)
        if not oyuncular:
            return False, "Kadronuzda oyuncu yok."
        if any(o["antrenman_tarihi"] == bugun for o in oyuncular):
            return False, "Bugün zaten antrenman yaptınız. Yarın tekrar gelin! ⏰"
        secilen = random.sample(oyuncular, min(5, len(oyuncular)))
        gelismeler = []
        with self._conn() as conn:
            for o in secilen:
                artis = random.randint(1, 3)
                if o.get("genc"):
                    artis += random.randint(1, 2)  # gençler daha hızlı gelişir
                yeni_guc = min(99, o["guc"] + artis)
                yeni_deger = max(8_000, yeni_guc * 1_000 + random.randint(0, 3_000))
                conn.execute("""
                    UPDATE oyuncular SET guc=?,deger=?,antrenman_tarihi=? WHERE oyuncu_id=?
                """, (yeni_guc, yeni_deger, bugun, o["oyuncu_id"]))
                gelismeler.append({
                    "isim": o["isim"],
                    "pozisyon": o["pozisyon"],
                    "artis": artis,
                    "yeni_guc": yeni_guc,
                    "genc": bool(o.get("genc")),
                })
            conn.commit()
        return True, gelismeler

    # ─── Takım gücü ─────────────────────────────────────────────────────────

    def takim_gucu(self, takim_id: int, taktik: str = "4-4-2") -> float:
        oyuncular = self.takim_oyunculari(takim_id)
        if not oyuncular:
            return 50.0
        bugun = date.today().isoformat()
        aktif = [o for o in oyuncular
                 if not o.get("sakatlik_bitis") or o["sakatlik_bitis"] <= bugun]
        if not aktif:
            aktif = oyuncular
        gucler = sorted([o["guc"] for o in aktif], reverse=True)
        en_iyi = gucler[:11]
        taban = sum(en_iyi) / len(en_iyi)
        h, d, _ = TAKTIKLER.get(taktik, (1.0, 1.0, ""))
        return taban * ((h + d) / 2)

    def yeterli_kadro_mu(self, takim_id: int) -> tuple:
        oyuncular = self.takim_oyunculari(takim_id)
        bugun = date.today().isoformat()
        aktif = [o for o in oyuncular
                 if not o.get("sakatlik_bitis") or o["sakatlik_bitis"] <= bugun]
        if len(aktif) < 11:
            return False, f"Sağlıklı oyuncu: {len(aktif)} (min. 11 gerekli)."
        if not any(o["pozisyon"] == "Kaleci" for o in aktif):
            return False, "Sağlıklı Kaleci yok!"
        return True, "ok"

    # ─── Fikstür ───────────────────────────────────────────────────────────

    def fikstur_var_mi(self, lig: int = 1) -> bool:
        with self._conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM fikstur WHERE lig=?", (lig,)
            ).fetchone()[0] > 0

    def fikstur_olustur(self, lig: int = 1, sezon: int = 1):
        takimlar = self.tum_takimlar(lig)
        if len(takimlar) < 2:
            return False
        ids = [t["takim_id"] for t in takimlar]
        if len(ids) % 2 == 1:
            ids.append(None)
        n = len(ids)
        tum_maclar = []
        ids_rot = ids[1:]
        for tur in range(n - 1):
            hafta = tur + 1
            eslesmeler = [(ids[0], ids_rot[0])]
            for i in range(1, n // 2):
                eslesmeler.append((ids_rot[-i], ids_rot[i]))
            for ev, dep in eslesmeler:
                if ev and dep:
                    tum_maclar.append((ev, dep, hafta))
            ids_rot = [ids_rot[-1]] + ids_rot[:-1]
        toplam = n - 1
        for ev, dep, hafta in list(tum_maclar):
            tum_maclar.append((dep, ev, hafta + toplam))
        with self._conn() as conn:
            conn.execute("DELETE FROM fikstur WHERE lig=? AND sezon=?", (lig, sezon))
            for ev, dep, hafta in tum_maclar:
                conn.execute("""
                    INSERT INTO fikstur (ev_takim_id,dep_takim_id,hafta,lig,oynanmis,sezon)
                    VALUES (?,?,?,?,0,?)
                """, (ev, dep, hafta, lig, sezon))
            conn.commit()
        return True

    def fikstur_takim_ekle(self, yeni_takim_id: int, lig: int = 1, sezon: int = 1):
        """Yeni takım gelince mevcut fikstüre maçlar ekle, puanlar sıfırlanmaz"""
        takimlar = self.tum_takimlar(lig)
        diger_ids = [t["takim_id"] for t in takimlar if t["takim_id"] != yeni_takim_id]
        if not diger_ids:
            return
        with self._conn() as conn:
            max_hafta = conn.execute(
                "SELECT COALESCE(MAX(hafta),0) FROM fikstur WHERE lig=?", (lig,)
            ).fetchone()[0]
        yeni_maclar = []
        for i, eski in enumerate(diger_ids):
            h1 = max_hafta + i * 2 + 1
            h2 = max_hafta + i * 2 + 2
            yeni_maclar.append((yeni_takim_id, eski, h1, lig, sezon))
            yeni_maclar.append((eski, yeni_takim_id, h2, lig, sezon))
        with self._conn() as conn:
            for ev, dep, h, l, s in yeni_maclar:
                conn.execute("""
                    INSERT INTO fikstur (ev_takim_id,dep_takim_id,hafta,lig,oynanmis,sezon)
                    VALUES (?,?,?,?,0,?)
                """, (ev, dep, h, l, s))
            conn.commit()

    def sonraki_mac(self, takim_id: int) -> Optional[dict]:
        takim = self.takim_id(takim_id)
        if not takim:
            return None
        lig = takim["lig"]
        with self._conn() as conn:
            r = conn.execute("""
                SELECT * FROM fikstur
                WHERE (ev_takim_id=? OR dep_takim_id=?) AND oynanmis=0 AND lig=?
                ORDER BY hafta ASC LIMIT 1
            """, (takim_id, takim_id, lig)).fetchone()
            return dict(r) if r else None

    def bugun_mac_oynadim_mi(self, takim_id: int) -> bool:
        bugun = date.today().isoformat()
        with self._conn() as conn:
            r = conn.execute("""
                SELECT COUNT(*) FROM fikstur
                WHERE (ev_takim_id=? OR dep_takim_id=?) AND oynanmis=1 AND oynanma_tarihi=?
            """, (takim_id, takim_id, bugun)).fetchone()
            return r[0] > 0

    def mac_oyna(self, mac_id: int, talep_eden_takim: int):
        with self._conn() as conn:
            r = conn.execute("SELECT * FROM fikstur WHERE mac_id=?", (mac_id,)).fetchone()
            if not r:
                return None, "Maç bulunamadı."
            mac = dict(r)
        if mac["oynanmis"]:
            return None, "Bu maç zaten oynandı."
        if talep_eden_takim not in (mac["ev_takim_id"], mac["dep_takim_id"]):
            return None, "Bu maç senin takımına ait değil."
        if self.bugun_mac_oynadim_mi(talep_eden_takim):
            return None, "Bugün zaten bir maç oynadın. Yarın geri gel! ⚽"
        ev_t = self.takim_id(mac["ev_takim_id"])
        dep_t = self.takim_id(mac["dep_takim_id"])
        ev_taktik = ev_t.get("taktik", "4-4-2")
        dep_taktik = dep_t.get("taktik", "4-4-2")
        ev_h, ev_d, _ = TAKTIKLER.get(ev_taktik, (1.0, 1.0, ""))
        dep_h, dep_d, _ = TAKTIKLER.get(dep_taktik, (1.0, 1.0, ""))
        ev_guc_ham = self.takim_gucu(mac["ev_takim_id"], ev_taktik)
        dep_guc_ham = self.takim_gucu(mac["dep_takim_id"], dep_taktik)
        ev_guc_adj = ev_guc_ham * 1.08 * ev_h / dep_d
        dep_guc_adj = dep_guc_ham * dep_h / ev_d
        toplam = ev_guc_adj + dep_guc_adj
        ev_oran = ev_guc_adj / toplam if toplam else 0.5
        ev_gol = max(0, min(9, round(random.gauss(ev_oran * 3.2, 1.1))))
        dep_gol = max(0, min(9, round(random.gauss((1 - ev_oran) * 3.2, 1.1))))
        ev_oyuncular = self.takim_oyunculari(mac["ev_takim_id"])
        dep_oyuncular = self.takim_oyunculari(mac["dep_takim_id"])
        olaylar = []

        def gol_atan(oyuncular, sayi):
            forvetler = [o for o in oyuncular if o["pozisyon"] in ("Forvet", "Orta Saha")]
            havuz = forvetler if forvetler else oyuncular
            atanlar = []
            with self._conn() as c:
                for _ in range(sayi):
                    if not havuz:
                        break
                    golcu = random.choice(havuz)
                    atanlar.append(golcu["isim"])
                    c.execute("UPDATE oyuncular SET gol=gol+1 WHERE oyuncu_id=?", (golcu["oyuncu_id"],))
                    diger = [o for o in havuz if o["oyuncu_id"] != golcu["oyuncu_id"]]
                    if diger:
                        asistci = random.choice(diger)
                        c.execute("UPDATE oyuncular SET asist=asist+1 WHERE oyuncu_id=?", (asistci["oyuncu_id"],))
                c.commit()
            return atanlar

        ev_gol_atanlar = gol_atan(ev_oyuncular, ev_gol)
        dep_gol_atanlar = gol_atan(dep_oyuncular, dep_gol)

        # Kart ve sakatlık olayları
        tum = [(o, "ev") for o in ev_oyuncular] + [(o, "dep") for o in dep_oyuncular]
        with self._conn() as c:
            for o, _t in tum:
                if random.random() < 0.18:
                    yeni_sari = (o.get("sari_kart") or 0) + 1
                    c.execute("UPDATE oyuncular SET sari_kart=? WHERE oyuncu_id=?", (yeni_sari, o["oyuncu_id"]))
                    olaylar.append(f"🟡 {o['isim']} sarı kart")
                    if yeni_sari >= 2 and random.random() < 0.4:
                        c.execute("UPDATE oyuncular SET kirmizi_kart=kirmizi_kart+1,sari_kart=0 WHERE oyuncu_id=?", (o["oyuncu_id"],))
                        olaylar.append(f"🔴 {o['isim']} çift sarıdan kırmızı!")
                elif random.random() < 0.04:
                    c.execute("UPDATE oyuncular SET kirmizi_kart=kirmizi_kart+1 WHERE oyuncu_id=?", (o["oyuncu_id"],))
                    olaylar.append(f"🔴 {o['isim']} direkt kırmızı!")
                if random.random() < 0.07:
                    gun = random.randint(2, 8)
                    bitis = (date.today() + timedelta(days=gun)).isoformat()
                    c.execute("UPDATE oyuncular SET sakatlik_bitis=? WHERE oyuncu_id=?", (bitis, o["oyuncu_id"]))
                    olaylar.append(f"🏥 {o['isim']} sakatlandı ({gun}g)")
            c.commit()

        bugun = date.today().isoformat()
        with self._conn() as conn:
            conn.execute("""
                UPDATE fikstur SET ev_gol=?,dep_gol=?,oynanmis=1,oynanma_tarihi=? WHERE mac_id=?
            """, (ev_gol, dep_gol, bugun, mac_id))

            def upd(tid, a, y):
                if a > y:
                    conn.execute("""
                        UPDATE takimlar SET puan=puan+3,galibiyet=galibiyet+1,
                        atilan_gol=atilan_gol+?,yenilen_gol=yenilen_gol+?,
                        mac_sayisi=mac_sayisi+1,son_mac=? WHERE takim_id=?
                    """, (a, y, bugun, tid))
                elif a < y:
                    conn.execute("""
                        UPDATE takimlar SET maglubiyet=maglubiyet+1,
                        atilan_gol=atilan_gol+?,yenilen_gol=yenilen_gol+?,
                        mac_sayisi=mac_sayisi+1,son_mac=? WHERE takim_id=?
                    """, (a, y, bugun, tid))
                else:
                    conn.execute("""
                        UPDATE takimlar SET puan=puan+1,beraberlik=beraberlik+1,
                        atilan_gol=atilan_gol+?,yenilen_gol=yenilen_gol+?,
                        mac_sayisi=mac_sayisi+1,son_mac=? WHERE takim_id=?
                    """, (a, y, bugun, tid))
            upd(mac["ev_takim_id"], ev_gol, dep_gol)
            upd(mac["dep_takim_id"], dep_gol, ev_gol)
            conn.commit()

        if ev_gol > dep_gol:
            self.para_guncelle(ev_t["user_id"], 5_000)
            self.para_guncelle(dep_t["user_id"], 1_000)
            kazanan_user, kaybeden_user = ev_t["user_id"], dep_t["user_id"]
            kazandi_ev = True
        elif dep_gol > ev_gol:
            self.para_guncelle(dep_t["user_id"], 5_000)
            self.para_guncelle(ev_t["user_id"], 1_000)
            kazanan_user, kaybeden_user = dep_t["user_id"], ev_t["user_id"]
            kazandi_ev = False
        else:
            self.para_guncelle(ev_t["user_id"], 2_500)
            self.para_guncelle(dep_t["user_id"], 2_500)
            kazanan_user = None
            kazandi_ev = None

        self._mac_basari_kontrol(ev_t["user_id"], ev_gol > dep_gol)
        self._mac_basari_kontrol(dep_t["user_id"], dep_gol > ev_gol)
        self._golcu_basari_kontrol()

        kazanan_takim_id = mac["ev_takim_id"] if ev_gol > dep_gol else (
            mac["dep_takim_id"] if dep_gol > ev_gol else None)
        self._bahis_ode(mac_id, kazanan_takim_id)

        return {
            "mac_id": mac_id,
            "hafta": mac["hafta"],
            "lig": mac["lig"],
            "ev_takim": ev_t["isim"],
            "dep_takim": dep_t["isim"],
            "ev_takim_id": mac["ev_takim_id"],
            "dep_takim_id": mac["dep_takim_id"],
            "ev_takim_user": ev_t["user_id"],
            "dep_takim_user": dep_t["user_id"],
            "ev_gol": ev_gol,
            "dep_gol": dep_gol,
            "ev_gol_atanlar": ev_gol_atanlar,
            "dep_gol_atanlar": dep_gol_atanlar,
            "ev_guc": round(ev_guc_ham, 1),
            "dep_guc": round(dep_guc_ham, 1),
            "ev_taktik": ev_taktik,
            "dep_taktik": dep_taktik,
            "olaylar": olaylar[:6],
        }, None

    def _mac_basari_kontrol(self, user_id: int, kazandi: bool):
        self.basari_ver(user_id, "ilk_mac")
        if not kazandi:
            return
        takim = self.takim_user(user_id)
        if not takim:
            return
        g = takim["galibiyet"]
        for esik, kod in [(5, "5_galibiyet"), (10, "10_galibiyet"), (25, "25_galibiyet")]:
            if g >= esik:
                self.basari_ver(user_id, kod)

    def _golcu_basari_kontrol(self):
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT t.user_id FROM oyuncular o
                JOIN takimlar t ON o.takim_id = t.takim_id
                WHERE o.gol >= 10
            """).fetchall()
            for r in rows:
                self.basari_ver(r["user_id"], "golcu_10")

    def son_maclar(self, takim_id: int, limit: int = 5) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT f.*,
                    (SELECT isim FROM takimlar WHERE takim_id=f.ev_takim_id)  AS ev_isim,
                    (SELECT isim FROM takimlar WHERE takim_id=f.dep_takim_id) AS dep_isim
                FROM fikstur f
                WHERE (f.ev_takim_id=? OR f.dep_takim_id=?) AND f.oynanmis=1
                ORDER BY f.oynanma_tarihi DESC, f.mac_id DESC LIMIT ?
            """, (takim_id, takim_id, limit)).fetchall()
            return [dict(r) for r in rows]

    def haftalik_fikstur(self, hafta: int, lig: int = 1) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT f.*,
                    (SELECT isim FROM takimlar WHERE takim_id=f.ev_takim_id)  AS ev_isim,
                    (SELECT isim FROM takimlar WHERE takim_id=f.dep_takim_id) AS dep_isim
                FROM fikstur f WHERE f.hafta=? AND f.lig=? ORDER BY f.mac_id
            """, (hafta, lig)).fetchall()
            return [dict(r) for r in rows]

    def mevcut_hafta(self, lig: int = 1) -> int:
        with self._conn() as conn:
            r = conn.execute(
                "SELECT MAX(hafta) FROM fikstur WHERE oynanmis=1 AND lig=?", (lig,)
            ).fetchone()[0]
            if r:
                return r
            r2 = conn.execute(
                "SELECT MIN(hafta) FROM fikstur WHERE oynanmis=0 AND lig=?", (lig,)
            ).fetchone()[0]
            return r2 or 1

    # ─── Spin Çarkı ─────────────────────────────────────────────────────────

    def spin_cevir(self, user_id: int):
        bugun = date.today().isoformat()
        with self._conn() as conn:
            r = conn.execute("SELECT * FROM spin_kaydi WHERE user_id=?", (user_id,)).fetchone()
            if r and r["son_spin"] == bugun:
                return None, "Bugün zaten çevirdin! Yarın tekrar gel. 🎰"
            # Ağırlıklı seçim
            agirliklar = [o[3] for o in SPIN_ODULLER]
            odul = random.choices(SPIN_ODULLER, weights=agirliklar, k=1)[0]
            yeni_toplam = ((r["toplam"] if r else 0) + 1)
            if r:
                conn.execute("UPDATE spin_kaydi SET son_spin=?,toplam=? WHERE user_id=?",
                             (bugun, yeni_toplam, user_id))
            else:
                conn.execute("INSERT INTO spin_kaydi VALUES (?,?,?)", (user_id, bugun, yeni_toplam))
            conn.commit()
        if odul[1] == "para":
            self.para_guncelle(user_id, odul[2])
        elif odul[1] == "xp":
            pass  # XP bot.py'den eklenir
        if yeni_toplam >= 5:
            self.basari_ver(user_id, "spin_5")
        return odul, yeni_toplam

    # ─── Bahis ──────────────────────────────────────────────────────────────

    def bahis_yap(self, user_id: int, mac_id: int, hedef_takim_id: int, miktar: int):
        if miktar < 500:
            return False, "Minimum bahis 500₺."
        para = self.para_getir(user_id)
        if para < miktar:
            return False, f"Yetersiz bakiye: {para:,}₺"
        with self._conn() as conn:
            mevcut = conn.execute(
                "SELECT COUNT(*) FROM bahisler WHERE mac_id=? AND user_id=? AND odendi=0",
                (mac_id, user_id)
            ).fetchone()[0]
            if mevcut:
                return False, "Bu maça zaten bahis yaptın."
            mac = conn.execute("SELECT * FROM fikstur WHERE mac_id=?", (mac_id,)).fetchone()
            if not mac or mac["oynanmis"]:
                return False, "Maç bulunamadı veya zaten oynandı."
            if hedef_takim_id not in (mac["ev_takim_id"], mac["dep_takim_id"]):
                return False, "Bu takım bu maçta oynamıyor."
            conn.execute(
                "INSERT INTO bahisler (mac_id,user_id,hedef_takim,miktar) VALUES (?,?,?,?)",
                (mac_id, user_id, hedef_takim_id, miktar)
            )
            conn.commit()
        self.para_guncelle(user_id, -miktar)
        t = self.takim_id(hedef_takim_id)
        return True, f"✅ *{t['isim']}* için {miktar:,}₺ bahis yaptın! (x2 kazanç)"

    def _bahis_ode(self, mac_id: int, kazanan_id: Optional[int]):
        with self._conn() as conn:
            bahisler = conn.execute(
                "SELECT * FROM bahisler WHERE mac_id=? AND odendi=0", (mac_id,)
            ).fetchall()
            for b in [dict(x) for x in bahisler]:
                if kazanan_id and b["hedef_takim"] == kazanan_id:
                    self.para_guncelle(b["user_id"], b["miktar"] * 2)
                    self.basari_ver(b["user_id"], "bahis_kazan")
                conn.execute("UPDATE bahisler SET odendi=1 WHERE bahis_id=?", (b["bahis_id"],))
            conn.commit()

    def mac_bahisleri(self, mac_id: int) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bahisler WHERE mac_id=? AND odendi=0", (mac_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── Başarılar ──────────────────────────────────────────────────────────

    def basari_ver(self, user_id: int, kod: str) -> bool:
        if kod not in BASARILAR:
            return False
        with self._conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO basarilar (user_id,basari_kodu,tarih) VALUES (?,?,?)",
                    (user_id, kod, date.today().isoformat())
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def kullanici_basarilari(self, user_id: int) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT basari_kodu, tarih FROM basarilar WHERE user_id=? ORDER BY tarih DESC",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── Cumhuriyet Kupası ───────────────────────────────────────────────────

    def kupa_olustur(self, sezon: int = 1):
        with self._conn() as conn:
            mevcut = conn.execute(
                "SELECT COUNT(*) FROM kupa_maclar WHERE sezon=?", (sezon,)
            ).fetchone()[0]
            if mevcut:
                return False, "Kupa bu sezon zaten oluşturuldu."
        tum = []
        for lig in (1, 2):
            tum.extend(self.tum_takimlar(lig))
        if len(tum) < 2:
            return False, "En az 2 takım gerekli."
        ids = [t["takim_id"] for t in tum]
        random.shuffle(ids)
        n = 1
        while n < len(ids):
            n *= 2
        while len(ids) < n:
            ids.append(None)
        with self._conn() as conn:
            for i in range(0, n, 2):
                ev, dep = ids[i], ids[i + 1]
                if ev and dep:
                    conn.execute("""
                        INSERT INTO kupa_maclar (tur,ev_takim_id,dep_takim_id,oynanmis,sezon)
                        VALUES (1,?,?,0,?)
                    """, (ev, dep, sezon))
                elif ev:
                    conn.execute("""
                        INSERT INTO kupa_maclar (tur,ev_takim_id,dep_takim_id,ev_gol,dep_gol,oynanmis,sezon)
                        VALUES (1,?,NULL,3,0,1,?)
                    """, (ev, sezon))
            conn.commit()
        return True, f"🏅 Cumhuriyet Kupası {len(tum)} takımla başladı!"

    def kupa_sonraki_mac(self, user_id: int, sezon: int = 1) -> Optional[dict]:
        takim = self.takim_user(user_id)
        if not takim:
            return None
        tid = takim["takim_id"]
        with self._conn() as conn:
            r = conn.execute("""
                SELECT * FROM kupa_maclar
                WHERE (ev_takim_id=? OR dep_takim_id=?) AND oynanmis=0 AND sezon=?
                ORDER BY tur ASC LIMIT 1
            """, (tid, tid, sezon)).fetchone()
            return dict(r) if r else None

    def kupa_mac_oyna(self, mac_id: int, talep_eden: int, sezon: int = 1):
        with self._conn() as conn:
            r = conn.execute("SELECT * FROM kupa_maclar WHERE mac_id=?", (mac_id,)).fetchone()
            if not r:
                return None, "Kupa maçı bulunamadı."
            mac = dict(r)
        if mac["oynanmis"]:
            return None, "Bu maç zaten oynandı."
        if talep_eden not in (mac["ev_takim_id"], mac["dep_takim_id"]):
            return None, "Bu senin kupa maçın değil."
        ev_t = self.takim_id(mac["ev_takim_id"])
        dep_t = self.takim_id(mac["dep_takim_id"])
        ev_guc = self.takim_gucu(mac["ev_takim_id"])
        dep_guc = self.takim_gucu(mac["dep_takim_id"])
        ev_oran = (ev_guc * 1.05) / ((ev_guc * 1.05) + dep_guc)
        ev_gol = max(0, min(9, round(random.gauss(ev_oran * 3.5, 1.2))))
        dep_gol = max(0, min(9, round(random.gauss((1 - ev_oran) * 3.5, 1.2))))
        uzatma = False
        if ev_gol == dep_gol:
            uzatma = True
            ev_gol += random.randint(0, 2)
            dep_gol += random.randint(0, 2)
            if ev_gol == dep_gol:
                ev_gol += random.randint(0, 1)
        kazanan_id = mac["ev_takim_id"] if ev_gol > dep_gol else mac["dep_takim_id"]
        kaybeden_id = mac["dep_takim_id"] if ev_gol > dep_gol else mac["ev_takim_id"]
        kazanan_t = self.takim_id(kazanan_id)
        kaybeden_t = self.takim_id(kaybeden_id)
        bugun = date.today().isoformat()
        with self._conn() as conn:
            conn.execute("""
                UPDATE kupa_maclar SET ev_gol=?,dep_gol=?,oynanmis=1,oynanma_tarihi=?
                WHERE mac_id=?
            """, (ev_gol, dep_gol, bugun, mac_id))
            conn.commit()
        self.para_guncelle(kazanan_t["user_id"], 8_000)
        self.para_guncelle(kaybeden_t["user_id"], 2_000)
        # Şampiyon kontrolü: bu turda başka oynanmamış maç var mı?
        with self._conn() as conn:
            kalan = conn.execute(
                "SELECT COUNT(*) FROM kupa_maclar WHERE tur=? AND oynanmis=0 AND sezon=?",
                (mac["tur"], sezon)
            ).fetchone()[0]
        sampiyon = None
        if kalan == 0:
            with self._conn() as conn:
                # Kazananları bir üst tura ekle
                galip_ids = [
                    dict(r)["ev_takim_id"] if dict(r)["ev_gol"] > dict(r)["dep_gol"] else dict(r)["dep_takim_id"]
                    for r in conn.execute(
                        "SELECT * FROM kupa_maclar WHERE tur=? AND sezon=?", (mac["tur"], sezon)
                    ).fetchall()
                    if dict(r)["dep_takim_id"] is not None
                ]
            if len(galip_ids) == 1:
                sampiyon = self.takim_id(galip_ids[0])
                if sampiyon:
                    self.basari_ver(sampiyon["user_id"], "kupa_sampiyon")
                    self.para_guncelle(sampiyon["user_id"], 50_000)
            elif len(galip_ids) > 1:
                random.shuffle(galip_ids)
                if len(galip_ids) % 2 == 1:
                    galip_ids.append(None)
                with self._conn() as conn:
                    for i in range(0, len(galip_ids), 2):
                        ev2, dep2 = galip_ids[i], galip_ids[i + 1]
                        if ev2 and dep2:
                            conn.execute("""
                                INSERT INTO kupa_maclar (tur,ev_takim_id,dep_takim_id,oynanmis,sezon)
                                VALUES (?,?,?,0,?)
                            """, (mac["tur"] + 1, ev2, dep2, sezon))
                        elif ev2:
                            conn.execute("""
                                INSERT INTO kupa_maclar (tur,ev_takim_id,dep_takim_id,ev_gol,dep_gol,oynanmis,sezon)
                                VALUES (?,?,NULL,3,0,1,?)
                            """, (mac["tur"] + 1, ev2, sezon))
                    conn.commit()
        return {
            "mac_id": mac_id,
            "tur": mac["tur"],
            "ev_takim": ev_t["isim"],
            "dep_takim": dep_t["isim"],
            "ev_takim_id": mac["ev_takim_id"],
            "dep_takim_id": mac["dep_takim_id"],
            "ev_takim_user": ev_t["user_id"],
            "dep_takim_user": dep_t["user_id"],
            "ev_gol": ev_gol,
            "dep_gol": dep_gol,
            "kazanan_id": kazanan_id,
            "kazanan_isim": kazanan_t["isim"],
            "uzatma": uzatma,
            "sampiyon": sampiyon,
        }, None

    def kupa_tablo(self, sezon: int = 1) -> list:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT k.*,
                    (SELECT isim FROM takimlar WHERE takim_id=k.ev_takim_id)  AS ev_isim,
                    (SELECT isim FROM takimlar WHERE takim_id=k.dep_takim_id) AS dep_isim
                FROM kupa_maclar k WHERE k.sezon=? ORDER BY k.tur, k.mac_id
            """, (sezon,)).fetchall()
            return [dict(r) for r in rows]

    # ─── Sezon Sıfırlama ────────────────────────────────────────────────────

    def sezon_sampiyon(self, lig: int = 1) -> Optional[dict]:
        t = self.tum_takimlar(lig)
        return t[0] if t else None

    def sezon_sifirla(self, lig: int = 1):
        takimlar = self.tum_takimlar(lig)
        if takimlar:
            self.basari_ver(takimlar[0]["user_id"],
                            "sezon_sampiyon" if lig == 1 else "lig2_sampiyonu")
        with self._conn() as conn:
            for t in takimlar:
                conn.execute("""
                    UPDATE takimlar SET puan=0,galibiyet=0,beraberlik=0,maglubiyet=0,
                    atilan_gol=0,yenilen_gol=0,mac_sayisi=0,son_mac=NULL,sezon=sezon+1
                    WHERE takim_id=?
                """, (t["takim_id"],))
                conn.execute("""
                    UPDATE oyuncular SET gol=0,asist=0,sari_kart=0,kirmizi_kart=0
                    WHERE takim_id=?
                """, (t["takim_id"],))
            conn.execute("DELETE FROM fikstur WHERE lig=?", (lig,))
            conn.commit()
        return len(takimlar)

    # ─── Grup Bildirimi ─────────────────────────────────────────────────────

    def grup_kaydet(self, chat_id: int):
        with self._conn() as conn:
            conn.execute("INSERT OR IGNORE INTO grup_chatler VALUES (?)", (chat_id,))
            conn.commit()

    def gruplari_getir(self) -> list:
        with self._conn() as conn:
            rows = conn.execute("SELECT chat_id FROM grup_chatler").fetchall()
            return [r["chat_id"] for r in rows]
