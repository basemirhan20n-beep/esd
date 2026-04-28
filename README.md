# 🏛️ Cumhuriyet Parti Yönetim Botu v2.0

## 🚀 Kurulum

```bash
pip install python-telegram-bot[job-queue]==21.6
```

**config.py** dosyasına bot tokenını gir:
```python
BOT_TOKEN = "SENIN_TOKEN_BURAYA"
ADMIN_IDS = [123456789]  # Telegram kullanıcı ID'lerin
```

```bash
python bot.py
```

---

## ⚽ Futbol Komutları

| Komut | Açıklama |
|-------|----------|
| `/takim_kur <İsim>` | Takım kur (2. lig → 1. lig) |
| `/takim` | Takım kadrosu ve istatistikler |
| `/piyasa` | Transfer pazarını gör |
| `/satin_al <id>` | Oyuncu satın al |
| `/sat <id> <fiyat>` | Oyuncu sat |
| `/sat_iptal <id>` | Satışı iptal et |
| `/antrenman` | Günlük antrenman (oyuncular güçlenir) |
| `/mac` | Sıradaki lig maçını oyna |
| `/lig` | 1. Lig tablosu |
| `/lig 2` | 2. Lig tablosu |
| `/fikstur` | Haftalık fikstür |
| `/son_maclar` | Son 5 maç |
| `/cuzdan` | Bakiye görüntüle |
| `/taktik <formasyon>` | Taktik seç (4-3-3, 4-4-2, 5-3-2, 3-5-2, 4-2-3-1) |
| `/altyapi` | Altyapıdan oyuncu çıkar (15.000₺) |
| `/istatistik` | Oyuncu gol/asist istatistikleri |
| `/golcular` | Sezon golcü sıralaması |
| `/kupa` | Kupa maçını oyna |
| `/kupa_tablo` | Kupa tablosu |
| `/spin` | Günlük şans çarkı |
| `/basarilar` | Başarı rozetlerin |

## ⚙️ Admin Komutları

| Komut | Açıklama |
|-------|----------|
| `/kupa_olustur` | Cumhuriyet Kupası başlat |
| `/sezon_sifirla [1/2]` | Sezonu sıfırla, şampiyon ödüllendir |
| `/fikstur_olustur [1/2]` | Manuel fikstür oluştur |
| `/rol_ver @kullanici Makam` | Kullanıcıya makam ver |
| `/rol_al @kullanici` | Makamı al |
| `/duyuru Mesaj` | Tüm kullanıcılara DM gönder |
| `/puan_ver @kullanici miktar` | XP ver |
| `/guven_ver @kullanici miktar` | Güven puanı değiştir |
| `/grup_kaydet` | Grubu maç bildirimleri için kaydet |

## 🏆 Lig Sistemi

- **2. Lig**: 10 takım dolunca başlar (otomatik)
- **1. Lig**: 15 takım dolunca başlar (otomatik)
- Yeni takım eklenince fikstüre eklenir, **puanlar sıfırlanmaz**
- Sezon sıfırlanınca terfi/düşüş mekanizması devreye girer

## 🎯 Özellikler

- 📨 Maç sonuçları **özel mesajla** rakibe bildirilir
- 📣 Grup kayıt: `/grup_kaydet` ile gruba sonuçlar gelir
- 🏥 Sakatlanma & kart sistemi (maç atlama)
- 🎯 Taktik avantajı (5 formasyon)
- 🌱 Altyapı: ucuz ama gelişmeye açık genç oyuncular
- 💰 Bahis: maç öncesi bahis, 2x ödeme
- 🎰 Şans çarkı: günlük para/XP/güç ödülü
- 🏅 Başarı rozetleri: otomatik kazanılır
- 🔄 Sezon sıfırlama: şampiyona ödül, terfi/düşüş

## 📁 Dosya Yapısı

```
bot.py          ← Ana bot, komutlar, görev sistemi
futbol.py       ← Futbol komutları ve callback handler
futbol_db.py    ← Veritabanı katmanı (tüm oyun mantığı)
database.py     ← Parti/kullanıcı veritabanı
config.py       ← Token ve admin ID'leri
requirements.txt
```
