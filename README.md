# 🏆 Sistem Pemeringkatan Aplikasi 🏆

Sistem ini dirancang untuk melakukan pemeringkatan aplikasi berdasarkan ulasan pengguna dari Google Play Store. Dengan menggunakan teknik web scraping, preprocessing teks, analisis sentimen, dan metode pemeringkatan SAW (Simple Additive Weighting) serta ARAS (Additive Ratio Assessment). Sistem ini dapat memberikan peringkat aplikasi berdasarkan lima kriteria yang digunakan, yaitu:
1. Jumlah Ulasan Positif
2. Jumlah Ulasan Non Positif
3. Jumlah Download
4. Total Ulasan
5. Rating Aplikasi

## ✨ Fitur Utama

- **📥 Scraping Data Ulasan**: Mengambil ulasan aplikasi dari Google Play Store berdasarkan rentang tanggal dan jumlah ulasan yang diinginkan.
- **🧹 Preprocessing Teks**: Membersihkan, menormalisasi, dan melakukan stemming pada teks ulasan.
- **😃 Analisis Sentimen**: Menganalisis sentimen ulasan menggunakan VADER (Valence Aware Dictionary and sEntiment Reasoner).
- **📊 Pemeringkatan Aplikasi**: Melakukan pemeringkatan aplikasi menggunakan metode SAW dan ARAS.
- **📈 Visualisasi Data**: Menampilkan hasil pemeringkatan dalam bentuk tabel dan grafik.

## 🛠️ Teknologi yang Digunakan

- **🎈 Streamlit**: Untuk membuat antarmuka pengguna berbasis web.
- **📦 Google Play Scraper**: Untuk mengambil data ulasan dan informasi aplikasi dari Google Play Store.
- **🐼 Pandas**: Untuk manipulasi dan analisis data.
- **📚 NLTK**: Untuk preprocessing teks dan analisis sentimen.
- **🌿 Sastrawi**: Untuk stemming teks dalam bahasa Indonesia.
- **🌐 Requests**: Untuk melakukan permintaan HTTP, termasuk translasi teks.

## 🚀 Cara Menggunakan
1. Clone repository ini ke lokal Anda:
```bash
https://github.com/Wibiemahardhika22/pemeringkatan-aplikasi.git
```
2. Masuk ke direktori proyek:
```bash
cd pemeringkatan-aplikasi
```
3. Instal dependensi yang diperlukan:
```bash
pip install -r requirements.txt
```
4. Jalankan aplikasi Streamlit:
```bash
streamlit run main.py
```
5. Buka browser dan akses [http://localhost:8501](http://localhost:8501) untuk melihat aplikasi.

## 📖 Panduan Penggunaan
1. Pilih Metode Input Data:
- 🔄 Scraping Data Baru: Masukkan nama aplikasi dan ID aplikasi, lalu tentukan rentang tanggal dan jumlah ulasan yang ingin diambil.
- 📂 Upload File CSV: Unggah file CSV yang berisi data aplikasi yang sudah diformat.

2. Mulai Scraping:
- Klik tombol `Mulai` untuk memulai proses scraping dan analisis data.

3. Lihat Hasil:
- Hasil scraping, preprocessing, analisis sentimen, dan pemeringkatan akan ditampilkan dalam bentuk tabel dan grafik.

## 📂 Struktur Proyek
```bash
pemeringkatan-aplikasi/
├── main.py                # File utama untuk menjalankan aplikasi Streamlit
├── function.py            # Berisi fungsi-fungsi utama untuk scraping, preprocessing, analisis sentimen, dan pemeringkatan
├── requirements.txt       # Daftar dependensi yang diperlukan
└── README.md              # Dokumentasi proyek
```

#
Dibuat dengan ❤️ oleh [Wibie Mahardhika Adi](https://linkedin.com/in/wibiemahardhika) | © 2025