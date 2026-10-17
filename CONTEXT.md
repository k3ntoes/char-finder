# Capo Finder — Project Context

> Dokumen ini merangkum semua keputusan desain dari sesi grilling. Update dokumen ini setiap ada keputusan baru sebelum implementasi dimulai.

---

## 🎯 Goal
Membangun web app untuk menemukan karakter (capo) di market game **The Syndicate** dengan statistik tinggi dan harga rendah. App mengambil data dari API market listing, menganalisis harga dan statistik, lalu memberikan rekomendasi pembelian berdasarkan algoritma HBDS (Hedonic-Bayesian Deal Scoring).

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|---|---|
| Package Manager & CLI | `uv` (`uv run`, `uv add`, virtualenv management) |
| Backend | FastAPI (Python) |
| Frontend | Jinja2 Templates (server-side rendering) with Tailwind CSS (Slate/Zinc neutral dark palette) |
| Database | SQLite (via Python built-in `sqlite3`) |
| Scheduler | APScheduler (AsyncIOScheduler) |
| HTTP Client | aiohttp |

> [!IMPORTANT]
> **No Scientific Libraries Needed**: `pandas` and `numpy` are explicitly **NOT needed**. Pure Python standard library (`math`, `statistics`, `collections`) handles all regression and Bayes calculations with ~2.5ms latency and ~1MB RAM footprint.


---

## 📡 API & Data Source

- **Endpoint:** `https://thesyndicate.games/api/v3/market/listings`
- **Active Dataset / Snapshot:** `latest_market_data.json` (digunakan sebagai active snapshot/fallback data utama).
- **Listing Filter Rule:** Web app hanya mengonsumsi dan menampilkan listing yang masuk rekomendasi pembelian (`deal_score >= 50`).
- **Auth:** Memerlukan headers dari browser (user login ke thesyndicate.games terlebih dahulu)
- **Root JSON Structure:**
```json
{
  "listings": [...],
  "floors": {
    "rare":      { "lamports": "7319133", "usd": 0.777 },
    "epic":      { "lamports": "36571643", "usd": 3.881 },
    "legendary": { "lamports": "372612948", "usd": 39.545 },
    "founder":   { "lamports": "2114060964", "usd": 224.365 },
    "god":       { "lamports": "4950495050", "usd": 525.396 }
  },
  "solUsd": 106.13,
  "at": "2026-10-16T14:31:06.187Z"
}
```

### Listing Item Fields
```
id, capoId, settling, sellerId, seller, listedAt, priceUsd, allInUsd,
priceLamports (string), gateLamports,
capo: { name, character_name, rarity, tier, personality, specialty,
        gender, portrait_variant, is_founder, is_promo, art_variant,
        mint_index, age, stat_muscle, stat_brains, stat_hustle,
        stat_grit, stat_rep, trait_greed, trait_finesse, trait_passion,
        promo_next_tier, tier_promoted_at, next_promo_hours,
        gates, img: {sm, md} }
```

---

## 🔐 Authentication

- User paste raw headers dari browser DevTools (Network tab → Request Headers)
- Format input: satu header per baris, `Header-Name: value`
- Headers disimpan ke SQLite, dibaca ulang saat app restart (tidak perlu input ulang)
- Nilai sensitif (Cookie, Authorization) di-mask saat ditampilkan di UI

---

## 🔄 Data Refresh

- **Interval:** Auto-refresh tiap **5 menit** via APScheduler background job
- **Cache:** Data disimpan di memory (`cached_listings`, `cached_floors`, `cached_sol_usd`)
- **Fallback:** Jika fetch gagal, gunakan data cache lama dan log error
- **Manual refresh:** Tersedia endpoint `/api/refresh` yang mendukung GET & POST secara **asinkron**.

---

## 📊 Scoring & Statistik

### Total Stat
```python
total_stat = stat_muscle + stat_brains + stat_hustle + stat_grit + stat_rep
```
> `trait_greed`, `trait_finesse`, `trait_passion` are NOT counted in `total_stat`, but ARE displayed as columns and filter options in UI.

### Stat Bucket
```python
stat_bucket = (total_stat // 10) * 10  # contoh: stat 47 → bucket 40
```

### Value Score (untuk sorting UI)
```python
value_score = total_stat / priceUsd
```

---

## 💰 Satuan Harga untuk Deal Detection

> **Keputusan: Gunakan LAMPORTS (bukan USD)** untuk semua perhitungan deal detection.

**Alasan:**
- Dalam 54 menit antara 2 fetch, **0 seller mengubah harga lamports mereka**
- Semua perubahan harga USD murni dari **fluktuasi kurs SOL/USD**
- Menggunakan USD menyebabkan **false positive**
- USD hanya digunakan untuk **display** di UI (menonjolkan harga in-game USD), bukan untuk kalkulasi algoritma

```python
# Konversi
price_lamports = int(listing["priceLamports"])  # sudah ada di data
floor_lamports = int(floors[rarity]["lamports"])  # dari root API
```

---

## 💾 Database Schema (SQLite)

### Tabel `headers`
```sql
CREATE TABLE headers (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT
);
```

### Tabel `settings`
```sql
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
```
*(Digunakan untuk menyimpan `ntfy_topic` dan konfigurasi user lainnya)*

### Tabel `notified_deals`
```sql
CREATE TABLE IF NOT EXISTS notified_deals (
  listing_id TEXT PRIMARY KEY,
  capo_id TEXT,
  deal_score REAL,
  notified_at TEXT
);
```

### Tabel `price_history`
Menyimpan agregat per fetch (bukan raw listing). 1 baris per `(rarity, stat_bucket)` per fetch cycle.
```sql
CREATE TABLE price_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fetched_at TEXT NOT NULL,
  rarity TEXT NOT NULL,
  stat_bucket INTEGER NOT NULL,
  min_lamports INTEGER NOT NULL,
  avg_lamports REAL NOT NULL,
  count INTEGER NOT NULL
);
CREATE INDEX idx_ph_rarity_bucket ON price_history(rarity, stat_bucket);
CREATE INDEX idx_ph_fetched_at ON price_history(fetched_at);
```

> **Cleanup:** Simpan maksimum 200 baris per `(rarity, stat_bucket)`, hapus terlama otomatis.
> **Rolling window:** Gunakan **24 fetch terakhir** (~2 jam) untuk baseline historis.

---

## 🔥 Algoritma HBDS v2 (Hedonic-Bayesian Deal Scoring)

> **Keputusan: Adopsi HBDS v2** dengan penyempurnaan utama:

### 1. Jangkar Harga Lantai (Floor Price Anchoring pada Intersep OLS)
Intersep regresi OLS dijangkar langsung pada *floor price* per rarity (`floor_lamports`) agar tidak ada fair price yang jatuh di bawah harga lantai pasar:
```python
intercept = max(floor_lamports, mean_p - slope * mean_s)
fair_price_lamports = intercept + slope * total_stat
```

### 2. Quality Gate & Penalti Eksponensial
- Penalti eksponensial untuk stat di bawah median (`s < median_stat`).
- Pembatasan skor di bawah 60 (listing dengan stat di bawah standar tidak bisa dikategorikan sebagai *Steal*).

### 3. Apresiasi Non-Linear untuk Stat Elit
- Apresiasi non-linear khusus untuk stat sangat tinggi (`s > median_stat * 1.5`).

### 4. Penyimpanan Parameter Lengkap
Setiap listing yang dievaluasi menyimpan parameter lengkap: `fair_price`, `val_ratio`, `disc_bucket`/`bayes_dev`, `floor_bonus`.

---

## 🔔 Notification System (ntfy.sh)

- **Pub/Sub Topic:** `ntfy.sh/<topic>`
- **Configuration:** `ntfy_topic` dikonfigurasi di halaman `/settings` dan disimpan di tabel SQLite `settings`.
- **Trigger Condition:** Hanya dipicu untuk listing baru (belum ada di tabel `notified_deals`) dengan `deal_score >= 80` (🔥 Steal).
- **Payload Format:**
  - **Title:** `🔥 Steal Detected: {name}`
  - **Message:** `Score {score} | {rarity} {tier} | Stat {total_stat} | {price_usd} USD`
  - **Click URL:** `https://thesyndicate.games/market`

---

## 💻 Testing / Fallback Mode & Port

- **Default Port:** `8000`
- **Offline / Demo Fallback:** Jika headers tidak diset atau API fetch gagal, aplikasi dapat memuat data sample dari `latest_market_data.json` atau `data2.json`.

---

## 🖥️ UI & Layout: Analytical Screener Dashboard

Arsitektur UI baru mengusung konsep **Analytical Screener Dashboard** modern:
- **Color Palette:** Slate / Zinc neutral dark theme.
- **Legacy UI Removal:** Bebas dari elemen game lawas/avatar yang tidak perlu; fokus penuh pada data analitik, metrik, dan efisiensi pembelian.
- **Two-Tier Screener Bar:** Bar filter bertingkat dua untuk navigasi cepat dan penyaringan ketat berdasarkan rarity, tier, specialty, price range, min stat, dan min deal score.
- **Dual-Name with 1-Click Copy:** Tampilan nama capo/karakter yang ringkas disertai tombol 1-Click Copy untuk ID/nama.
- **Prominent USD Pricing:** Tampilan harga in-game USD yang menonjol (`priceUsd`, `fair_price`, penghematan).
- **HBDS Detail Accordion:** Akordeon rincian breakdown HBDS v2 (menampilkan komponen diskon fair price, bucket deviation, value ratio, dan floor bonus).

### Routes
| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Halaman utama — Analytical Screener Dashboard |
| GET | `/settings` | Halaman pengaturan auth headers & ntfy.sh topic |
| POST | `/settings` | Simpan auth headers, ntfy_topic, dan opsi load sample data |
| GET / POST | `/api/refresh` | Manual trigger fetch asinkron, return JSON |

---

## 📁 File Structure

```
char-finder/
├── main.py           # FastAPI app, routes, filter logic
├── db.py             # SQLite handler (headers + settings + notified_deals + price_history)
├── fetcher.py        # Fetch API, HBDS v2 scoring, OLS regression, ntfy sender, sample fallback
├── scheduler.py      # APScheduler background job (5 menit)
├── templates/
│   ├── base.html     # Layout, navbar, floors panel, status bar
│   ├── index.html    # Analytical Screener Dashboard & akordeon rincian HBDS
│   └── settings.html # Form input/edit auth headers & ntfy topic + Load Sample Data
├── CONTEXT.md        # Dokumen ini
├── latest_market_data.json # Active market dataset snapshot
├── data.json         # Contoh response API fetch 1
├── data2.json        # Contoh response API fetch 2
└── requirements.txt
```

---

*Terakhir diperbarui: 2026-10-17*
