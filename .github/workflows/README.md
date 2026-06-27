# ADEK HARIANTO — QR/Barcode Scan & Excel Match (Android APK)

Aplikasi ini membungkus file `index.html` (scanner QR/barcode yang mencocokkan
data dengan file Excel) menjadi APK Android, menggunakan:

- **Kivy** sebagai shell aplikasi minimal
- **Android WebView native** (diakses lewat `pyjnius`) untuk menjalankan HTML —
  ini WAJIB karena WebView bawaan Kivy tidak mendukung akses kamera (`getUserMedia`)
  yang dipakai library `html5-qrcode` di dalam `index.html`.
- **Buildozer / python-for-android** untuk mengompilasi semuanya jadi APK.

## Struktur folder

```
qrscan_app/
├── .github/workflows/
│   └── build.yml            ← workflow GitHub Actions (build APK otomatis
│                                di cloud, lihat "Cara build APK" → Opsi A)
├── .gitignore                ← agar folder build sementara tidak ikut commit
├── main.py                  ← shell Kivy, memuat WebView Android
├── buildozer.spec           ← konfigurasi build APK
├── icon.png                 ← icon aplikasi (512x512, siap pakai)
├── icon.svg                 ← sumber vektor icon (kalau mau diedit ulang)
├── assets/
│   ├── index.html           ← file HTML scanner (sudah dibersihkan dari
│   │                           script internal /_sdk/* yang tidak relevan)
│   ├── lib/                 ← library JS (KOSONG — Anda perlu unduh sendiri,
│   │                           lihat bagian "Mengunduh library offline")
│   └── fonts/
│       └── dm-sans.css      ← CSS font dengan fallback ke font sistem
└── src/org/adekharianto/qrscan/
    └── WebViewHelper.java   ← helper Java: izin kamera utk WebView +
                                jembatan simpan file .xlsx ke folder Download
```

## Yang saya ubah dari HTML asli Anda

1. **Dihapus**: `<script src="/_sdk/telemetry_sdk.js">`, `/_sdk/data_sdk.js`,
   `/_sdk/resizing_sdk.js`, `/_sdk/editing_sdk.js` — ini adalah script internal
   platform tempat Anda men-generate HTML (kemungkinan Canva), tidak ada saat
   dijalankan offline di APK, dan akan menyebabkan request gagal/error console.
2. **Dihapus**: script Cloudflare challenge-platform di akhir file — tidak
   relevan untuk aplikasi offline dan butuh koneksi ke domain tertentu yang
   tidak akan tersedia di APK.
3. **Dihapus** atribut `data-template-id` (tidak berfungsi tanpa SDK editor,
   aman dihapus) — saya isi langsung teks dan style yang sebelumnya kosong
   (judul, label, dsb) supaya tampilan tidak kosong/blank.
4. **Ditambahkan**: pemanggilan opsional `window.AndroidBridge.saveXlsxBase64()`
   di fungsi `downloadXlsx()` — jika berjalan di APK (bridge tersedia), file
   akan tersimpan langsung ke folder **Download** HP lewat kode Java, karena
   `XLSX.writeFile()` browser biasa (yang memicu unduhan otomatis) tidak selalu
   berfungsi di dalam WebView Android tanpa penanganan khusus. Jika dibuka di
   browser desktop biasa, fallback ke `XLSX.writeFile()` tetap berjalan seperti
   semula.
5. **Diubah**: 4 referensi `<script src="https://...">` (Tailwind, XLSX.js,
   html5-qrcode, Lucide) diarahkan ke file lokal di `assets/lib/`, dan font
   Google Fonts diarahkan ke `assets/fonts/dm-sans.css` — agar aplikasi bisa
   berjalan tanpa koneksi internet. **File-file library ini perlu Anda unduh
   sendiri** sebelum build (lihat bagian "Mengunduh library offline" di bawah),
   karena environment saya tidak punya akses internet untuk mengunduhkannya
   langsung ke project ini.

Fungsionalitas inti **tidak diubah**: logika upload Excel, pemilihan kolom kunci,
scan kamera, input manual, pencocokan, statistik, dan export — semuanya sama
seperti file asli Anda.

## Mengunduh library offline (PENTING — lakukan sebelum build)

Folder `assets/lib/` saat ini masih **kosong** (cuma ada file penanda
`PUT_LIBRARY_FILES_HERE.txt`). Sandbox tempat saya membuat project ini tidak
punya akses internet, jadi Anda perlu mengunduh 4 file JavaScript ini sendiri
dan menaruhnya di folder `assets/lib/` dengan nama file **persis seperti di
bawah** (huruf besar/kecil harus sama):

| Nama file (di `assets/lib/`) | Link unduhan |
|---|---|
| `tailwind.min.js` | https://cdn.tailwindcss.com/3.4.17 |
| `xlsx.full.min.js` | https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js |
| `html5-qrcode.min.js` | https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js |
| `lucide.min.js` | https://cdn.jsdelivr.net/npm/lucide@0.263.0/dist/umd/lucide.min.js |

### Cara mengunduh (pilih salah satu)

**Opsi A — Browser (paling mudah, tanpa command line):**
1. Buka link di atas satu per satu di Chrome/browser laptop.
2. Tekan `Ctrl+S` (atau klik kanan → "Save As" / "Simpan halaman sebagai").
3. Pilih "Save as text" / format `.js`, ganti nama file sesuai kolom kiri
   tabel di atas, simpan ke folder `qrscan_app/assets/lib/`.

**Opsi B — Terminal (Linux/Mac/WSL), lebih cepat untuk 4 file sekaligus:**
```bash
cd qrscan_app/assets/lib
curl -sL -o tailwind.min.js "https://cdn.tailwindcss.com/3.4.17"
curl -sL -o xlsx.full.min.js "https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"
curl -sL -o html5-qrcode.min.js "https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"
curl -sL -o lucide.min.js "https://cdn.jsdelivr.net/npm/lucide@0.263.0/dist/umd/lucide.min.js"
ls -la
```
Setelah selesai, pastikan ukuran tiap file **tidak 0 byte / tidak kosong**
(`ls -la` harus menunjukkan ukuran puluhan–ratusan KB, bukan beberapa byte).
Jika ada yang 0 byte atau isinya halaman error HTML, link mungkin sudah usang —
cari versi terbaru di https://www.jsdelivr.com/ atau https://unpkg.com/ dengan
mencari nama paketnya (`xlsx`, `html5-qrcode`, `lucide`).

Setelah file diunduh, `index.html` sudah saya ubah agar otomatis memuat dari
folder lokal ini (`lib/tailwind.min.js`, dst) — tidak perlu edit HTML lagi.

### Font (opsional, boleh dilewati)

File asli memakai font **DM Sans** dari Google Fonts. Untuk mode offline,
saya sudah siapkan `assets/fonts/dm-sans.css` dengan fallback otomatis ke
font sistem Android (Roboto) — jadi **boleh dilewati saja**, tampilan tetap
rapi tanpa font khusus.

Jika tetap ingin font DM Sans asli secara offline:
1. Buka https://fonts.google.com/specimen/DM+Sans, unduh family-nya (tombol
   "Get font" → "Download all").
2. Dari file `.ttf` yang didapat, convert ke `.woff2` (bisa pakai situs
   konversi seperti https://transfonter.org/, pilih hanya weight 400/Regular,
   500/Medium, 700/Bold).
3. Beri nama `DMSans-Regular.woff2`, `DMSans-Medium.woff2`, `DMSans-Bold.woff2`,
   taruh di folder `assets/fonts/`.

### Verifikasi sebelum build

Setelah semua file diunduh, struktur folder `assets/` harus seperti ini:

```
assets/
├── index.html
├── lib/
│   ├── tailwind.min.js
│   ├── xlsx.full.min.js
│   ├── html5-qrcode.min.js
│   └── lucide.min.js
└── fonts/
    └── dm-sans.css          (+ file .woff2 jika Anda menambahkannya)
```

Cara cepat tes tanpa build APK dulu: buka `assets/index.html` langsung di
browser laptop (dobel klik filenya). Jika tampilan muncul normal dan tidak
ada error merah di Console browser (`F12` → tab Console) terkait `xlsx`,
`Html5Qrcode`, atau `lucide`, berarti semua library sudah benar dan siap
dibawa ke proses build APK.

## Cara build APK

Ada 2 cara: **(A) lewat GitHub Actions** (tidak perlu install apa pun di
laptop, server GitHub yang kerja) atau **(B) build manual di Linux/WSL sendiri**.
Kalau laptop Anda Windows tanpa WSL, atau cuma mau cara paling simpel, pakai
opsi A.

### Opsi A — Build otomatis lewat GitHub Actions (disarankan, tanpa install apa pun)

File `.github/workflows/build.yml` sudah saya siapkan di project ini. File
ini membuat GitHub menjalankan Buildozer di server Linux mereka sendiri,
gratis untuk repo publik.

**Langkah-langkah:**

1. **Buat akun GitHub** kalau belum punya: https://github.com/signup
2. **Buat repository baru** (kosong): klik tombol hijau "New" di
   https://github.com/new, beri nama misalnya `qrscan-app`, pilih **Public**
   (supaya GitHub Actions gratis), jangan centang "Add README" (biar tidak
   konflik), klik **Create repository**.
3. **Upload semua file project ini** ke repo tersebut. Dua cara:
   - **Tanpa command line (lewat browser)**: di halaman repo kosong yang baru
     dibuat, klik link **"uploading an existing file"**, lalu drag-and-drop
     seluruh isi folder `qrscan_app/` (termasuk folder `.github`, `assets`,
     `src` — pastikan strukturnya tetap, jangan upload file satu-satu tanpa
     foldernya). Lalu klik **Commit changes**.

     ⚠️ **Penting**: drag-and-drop folder lewat browser kadang **tidak
     mendeteksi folder tersembunyi** seperti `.github`. Kalau setelah upload
     Anda tidak melihat folder `.github/workflows/build.yml` muncul di repo,
     buat manual: di halaman repo, klik **Add file → Create new file**, lalu
     di kolom nama file ketik path lengkapnya sekaligus:
     `.github/workflows/build.yml` (GitHub otomatis membuat foldernya), lalu
     copy-paste isi file `build.yml` dari project ini ke kotak editor, dan
     **Commit changes**.
   - **Lewat command line** (kalau familiar Git, dan ini cara paling aman
     karena folder `.github` pasti ikut terupload dengan benar):
     ```bash
     cd qrscan_app
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin https://github.com/USERNAME/qrscan-app.git
     git push -u origin main
     ```
     Ganti `USERNAME` dengan username GitHub Anda dan `qrscan-app` dengan nama
     repo yang Anda buat.
4. **Lengkapi dulu folder `assets/lib/`** dengan 4 file JS (lihat bagian
   "Mengunduh library offline" di atas) **sebelum** push/upload, supaya hasil
   APK-nya tidak blank.
5. Setelah file ter-upload, buka tab **Actions** di halaman repo GitHub Anda
   (menu di bagian atas, sebaris dengan "Code", "Issues", dll). Workflow
   "Build Android APK" akan otomatis mulai berjalan.
6. Tunggu sekitar **20–40 menit** untuk build pertama kali (build berikutnya
   lebih cepat karena ada cache). Anda bisa klik run yang sedang berjalan
   untuk melihat progress log secara langsung.
7. Setelah selesai (tanda centang hijau ✅), klik run tersebut, scroll ke
   bawah ke bagian **Artifacts**, lalu klik **adekharianto-debug-apk** untuk
   mendownload file `.zip` yang berisi APK Anda.
8. Ekstrak zip tersebut, dapatkan file `.apk`, kirim ke HP Android (lewat
   WhatsApp ke diri sendiri, Google Drive, kabel USB, dll), lalu install
   (aktifkan dulu "Izinkan instal dari sumber tidak dikenal" di setelan HP).

**Kalau build gagal (tanda silang merah ❌):** klik run yang gagal, klik step
yang ada tanda merahnya untuk lihat detail error log-nya, lalu Anda bisa
tempel pesan error itu ke saya untuk saya bantu perbaiki.

**Untuk build ulang setelah mengubah kode**: cukup push/upload perubahan file
lagi ke GitHub (commit baru), workflow akan otomatis jalan lagi. Bisa juga
dipicu manual tanpa perlu ubah kode: buka tab **Actions** → pilih workflow
**Build Android APK** di sidebar kiri → klik tombol **Run workflow**.

### Opsi B — Build manual di Linux/WSL milik Anda sendiri

Build APK **harus** dilakukan di komputer Linux (atau WSL di Windows) yang
punya akses internet, karena Buildozer akan mengunduh Android SDK/NDK (~beberapa
GB) saat pertama kali build. Sandbox saya di sini tidak punya akses internet,
jadi saya tidak bisa menjalankan build sungguhan — tapi semua file sudah siap.

### 1. Siapkan environment (sekali saja)

```bash
sudo apt update
sudo apt install -y python3-pip build-essential git python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    zlib1g-dev openjdk-17-jdk unzip

pip3 install --user buildozer cython
```

Pastikan `JAVA_HOME` mengarah ke JDK 17, contoh:
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### 2. Siapkan icon (opsional tapi disarankan)

`buildozer.spec` mereferensikan `icon.png` di root folder. Letakkan file PNG
512x512 di `qrscan_app/icon.png`, atau hapus baris `icon.filename` di
`buildozer.spec` jika ingin pakai ikon default Kivy.

### 3. Build APK debug

Dari dalam folder `qrscan_app/`:

```bash
cd qrscan_app
buildozer -v android debug
```

Proses pertama kali bisa makan waktu 20–60 menit (mengunduh Android SDK, NDK,
dan mengompilasi semua dependency Python untuk Android). APK hasil build akan
muncul di:

```
qrscan_app/bin/adekharianto-1.0-arm64-v8a_armeabi-v7a-debug.apk
```

### 4. Install ke HP

Aktifkan **USB debugging** di HP Android, sambungkan via USB, lalu:

```bash
buildozer android deploy run logcat
```

Atau cukup salin file `.apk` ke HP dan install manual (aktifkan dulu
"Izinkan instal dari sumber tidak dikenal" di setelan HP).

### 5. Build APK release (untuk dibagikan/Play Store)

```bash
buildozer android release
```

APK release perlu di-sign sendiri dengan keystore Anda sebelum bisa
didistribusikan — lihat dokumentasi resmi Buildozer untuk langkah signing:
https://buildozer.readthedocs.io/en/latest/

## Izin yang diminta aplikasi

- **Kamera** — untuk scan QR/barcode (`html5-qrcode`)
- **Storage** — untuk membaca file Excel yang diupload & menyimpan hasil export

Saat aplikasi pertama dijalankan di HP, akan muncul dialog izin kamera/storage
dari Android — pengguna harus menekan **Izinkan**, karena WebView akan otomatis
meneruskan permintaan kamera dari halaman web setelah izin sistem diberikan
(ditangani oleh `WebViewHelper.java`).

## Troubleshooting umum

- **Kamera tidak muncul / layar hitam di scanner**: pastikan izin kamera sudah
  diberikan di Setelan → Aplikasi → ADEK HARIANTO → Izin. Beberapa HP juga
  perlu izin kamera diberikan ulang setelah install pertama.
- **Build gagal di tahap NDK**: pastikan versi `android.ndk` di `buildozer.spec`
  cocok dengan yang berhasil diunduh; jika error, coba hapus folder
  `~/.buildozer` dan build ulang dari awal agar Buildozer mengunduh versi yang
  konsisten.
- **File export tidak muncul di folder Download**: pastikan izin storage
  diberikan; di Android 11+ aplikasi memakai `MediaStore` API (sudah ditangani
  di `WebViewHelper.java`) jadi tidak perlu izin storage manual untuk Android
  11+, tapi tetap dicoba minta untuk kompatibilitas Android lama.
- **Tampilan blank putih saat dibuka**: cek dengan `buildozer android deploy run logcat`
  lalu cari error di Logcat terkait `WebView` atau `JavaScript`. Penyebab paling
  umum: salah satu file di `assets/lib/` belum diunduh atau namanya tidak sama
  persis dengan yang diminta `index.html` — cek ulang langkah di bagian
  "Mengunduh library offline" di atas. Aplikasi ini didesain berjalan
  **100% offline** setelah semua library lokal terpasang dengan benar, jadi
  tidak butuh koneksi internet sama sekali saat dipakai sehari-hari.

## Catatan penting

- Estimasi ukuran APK akhir: sekitar 20–35 MB (sedikit lebih besar karena
  library JS sekarang dibundel offline di dalam APK, bukan dimuat dari CDN).
- Build pertama kali butuh ruang disk ~5–8 GB untuk Android SDK/NDK.
- Permission `INTERNET` tetap ada di `buildozer.spec` karena beberapa komponen
  WebView Android meminta izin ini secara default, tapi aplikasi tidak akan
  melakukan request keluar apa pun selama dipakai — semua sudah lokal.
- Jika Anda mau saya buatkan versi tampilan native Kivy (bukan WebView) untuk
  performa lebih ringan, bilang saja — saya siapkan revisinya.
