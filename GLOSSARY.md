# Glossary: The Syndicate & Char-Finder

Dokumen ini mendefinisikan terminologi domain murni (domain-only concepts) yang digunakan dalam ekosistem The Syndicate dan aplikasi Char-Finder tanpa terikat pada detail implementasi teknis tertentu.

---

## 1. Entitas & Atribut Karakter

### Capo
Karakter sindikat yang memiliki atribut lengkap berupa 5 statistik tempur, 3 trait kepribadian, spesialisasi peran, dan tingkatan kelangkaan (*rarity*).

### Combat Stats
Atribut inti karakter yang merepresentasikan kapabilitas tempur dan operasional capo di dalam sindikat:
- **`stat_muscle`**: Kekuatan fisik dan kapasitas intimidasi capo.
- **`stat_brains`**: Kecerdasan taktikal, strategi, dan kemampuan analitis.
- **`stat_hustle`**: Kecepatan eksekusi, kelincahan, dan efisiensi operasional.
- **`stat_grit`**: Ketahanan mental, daya tahan terhadap tekanan, dan loyalitas.
- **`stat_rep`**: Reputasi, pengaruh sosial, dan kedudukan di dalam sindikat.
- **`total_stat`**: Akumulasi total dari kelima combat stats di atas (berkisar antara 16 hingga 500).

### Traits
Atribut psikologis dan kepribadian capo yang mempengaruhi karakteristik perilaku dan kecocokan peran:
- **`greed`**: Tingkat ambisi material dan orientasi keuntungan (rentang nilai 1–10).
- **`finesse`**: Tingkat kehalusan teknik, presisi, dan gaya operasional (rentang nilai 1–10).
- **`passion`**: Tingkat dorongan emosional, semangat, dan intensitas (rentang nilai 1–10).

### Specialties
Peran spesialisasi resmi yang diemban oleh seorang capo:
- **`enforcer`**: Spesialis garis depan untuk pengamanan dan aksi fisik langsung.
- **`hustler`**: Spesialis pengumpulan sumber daya dan optimalisasi transaksi cepat.
- **`fixer`**: Spesialis penyelesaian masalah rumit, negosiasi tingkat tinggi, dan manipulasi situasi.
- **`survivor`**: Spesialis ketahanan dalam kondisi ekstrem dan mitigasi risiko krisis.
- **`negotiator`**: Spesialis diplomasi, peredaan konflik, dan kesepakatan strategis.

### Rarities
Tingkatan kelangkaan capo yang menentukan prestise dan basis nilai kelangkaan di ekosistem:
- **`rare`**
- **`epic`**
- **`legendary`**
- **`founder`**
- **`god`**

---

## 2. Ekonomi & Pasar

### Listing
Penawaran penjualan capo di pasar terdesentralisasi yang mencantumkan harga penawaran dalam satuan Lamports serta nilai ekuivalen USD.

### Floor Price
Harga terendah aktif yang tercatat untuk suatu tingkatan kelangkaan (*rarity*) tertentu di pasar, yang berfungsi sebagai jangkar acuan (*Floor Snipe Booster*).

### Lamports / SOL
Satuan mata uang *on-chain* riil yang digunakan sebagai acuan valuasi dasar dan penyelesaian transaksi utama (menghindari volatilitas mata uang fiat seperti USD).

---

## 3. Valuasi & Rekomendasi

### HBDS (Hedonic-Bayesian Deal Scoring)
Algoritma valuasi mutakhir berbasis regresi hedonik OLS (Ordinary Least Squares) dan penyesuaian Bayesian shrinkage untuk mengukur deviasi harga listing terhadap harga wajar statistik berdasarkan karakteristik capo.

### Deal Tiers
Klasifikasi tingkat keuntungan penawaran berdasarkan skor HBDS:
- **Steal (`deal_score >= 80`)**: Listing dengan diskon ekstrem terhadap harga wajar atau sangat dekat dengan harga lantai namun memiliki statistik tinggi.
- **Great Deal (`deal_score 65–79`)**: Capo dengan efisiensi statistik yang jauh melampaui median pasar.
- **Good Value (`deal_score 50–64`)**: Capo yang ditawarkan di atas nilai wajar pasar namun masih memberikan nilai yang rasional.
- **Overpriced (`deal_score < 50`)**: Listing dengan harga di atas nilai wajar yang tidak direkomendasikan untuk dibeli.
