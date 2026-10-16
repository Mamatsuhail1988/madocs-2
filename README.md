# MADOCS 2.0 — Laman web statik

Laman rasmi **Pertubuhan Doktor Khatan Malaysia (MADOCS)** versi 2.0.
Dibina sebagai laman statik (HTML/CSS/JS biasa) — tiada WordPress, tiada pangkalan data,
tiada plugin untuk dikemas kini. Hos: GitHub Pages, domain: `madocs.drsuhailsatri.com`.

---

## 1. Struktur fail

```
index.html                  Halaman utama
tentang/                    Tentang MADOCS (visi, misi, tadbir urus, jawatankuasa)
pendidikan/                 Pendidikan & Latihan (senarai program)
  <slug>/                   Halaman butiran setiap program latihan
keahlian/                   Keahlian (manfaat, kelayakan, kategori, yuran, FAQ)
  sertai/                   Borang permohonan keahlian
aktiviti/                   Senarai aktiviti + halaman butiran setiap aktiviti
sumber/                     Pusat Sumber
berita/                     Berita + halaman artikel
hubungi/                    Hubungi urusetia
carian/                     Halaman carian (+ index.json)
dasar-privasi/, terma/      Dasar Privasi & Terma Penggunaan
404.html                    Halaman ralat
styles.css                  Semua gaya (dijana daripada _src/base.css + _src/extra.css)
app.js                      Menu mudah alih, carian, carousel aktiviti
assets/                     Imej (WebP), logo, favicon
data/                       KANDUNGAN — ini yang anda edit
_src/, _icons/, build.py    Sumber pembinaan (tidak perlu diubah untuk kemas kini biasa)
CNAME, robots.txt, sitemap.xml, .nojekyll
```

## 2. Bagaimana mengemas kini kandungan

Kandungan **tidak** diedit terus dalam fail `.html`. Semua kandungan boleh berubah berada dalam
folder `data/` sebagai fail JSON mudah:

| Fail | Kandungan |
|---|---|
| `data/site.json` | Nama pertubuhan, e-mel, telefon, no. pendaftaran, pautan sosial |
| `data/kursus.json` | Program latihan: tarikh, tempat, yuran, status pendaftaran, objektif, rangka program |
| `data/aktiviti.json` | Aktiviti/program yang telah dijalankan |
| `data/berita.json` | Berita dan pengumuman |
| `data/sumber.json` | Sumber klinikal (akses: `awam` atau `ahli`) |
| `data/keahlian.json` | Manfaat, kelayakan, kategori, yuran, proses, FAQ |
| `data/jawatankuasa.json` | Senarai Jawatankuasa Eksekutif |
| `data/stats.json` | Angka ringkasan di laman utama |

Setiap fail mempunyai kunci `cara_edit` di baris pertama — baca itu dahulu.

Selepas mengubah mana-mana fail `data/`, jalankan:

```bash
python3 build.py            # bina semula semua halaman HTML
python3 build.py --report   # senarai kandungan yang masih belum disediakan
```

Kemudian commit dan push. Laman dikemas kini dalam masa kira-kira satu minit.

**Jika tiada Python di mesin anda:** hantar perubahan kepada Abu (agen Hermes) melalui Telegram —
dia akan edit `data/`, jalankan `build.py` dan push.

## 3. Peraturan kandungan (dari PRD)

- **§11 Angka:** angka di laman utama hanya dipaparkan jika `data/stats.json` → `"disahkan": true`.
  Semasa `false`, laman menunjukkan "Menunggu pengesahan" — ini disengajakan, bukan pepijat.
- **§12 Program latihan:** setiap program perlu tarikh, masa, tempat, peserta sasaran, yuran,
  kapasiti, tarikh tutup pendaftaran, objektif dan rangka program. Medan kosong akan tersembunyi
  dan dilaporkan oleh `build.py --report`.
- **§21 Semakan klinikal:** bahan dalam Pusat Sumber mesti melalui semakan klinikal sebelum
  diterbitkan. Jangan letak pautan mentah.
- **§47 Data peribadi:** borang menghantar data kepada urusetia. Jangan terbitkan nama ahli,
  nombor pendaftaran MMC atau maklumat peribadi di laman awam.

## 4. Status borang (keahlian & hubungi)

Borang keahlian dan borang hubungi sudah siap dari segi antara muka, tetapi **belum disambungkan
ke mana-mana perkhidmatan**:

- `data/site.json` → `"borang_endpoint"` kosong bermakna laman memaparkan notis dan mengarahkan
  pengguna ke e-mel/telefon urusetia (tiada borang yang "hilang" secara senyap).
- Untuk mengaktifkan: daftar perkhidmatan borang (contoh: Web3Forms, Formspree, atau Google Form)
  dan letakkan URL penghantarannya dalam `borang_endpoint`. Semua medan borang akan dihantar ke sana.

## 5. Menerbitkan (GitHub Pages)

1. Repo GitHub mengandungi fail di akar folder ini (index.html di akar).
2. DNS: `madocs.drsuhailsatri.com` → CNAME `mamatsuhail1988.github.io` (selepas Pages diaktifkan).
3. Fail `CNAME` dalam repo sudah mengandungi `madocs.drsuhailsatri.com`.
4. Aktifkan Pages: Settings → Pages → Source: branch `main`, folder `/ (root)`.

## 6. Kandungan yang masih diperlukan daripada MADOCS

Jalankan `python3 build.py --report` untuk senarai penuh. Yang utama:

- Pengesahan angka statistik (§11)
- Nama dan gambar Jawatankuasa Eksekutif (§9.2, §55)
- Visi, misi, sejarah dan dokumen perlembagaan rasmi (§55)
- Kategori, kelayakan dan yuran keahlian (§56.1–§56.3)
- Program latihan akan datang yang lengkap butirannya (§12, §58)
- Bahan Pusat Sumber yang telah disemak (§19, §21)
- Berita/pengumuman pertama (§23)
- Gambar sebenar aktiviti MADOCS (§24, §32)

## 7. Lesen & hak cipta

Nama, logo dan kandungan MADOCS tidak boleh digunakan semula untuk tujuan komersial tanpa
kebenaran bertulis.
