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
| Frontend | Jinja2 Templates (server-side rendering) |
| Database | SQLite (via Python built-in `sqlite3`) |
| Scheduler | APScheduler (AsyncIOScheduler) |
| HTTP Client | aiohttp |

> [!IMPORTANT]
> **No Scientific Libraries Needed**: `pandas` and `numpy` are explicitly **NOT needed**. Pure Python standard library (`math`, `statistics`, `collections`) handles all regression and Bayes calculations with ~2.5ms latency and ~1MB RAM footprint.


---

## 📡 API

- **Endpoint:** `https://thesyndicate.games/api/v3/market/listings`
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
- **Manual refresh:** Tersedia endpoint `GET /api/refresh` yang bisa dipanggil via tombol di UI

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

**Alasan (berdasarkan simulasi data.json vs data2.json):**
- Dalam 54 menit antara 2 fetch, **0 seller mengubah harga lamports mereka**
- Semua perubahan harga USD (rata-rata -1.87%) murni dari **fluktuasi kurs SOL/USD** ($106.13 → $104.15)
- Menggunakan USD menyebabkan **false positive**: listing stat rendah tiba-tiba jadi "deal" hanya karena SOL dump
- USD hanya digunakan untuk **display** di UI, bukan untuk kalkulasi algoritma

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

## 🔥 Algoritma Deal Detection: HBDS (Hedonic-Bayesian Deal Scoring)

> **Keputusan: Adopsi HBDS** menggantikan logika 3 kondisi lama.
>
> Alasan: Old logic menghasilkan ~0% deal discovery, 5 false positive, dan melewatkan 121 deal nyata dalam simulasi.

### Input
- `listings` dari fetch terbaru
- `floors` dari root API (lamports per rarity)
- `bucket_history`: data agregat dari SQLite (24 fetch terakhir)

### Step 1: OLS Regression per Rarity (Fair Price)
Untuk setiap rarity, hitung regresi linear `fair_price_lamports = intercept + slope * total_stat`:

```python
mean_s = sum(stats) / n
mean_p = sum(prices_lamps) / n
var_s = sum((s - mean_s)**2 for s in stats)
cov_sp = sum((stats[i]-mean_s)*(prices[i]-mean_p) for i in range(n))
slope = max(0.0, cov_sp / var_s if var_s > 0 else 0.0)
intercept = max(floor_lamports, mean_p - slope * mean_s)
fair_price_lamports = intercept + slope * total_stat
```

### Step 2: Empirical Bayes Shrinkage (Bucket Benchmark)
```python
hist_avg_lamps, hist_count = bucket_history.get((rarity, stat_bucket), (None, 0))
if hist_avg_lamps is None:
    hist_avg_lamps = fair_price_lamports
    hist_count = 0

K = 5  # shrinkage constant
alpha = hist_count / (hist_count + K)
benchmark_lamports = alpha * hist_avg_lamps + (1 - alpha) * fair_price_lamports
```

### Step 3: Sinyal Deal
```python
# A. Diskon vs fair price
disc_fair = max(0.0, (fair_price - price) / fair_price)

# B. Diskon vs bucket benchmark
disc_bucket = max(0.0, (benchmark - price) / benchmark)

# C. Value efficiency ratio
val_score = total_stat / price_lamports
val_ratio = val_score / median_val_score_rarity  # median dari seluruh rarity di fetch ini

# D. Floor snipe booster
if price <= floor_lamports * 1.15 and total_stat > median_stat_rarity:
    floor_bonus = min(1.0, (total_stat - median_stat_rarity) / median_stat_rarity)
else:
    floor_bonus = 0.0
```

### Step 4: Composite Score (0–100)
```python
base_score = (
    min(40.0, disc_fair * 60.0) +
    min(35.0, disc_bucket * 50.0) +
    min(25.0, max(0.0, (val_ratio - 1.0) * 15.0))
)
if floor_bonus > 0:
    base_score = max(base_score, 50.0 + floor_bonus * 40.0)

deal_score = round(min(100.0, base_score), 1)
```

### Badge & Threshold
| Score | Badge | Keterangan |
|---|---|---|
| ≥ 80 | 🔥 **Steal** | Diskon masif vs fair value / floor snipe high stat |
| 65–79 | ⚡ **Great Deal** | Diskon signifikan vs peers |
| 50–64 | ✍️ **Good Value** | Di atas median efisiensi pasar |
| < 50 | ○ Tidak ditandai | Fair price atau overpriced |

### Cold Start & Fallback
| Kondisi | Penanganan |
|---|---|
| 0 history di DB | Regresi berjalan dari data live fetch (α=0, full fallback ke fair_price) |
| Bucket sparse (N < 5) | Bayes shrinkage otomatis meredam noise |
| Ultra-rare (god/founder, N < 5 total) | slope=0, fair_price=floor_lamports, evaluasi via floor_bonus & val_ratio |

### Explainability String (untuk UI)
```
"🔥 Deal Score: 91.4 | 62.7% below fair value | 57.5% below bucket avg | 3.2x stats-per-SOL vs peers"
```

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
- **Offline / Demo Fallback:** Jika headers tidak diset atau API fetch gagal, aplikasi dapat memuat data sample dari `data2.json` (juga menyediakan tombol 'Load Sample Data' di halaman settings/UI).

---

## 🖥️ UI & Routes

### Routes
| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Halaman utama — tabel listing dengan filter |
| GET | `/settings` | Halaman pengaturan auth headers & ntfy.sh topic |
| POST | `/settings` | Simpan auth headers, ntfy_topic, dan opsi load sample data |
| GET | `/api/refresh` | Manual trigger fetch, return JSON |

### Filter yang Tersedia (di halaman `/`)
- `rarity` (dropdown)
- `tier` (dropdown)
- `specialty` (dropdown)
- `personality` (dropdown)
- `gender` (dropdown)
- `trait_greed` / `trait_finesse` / `trait_passion` (dropdown/filter)
- `min_price` / `max_price` (USD, number input)
- `min_stat` (number input)
- `min_deal_score` (number input, 0–100)
- `sort_by`: `deal_score` | `value_score` | `price_usd` | `total_stat` (default: `deal_score` desc)

### Tabel Kolom
`#`, `Name`, `Character`, `Rarity`, `Tier`, `Specialty`,
`Total Stat`, `Muscle`, `Brains`, `Hustle`, `Grit`, `Rep`,
`Greed`, `Finesse`, `Passion`,
`Price USD`, `Floor USD`, `Fair Price`, `Disc %`, `Deal Score`, `Badge`,
`Seller`, `Listed At`

### UI Features
- **Theme:** Dark mode
- **Floors Panel:** Info bar menampilkan floors per rarity + SOL/USD price (real-time)
- **Deal rows:** Warna baris berbeda per badge tier (Steal = hijau terang, Great Deal = hijau, Good Value = biru)
- **Sortable columns:** Klik header kolom untuk toggle asc/desc
- **Stats summary:** Total: X | Filtered: Y | 🔥 Deals: Z
- **Refresh button:** Panggil `/api/refresh` via JS fetch + tampilkan waktu refresh terakhir
- **Explainability tooltip:** Hover pada deal score menampilkan breakdown komponen score

---

## 📁 File Structure

```
char-finder/
├── main.py           # FastAPI app, routes, filter logic
├── db.py             # SQLite handler (headers + settings + notified_deals + price_history dalam Lamports)
├── fetcher.py        # Fetch API, HBDS scoring, OLS regression, ntfy sender, sample fallback
├── scheduler.py      # APScheduler background job (5 menit)
├── templates/
│   ├── base.html     # Layout, navbar, floors panel, status bar
│   ├── index.html    # Tabel sortable + filter
│   └── settings.html # Form input/edit auth headers & ntfy topic + Load Sample Data
├── CONTEXT.md        # Dokumen ini
├── data.json         # Contoh response API fetch 1
├── data2.json        # Contoh response API fetch 2
└── requirements.txt
```

---

## ⏳ Keputusan yang Belum Final (Resolved)

- [x] Apakah traits (`trait_greed`, `trait_finesse`, `trait_passion`) akan ikut dihitung di versi berikutnya? *(Resolved: Tidak dihitung di `total_stat`, tapi ditampilkan sebagai kolom dan filter UI)*
- [x] Fitur watchlist/favorit capo? *(Deferred to v2)*
- [x] Notifikasi saat deal ditemukan? *(Resolved: ntfy.sh pub/sub untuk score >= 80)*
- [x] Port default server (usulan: `8000`) *(Resolved: Port 8000 + offline/demo fallback ke data2.json)*

---

## 📈 Simulasi Validasi Algoritma

Berdasarkan perbandingan `data.json` (Fetch 1, 14:31 UTC) vs `data2.json` (Fetch 2, 15:25 UTC):

| Metrik | Old Logic | HBDS |
|---|---|---|
| Deal terdeteksi | 34 (3.59%) | 150 (15.84%) |
| False positive | 5 (kurs SOL turun) | 0 |
| Deal terlewatkan | 121 | 0 |
| High-tier detection | ❌ | ✅ |
| Output | Binary | Score 0–100 |

Contoh deal yang dilewatkan Old Logic tapi ditangkap HBDS:
- `Inferno Ornella` (epic captain, stat 89, $5.16 vs fair $13.70, disc 62%, score 95.84)
- `Flare Pasquale` (epic captain, stat 95, $5.21 vs fair $14.22, disc 63%, score 92.19)
- `Sean Loomis` (rare captain, stat 39, $0.829, score 100 🔥)

---

*Terakhir diperbarui: 2026-10-16*
