# 0001. Redesain Menjadi Analytical Screener Dashboard & Filter Rekomendasi Terkurasi

- **Status**: Accepted
- **Date**: 2026-10-17
- **Deciders**: Core Engineering & Product Team

## Context

Tampilan antarmuka (*UI*) legacy pada aplikasi Char-Finder menggunakan tema skeuomorphic *pawn shop* game yang menyertakan tab kosong (`[ BUY ]`, `[ SELL ]`, dll.), serta mengalami masalah teknis berupa avatar gambar rusak (*broken images*) akibat URL legacy server relatif (`/_next/image...`). Selain itu, antarmuka lama tidak menyediakan filter untuk statistik tempur maupun spesialisasi karakter. 

Secara arsitektural dan fungsional, platform web seharusnya hanya menyajikan rekomendasi pembelian berkualitas tinggi (yaitu sekitar 169 capo dengan `deal_score >= 50` dari total 919 listing mentah yang ada di `latest_market_data.json`), alih-alih membebani pengguna dengan seluruh mentah listing pasar yang tidak efisien.

## Decision

1. **Penghapusan Tema Skeuomorphic & Tab Kosong**:
   Menghapus seluruh elemen visual skeuomorphic game legacy dan braket dekoratif, menggantinya dengan layout *Analytical Screener Dashboard* bernuansa *Modern Neutral Dark (Zinc/Slate)* yang berpedoman ketat pada standar `/antislop` (C-1 Information Density, C-2 Fast Interaction, R-02 No gratuitous clutter, R-03 Semantic colors).

2. **Penghapusan Avatar Sepenuhnya**:
   Menghilangkan kolom dan komponen avatar secara total untuk mengeliminasi ketergantungan pada asset server legacy yang gagal diakses dan mempercepat waktu muat render tabel.

3. **Fokus Kurasi Rekomendasi Pembelian**:
   Hanya menampilkan listing yang masuk dalam kategori rekomendasi pembelian (`deal_score >= 50`, ~169 capo terpilih), dengan pengaturan default pengurutan (*sorting*) berdasarkan `deal_score` secara descending.

4. **Adopsi Two-Tier Screener Bar**:
   - **Tier 1**: Berisi *quick deal tier segmenter* (`All Deals`, `🔥 Steals`, `⚡ Great Deals`, `✍️ Good Value`), filter Rarity, Price range, dan Global Search.
   - **Tier 2 (Collapsible Drawer)**: Menyediakan filter lanjutan untuk nilai minimum 5 statistik tempur, 3 traits kepribadian, dan 5 spesialisasi resmi.

5. **High-Density Screener Table**:
   Menggunakan tabel data berkerapatan tinggi dengan perataan angka monospaced (`font-mono tabular-nums`), *sortable headers*, serta fitur *Inline Expandable Sub-Row* untuk transparansi kalkulasi HBDS secara mendalam (mencakup *fair price*, deviasi Bayesian, dan *floor booster*).

6. **Live Market Ticker & System Health Bar**:
   Mengganti header lama dengan bar informasi real-time yang menampilkan harga lantai (*floor price*) per tier rarity, kurs konversi SOL/USD, status sistem (live/offline), serta timestamp sinkronisasi data terakhir.

## Consequences

### Positive Consequences
- **Peningkatan Efisiensi Kognitif & Informasi**: Pengguna dapat langsung fokus pada peluang pembelian terbaik tanpa gangguan elemen dekoratif yang tidak perlu.
- **Performa & Kecepatan**: Menghilangkan resource eksternal yang rusak (avatar) mempercepat render DOM dan mengurangi latensi interaksi.
- **Akurasi Filtering**: Kemampuan filter multi-parameter berdasarkan statistik tempur, trait, dan spesialisasi memberikan presisi pencarian tingkat institusional.
- **Kepatuhan Desain**: Sepenuhnya selaras dengan prinsip desain bersih dan fungsional (`/antislop`).

### Negative Consequences / Trade-Offs
- Pengguna yang ingin melihat seluruh 919 listing mentah (termasuk yang *overpriced*) tidak lagi dapat melihatnya secara langsung dalam pandangan utama, karena sistem difokuskan murni untuk *curated screener* (`deal_score >= 50`).
