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
})();
