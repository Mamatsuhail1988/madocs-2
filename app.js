/* MADOCS 2.0 — skrip laman */
(function () {
  "use strict";

  /* ---- bahasa: halaman Inggeris berada di bawah /en/ ---- */
  var EN = document.documentElement.lang === "en";
  var JEJAK_CARIAN = EN ? "/en/search" : "/carian";
  var TEKS = EN ? {
    minimum: "Type at least 2 characters to start searching.",
    hasil: "results found for",
    tiada: "No results",
    cuba: "Try another keyword, or contact the MADOCS secretariat for help.",
    buka: "Open",
    gagal: "The search index could not be loaded."
  } : {
    minimum: "Taip sekurang-kurangnya 2 aksara untuk mula mencari.",
    hasil: "hasil dijumpai untuk",
    tiada: "Tiada hasil",
    cuba: "Cuba kata kunci lain, atau hubungi urusetia MADOCS untuk bantuan.",
    buka: "Buka",
    gagal: "Indeks carian tidak dapat dimuatkan."
  };

  /* ---- menu mudah alih ---- */
  var butangMenu = document.querySelector(".menu-toggle");
  var menu = document.getElementById("menu-mudah");
  if (butangMenu && menu) {
    butangMenu.addEventListener("click", function () {
      var buka = menu.hasAttribute("hidden");
      if (buka) { menu.removeAttribute("hidden"); } else { menu.setAttribute("hidden", ""); }
      butangMenu.setAttribute("aria-expanded", buka ? "true" : "false");
    });
  }

  /* ---- anak panah carousel aktiviti ---- */
  var grid = document.querySelector(".activity-grid");
  var anak = document.querySelectorAll(".carousel-arrow");
  if (grid && anak.length) {
    var bolehSkrol = grid.scrollWidth > grid.clientWidth + 4;
    grid.style.overflowX = "auto";
    grid.style.scrollSnapType = "x mandatory";
    Array.prototype.forEach.call(grid.children, function (c) { c.style.scrollSnapAlign = "start"; });
    if (!bolehSkrol) {
      Array.prototype.forEach.call(anak, function (b) { b.style.display = "none"; });
    } else {
      anak.forEach(function (b) {
        b.addEventListener("click", function () {
          var arah = b.classList.contains("left") ? -1 : 1;
          grid.scrollBy({ left: arah * grid.clientWidth * 0.8, behavior: "smooth" });
        });
      });
    }
  }

  /* ---- carian pantas di laman utama ---- */
  var pantas = document.getElementById("carian-pantas");
  var butang = document.getElementById("butang-carian");
  function pergiCarian() {
    if (!pantas || !pantas.value.trim()) { return; }
    window.location.href = JEJAK_CARIAN + "/?q=" + encodeURIComponent(pantas.value.trim());
  }
  if (pantas) {
    pantas.addEventListener("keydown", function (e) { if (e.key === "Enter") { pergiCarian(); } });
  }
  if (butang && pantas) {
    butang.addEventListener("click", function (e) { e.preventDefault(); pergiCarian(); });
  }

  /* ---- halaman carian ---- */
  var medan = document.getElementById("medan-carian");
  if (medan) {
    var info = document.getElementById("hasil-info");
    var senarai = document.getElementById("hasil-senarai");
    var indeks = null;

    function sorot(teks, kata) {
      if (!kata || !teks) { return teks || ""; }
      var i = teks.toLowerCase().indexOf(kata.toLowerCase());
      if (i < 0) { return teks; }
      return teks.slice(0, i) + "<mark>" + teks.slice(i, i + kata.length) + "</mark>" + teks.slice(i + kata.length);
    }

    function papar(kata) {
      var hasil = [];
      if (kata.length >= 2 && indeks) {
        var k = kata.toLowerCase();
        hasil = indeks.filter(function (it) {
          return (it.t + " " + (it.r || "") + " " + (it.j || "")).toLowerCase().indexOf(k) >= 0;
        });
      }
      if (kata.length < 2) {
        info.textContent = TEKS.minimum;
        senarai.innerHTML = "";
        return;
      }
      info.textContent = hasil.length + " " + TEKS.hasil + " \"" + kata + "\".";
      if (!hasil.length) {
        senarai.innerHTML = '<div class="kosong"><h3>' + TEKS.tiada + '</h3><p>' + TEKS.cuba + '</p></div>';
        return;
      }
      senarai.innerHTML = hasil.map(function (it) {
        return '<article class="item no-photo"><div class="item-body">' +
          '<span class="badge">' + it.j + "</span>" +
          '<h3><a href="' + it.u + '">' + sorot(it.t, kata) + "</a></h3>" +
          '<p>' + sorot(it.r || "", kata) + "</p>" +
          '<a class="lebih" href="' + it.u + '">' + TEKS.buka + "</a></div></article>";
      }).join("");
    }

    var q = new URLSearchParams(window.location.search).get("q") || "";
    fetch(JEJAK_CARIAN + "/index.json")
      .then(function (r) { return r.json(); })
      .then(function (j) { indeks = j; if (q) { medan.value = q; papar(q); } else { papar(""); } })
      .catch(function () { info.textContent = TEKS.gagal; });

    medan.addEventListener("input", function () { papar(medan.value.trim()); });
  }

  /* ---- pengepala mengecil selepas skrol ---- */
  var pengepala = document.querySelector(".header");
  if (pengepala) {
    var tandaKompak = function () {
      if (window.scrollY > 40) { pengepala.classList.add("kompak"); }
      else { pengepala.classList.remove("kompak"); }
    };
    tandaKompak();
    window.addEventListener("scroll", tandaKompak, { passive: true });
  }

  /* ---- kemunculan lembut semasa skrol ----
     Kelas .mula ditambah oleh JS sahaja: jika JS gagal atau pengguna minta kurang
     gerakan, kandungan kekal kelihatan (tiada risiko halaman kosong). */
  var kurangGerak = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!kurangGerak && "IntersectionObserver" in window) {
    var blok = document.querySelectorAll(
      ".section-pad > .shell > *, .page-hero > .shell > *, .course-feature, .activity-card, .item, .card, .content-wrap > .shell > *");
    if (blok.length) {
      var pemerhati = new IntersectionObserver(function (masuk) {
        masuk.forEach(function (satu) {
          if (!satu.isIntersecting) { return; }
          satu.target.classList.add("muncul");
          pemerhati.unobserve(satu.target);
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      Array.prototype.forEach.call(blok, function (el, i) {
        el.classList.add("mula");
        el.style.transitionDelay = (Math.min(i % 4, 3) * 45) + "ms";
        pemerhati.observe(el);
      });
    }
  }
})();

/* ---- MADOCS 2.0: lightbox galeri ----
   Thumbnail galeri ialah <button> supaya boleh dicapai papan kekunci. Klik atau Enter
   membuka lapisan penuh; Esc menutup, anak panah kiri/kanan menukar gambar. */
(function () {
  "use strict";
  var EN = document.documentElement.lang === "en";
  var TEKS = EN ? { tutup: "Close", sebelum: "Previous photo", selepas: "Next photo" }
                : { tutup: "Tutup", sebelum: "Gambar sebelum", selepas: "Gambar seterusnya" };
  var senarai = Array.prototype.slice.call(document.querySelectorAll(".galeri .gambar"));
  if (!senarai.length) { return; }

  var kotak = document.createElement("div");
  kotak.className = "lightbox";
  kotak.setAttribute("role", "dialog");
  kotak.setAttribute("aria-modal", "true");
  kotak.hidden = true;
  kotak.innerHTML =
    '<button class="lb-tutup" type="button" aria-label="' + TEKS.tutup + '">\u00d7</button>' +
    '<button class="lb-sebelum" type="button" aria-label="' + TEKS.sebelum + '">\u2039</button>' +
    '<img alt="">' +
    '<p class="lb-kapsyen"></p>' +
    '<button class="lb-selepas" type="button" aria-label="' + TEKS.selepas + '">\u203a</button>';
  document.body.appendChild(kotak);

  var imej = kotak.querySelector("img");
  var kapsyen = kotak.querySelector(".lb-kapsyen");
  var indeks = 0;
  var fokus_asal = null;
  var adaSebelum = senarai.length > 1;
  kotak.querySelector(".lb-sebelum").hidden = !adaSebelum;
  kotak.querySelector(".lb-selepas").hidden = !adaSebelum;

  function tunjuk(i) {
    indeks = (i + senarai.length) % senarai.length;
    var butang = senarai[indeks];
    imej.src = butang.getAttribute("data-besar");
    imej.alt = butang.getAttribute("data-kapsyen") || "";
    kapsyen.textContent = butang.getAttribute("data-kapsyen") || "";
  }

  function buka(i) {
    fokus_asal = document.activeElement;
    tunjuk(i);
    kotak.hidden = false;
    document.body.style.overflow = "hidden";
    kotak.querySelector(".lb-tutup").focus();
  }

  function tutup() {
    kotak.hidden = true;
    imej.src = "";
    document.body.style.overflow = "";
    if (fokus_asal && fokus_asal.focus) { fokus_asal.focus(); }
  }

  senarai.forEach(function (butang, i) {
    butang.addEventListener("click", function () { buka(i); });
  });
  kotak.querySelector(".lb-tutup").addEventListener("click", tutup);
  kotak.querySelector(".lb-sebelum").addEventListener("click", function () { tunjuk(indeks - 1); });
  kotak.querySelector(".lb-selepas").addEventListener("click", function () { tunjuk(indeks + 1); });
  kotak.addEventListener("click", function (e) { if (e.target === kotak) { tutup(); } });
  document.addEventListener("keydown", function (e) {
    if (kotak.hidden) { return; }
    if (e.key === "Escape") { tutup(); }
    else if (e.key === "ArrowLeft") { tunjuk(indeks - 1); }
    else if (e.key === "ArrowRight") { tunjuk(indeks + 1); }
  });
})();
