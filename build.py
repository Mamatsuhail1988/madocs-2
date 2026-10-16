#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Penjana laman statik MADOCS 2.0 (madocs.drsuhailsatri.com)

Cara guna:
    python3 build.py            # bina semua halaman ke folder ini
    python3 build.py --report   # tunjuk kandungan yang masih belum disediakan

Kandungan yang boleh diubah terletak dalam folder data/*.json.
Jangan sunting fail .html terus — ia ditulis semula oleh skrip ini.
"""

import json
import html
import re
import shutil
import sys
from pathlib import Path
from datetime import date, datetime

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ICON_DIR = ROOT / "_icons"

HARI = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]
BULAN = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
         "Ogos", "September", "Oktober", "November", "Disember"]
BULAN_SING = ["JAN", "FEB", "MAC", "APR", "MEI", "JUN", "JUL", "OGO", "SEP", "OKT", "NOV", "DIS"]

STATUS_LABEL = {
    "open": ("Pendaftaran dibuka", "open"),
    "limited": ("Kerusi terhad", "limited"),
    "closed": ("Pendaftaran ditutup", "closed"),
    "done": ("Selesai", "done"),
}


# ----------------------------------------------------------------- utiliti
def esc(s):
    return html.escape(str(s), quote=True)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def tarikh_pjg(d):
    if not d:
        return ""
    return "%s, %d %s %d" % (HARI[d.weekday()], d.day, BULAN[d.month - 1], d.year)


def tarikh_pdk(d):
    if not d:
        return ""
    return "%d %s %d" % (d.day, BULAN[d.month - 1], d.year)


def muat_ikon():
    cache = {}

    def get(name):
        if name in cache:
            return cache[name]
        p = ICON_DIR / (name + ".svg")
        if not p.exists():
            cache[name] = '<span class="ikon-ganti" aria-hidden="true"></span>'
            return cache[name]
        raw = p.read_text(encoding="utf-8")
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
        inner = re.search(r"(?s)<svg[^>]*>(.*?)</svg>", raw)
        body = inner.group(1).strip() if inner else ""
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
               'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
               'stroke-linejoin="round" class="lucide lucide-%s" aria-hidden="true">%s</svg>' % (name, body))
        cache[name] = svg
        return svg

    return get


icon = muat_ikon()

SITE = load("site.json")
BASE = SITE.get("base_url", "").rstrip("/")
PAGES = []          # untuk sitemap
KURANG = []         # kandungan yang belum disediakan (untuk --report)


def kurang(item):
    KURANG.append(item)


# ----------------------------------------------------------------- cangkerang
NAV = [
    ("Utama", "/", "utama"),
    ("Tentang", "/tentang/", "tentang"),
    ("Pendidikan & Latihan", "/pendidikan/", "pendidikan"),
    ("Keahlian", "/keahlian/", "keahlian"),
    ("Aktiviti", "/aktiviti/", "aktiviti"),
    ("Sumber", "/sumber/", "sumber"),
    ("Berita", "/berita/", "berita"),
    ("Hubungi", "/hubungi/", "hubungi"),
]


def head(tajuk, deskripsi, laluan, og_jenis="website", jsonld=None):
    kanon = BASE + laluan
    sekatan = []
    sekatan.append('<meta charset="utf-8">')
    sekatan.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    sekatan.append("<title>%s</title>" % esc(tajuk))
    sekatan.append('<meta name="description" content="%s">' % esc(deskripsi))
    sekatan.append('<link rel="canonical" href="%s">' % esc(kanon))
    sekatan.append('<meta name="theme-color" content="#041e54">')
    sekatan.append('<link rel="icon" href="/assets/favicon-64.png" sizes="64x64">')
    sekatan.append('<link rel="apple-touch-icon" href="/assets/apple-touch-180.png">')
    sekatan.append('<link rel="stylesheet" href="/styles.css">')
    sekatan.append('<meta property="og:type" content="%s">' % og_jenis)
    sekatan.append('<meta property="og:site_name" content="MADOCS">')
    sekatan.append('<meta property="og:locale" content="ms_MY">')
    sekatan.append('<meta property="og:title" content="%s">' % esc(tajuk))
    sekatan.append('<meta property="og:description" content="%s">' % esc(deskripsi))
    sekatan.append('<meta property="og:url" content="%s">' % esc(kanon))
    sekatan.append('<meta property="og:image" content="%s/assets/hero-clinical.webp">' % esc(BASE))
    sekatan.append('<meta name="twitter:card" content="summary_large_image">')
    data = [organisasi_ld()]
    if jsonld:
        data.extend(jsonld if isinstance(jsonld, list) else [jsonld])
    for d in data:
        sekatan.append('<script type="application/ld+json">%s</script>'
                       % json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(sekatan)


def organisasi_ld():
    o = {
        "@context": "https://schema.org",
        "@type": "NGO",
        "name": SITE["nama"],
        "alternateName": SITE["singkatan"],
        "url": BASE + "/",
        "email": SITE["email"],
        "telephone": SITE["telefon"],
        "foundingDate": SITE["ditubuhkan"],
        "identifier": SITE["pendaftaran"],
        "areaServed": "MY",
        "logo": BASE + "/assets/logo-128.webp",
        "address": {"@type": "PostalAddress", "addressCountry": "MY"},
    }
    return o


def topbar():
    sos = SITE.get("sosial") or {}
    sosial = "".join('<a href="%s" rel="noopener" aria-label="%s">%s</a>'
                     % (esc(v), esc(k.capitalize()), esc(k[0].upper()))
                     for k, v in sos.items() if v)
    if not sosial:
        sosial = '<a href="mailto:%s" aria-label="E-mel MADOCS">%s</a>' % (esc(SITE["email"]), icon("mail"))
    return f"""<div class="topbar">
  <div class="shell topbar-inner">
    <span>{icon('shield-check')} {esc(SITE['pendaftaran'])}</span>
    <div>
      <a href="mailto:{esc(SITE['email'])}">{icon('mail')} {esc(SITE['email'])}</a>
      <i></i>
      <a href="tel:{esc(SITE['telefon'])}">{icon('phone')} {esc(SITE['telefon_papar'])}</a>
    </div>
  </div>
</div>"""


def header(aktif):
    pautan = "".join(
        '<a class="%s" href="%s"%s>%s</a>'
        % ("active" if kunci == aktif else "", href, ' aria-current="page"' if kunci == aktif else "", esc(label))
        for label, href, kunci in NAV)
    mudah = "".join('<a href="%s">%s</a>' % (href, esc(label)) for label, href, kunci in NAV)
    return f"""<header class="header">
  <div class="shell nav-row">
    <a href="/" class="logo" aria-label="Laman utama MADOCS">
      <img src="/assets/logo-128.webp" alt="Lambang MADOCS" width="55" height="55">
      <span>
        <strong>MADOCS</strong>
        <small>Pertubuhan Doktor Khatan Malaysia</small>
      </span>
    </a>
    <nav class="desktop-nav" aria-label="Navigasi utama">{pautan}</nav>
    <a class="join-nav" href="/keahlian/sertai/" style="text-decoration:none">Sertai MADOCS</a>
    <button class="menu-toggle" aria-label="Buka atau tutup menu" aria-expanded="false">{icon('menu')}</button>
  </div>
  <nav class="mobile-nav" id="menu-mudah" aria-label="Navigasi mudah alih" hidden>
    {mudah}
    <a class="btn btn-primary" href="/keahlian/sertai/" style="justify-content:center">Sertai MADOCS</a>
  </nav>
</header>"""


def footer():
    pintasan = "".join('<a href="%s">%s</a>' % (href, esc(label)) for label, href, kunci in NAV[:6])
    return f"""<footer>
  <div class="shell footer-grid">
    <div>
      <h3>TENTANG MADOCS</h3>
      <p>{esc(SITE['nama'])} ({esc(SITE['singkatan'])}) ialah persatuan profesional yang meningkatkan standard amalan berkhatan selamat melalui pendidikan, latihan, advokasi dan kerjasama profesional.</p>
      <div class="socials">
        <a href="mailto:{esc(SITE['email'])}" aria-label="E-mel">{icon('mail')}</a>
        <a href="tel:{esc(SITE['telefon'])}" aria-label="Telefon">{icon('phone')}</a>
        <a href="/hubungi/" aria-label="Hubungi kami">{icon('globe')}</a>
      </div>
    </div>
    <div>
      <h3>PINTASAN</h3>
      {pintasan}
      <a href="/carian/">Carian</a>
    </div>
    <div>
      <h3>HUBUNGI KAMI</h3>
      <p>{esc(SITE['nama'])}<br>No. Pendaftaran : {esc(SITE['pendaftaran'])}</p>
      <a href="mailto:{esc(SITE['email'])}">{icon('mail')} {esc(SITE['email'])}</a>
      <a href="tel:{esc(SITE['telefon'])}">{icon('phone')} {esc(SITE['telefon_papar'])}</a>
      <span>{icon('map-pin')} {esc(SITE['alamat'])}</span>
    </div>
    <div>
      <h3>LANGGAN BERITA</h3>
      <p>Hantar e-mel kepada urusetia untuk menerima kemas kini kursus, aktiviti dan berita MADOCS.</p>
      <form action="mailto:{esc(SITE['email'])}" method="get" enctype="text/plain">
        <label>{icon('mail')}<input type="email" name="email" placeholder="Alamat e-mel anda" aria-label="Alamat e-mel" required></label>
        <button type="submit">LANGGAN</button>
      </form>
    </div>
  </div>
  <div class="shell footer-bottom">
    <span>© {date.today().year} {esc(SITE['nama'])}. Hak cipta terpelihara.</span>
    <span><a href="/dasar-privasi/">Dasar Privasi</a><i></i><a href="/terma/">Terma Penggunaan</a></span>
  </div>
</footer>"""


def halaman(aktif, tajuk, deskripsi, laluan, isi, og_jenis="website", jsonld=None, masuk_sitemap=True):
    dokumen = f"""<!DOCTYPE html>
<html lang="ms">
<head>
{head(tajuk, deskripsi, laluan, og_jenis, jsonld)}
</head>
<body>
<a class="skip-link" href="#kandungan">Lompat ke kandungan utama</a>
{topbar()}
{header(aktif)}
<main id="kandungan">
{isi}
</main>
{footer()}
<script src="/app.js" defer></script>
</body>
</html>
"""
    tulis(laluan, dokumen, masuk_sitemap)


def tulis(laluan, kandungan, masuk_sitemap=True):
    """laluan contohnya '/tentang/' atau '/404.html'."""
    if laluan.endswith("/"):
        fail = ROOT / (laluan.strip("/") or "") / "index.html" if laluan != "/" else ROOT / "index.html"
    else:
        fail = ROOT / laluan.strip("/")
    fail.parent.mkdir(parents=True, exist_ok=True)
    fail.write_text(kandungan, encoding="utf-8")
    if masuk_sitemap:
        PAGES.append(laluan)


# ----------------------------------------------------------------- komponen
def crumbs(items):
    bahagian = []
    for i, (label, href) in enumerate(items):
        if i:
            bahagian.append(icon("chevron-right"))
        bahagian.append('<a href="%s">%s</a>' % (href, esc(label)) if href else "<span>%s</span>" % esc(label))
    return '<nav class="crumbs" aria-label="Jejak navigasi">%s</nav>' % "".join(bahagian)


def page_hero(jejak, tajuk, huraian="", butang="", kicker=""):
    k = '<p class="hero-kicker">%s</p>' % esc(kicker) if kicker else ""
    return f"""<section class="page-hero">
  <div class="shell">
    {crumbs(jejak)}
    {k}
    <h1>{esc(tajuk)}</h1>
    {f'<p>{esc(huraian)}</p>' if huraian else ''}
    {butang}
  </div>
</section>"""


def badge_status(status):
    label, kelas = STATUS_LABEL.get(status, (status, ""))
    return '<span class="badge %s">%s</span>' % (kelas, esc(label))


def kad_kursus(k, keutamaan=False):
    d = parse_date(k.get("tarikh"))
    badge = ""
    if d:
        badge = ('<span class="date-badge"><b>%d</b> %s<small>%d</small></span>'
                 % (d.day, BULAN_SING[d.month - 1], d.year))
    fakta = []
    if d:
        fakta.append(f"<li>{icon('calendar-days')}{esc(tarikh_pjg(d))}</li>")
    if k.get("tempat"):
        fakta.append(f"<li>{icon('map-pin')}{esc(k['tempat'])}</li>")
    if k.get("sasaran"):
        fakta.append(f"<li>{icon('users')}{esc(k['sasaran'])}</li>")
    if k.get("masa_mula"):
        fakta.append(f"<li>{icon('clock')}{esc(k['masa_mula'])}–{esc(k.get('masa_tamat',''))}</li>")
    tag = "".join("<span>%s</span>" % esc(t) for t in (k.get("tag") or []))
    img = k.get("gambar") or "assets/hero-clinical.webp"
    alt = k.get("gambar_alt") or k.get("tajuk", "")
    return f"""<article class="course-feature">
  <div class="course-photo">
    <img src="/{esc(img)}" alt="{esc(alt)}" loading="{'eager' if keutamaan else 'lazy'}" decoding="async">
    {badge}
  </div>
  <div class="course-info">
    <span class="course-code">{esc(k.get('kod',''))}</span>
    <h3>{esc(k['tajuk'])}</h3>
    <ul>{''.join(fakta)}</ul>
    {f'<div class="tags">{tag}</div>' if tag else ''}
    <div class="course-actions">
      <a class="small-btn filled" href="/pendidikan/{esc(k['slug'])}/" style="display:inline-flex;align-items:center;text-decoration:none">Lihat kursus</a>
      {'<a class="small-btn" href="%s" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;text-decoration:none">Daftar</a>' % esc(k['daftar_url']) if k.get('daftar_url') else '<a class="small-btn" href="/hubungi/" style="display:inline-flex;align-items:center;text-decoration:none">Daftar</a>'}
    </div>
  </div>
</article>"""


def kad_aktiviti(a):
    d = parse_date(a.get("tarikh"))
    kelas = "teal" if (a.get("kategori") or "").upper() in ("TTT", "PCC") else ""
    return f"""<article class="activity-card">
  <div class="activity-image">
    <img src="/{esc(a.get('gambar','assets/hero-clinical.webp'))}" alt="{esc(a.get('gambar_alt') or a['tajuk'])}" loading="lazy" decoding="async">
    <span class="{kelas}">{esc(a.get('kategori',''))}</span>
  </div>
  <div class="activity-info">
    <h3>{esc(a['tajuk'])}</h3>
    <p>{icon('calendar-days')}{esc(tarikh_pdk(d))}</p>
    <p>{icon('map-pin')}{esc(a.get('tempat',''))}</p>
    <a href="/aktiviti/{esc(a['slug'])}/">Baca lanjut {icon('arrow-right')}</a>
  </div>
</article>"""


def item_kandungan(tajuk, url, ringkas, tarikh=None, kategori="", gambar=None, alt="", meta_ikon="calendar-days"):
    """Kad senarai untuk berita / aktiviti / sumber."""
    foto = ('<div class="item-photo"><img src="/%s" alt="%s" loading="lazy" decoding="async"></div>'
            % (esc(gambar), esc(alt or tajuk))) if gambar else ""
    kelas = "" if gambar else " no-photo"
    badge = '<span class="badge">%s</span>' % esc(kategori) if kategori else ""
    masa = ('<time datetime="%s">%s %s</time>' % (esc(tarikh), icon(meta_ikon), esc(tarikh_pdk(parse_date(tarikh))))) if tarikh else ""
    return f"""<article class="item{kelas}">
  {foto}
  <div class="item-body">
    {badge}
    <h3><a href="{esc(url)}">{esc(tajuk)}</a></h3>
    <div class="item-meta">{masa}</div>
    {f'<p>{esc(ringkas)}</p>' if ringkas else ''}
    <a class="lebih" href="{esc(url)}">Baca lanjut {icon('arrow-right')}</a>
  </div>
</article>"""


def kosong(ikon_nama, tajuk, mesej, butang=""):
    return f"""<div class="kosong">
  <span class="ikon">{icon(ikon_nama)}</span>
  <h3>{esc(tajuk)}</h3>
  <p>{esc(mesej)}</p>
  {butang}
</div>"""


def cta_komuniti(tajuk="SERTAI KOMUNITI PROFESIONAL MADOCS",
                 mesej="Bersama-sama kita memartabatkan amalan khatan yang selamat, profesional dan beretika di Malaysia.",
                 label="SERTAI MADOCS SEKARANG", href="/keahlian/sertai/"):
    return f"""<section class="community-cta">
  <div class="shell cta-grid">
    <span class="cta-icon">{icon('users')}</span>
    <div>
      <h2>{esc(tajuk)}</h2>
      <p>{esc(mesej)}</p>
    </div>
    <a href="{href}" style="text-decoration:none;min-height:46px;color:var(--blue);text-transform:uppercase;background:#fff;border-radius:5px;align-items:center;gap:14px;padding:0 28px;font-size:10px;font-weight:800;display:inline-flex;box-shadow:0 8px 22px #041e5433">{esc(label)} {icon('arrow-right')}</a>
  </div>
</section>"""


def laman_ringkas(slug, tajuk, isi_html):
    """Halaman teks ringkas (dasar privasi, terma)."""
    dalam = f"""<section class="page-hero">
  <div class="shell">{crumbs([("Utama", "/")])}<h1>{esc(tajuk)}</h1></div>
</section>
<section class="content-wrap"><div class="shell"><div class="card prose">{isi_html}</div></div></section>"""
    halaman("", tajuk + " | MADOCS", tajuk + " MADOCS.", "/%s/" % slug, dalam)


# ----------------------------------------------------------------- halaman: utama
def bina_utama():
    stats = load("stats.json")
    kursus = load("kursus.json")["kursus"]
    aktiviti = load("aktiviti.json")["aktiviti"]
    sumber = load("sumber.json")["sumber"]
    berita = load("berita.json")["berita"]
    keahlian = load("keahlian.json")
    hari_ini = date.today()

    akan_datang = sorted([k for k in kursus
                          if k.get("status") in ("open", "limited")
                          and (parse_date(k.get("tarikh")) or hari_ini) >= hari_ini],
                         key=lambda k: k.get("tarikh") or "")
    lepas = sorted([k for k in kursus if k not in akan_datang],
                   key=lambda k: k.get("tarikh") or "", reverse=True)

    # --- sepanduk kredensial
    kred = [("shield-check", "Persatuan Profesional<br>Berdaftar", SITE["pendaftaran"]),
            ("graduation-cap", "Pendidikan Klinikal<br>&amp; Latihan", "CCC · PCC · TTT"),
            ("stethoscope", "Pembangunan<br>Profesional", "CPD &amp; Pembelajaran Berterusan"),
            ("users", "Komuniti<br>Seluruh Negara", "Seluruh Malaysia")]
    kred_html = "".join(
        '<div><span>%s</span><p><strong>%s</strong><small>%s</small></p></div>' % (icon(i), t, s)
        for i, t, s in kred)

    # --- statistik (PRD §11: hanya jika disahkan)
    if stats.get("disahkan"):
        stat_items = "".join(
            '<div class="stat"><span>%s</span><p><strong>%s</strong><b>%s</b><small>%s</small></p></div>'
            % (icon(it.get("ikon", "target")), esc(it["nilai"]), esc(it["label"]), esc(it.get("sub", "")))
            for it in stats["items"])
    else:
        kurang("Angka statistik (PRD §11) belum disahkan — data/stats.json masih 'disahkan': false.")
        stat_items = "".join(
            '<div class="stat"><span>%s</span><p><strong>—</strong><b>%s</b><small>Menunggu pengesahan</small></p></div>'
            % (icon(it.get("ikon", "target")), esc(it["label"]))
            for it in stats["items"])

    # --- kursus akan datang
    if akan_datang:
        kursus_html = kad_kursus(akan_datang[0], keutamaan=True)
        baki = "".join(
            '<article class="item no-photo"><div class="item-body">%s<h3><a href="/pendidikan/%s/">%s</a></h3>'
            '<div class="item-meta"><time datetime="%s">%s %s</time><span>%s %s</span></div>'
            '<a class="lebih" href="/pendidikan/%s/">Lihat butiran %s</a></div></article>'
            % (badge_status(k.get("status")), esc(k["slug"]), esc(k["tajuk"]), esc(k.get("tarikh", "")),
               icon("calendar-days"), esc(tarikh_pjg(parse_date(k.get("tarikh")))), icon("map-pin"),
               esc(k.get("tempat", "")), esc(k["slug"]), icon("arrow-right"))
            for k in akan_datang[1:4])
        kursus_html += ('<div class="listing" style="margin-top:18px">%s</div>' % baki) if baki else ""
    else:
        kurang("Tiada kursus akan datang dalam data/kursus.json — PRD §58 memerlukan sekurang-kurangnya satu program latihan yang boleh diterbitkan.")
        kursus_html = kosong(
            "calendar-days", "Tiada kursus akan datang buat masa ini",
            "Jadual latihan sedang disusun. Hubungi urusetia MADOCS untuk maklumat program seterusnya, atau lihat program yang telah dijalankan.",
            '<div style="margin-top:20px"><a class="btn btn-primary" href="/pendidikan/">Lihat program lepas</a></div>')
        if lepas:
            kursus_html += '<div style="margin-top:22px">%s</div>' % kad_kursus(lepas[0])

    # --- perkhidmatan
    servis = [("graduation-cap", "Pendidikan &amp; Latihan", "Program latihan klinikal berstruktur untuk meningkatkan kemahiran dan kompetensi pengamal."),
              ("shield-check", "Standard Klinikal", "Menyokong amalan berkhatan yang selamat melalui garis panduan dan standard terbaik."),
              ("target", "Pembangunan Profesional", "Menyediakan platform CPD, sokongan profesional dan perkongsian ilmu berterusan."),
              ("heart-handshake", "Advokasi &amp; Komuniti", "Mewakili kepentingan ahli dan menyokong program CSR serta kesihatan masyarakat.")]
    servis_html = "".join('<article><span>%s</span><div><h3>%s</h3><p>%s</p></div></article>'
                          % (icon(i), t, p) for i, t, p in servis)

    # --- mengapa sertai
    manfaat = "".join('<div class="tile"><span class="ikon">%s</span><h3>%s</h3></div>'
                      % (icon("check"), esc(m)) for m in keahlian.get("manfaat", []))

    # --- aktiviti
    aktiviti_html = "".join(kad_aktiviti(a) for a in aktiviti[:4]) or kosong(
        "users", "Belum ada aktiviti diterbitkan", "Gambar dan laporan aktiviti MADOCS akan dimuat naik oleh urusetia.")

    # --- sumber
    if sumber:
        sumber_html = "".join(
            item_kandungan(s["tajuk"], "/sumber/%s/" % s["slug"], s.get("ringkas", ""),
                           kategori=s.get("kategori", ""), gambar=s.get("gambar"))
            for s in sumber[:3])
        sumber_html = '<div class="listing">%s</div>' % sumber_html
    else:
        kurang("Tiada sumber klinikal dalam data/sumber.json (PRD §19, §49).")
        sumber_html = kosong("book-open", "Pusat Sumber sedang disediakan",
                             "Bahan rujukan klinikal, garis panduan dan bahan pendidikan akan diterbitkan di sini selepas semakan klinikal (PRD §21).")

    # --- berita
    if berita:
        berita_html = "".join(
            item_kandungan(b["tajuk"], "/berita/%s/" % b["slug"], b.get("ringkas", ""),
                           tarikh=b.get("tarikh"), kategori=b.get("kategori", ""), gambar=b.get("gambar"))
            for b in berita[:3])
        berita_html = '<div class="listing">%s</div>' % berita_html
    else:
        kurang("Tiada berita dalam data/berita.json (PRD §49).")
        berita_html = kosong("file-text", "Belum ada berita diterbitkan",
                             "Pengumuman dan berita MADOCS akan diterbitkan di sini.")

    isi = f"""<section class="hero">
  <img src="/assets/hero-clinical.webp" alt="Profesional perubatan dalam latihan klinikal MADOCS" width="1920" height="1920" class="hero-image" fetchpriority="high" decoding="async">
  <div class="hero-wash"></div>
  <div class="shell hero-content">
    <div class="hero-copy">
      <p class="hero-kicker">Ditubuhkan {esc(SITE['ditubuhkan'])} · Malaysia</p>
      <h1>{esc(SITE['nama'].upper())} ({esc(SITE['singkatan'])})</h1>
      <h2>Memajukan Amalan Berkhatan Selamat di Malaysia</h2>
      <p>Memperkasa pengamal perubatan melalui pendidikan, latihan klinikal berstruktur, pembangunan profesional dan amalan khatan yang selamat.</p>
      <div class="hero-buttons">
        <a href="/pendidikan/" class="btn btn-primary">{icon('book-open')} LIHAT KURSUS</a>
        <a href="/keahlian/sertai/" class="btn btn-outline">SERTAI MADOCS</a>
      </div>
    </div>
  </div>
</section>

<section class="credential-band">
  <div class="shell credential-grid">{kred_html}</div>
</section>

<section class="section-pad" id="tentang">
  <div class="shell overview-grid">
    <div class="upcoming">
      <div class="section-title-row"><h2>TENTANG MADOCS</h2></div>
      <div class="prose">
        <p>{esc(SITE['nama'])} ({esc(SITE['singkatan'])}) ialah persatuan profesional yang menghimpunkan doktor yang terlibat dalam amalan, pendidikan dan latihan berkhatan di Malaysia.</p>
        <p>Kami menyediakan platform latihan klinikal berstruktur, pembangunan profesional berterusan dan perkongsian ilmu bagi meningkatkan kualiti serta keselamatan perkhidmatan berkhatan untuk masyarakat.</p>
      </div>
      <div style="margin-top:18px"><a class="btn btn-primary" href="/tentang/">Kenali MADOCS {icon('arrow-right')}</a></div>
    </div>
    <div class="what-we-do">
      <div class="section-title-row"><h2>APA YANG KAMI LAKUKAN</h2></div>
      <div class="service-grid">{servis_html}</div>
    </div>
  </div>
</section>

<section class="stats-band">
  <div class="shell stats-grid">
    <h2>MADOCS DALAM<br>ANGKA</h2>
    {stat_items}
  </div>
</section>

<section class="section-pad" id="kursus">
  <div class="shell">
    <div class="section-title-row activities-head">
      <h2>KURSUS AKAN DATANG</h2>
      <a href="/pendidikan/">Lihat semua kursus {icon('arrow-right')}</a>
    </div>
    {kursus_html}
  </div>
</section>

<section class="section-pad" style="background:var(--ice);border-block:1px solid var(--line)">
  <div class="shell">
    <div class="section-title-row activities-head">
      <h2>MENGAPA SERTAI MADOCS</h2>
      <a href="/keahlian/">Maklumat keahlian {icon('arrow-right')}</a>
    </div>
    <div class="grid-3">{manfaat}</div>
  </div>
</section>

<section class="activities section-pad" id="aktiviti">
  <div class="shell">
    <div class="section-title-row activities-head">
      <h2>AKTIVITI TERKINI</h2>
      <a href="/aktiviti/">Lihat semua aktiviti {icon('arrow-right')}</a>
    </div>
    <div class="activity-stage">
      <button class="carousel-arrow left" aria-label="Aktiviti sebelumnya">{icon('arrow-left')}</button>
      <div class="activity-grid">{aktiviti_html}</div>
      <button class="carousel-arrow right" aria-label="Aktiviti seterusnya">{icon('arrow-right')}</button>
    </div>
  </div>
</section>

<section class="section-pad" style="background:var(--ice);border-block:1px solid var(--line)">
  <div class="shell">
    <div class="section-title-row activities-head">
      <h2>PUSAT SUMBER</h2>
      <a href="/sumber/">Semua sumber {icon('arrow-right')}</a>
    </div>
    {sumber_html}
  </div>
</section>

<section class="section-pad">
  <div class="shell">
    <div class="section-title-row activities-head">
      <h2>BERITA TERKINI</h2>
      <a href="/berita/">Semua berita {icon('arrow-right')}</a>
    </div>
    {berita_html}
  </div>
</section>

{cta_komuniti()}

<section class="content-wrap" style="padding-top:34px">
  <div class="shell">
    <div class="search-bar">
      {icon('search')}
      <input type="search" id="carian-pantas" placeholder="Cari kursus, berita, sumber atau aktiviti…" aria-label="Carian pantas">
      <a class="small-btn filled" id="butang-carian" href="/carian/" style="display:inline-flex;align-items:center;text-decoration:none">CARI</a>
    </div>
  </div>
</section>"""

    halaman("utama", "MADOCS — Pertubuhan Doktor Khatan Malaysia",
            "Pertubuhan Doktor Khatan Malaysia (MADOCS) memajukan amalan berkhatan selamat melalui pendidikan, latihan klinikal berstruktur dan pembangunan profesional doktor di Malaysia.",
            "/", isi)


# ----------------------------------------------------------------- halaman: tentang
def bina_tentang():
    jk = load("jawatankuasa.json")["jawatankuasa"]
    if not jk:
        kurang("Senarai Jawatankuasa Eksekutif kosong (data/jawatankuasa.json) — diperlukan oleh PRD §9.2 dan §55.")
        ahli_html = kosong("users", "Senarai jawatankuasa belum disediakan",
                           "Struktur halaman ini sedia untuk memaparkan Jawatankuasa Eksekutif sebaik sahaja nama dan gambar disahkan oleh MADOCS.")
    else:
        ahli_html = '<div class="grid-4">%s</div>' % "".join(
            '<div class="tile">%s<h3>%s</h3><p>%s</p></div>'
            % ('<img src="/%s" alt="%s" style="width:100%%;border-radius:10px;margin-bottom:14px">' % (esc(a["gambar"]), esc(a["nama"])) if a.get("gambar") else "",
               esc(a["nama"]), esc(a.get("jawatan", "")))
            for a in jk)

    fakta = {'<dt>': '<dt>', }
    tadbir = f"""<dl class="facts">
  <div><dt>Nama berdaftar</dt><dd>{esc(SITE['nama'])} ({esc(SITE['nama_en'])})</dd></div>
  <div><dt>Nombor pendaftaran</dt><dd>{esc(SITE['pendaftaran'])}</dd></div>
  <div><dt>Ditubuhkan</dt><dd>{esc(SITE['ditubuhkan'])}</dd></div>
  <div><dt>Skop</dt><dd>Malaysia</dd></div>
  <div><dt>E-mel urusetia</dt><dd><a href="mailto:{esc(SITE['email'])}">{esc(SITE['email'])}</a></dd></div>
</dl>"""
    kurang("Visi, misi, sejarah dan dokumen tadbir urus/perlembagaan (PRD §9.2, §55) belum disediakan — halaman menggunakan teks sementara.")

    isi = page_hero([("Utama", "/"), ("Tentang", None)], "Tentang MADOCS",
                    "Persatuan profesional yang menghimpunkan doktor terlibat dalam amalan berkhatan di Malaysia.") + f"""
<section class="content-wrap">
  <div class="shell split">
    <div>
      <div class="card prose">
        <h2>Latar belakang</h2>
        <p>{esc(SITE['nama'])} ({esc(SITE['singkatan'])}) ialah pertubuhan profesional yang berdaftar dengan Pendaftar Pertubuhan Malaysia. MADOCS menghimpunkan doktor yang terlibat dalam amalan berkhatan dengan matlamat meningkatkan standard klinikal, keselamatan pesakit dan kualiti latihan.</p>
        <p>Kandungan rasmi mengenai visi, misi dan sejarah penubuhan akan diterbitkan di sini sebaik sahaja disahkan oleh jawatankuasa.</p>
        <h2>Visi</h2>
        <p>Menjadi platform digital profesional yang terkemuka bagi doktor yang terlibat dalam amalan berkhatan di Malaysia.</p>
        <h2>Misi</h2>
        <ul>
          <li>Meningkatkan standard dan keselamatan amalan berkhatan melalui pendidikan dan latihan.</li>
          <li>Menyediakan latihan klinikal berstruktur dan pembangunan profesional berterusan.</li>
          <li>Menyokong perkongsian ilmu, penyelidikan dan jaringan profesional antara doktor.</li>
          <li>Mewakili kepentingan ahli dan menyokong program kesihatan masyarakat.</li>
        </ul>
        <h2>Tadbir urus</h2>
        {tadbir}
        <p class="nota-isi">Butiran perlembagaan dan dokumen rasmi akan diterbitkan selepas kelulusan jawatankuasa.</p>
      </div>
      <div class="card">
        <h2>Jawatankuasa Eksekutif</h2>
        {ahli_html}
      </div>
    </div>
    <aside class="side">
      <div class="card">
        <h3>Pintasan</h3>
        <nav class="side-nav">
          <a class="aktif" href="/tentang/">Tentang MADOCS</a>
          <a href="/pendidikan/">Pendidikan &amp; Latihan</a>
          <a href="/keahlian/">Keahlian</a>
          <a href="/hubungi/">Hubungi urusetia</a>
        </nav>
      </div>
      <div class="card">
        <h3>Sertai MADOCS</h3>
        <p style="font-size:11px;line-height:1.7;color:#3b4659">Doktor yang berminat dalam amalan berkhatan dialu-alukan menyertai MADOCS.</p>
        <a class="btn-blok" href="/keahlian/sertai/" style="margin-top:14px">Borang keahlian {icon('arrow-right')}</a>
      </div>
    </aside>
  </div>
</section>"""
    halaman("tentang", "Tentang MADOCS | Pertubuhan Doktor Khatan Malaysia",
            "Mengenai Pertubuhan Doktor Khatan Malaysia (MADOCS): latar belakang, visi, misi, tadbir urus dan jawatankuasa eksekutif.",
            "/tentang/", isi)


# ----------------------------------------------------------------- halaman: pendidikan
def bina_pendidikan():
    kursus = load("kursus.json")["kursus"]
    hari_ini = date.today()
    akan = sorted([k for k in kursus if k.get("status") in ("open", "limited")], key=lambda k: k.get("tarikh") or "")
    lepas = sorted([k for k in kursus if k.get("status") in ("closed", "done")], key=lambda k: k.get("tarikh") or "", reverse=True)

    kategori = [("graduation-cap", "Kursus Komprehensif Berkhatan", "CCC", "Latihan menyeluruh: teori, demonstrasi, amali dan penilaian."),
                ("stethoscope", "Pendidikan Klinikal &amp; Procedural", "PCC", "Kemahiran prosedur klinikal dan pengurusan komplikasi."),
                ("users", "Latihan Tenaga Pengajar", "TTT", "Menyediakan tenaga pengajar bertauliah dalam latihan MADOCS."),
                ("file-text", "Seminar, Bengkel &amp; Konferens", "Aktiviti", "Pembelajaran berterusan dan perkongsian ilmu profesional.")]

    def senarai(items, kosong_teks):
        if not items:
            return kosong_teks
        return '<div class="listing">%s</div>' % "".join(
            item_kandungan(k["tajuk"], "/pendidikan/%s/" % k["slug"], k.get("ringkas", ""),
                           tarikh=k.get("tarikh"), kategori=k.get("kod", ""), gambar=k.get("gambar"))
            for k in items)

    isi = page_hero([("Utama", "/"), ("Pendidikan & Latihan", None)],
                    "Pendidikan & Latihan",
                    "Program latihan klinikal berstruktur untuk doktor yang terlibat dalam amalan berkhatan.",
                    '<div class="hero-buttons"><a class="btn btn-primary" href="#akan-datang">KURSUS AKAN DATANG</a>'
                    '<a class="btn btn-outline" href="/keahlian/sertai/">SERTAI MADOCS</a></div>') + f"""
<section class="content-wrap">
  <div class="shell">
    <div class="grid-4">{''.join('<div class="tile"><span class="ikon">%s</span><h3>%s</h3><p>%s</p></div>' % (icon(i), t, p) for i, t, c, p in kategori)}</div>
  </div>
</section>

<section class="content-wrap" id="akan-datang" style="padding-top:0">
  <div class="shell">
    <div class="section-title-row activities-head"><h2>KURSUS AKAN DATANG</h2></div>
    {senarai(akan, kosong("calendar-days", "Tiada kursus akan datang buat masa ini",
                          "Jadual latihan sedang disusun. Hubungi urusetia MADOCS atau semak semula tidak lama lagi.",
                          '<div style="margin-top:20px"><a class="btn btn-primary" href="/hubungi/">Hubungi urusetia</a></div>'))}
  </div>
</section>

<section class="content-wrap" style="padding-top:0">
  <div class="shell">
    <div class="section-title-row activities-head"><h2>PROGRAM LEPAS</h2></div>
    {senarai(lepas, kosong("clock", "Belum ada rekod program lepas", "Rekod program yang telah dijalankan akan diterbitkan di sini."))}
  </div>
</section>

{cta_komuniti(tajuk='PERTANYAAN TENTANG LATIHAN MADOCS',
              mesej='Urusetia MADOCS boleh membantu anda memilih program latihan yang sesuai dengan keperluan amalan anda.',
              label='HUBUNGI URUSETIA', href='/hubungi/')}"""
    halaman("pendidikan", "Pendidikan & Latihan | MADOCS",
            "Kursus, bengkel dan latihan klinikal berstruktur MADOCS untuk doktor di Malaysia: CCC, PCC, TTT dan aktiviti pembelajaran berterusan.",
            "/pendidikan/", isi)


def bina_kursus_detail(k):
    d = parse_date(k.get("tarikh"))
    selesai = k.get("status") in ("closed", "done")
    fakta = []

    def baris(kunci, nilai):
        if nilai:
            fakta.append("<div><dt>%s</dt><dd>%s</dd></div>" % (esc(kunci), nilai))

    baris("Tarikh", esc(tarikh_pjg(d)) if d else "")
    if k.get("masa_mula"):
        baris("Masa", esc(k["masa_mula"]) + " – " + esc(k.get("masa_tamat", "")))
    baris("Tempat", esc(k.get("tempat", "")))
    baris("Penganjur", esc(k.get("penganjur", "")))
    baris("Tenaga pengajar", esc(k.get("fakulti", "")))
    baris("Peserta sasaran", esc(k.get("sasaran", "")))
    if k.get("yuran") or k.get("yuran_ahli"):
        baris("Yuran", esc(k.get("yuran") or ""))
    if k.get("yuran_ahli"):
        baris("Yuran ahli", esc(k["yuran_ahli"]))
    if k.get("yuran_bukan_ahli"):
        baris("Yuran bukan ahli", esc(k["yuran_bukan_ahli"]))
    if k.get("tutup_daftar"):
        baris("Tutup pendaftaran", esc(tarikh_pdk(parse_date(k["tutup_daftar"]))))
    if k.get("kapasiti"):
        baris("Kapasiti peserta", esc(k["kapasiti"]))
    baris("Status", badge_status(k.get("status")))

    for medan, label in (("objektif", "Objektif pembelajaran"), ("rangka", "Rangka program")):
        if not k.get(medan):
            kurang("Butiran '%s' belum diisi untuk kursus %s (PRD §12)." % (label, k["kod"]))
    for medan in ("yuran", "tutup_daftar", "kapasiti", "fakulti"):
        if not k.get(medan):
            kurang("Medan '%s' kosong untuk kursus %s (PRD §12)." % (medan, k["kod"]))

    objektif = ""
    if k.get("objektif"):
        objektif = "<h2>Objektif pembelajaran</h2><ul>%s</ul>" % "".join("<li>%s</li>" % esc(o) for o in k["objektif"])
    rangka = ""
    if k.get("rangka"):
        rangka = "<h2>Rangka program</h2><dl class='facts'>%s</dl>" % "".join(
            "<div><dt>%s</dt><dd>%s</dd></div>" % (esc(r.get("masa", "")), esc(r.get("slot", ""))) for r in k["rangka"])

    kandungan = "".join("<p>%s</p>" % esc(p) for p in k.get("kandungan", []))

    # pautan kalendar & kongsi (§13)
    kal = ""
    if d and k.get("masa_mula"):
        h1, m1 = (k["masa_mula"].split(":") + ["00"])[:2]
        h2_, m2 = ((k.get("masa_tamat") or k["masa_mula"]).split(":") + ["00"])[:2]
        mula = "%sT%s%s00" % (d.strftime("%Y%m%d"), h1.zfill(2), m1.zfill(2))
        tamat = "%sT%s%s00" % (d.strftime("%Y%m%d"), h2_.zfill(2), m2.zfill(2))
        kal = ("https://calendar.google.com/calendar/render?action=TEMPLATE&text=%s&dates=%s/%s&details=%s&location=%s"
               % (k["tajuk"].replace(" ", "+"), mula, tamat,
                  ("Maklumat lanjut: " + BASE + "/pendidikan/" + k["slug"] + "/").replace(" ", "+"),
                  (k.get("tempat") or "").replace(" ", "+")))
    url_kongsi = BASE + "/pendidikan/" + k["slug"] + "/"
    kongsi = f"""<div class="chips" aria-label="Kongsi kursus ini">
  <span style="background:#fff;border:1px solid var(--line)">Kongsi:</span>
  <a class="badge" href="https://wa.me/?text={esc(k['tajuk'] + ' — ' + url_kongsi)}" target="_blank" rel="noopener">WhatsApp</a>
  <a class="badge" href="https://www.facebook.com/sharer/sharer.php?u={esc(url_kongsi)}" target="_blank" rel="noopener">Facebook</a>
  <a class="badge" href="https://t.me/share/url?url={esc(url_kongsi)}&text={esc(k['tajuk'])}" target="_blank" rel="noopener">Telegram</a>
  <a class="badge" href="mailto:?subject={esc(k['tajuk'])}&body={esc(url_kongsi)}">E-mel</a>
</div>"""

    if selesai:
        butang_daftar = (f'<div class="form-note" style="margin-top:18px"><b>Program ini telah selesai.</b> '
                         f'Maklumat program akan datang boleh dilihat di halaman <a href="/pendidikan/">Pendidikan &amp; Latihan</a>. '
                         f'Untuk pertanyaan, hubungi urusetia MADOCS.</div>')
    elif k.get("daftar_url"):
        butang_daftar = (f'<a class="btn-hantar" href="{esc(k["daftar_url"])}" target="_blank" rel="noopener">'
                         f'DAFTAR SEKARANG {icon("external-link")}</a>')
    else:
        kurang("Pautan pendaftaran (daftar_url) belum ditetapkan untuk kursus %s (PRD §14)." % k["kod"])
        butang_daftar = (f'<a class="btn-hantar" href="/hubungi/?kursus={esc(k["slug"])}">'
                         f'DAFTAR MELALUI URUSETIA {icon("arrow-right")}</a>')

    kaitan = [x for x in load("kursus.json")["kursus"] if x["slug"] != k["slug"]][:2]
    kaitan_html = ""
    if kaitan:
        kaitan_html = '<div class="card"><h2>Program lain</h2><div class="listing">%s</div></div>' % "".join(
            item_kandungan(x["tajuk"], "/pendidikan/%s/" % x["slug"], x.get("ringkas", ""),
                           tarikh=x.get("tarikh"), kategori=x.get("kod", "")) for x in kaitan)

    ld = []
    if d:
        ld.append({"@context": "https://schema.org", "@type": "Course",
                   "name": k["tajuk"], "description": k.get("ringkas", ""),
                   "provider": {"@type": "Organization", "name": SITE["nama"], "sameAs": BASE + "/"},
                   "url": url_kongsi,
                   "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "onsite",
                                         "startDate": k.get("tarikh", ""),
                                         "location": {"@type": "Place", "name": k.get("tempat", ""),
                                                      "address": {"@type": "PostalAddress", "addressCountry": "MY"}}}})

    isi = page_hero([("Utama", "/"), ("Pendidikan & Latihan", "/pendidikan/"), (k["kod"], None)],
                    k["tajuk"], k.get("ringkas", "")) + f"""
<section class="content-wrap">
  <div class="shell split">
    <div>
      <div class="card">
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:16px">
          <span class="course-code">{esc(k.get('kod',''))}</span>{badge_status(k.get('status'))}
        </div>
        {'<img src="/%s" alt="%s" style="width:100%%;border-radius:11px;margin-bottom:22px">' % (esc(k['gambar']), esc(k.get('gambar_alt') or k['tajuk'])) if k.get('gambar') else ''}
        <div class="prose">{kandungan}</div>
        {objektif}
        {rangka}
      </div>
      <div class="card">
        <h2>Maklumat program</h2>
        <dl class="facts">{''.join(fakta)}</dl>
        <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;align-items:center">
          {butang_daftar}
          {f'<a class="btn btn-outline" href="{kal}" target="_blank" rel="noopener">{icon("calendar-days")} TAMBAH KE KALENDAR</a>' if kal else ''}
        </div>
        {kongsi}
      </div>
      {kaitan_html}
    </div>
    <aside class="side">
      <div class="card">
        <h3>Ringkasan</h3>
        <div class="item-meta" style="display:grid;gap:9px">
          <time datetime="{esc(k.get('tarikh',''))}">{icon('calendar-days')}{esc(tarikh_pjg(d))}</time>
          <span>{icon('map-pin')}{esc(k.get('tempat',''))}</span>
          <span>{icon('users')}{esc(k.get('sasaran',''))}</span>
        </div>
        <a class="btn-blok" href="{'/pendidikan/' if selesai else '#kandungan'}" style="margin-top:16px">{icon('calendar-days')} {'Kursus akan datang' if selesai else 'Maklumat pendaftaran'}</a>
      </div>
      <div class="card">
        <h3>Perlukan bantuan?</h3>
        <p style="font-size:11px;line-height:1.7;color:#3b4659">Hubungi urusetia MADOCS untuk pertanyaan tentang pendaftaran, yuran atau keperluan kursus.</p>
        <a class="btn-blok ghost" href="/hubungi/" style="margin-top:14px">{icon('mail')} Hubungi urusetia</a>
      </div>
    </aside>
  </div>
</section>"""

    halaman("pendidikan", "%s — %s | MADOCS" % (k["tajuk"], k.get("kod", "")),
            k.get("ringkas", "%s oleh MADOCS." % k["tajuk"])[:180],
            "/pendidikan/%s/" % k["slug"], isi, og_jenis="article", jsonld=ld)


# ----------------------------------------------------------------- halaman: keahlian
def bina_keahlian():
    kh = load("keahlian.json")
    disahkan = kh.get("disahkan")
    jika_belum = ""

    if not disahkan:
        kurang("Maklumat keahlian (kelayakan, kategori, yuran) belum disahkan — data/keahlian.json 'disahkan': false (PRD §56.1–§56.3).")
        jika_belum = ('<div class="pengesahan"><b>Belum disahkan jawatankuasa:</b> kelayakan, kategori dan yuran keahlian '
                      'sedang disahkan. Laman ini hanya menerbitkan maklumat yang telah diluluskan. Sila hubungi urusetia '
                      'MADOCS untuk maklumat terkini.</div>')

    manfaat = "".join('<div class="tile"><span class="ikon">%s</span><h3>%s</h3></div>' % (icon("check"), esc(m))
                      for m in kh.get("manfaat", []))

    def jadual(baris, kepala, kosong_teks):
        if not baris:
            return '<div class="form-note">%s</div>' % esc(kosong_teks)
        return ('<div class="table-wrap"><table class="data"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
                % ("".join("<th>%s</th>" % esc(h) for h in kepala),
                   "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in baris)))

    kategori = jadual([[esc(k["nama"]), esc(k.get("kelayakan", "")), esc(k.get("yuran", ""))] for k in kh.get("kategori", [])],
                      ["Kategori", "Kelayakan", "Yuran"],
                      "Kategori keahlian sedang disahkan oleh jawatankuasa MADOCS.")

    yuran = jadual([[esc(y["kategori"]), esc(y["yuran"]), esc(y.get("nota", ""))] for y in kh.get("yuran", [])],
                   ["Kategori", "Yuran", "Nota"],
                   "Struktur yuran keahlian sedang disahkan. Sila rujuk urusetia MADOCS.")

    kelayakan = "".join("<li>%s</li>" % esc(x) for x in kh.get("kelayakan", [])) or \
        "<li>Butiran kelayakan sedang disahkan oleh jawatankuasa.</li>"
    dokumen = "".join("<li>%s</li>" % esc(x) for x in kh.get("dokumen", [])) or \
        "<li>Senarai dokumen sokongan akan disediakan oleh urusetia.</li>"
    proses = "".join('<div><time>Langkah %d</time><strong>%s</strong></div>' % (i + 1, esc(p))
                     for i, p in enumerate(kh.get("proses", [])))

    faq = "".join('<details><summary>%s</summary><div class="jawapan"><p>%s</p></div></details>' % (esc(f["s"]), esc(f["j"]))
                  for f in kh.get("faq", []))
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": f["s"],
                              "acceptedAnswer": {"@type": "Answer", "text": f["j"]}} for f in kh.get("faq", [])]}

    isi = page_hero([("Utama", "/"), ("Keahlian", None)], "Keahlian MADOCS",
                    "Sertai komuniti profesional doktor yang terlibat dalam amalan berkhatan di Malaysia.",
                    '<div class="hero-buttons"><a class="btn btn-primary" href="/keahlian/sertai/">SERTAI MADOCS</a>'
                    '<a class="btn btn-outline" href="#faq">SOALAN LAZIM</a></div>') + f"""
<section class="content-wrap">
  <div class="shell">
    {jika_belum}
    <div class="grid-2" style="align-items:start">
      <div class="card prose">
        <h2>Mengapa menyertai MADOCS</h2>
        <p>MADOCS menghimpunkan doktor yang serius dalam meningkatkan kualiti amalan berkhatan. Keahlian memberi akses kepada latihan klinikal berstruktur, rangkaian profesional dan sumber pendidikan.</p>
        <div class="grid-2" style="margin-top:20px;gap:12px">{manfaat}</div>
      </div>
      <div>
        <div class="card">
          <h2>Kategori &amp; kelayakan</h2>
          {kategori}
          <h3>Kelayakan asas</h3>
          <ul class="prose" style="padding-left:18px">{kelayakan}</ul>
        </div>
        <div class="card">
          <h2>Yuran keahlian</h2>
          {yuran}
        </div>
        <div class="card">
          <h2>Dokumen diperlukan</h2>
          <ul class="prose" style="padding-left:18px">{dokumen}</ul>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="content-wrap" style="padding-top:0">
  <div class="shell split lebar">
    <div>
      <div class="card">
        <h2>Proses permohonan</h2>
        <div class="timeline">{proses}</div>
        <div style="margin-top:24px"><a class="btn-hantar" href="/keahlian/sertai/">MULA PERMOHONAN {icon('arrow-right')}</a></div>
      </div>
      <div class="card" id="faq">
        <h2>Soalan lazim</h2>
        <div class="faq">{faq}</div>
      </div>
    </div>
  </div>
</section>

{cta_komuniti(label='SERTAI MADOCS SEKARANG')}"""
    halaman("keahlian", "Keahlian | MADOCS",
            "Keahlian MADOCS: manfaat, kelayakan, kategori, yuran dan proses permohonan untuk doktor yang terlibat dalam amalan berkhatan di Malaysia.",
            "/keahlian/", isi, jsonld=[ld_faq])


def bina_sertai():
    endpoint = (SITE.get("borang_endpoint") or "").strip()
    if not endpoint:
        kurang("Borang keahlian belum diaktifkan (site.json → borang_endpoint kosong). Buat masa ini pengguna diarahkan ke e-mel/WhatsApp urusetia (PRD §16).")

    pilihan_kategori = ['<option value="">Pilih kategori</option>'] + [
        '<option value="%s">%s</option>' % (esc(k["nama"]), esc(k["nama"])) for k in load("keahlian.json").get("kategori", [])]

    if endpoint:
        aksi = f'<form class="form" action="{esc(endpoint)}" method="POST">'
        hantar = f'<button class="btn-hantar" type="submit">HANTAR PERMOHONAN {icon("arrow-right")}</button>'
        nota = ('<div class="form-note">Maklumat anda dihantar kepada urusetia MADOCS untuk semakan. '
                'Sila pastikan butiran tepat. Data peribadi diproses menurut <a href="/dasar-privasi/">Dasar Privasi</a> kami.</div>')
    else:
        aksi = '<form class="form" method="get" action="/hubungi/">'
        hantar = ('<a class="btn-hantar" href="mailto:%s?subject=Permohonan%%20Keahlian%%20MADOCS">'
                  'E-MEL URUSETIA %s</a>' % (esc(SITE["email"]), icon("mail")))
        nota = ('<div class="form-note"><b>Borang dalam talian belum diaktifkan.</b> Buat masa ini, sila hantar '
                'permohonan melalui e-mel atau WhatsApp urusetia MADOCS: <a href="mailto:%s">%s</a> · '
                '<a href="tel:%s">%s</a>. Sediakan butiran di bawah untuk memudahkan urusan.</div>'
                % (esc(SITE["email"]), esc(SITE["email"]), esc(SITE["telefon"]), esc(SITE["telefon_papar"])))

    borang = f"""{aksi}
  <div class="form-grid">
    <div class="field"><label for="nama">Nama penuh (dengan gelaran) *</label><input id="nama" name="nama" required autocomplete="name"></div>
    <div class="field"><label for="email">E-mel *</label><input id="email" name="email" type="email" required autocomplete="email"></div>
    <div class="field"><label for="telefon">No. telefon / WhatsApp *</label><input id="telefon" name="telefon" required autocomplete="tel"></div>
    <div class="field"><label for="mmc">No. pendaftaran MMC</label><input id="mmc" name="mmc" placeholder="cth. 12345"></div>
    <div class="field"><label for="praktis">Tempat praktis / klinik</label><input id="praktis" name="praktis"></div>
    <div class="field"><label for="negeri">Negeri</label>
      <select id="negeri" name="negeri">
        <option value="">Pilih negeri</option>
        {''.join('<option>%s</option>' % n for n in ['Johor','Kedah','Kelantan','Melaka','Negeri Sembilan','Pahang','Perak','Perlis','Pulau Pinang','Sabah','Sarawak','Selangor','Terengganu','W.P. Kuala Lumpur','W.P. Labuan','W.P. Putrajaya'])}
      </select>
    </div>
    <div class="field"><label for="kategori">Kategori keahlian</label>
      <select id="kategori" name="kategori">{''.join(pilihan_kategori)}</select>
    </div>
    <div class="field penuh"><label for="pengalaman">Pengalaman berkaitan amalan berkhatan</label>
      <textarea id="pengalaman" name="pengalaman" placeholder="Ringkaskan pengalaman, latihan atau minat anda berkaitan amalan berkhatan."></textarea>
    </div>
    <div class="field penuh">
      <label class="pilihan"><input type="checkbox" name="persetujuan" required> Saya mengesahkan maklumat di atas benar dan bersetuju data peribadi saya diproses untuk tujuan keahlian MADOCS.</label>
    </div>
  </div>
  <div style="margin-top:22px">{hantar}</div>
  <p class="nota-isi" style="margin-top:14px">* Wajib diisi.</p>
</form>"""

    isi = page_hero([("Utama", "/"), ("Keahlian", "/keahlian/"), ("Permohonan", None)],
                    "Borang Permohonan Keahlian",
                    "Isi maklumat di bawah. Urusetia MADOCS akan menghubungi anda selepas semakan.") + f"""
<section class="content-wrap">
  <div class="shell split">
    <div>
      <div class="card">
        {nota}
        {borang}
      </div>
    </div>
    <aside class="side">
      <div class="card">
        <h3>Sebelum menghantar</h3>
        <ul class="prose" style="padding-left:18px;font-size:11px">
          <li>Sediakan nombor pendaftaran MMC dan butiran amalan anda.</li>
          <li>Pastikan e-mel dan nombor telefon aktif.</li>
          <li>Permohonan disemak oleh Jawatankuasa Keahlian.</li>
        </ul>
      </div>
      <div class="card">
        <h3>Soalan?</h3>
        <p style="font-size:11px;line-height:1.7;color:#3b4659">Urusetia MADOCS sedia membantu.</p>
        <a class="btn-blok ghost" href="/hubungi/" style="margin-top:14px">{icon('mail')} Hubungi urusetia</a>
      </div>
    </aside>
  </div>
</section>"""
    halaman("keahlian", "Borang Permohonan Keahlian | MADOCS",
            "Borang permohonan keahlian MADOCS untuk doktor yang terlibat dalam amalan berkhatan di Malaysia.",
            "/keahlian/sertai/", isi)


# ----------------------------------------------------------------- halaman: aktiviti
def bina_aktiviti():
    aktiviti = sorted(load("aktiviti.json")["aktiviti"], key=lambda a: a.get("tarikh") or "", reverse=True)
    senarai = ('<div class="listing">%s</div>' % "".join(
        item_kandungan(a["tajuk"], "/aktiviti/%s/" % a["slug"], a.get("ringkas", ""),
                       tarikh=a.get("tarikh"), kategori=a.get("kategori", ""), gambar=a.get("gambar"),
                       alt=a.get("gambar_alt", "")) for a in aktiviti)) if aktiviti else kosong(
        "users", "Belum ada aktiviti diterbitkan",
        "Laporan dan gambar aktiviti MADOCS akan diterbitkan di sini.")

    isi = page_hero([("Utama", "/"), ("Aktiviti", None)], "Aktiviti MADOCS",
                    "Program latihan, seminar, bengkel dan aktiviti komuniti MADOCS di seluruh Malaysia.",
                    '<div class="hero-buttons"><a class="btn btn-primary" href="/pendidikan/">PROGRAM AKAN DATANG</a>'
                    '<a class="btn btn-outline" href="/keahlian/sertai/">SERTAI MADOCS</a></div>') + f"""
<section class="content-wrap">
  <div class="shell">{senarai}</div>
</section>
{cta_komuniti(label='HUBUNGI URUSETIA', href='/hubungi/')}"""
    halaman("aktiviti", "Aktiviti | MADOCS",
            "Aktiviti dan program MADOCS: latihan klinikal, seminar, bengkel dan program komuniti di seluruh Malaysia.",
            "/aktiviti/", isi)


def bina_aktiviti_detail(a):
    d = parse_date(a.get("tarikh"))
    gambar = ('<img src="/%s" alt="%s" style="width:100%%;border-radius:11px;margin-bottom:22px">'
              % (esc(a["gambar"]), esc(a.get("gambar_alt") or a["tajuk"]))) if a.get("gambar") else ""
    if not a.get("ringkas"):
        kurang("Keterangan/laporan belum ditulis untuk aktiviti '%s' (PRD §24)." % a["tajuk"])
    ld = {"@context": "https://schema.org", "@type": "Event", "name": a["tajuk"],
          "startDate": a.get("tarikh", ""),
          "eventStatus": "https://schema.org/EventScheduled",
          "location": {"@type": "Place", "name": a.get("tempat", ""), "address": {"@type": "PostalAddress", "addressCountry": "MY"}},
          "organizer": {"@type": "Organization", "name": SITE["nama"], "url": BASE + "/"}}
    isi = page_hero([("Utama", "/"), ("Aktiviti", "/aktiviti/"), (a["tajuk"], None)], a["tajuk"],
                    a.get("ringkas") or tarikh_pdk(d)) + f"""
<section class="content-wrap">
  <div class="shell split">
    <div>
      <div class="card">
        <div class="chips" style="margin-bottom:16px"><span class="badge">{esc(a.get('kategori',''))}</span></div>
        {gambar}
        <div class="prose">
          {('<p>%s</p>' % esc(a['ringkas'])) if a.get('ringkas') else '<p class="nota-isi">Laporan penuh aktiviti ini belum disediakan.</p>'}
        </div>
      </div>
    </div>
    <aside class="side">
      <div class="card">
        <h3>Butiran</h3>
        <div class="item-meta" style="display:grid;gap:9px">
          <time datetime="{esc(a.get('tarikh',''))}">{icon('calendar-days')}{esc(tarikh_pjg(d))}</time>
          <span>{icon('map-pin')}{esc(a.get('tempat',''))}</span>
        </div>
        <a class="btn-blok ghost" href="/aktiviti/" style="margin-top:16px">{icon('arrow-left')} Semua aktiviti</a>
      </div>
      <div class="card">
        <h3>Ingin menyertai program seterusnya?</h3>
        <a class="btn-blok" href="/pendidikan/" style="margin-top:12px">Lihat kursus akan datang</a>
      </div>
    </aside>
  </div>
</section>"""
    halaman("aktiviti", "%s | Aktiviti MADOCS" % a["tajuk"],
            a.get("ringkas") or ("%s — %s, %s" % (a["tajuk"], a.get("tempat", ""), tarikh_pdk(d))),
            "/aktiviti/%s/" % a["slug"], isi, og_jenis="article", jsonld=[ld])


# ----------------------------------------------------------------- halaman: sumber
def bina_sumber():
    sumber = sorted(load("sumber.json")["sumber"], key=lambda s: s.get("tarikh") or "", reverse=True)
    if sumber:
        kad = "".join(
            '<article class="item">'
            '<div class="item-body"><span class="badge %s">%s</span>'
            '<h3>%s</h3><div class="item-meta"><time datetime="%s">%s %s</time><span>%s %s</span></div>'
            '<p>%s</p><a class="lebih" href="%s"%s>%s</a></div></article>'
            % ("member" if s.get("akses") == "ahli" else "", "Ahli sahaja" if s.get("akses") == "ahli" else "Awam",
               esc(s["tajuk"]), esc(s.get("tarikh", "")), icon("calendar-days"), esc(tarikh_pdk(parse_date(s.get("tarikh")))),
               icon("file-text"), esc(s.get("kategori", "")), esc(s.get("ringkas", "")),
               esc(s.get("fail", "#")), ' target="_blank" rel="noopener"' if s.get("fail", "").startswith("http") else "",
               "Muat turun" if s.get("fail") else "Baca")
            for s in sumber)
        senarai = '<div class="listing">%s</div>' % kad
    else:
        kurang("Pusat Sumber kosong (data/sumber.json) — PRD §19 dan §49.")
        senarai = kosong("book-open", "Pusat Sumber sedang disediakan",
                         "Bahan rujukan klinikal, garis panduan, bahan pendidikan dan pautan luaran akan diterbitkan di sini selepas semakan klinikal oleh penyemak bertauliah (PRD §21).",
                         '<div style="margin-top:20px"><a class="btn btn-primary" href="/hubungi/">Hantar bahan untuk semakan</a></div>')

    isi = page_hero([("Utama", "/"), ("Sumber", None)], "Pusat Sumber",
                    "Bahan rujukan klinikal, garis panduan dan bahan pendidikan untuk doktor yang terlibat dalam amalan berkhatan.") + f"""
<section class="content-wrap">
  <div class="shell">
    <div class="form-note"><b>Nota klinikal:</b> bahan di Pusat Sumber MADOCS adalah untuk tujuan pendidikan profesional dan tidak menggantikan penilaian klinikal individu. Setiap bahan klinikal akan disemak oleh penyemak bertauliah sebelum diterbitkan (PRD §21).</div>
    {senarai}
  </div>
</section>"""
    halaman("sumber", "Pusat Sumber | MADOCS",
            "Pusat Sumber MADOCS: rujukan klinikal, garis panduan dan bahan pendidikan untuk doktor dalam amalan berkhatan.",
            "/sumber/", isi)


# ----------------------------------------------------------------- halaman: berita
def bina_berita():
    berita = sorted(load("berita.json")["berita"], key=lambda b: b.get("tarikh") or "", reverse=True)
    if berita:
        senarai = '<div class="listing">%s</div>' % "".join(
            item_kandungan(b["tajuk"], "/berita/%s/" % b["slug"], b.get("ringkas", ""),
                           tarikh=b.get("tarikh"), kategori=b.get("kategori", ""), gambar=b.get("gambar"))
            for b in berita)
    else:
        kurang("Tiada berita diterbitkan (data/berita.json) — PRD §49.")
        senarai = kosong("file-text", "Belum ada berita diterbitkan",
                         "Pengumuman, berita latihan dan kemas kini profesional MADOCS akan diterbitkan di sini.",
                         '<div style="margin-top:20px"><a class="btn btn-primary" href="/hubungi/">Hubungi urusetia</a></div>')

    isi = page_hero([("Utama", "/"), ("Berita", None)], "Berita & Pengumuman",
                    "Berita terkini, pengumuman dan kemas kini profesional daripada MADOCS.") + f"""
<section class="content-wrap"><div class="shell">{senarai}</div></section>"""
    halaman("berita", "Berita & Pengumuman | MADOCS",
            "Berita, pengumuman dan kemas kini profesional daripada Pertubuhan Doktor Khatan Malaysia (MADOCS).",
            "/berita/", isi)


def bina_berita_detail(b):
    d = parse_date(b.get("tarikh"))
    gambar = ('<img src="/%s" alt="%s" style="width:100%%;border-radius:11px;margin-bottom:22px">'
              % (esc(b["gambar"]), esc(b.get("gambar_alt") or b["tajuk"]))) if b.get("gambar") else ""
    kandungan = "".join("<p>%s</p>" % esc(p) for p in b.get("kandungan", []))
    if not b.get("kandungan"):
        kurang("Kandungan penuh belum diisi untuk berita '%s' (PRD §23)." % b["tajuk"])
        kandungan = '<p class="nota-isi">Kandungan penuh artikel ini belum disediakan.</p>'
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": b["tajuk"],
          "datePublished": b.get("tarikh", ""), "description": b.get("ringkas", ""),
          "author": {"@type": "Organization", "name": b.get("penulis") or SITE["nama"]},
          "publisher": {"@type": "Organization", "name": SITE["nama"], "logo": {"@type": "ImageObject", "url": BASE + "/assets/logo-128.webp"}},
          "mainEntityOfPage": BASE + "/berita/" + b["slug"] + "/"}
    isi = page_hero([("Utama", "/"), ("Berita", "/berita/"), (b["tajuk"], None)], b["tajuk"],
                    tarikh_pdk(d)) + f"""
<section class="content-wrap">
  <div class="shell split">
    <div class="card">
      {gambar}
      <div class="prose">{kandungan}</div>
    </div>
    <aside class="side">
      <div class="card">
        <h3>Butiran</h3>
        <div class="item-meta" style="display:grid;gap:9px">
          <time datetime="{esc(b.get('tarikh',''))}">{icon('calendar-days')}{esc(tarikh_pjg(d))}</time>
          <span>{icon('file-text')}{esc(b.get('kategori',''))}</span>
          <span>{icon('users')}{esc(b.get('penulis') or 'Urusetia MADOCS')}</span>
        </div>
        <a class="btn-blok ghost" href="/berita/" style="margin-top:16px">{icon('arrow-left')} Semua berita</a>
      </div>
    </aside>
  </div>
</section>"""
    halaman("berita", "%s | Berita MADOCS" % b["tajuk"],
            b.get("ringkas", "")[:180], "/berita/%s/" % b["slug"], isi, og_jenis="article", jsonld=[ld])


# ----------------------------------------------------------------- halaman: hubungi
def bina_hubungi():
    endpoint = (SITE.get("borang_endpoint") or "").strip()
    if endpoint:
        buka = '<form class="form" action="%s" method="POST">' % esc(endpoint)
        hantar = '<button class="btn-hantar" type="submit">HANTAR MESEJ %s</button>' % icon("arrow-right")
    else:
        kurang("Borang hubungi belum diaktifkan (site.json → borang_endpoint kosong).")
        buka = '<form class="form" method="get" action="/hubungi/">'
        hantar = ('<a class="btn-hantar" href="mailto:%s?subject=Pertanyaan%%20laman%%20MADOCS">E-MEL URUSETIA %s</a>'
                  % (esc(SITE["email"]), icon("mail")))

    isi = page_hero([("Utama", "/"), ("Hubungi", None)], "Hubungi MADOCS",
                    "Hubungi urusetia MADOCS untuk pertanyaan tentang keahlian, latihan, kerjasama atau sebarang maklumat.") + f"""
<section class="content-wrap">
  <div class="shell split">
    <div>
      <div class="card">
        <h2>Hantar pertanyaan</h2>
        {'<div class="form-note"><b>Borang dalam talian belum diaktifkan.</b> Sila hubungi urusetia melalui e-mel atau telefon di sebelah. Butiran di bawah boleh anda salin ke dalam e-mel.</div>' if not endpoint else ''}
        {buka}
          <div class="form-grid">
            <div class="field"><label for="hnama">Nama *</label><input id="hnama" name="nama" required autocomplete="name"></div>
            <div class="field"><label for="hemail">E-mel *</label><input id="hemail" name="email" type="email" required autocomplete="email"></div>
            <div class="field"><label for="htelefon">No. telefon</label><input id="htelefon" name="telefon" autocomplete="tel"></div>
            <div class="field"><label for="htopik">Topik</label>
              <select id="htopik" name="topik">
                <option>Keahlian</option><option>Latihan / kursus</option><option>Pendaftaran kursus</option>
                <option>Sumber klinikal</option><option>Kerjasama / tajaan</option><option>Lain-lain</option>
              </select>
            </div>
            <div class="field penuh"><label for="hmesej">Mesej *</label><textarea id="hmesej" name="mesej" required></textarea></div>
          </div>
          <div style="margin-top:22px">{hantar}</div>
        </form>
      </div>
    </div>
    <aside class="side">
      <div class="card">
        <h3>Urusetia MADOCS</h3>
        <div class="item-meta" style="display:grid;gap:10px">
          <a href="mailto:{esc(SITE['email'])}">{icon('mail')}{esc(SITE['email'])}</a>
          <a href="tel:{esc(SITE['telefon'])}">{icon('phone')}{esc(SITE['telefon_papar'])}</a>
          <span>{icon('map-pin')}{esc(SITE['alamat'])}</span>
          <span>{icon('shield-check')}{esc(SITE['pendaftaran'])}</span>
        </div>
      </div>
      <div class="card">
        <h3>Keahlian</h3>
        <p style="font-size:11px;line-height:1.7;color:#3b4659">Ingin menyertai MADOCS? Mulakan dengan borang permohonan keahlian.</p>
        <a class="btn-blok" href="/keahlian/sertai/" style="margin-top:14px">Borang keahlian {icon('arrow-right')}</a>
      </div>
    </aside>
  </div>
</section>"""
    halaman("hubungi", "Hubungi MADOCS",
            "Hubungi urusetia MADOCS: e-mel, telefon dan borang pertanyaan untuk keahlian, latihan dan kerjasama.",
            "/hubungi/", isi)


# ----------------------------------------------------------------- halaman: carian
def bina_carian():
    isi = page_hero([("Utama", "/"), ("Carian", None)], "Carian",
                    "Cari kursus, aktiviti, berita, sumber dan halaman MADOCS.") + """
<section class="content-wrap">
  <div class="shell">
    <div class="search-bar">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-search" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
      <input type="search" id="medan-carian" placeholder="Taip kata kunci…" aria-label="Kata kunci carian" autofocus>
    </div>
    <p class="hasil" id="hasil-info" aria-live="polite"></p>
    <div class="listing" id="hasil-senarai"></div>
  </div>
</section>"""
    halaman("", "Carian | MADOCS", "Cari kandungan laman MADOCS: kursus, aktiviti, berita dan sumber.",
            "/carian/", isi)

    indeks = []
    for k in load("kursus.json")["kursus"]:
        indeks.append({"t": k["tajuk"], "u": "/pendidikan/%s/" % k["slug"], "r": k.get("ringkas", ""), "j": "Kursus"})
    for a in load("aktiviti.json")["aktiviti"]:
        indeks.append({"t": a["tajuk"], "u": "/aktiviti/%s/" % a["slug"], "r": a.get("ringkas", ""), "j": "Aktiviti"})
    for b in load("berita.json")["berita"]:
        indeks.append({"t": b["tajuk"], "u": "/berita/%s/" % b["slug"], "r": b.get("ringkas", ""), "j": "Berita"})
    for s in load("sumber.json")["sumber"]:
        indeks.append({"t": s["tajuk"], "u": "/sumber/%s/" % s["slug"], "r": s.get("ringkas", ""), "j": "Sumber"})
    indeks += [
        {"t": "Tentang MADOCS", "u": "/tentang/", "r": "Latar belakang, visi, misi dan jawatankuasa eksekutif.", "j": "Halaman"},
        {"t": "Pendidikan & Latihan", "u": "/pendidikan/", "r": "Program latihan klinikal berstruktur MADOCS.", "j": "Halaman"},
        {"t": "Keahlian MADOCS", "u": "/keahlian/", "r": "Manfaat, kelayakan, kategori dan yuran keahlian.", "j": "Halaman"},
        {"t": "Borang permohonan keahlian", "u": "/keahlian/sertai/", "r": "Mohon menjadi ahli MADOCS.", "j": "Halaman"},
        {"t": "Aktiviti MADOCS", "u": "/aktiviti/", "r": "Program dan aktiviti yang telah dijalankan.", "j": "Halaman"},
        {"t": "Pusat Sumber", "u": "/sumber/", "r": "Rujukan klinikal dan bahan pendidikan.", "j": "Halaman"},
        {"t": "Hubungi MADOCS", "u": "/hubungi/", "r": "E-mel, telefon dan borang pertanyaan urusetia.", "j": "Halaman"},
    ]
    (ROOT / "carian").mkdir(exist_ok=True)
    (ROOT / "carian" / "index.json").write_text(json.dumps(indeks, ensure_ascii=False, indent=0), encoding="utf-8")


# ----------------------------------------------------------------- fail statik
def bina_fail_statik():
    # CSS gabungan
    (ROOT / "styles.css").write_text(
        (_src_css("base.css") + "\n" + _src_css("extra.css")), encoding="utf-8")

    # CSS tambahan kecil untuk carian
    with open(ROOT / "styles.css", "a", encoding="utf-8") as f:
        f.write("\n.ikon-ganti{display:inline-block;width:1em;height:1em}\n")

    # robots + sitemap + CNAME
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE, encoding="utf-8")
    peta = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in sorted(set(PAGES)):
        keutamaan = "1.0" if p == "/" else ("0.8" if p.count("/") <= 2 else "0.6")
        peta.append("  <url><loc>%s%s</loc><priority>%s</priority></url>" % (BASE, p, keutamaan))
    peta.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(peta) + "\n", encoding="utf-8")
    (ROOT / "CNAME").write_text("madocs.drsuhailsatri.com\n", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")


def _src_css(name):
    return (ROOT / "_src" / name).read_text(encoding="utf-8")


def bina_404():
    isi = page_hero([("Utama", "/"), ("Halaman tidak dijumpai", None)], "404 — Halaman tidak dijumpai",
                    "Maaf, halaman yang anda cari tidak wujud atau telah berpindah.") + """
<section class="content-wrap">
  <div class="shell split lebar">
    <div class="kosong">
      <span class="ikon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-search" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg></span>
      <h3>Halaman tidak dijumpai</h3>
      <p>Semak pautan anda, atau gunakan carian dan navigasi di bawah untuk mencari kandungan yang anda perlukan.</p>
      <div style="margin-top:22px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
        <a class="btn btn-primary" href="/">Ke laman utama</a>
        <a class="btn btn-outline" href="/carian/">Cari kandungan</a>
        <a class="btn btn-outline" href="/hubungi/">Hubungi kami</a>
      </div>
    </div>
  </div>
</section>"""
    halaman("", "404 — Halaman tidak dijumpai | MADOCS",
            "Halaman yang anda cari tidak dijumpai.", "/404.html", isi, masuk_sitemap=False)


def bina_dasar():
    laman_ringkas("dasar-privasi", "Dasar Privasi", f"""
<p>{esc(SITE['nama'])} ({esc(SITE['singkatan'])}) mengumpul maklumat peribadi yang dihantar secara sukarela melalui laman ini, contohnya melalui borang permohonan keahlian, pendaftaran kursus atau borang pertanyaan.</p>
<h2>Maklumat yang dikumpul</h2>
<ul><li>Maklumat hubungan (nama, e-mel, nombor telefon).</li><li>Maklumat profesional (nombor pendaftaran MMC, tempat praktis, negeri).</li><li>Maklumat yang anda taip dalam mesej atau permohonan.</li></ul>
<h2>Kegunaan maklumat</h2>
<p>Maklumat digunakan semata-mata untuk memproses keahlian, pendaftaran program latihan, pertanyaan dan komunikasi berkaitan aktiviti MADOCS.</p>
<h2>Perkongsian</h2>
<p>Maklumat peribadi tidak dijual atau dikongsi dengan pihak ketiga untuk tujuan pemasaran. Nama ahli dan maklumat peribadi tidak diterbitkan di laman awam.</p>
<h2>Penyimpanan</h2>
<p>Maklumat disimpan setakat yang diperlukan untuk tujuan di atas dan dilindungi mengikut amalan pentadbiran yang munasabah.</p>
<h2>Hubungi kami</h2>
<p>Untuk permintaan akses, pembetulan atau penghapusan data, hubungi <a href="mailto:{esc(SITE['email'])}">{esc(SITE['email'])}</a>.</p>
<p class="nota-isi">Dokumen ini draf untuk semakan jawatankuasa dan akan dikemas kini mengikut keperluan perundangan yang berkuat kuasa, termasuk Akta Perlindungan Data Peribadi 2010 (pindaan 2024).</p>
""")
    laman_ringkas("terma", "Terma Penggunaan", f"""
<p>Dengan menggunakan laman ini, anda bersetuju dengan terma berikut.</p>
<h2>Kandungan</h2>
<p>Kandungan laman ini adalah untuk tujuan maklumat dan pendidikan profesional. Ia tidak menggantikan penilaian, nasihat atau keputusan klinikal individu oleh pengamal yang bertauliah.</p>
<h2>Ketepatan maklumat</h2>
<p>MADOCS berusaha memastikan maklumat di laman ini tepat dan terkini. Maklumat seperti jadual latihan, yuran dan keahlian boleh berubah dan akan dikemas kini dari semasa ke semasa.</p>
<h2>Hak cipta</h2>
<p>Nama, logo dan kandungan MADOCS tidak boleh digunakan semula untuk tujuan komersial tanpa kebenaran bertulis.</p>
<h2>Pautan luar</h2>
<p>Pautan ke laman pihak ketiga disediakan untuk kemudahan. MADOCS tidak bertanggungjawab ke atas kandungan laman tersebut.</p>
""")


# ----------------------------------------------------------------- utama
def main():
    bina_fail_statik()
    bina_utama()
    bina_tentang()
    bina_pendidikan()
    for k in load("kursus.json")["kursus"]:
        bina_kursus_detail(k)
    bina_keahlian()
    bina_sertai()
    bina_aktiviti()
    for a in load("aktiviti.json")["aktiviti"]:
        bina_aktiviti_detail(a)
    bina_sumber()
    bina_berita()
    for b in load("berita.json")["berita"]:
        bina_berita_detail(b)
    bina_hubungi()
    bina_carian()
    bina_dasar()
    bina_404()

    if "--report" in sys.argv:
        print("\n=== KANDUNGAN YANG MASIH DIPERLUKAN (%d) ===" % len(KURANG))
        for i, k in enumerate(sorted(set(KURANG)), 1):
            print("%2d. %s" % (i, k))
    print("\nSelesai: %d halaman dibina." % len(PAGES))


if __name__ == "__main__":
    main()
