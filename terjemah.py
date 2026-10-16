#!/usr/bin/env python3
"""Lapisan dwi-bahasa untuk laman MADOCS.

Sumber kandungan kekal **Bahasa Melayu** (`build.py` + `data/*.json`). Versi Inggeris dijana
dengan menterjemah HTML yang sudah dibina menggunakan kamus `data/terjemahan.json`
({"teks BM": "English"}). Satu sumber kandungan, tiada pendua teks, dan apa-apa teks yang
belum diterjemah muncul dalam BM (bukan hilang atau kosong).

Alat:
  python3 terjemah.py --kumpul     # senarai teks unik untuk diterjemah -> /home/ubuntu/madocs-admin/teks-untuk-terjemah.json
  python3 terjemah.py --laporan    # teks yang masih belum ada terjemahan
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
KAMUS = ROOT / "data" / "terjemahan.json"

# --- pemetaan laluan: BM -> EN (slug Inggeris untuk pembaca Inggeris) -----------------
SLAG_EN = {
    "/": "/en/",
    "/tentang/": "/en/about/",
    "/prakata-presiden/": "/en/president-foreword/",
    "/pendidikan/": "/en/education/",
    "/keahlian/": "/en/membership/",
    "/keahlian/sertai/": "/en/membership/join/",
    "/aktiviti/": "/en/activities/",
    "/berita/": "/en/news/",
    "/sumber/": "/en/resources/",
    "/hubungi/": "/en/contact/",
    "/carian/": "/en/search/",
    "/dasar-privasi/": "/en/privacy/",
    "/terma/": "/en/terms/",
    "/kebolehaksesan/": "/en/accessibility/",
}

# --- penanda yang diletak oleh build.py dan diganti di sini --------------------------
PENANDA_BAHASA = "<!--TUKAR-BAHASA-->"
PENANDA_HREFLANG = "<!--HREFLANG-->"


def peta_slug(bm_slugs) -> dict[str, str]:
    """Pemetaan laluan BM -> EN, termasuk halaman berparameter (kursus/aktiviti/berita/sumber)."""
    peta = dict(SLAG_EN)
    for s in bm_slugs:
        if s in peta:
            continue
        for awalan, ganti in (("/pendidikan/", "/en/education/"), ("/aktiviti/", "/en/activities/"),
                              ("/berita/", "/en/news/"), ("/sumber/", "/en/resources/")):
            if s.startswith(awalan) and len(s) > len(awalan):
                peta[s] = ganti + s[len(awalan):]
                break
    return peta


RE_BUANG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
RE_TEG = re.compile(r"<[^>]+>")
RE_TEG_KUMPUL = re.compile(r"(<[^>]+>)")  # split yang MENGEKALKAN tag
RE_ATR = re.compile(r'\b(alt|title|aria-label|placeholder)="([^"]*)"')
RE_META = re.compile(r'(<meta[^>]+(?:name|property)="(?:description|og:title|og:description|twitter:title|twitter:description)"[^>]*content=")([^"]*)(")', re.I)
RE_LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
ADA_HURUF = re.compile(r"[A-Za-z]")


def teks_dalam_html(s: str) -> set[str]:
    """Semua cebisan teks yang boleh diterjemah (antara tag + atribut teks)."""
    keluar: set[str] = set()
    bersih = RE_BUANG.sub(lambda m: " " * len(m.group(0)), s)
    for cebis in RE_TEG.split(bersih):
        if ADA_HURUF.search(cebis) and cebis.strip():
            keluar.add(cebis.strip())
    for _, v in RE_ATR.findall(s):
        if ADA_HURUF.search(v) and v.strip():
            keluar.add(v.strip())
    for _, v, _ in RE_META.findall(s):
        if ADA_HURUF.search(v) and v.strip():
            keluar.add(v.strip())
    return keluar


def halaman_dibina(root: pathlib.Path = ROOT) -> list[pathlib.Path]:
    return sorted(p for p in root.rglob("*.html") if ".git" not in p.parts and "/en/" not in str(p))


def muat_kamus() -> dict[str, str]:
    if not KAMUS.exists():
        return {}
    data = json.loads(KAMUS.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, str) and v.strip()}


# --- terjemahan dokumen ---
def _terjemah_teks_antara_tag(s: str, kamus: dict[str, str]) -> str:
    """Terjemah cebisan teks antara tag; blok <script>/<style> dikekalkan tanpa diusik."""
    keluar: list[str] = []
    pos = 0
    for m in RE_BUANG.finditer(s):
        keluar.append(_terjemah_kepingan(s[pos:m.start()], kamus))
        keluar.append(m.group(0))
        pos = m.end()
    keluar.append(_terjemah_kepingan(s[pos:], kamus))
    return "".join(keluar)


def _terjemah_kepingan(bahagian: str, kamus: dict[str, str]) -> str:
    kepingan = RE_TEG_KUMPUL.split(bahagian)
    for j, kepingan_teks in enumerate(kepingan):
        if j % 2:              # indeks ganjil = teg, jangan sentuh
            continue
        kunci = kepingan_teks.strip()
        if kunci and kunci in kamus:
            kepingan[j] = kepingan_teks.replace(kunci, kamus[kunci], 1)
    return "".join(kepingan)


# ---------------------------------------------------------------------------------------
def terjemah_html(s: str, kamus: dict[str, str], peta: dict[str, str],
                  laluan_bm: str, laluan_en: str, asas: str) -> str:
    """Hasilkan versi Inggeris bagi satu halaman HTML Bahasa Melayu."""
    # 1) teks antara tag — blok <script>/<style> dikekalkan bulat-bulat
    #    (hati-hati: re.split dengan kumpulan tangkap hanya menyimpan NAMA teg, bukan bloknya)
    s = _terjemah_teks_antara_tag(s, kamus)

    # 2) atribut teks
    def ganti_atr(m):
        nilai = m.group(2).strip()
        return '%s="%s"' % (m.group(1), kamus.get(nilai, nilai)) if nilai in kamus else m.group(0)
    s = RE_ATR.sub(ganti_atr, s)

    # 3) meta description / og / twitter
    def ganti_meta(m):
        nilai = m.group(2).strip()
        return m.group(1) + kamus.get(nilai, nilai) + m.group(3)
    s = RE_META.sub(ganti_meta, s)

    # 4) pautan dalaman -> laluan Inggeris
    def ganti_href(m):
        url = m.group(2)
        if url.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            return m.group(0)
        asas_url, _, fragmen = url.partition("#")
        asal, _, soal = asas_url.partition("?")
        if asal in peta:
            return '%s="%s%s%s"' % (m.group(1), peta[asal],
                                    ("?" + soal) if soal else "",
                                    ("#" + fragmen) if fragmen else "")
        return m.group(0)
    s = re.sub(r'\b(href|action)="([^"]*)"', ganti_href, s)

    # 5) rujukan indeks carian + skrip
    s = s.replace('"/carian/index.json"', '"/en/search/index.json"').replace("'/carian/index.json'", "'/en/search/index.json'")
    s = s.replace('"/carian/?q=', '"/en/search/?q=')

    # 6) bahasa dokumen + locale
    s = s.replace('<html lang="ms">', '<html lang="en">')
    s = s.replace('content="ms_MY"', 'content="en_MY"')

    # 7) canonical + og:url -> laluan Inggeris
    s = s.replace(asas + laluan_bm, asas + laluan_en)

    # 8) data berstruktur: terjemah nama/deskripsi sahaja, kekalkan baki
    def ganti_ld(m):
        try:
            data = json.loads(m.group(2))
        except Exception:
            return m.group(0)
        def dalam(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        if k in ("name", "alternateName", "description", "headline") and v in kamus:
                            obj[k] = kamus[v]
                    else:
                        dalam(v)
            elif isinstance(obj, list):
                for x in obj:
                    dalam(x)
        dalam(data)
        return m.group(1) + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + m.group(3)
    s = RE_LD.sub(ganti_ld, s)
    return s


def suntik_navigasi_bahasa(s: str, peta: dict[str, str], laluan: str, asas: str) -> str:
    """Ganti penanda dengan pautan tukar bahasa + hreflang (halaman BM dan EN)."""
    songsang = {v: k for k, v in peta.items()}
    pasangan = songsang.get(laluan, "/") if laluan.startswith("/en/") else peta.get(laluan)
    if not pasangan:
        return s.replace(PENANDA_BAHASA, "").replace(PENANDA_HREFLANG, "")
    if laluan.startswith("/en/"):
        sauh = ('<a class="tukar-bahasa" href="%s" hreflang="ms" lang="ms" '
                'aria-label="Baca halaman ini dalam Bahasa Melayu">BM</a>' % pasangan)
        url_ms, url_en = pasangan, laluan
    else:
        sauh = ('<a class="tukar-bahasa" href="%s" hreflang="en" lang="en" '
                'aria-label="Read this page in English">EN</a>' % pasangan)
        url_ms, url_en = laluan, pasangan
    s = s.replace(PENANDA_BAHASA, sauh)
    hreflang = (
        '<link rel="alternate" hreflang="ms" href="%s%s">\n'
        '<link rel="alternate" hreflang="en" href="%s%s">\n'
        '<link rel="alternate" hreflang="x-default" href="%s%s">'
        % (asas, url_ms, asas, url_en, asas, url_ms)
    )
    return s.replace(PENANDA_HREFLANG, hreflang)


# --- alat CLI -------------------------------------------------------------------------
def kumpul(root: pathlib.Path = ROOT) -> dict[str, str]:
    semua: set[str] = set()
    for f in halaman_dibina(root):
        semua |= teks_dalam_html(f.read_text(encoding="utf-8"))
    for j in root.glob("carian/index.json"):
        try:
            indeks = json.loads(j.read_text(encoding="utf-8"))
        except Exception:
            continue
        for it in indeks:
            for kunci in ("t", "r", "j"):
                if it.get(kunci):
                    semua.add(it[kunci])
    kamus = muat_kamus()
    return {t: kamus.get(t, "") for t in sorted(semua)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Alat dwi-bahasa MADOCS")
    ap.add_argument("--kumpul", action="store_true", help="tulis senarai teks untuk diterjemah")
    ap.add_argument("--laporan", action="store_true", help="senaraikan teks yang belum diterjemah")
    ap.add_argument("-o", "--output", default="/home/ubuntu/madocs-admin/teks-untuk-terjemah.json")
    args = ap.parse_args()

    peta = kumpul()
    belum = [t for t, v in peta.items() if not v]
    if args.laporan:
        print(f"jumlah teks unik: {len(peta)} · sudah diterjemah: {len(peta) - len(belum)} · belum: {len(belum)}")
        for t in belum:
            print("  •", t)
        return 0
    if args.kumpul:
        pathlib.Path(args.output).write_text(json.dumps(peta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"ditulis: {args.output} ({len(peta)} teks, {len(belum)} belum diterjemah)")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
