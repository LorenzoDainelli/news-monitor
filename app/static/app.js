// JS dell'app — interazioni del design freeze v1.0.
// 1) Conferma di eliminazione INLINE (come nel prototipo: Conferma/Annulla al
//    posto del bottone, reversibile). Testi tradotti via data-confirm/data-cancel;
//    se mancano si torna al window.confirm classico (data-msg).
document.addEventListener('submit', function (e) {
  var f = e.target;
  if (!(f.classList && f.classList.contains('js-confirm'))) return;
  if (f.dataset.confirmed === '1') return;
  if (!f.dataset.confirm) {                       // fallback: dialog nativo
    if (!window.confirm(f.dataset.msg || 'OK?')) e.preventDefault();
    return;
  }
  e.preventDefault();
  if (f.dataset.armed === '1') return;
  f.dataset.armed = '1';
  var btn = f.querySelector('[type=submit]');
  if (btn) btn.style.display = 'none';
  var wrap = document.createElement('span');
  wrap.style.cssText = 'display:inline-flex;gap:6px;white-space:nowrap;';
  var ok = document.createElement('button');
  ok.type = 'button'; ok.className = 'btn sm danger'; ok.textContent = f.dataset.confirm;
  var no = document.createElement('button');
  no.type = 'button'; no.className = 'btn sm ghost'; no.textContent = f.dataset.cancel || '✕';
  ok.addEventListener('click', function () { f.dataset.confirmed = '1'; f.submit(); });
  no.addEventListener('click', function () { wrap.remove(); if (btn) btn.style.display = ''; f.dataset.armed = ''; });
  wrap.appendChild(ok); wrap.appendChild(no);
  f.appendChild(wrap);
});

// 2) Count-up dell'hero (dashboard): [data-countup] con il valore finale.
//    Con animazioni spente (o reduced-motion) il numero appare subito.
(function () {
  var els = document.querySelectorAll('[data-countup]');
  if (!els.length) return;
  var lang = document.documentElement.lang || 'it';
  var still = document.documentElement.dataset.anim === 'spente' ||
    (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  els.forEach(function (el) {
    var end = parseFloat(el.dataset.countup);
    if (isNaN(end)) return;
    var fmt = function (v) {
      return '€ ' + v.toLocaleString(lang, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    };
    if (still) { el.textContent = fmt(end); return; }
    var t0 = null, dur = 900;
    function step(ts) {
      if (!t0) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur);
      var eased = 1 - Math.pow(1 - p, 3);        // ease-out cubico
      el.textContent = fmt(end * eased);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
})();

// 3) Toggle di un blocco (es. form inline "Aggiungi posizione"):
//    <button data-toggle="#id" data-alt="Chiudi">Aggiungi</button>
document.addEventListener('click', function (e) {
  var b = e.target.closest('[data-toggle]');
  if (!b) return;
  var el = document.querySelector(b.dataset.toggle);
  if (!el) return;
  var open = el.style.display !== 'none';
  el.style.display = open ? 'none' : '';
  if (b.dataset.alt) {
    var cur = b.dataset.alt;
    b.dataset.alt = b.textContent.trim();
    b.textContent = cur;
  }
  if (!open) {
    var first = el.querySelector('input, select, textarea');
    if (first) first.focus();
  }
});

// 4) PAC: al variare dell'importo le quote si ricalcolano LIVE (come nel
//    prototipo). Le righe portano data-target (percentuale); il totale è
//    quote + importi fissi (data-fixed sul campo).
(function () {
  var inp = document.getElementById('pac-importo');
  if (!inp) return;
  var lang = document.documentElement.lang || 'it';
  var eur = function (v) {
    return '€ ' + v.toLocaleString(lang, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  };
  function ricalcola() {
    var raw = (inp.value || '').replace(/\./g, '').replace(',', '.');
    var imp = parseFloat(raw);
    if (isNaN(imp) || imp < 0) return;
    var somma = 0;
    document.querySelectorAll('[data-target]').forEach(function (cell) {
      var q = Math.round(imp * parseFloat(cell.dataset.target)) / 100;
      somma += q;
      cell.textContent = eur(q);
    });
    var fissi = parseFloat(inp.dataset.fixed || '0') || 0;
    var tot = document.getElementById('pac-totale');
    if (tot) tot.textContent = eur(somma + fissi);
  }
  inp.addEventListener('input', ricalcola);
})();

// 5) Drawer del dettaglio posizione (PositionDetail del freeze): i link con
//    data-drawer aprono il dettaglio in un pannello che scivola da destra
//    (backdrop sfocato, ESC/X/click fuori per chiudere). Senza JS o in caso
//    di errore si naviga normalmente alla pagina.
(function () {
  var reduce = function () { return document.documentElement.dataset.anim === 'spente'; };
  var root = null, aside = null, backdrop = null, prevOverflow = '';

  function onKey(e) { if (e.key === 'Escape') close(); }

  function close() {
    if (!root) return;
    var r = root, a = aside, b = backdrop;
    root = null;
    document.removeEventListener('keydown', onKey);
    document.body.style.overflow = prevOverflow;
    if (reduce()) { r.remove(); return; }
    b.style.opacity = '0';
    a.style.transform = 'translateX(102%)';
    setTimeout(function () { r.remove(); }, 260);
  }

  function open(url) {
    if (root) return;
    root = document.createElement('div');
    root.style.cssText = 'position:fixed;inset:0;z-index:60;';
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    backdrop = document.createElement('div');
    backdrop.style.cssText = 'position:absolute;inset:0;background:rgba(20,26,12,.38);backdrop-filter:blur(2px);-webkit-backdrop-filter:blur(2px);opacity:0;' +
      (reduce() ? '' : 'transition:opacity var(--dur-base) var(--ease-out);');
    backdrop.addEventListener('click', close);
    aside = document.createElement('aside');
    aside.style.cssText = 'position:absolute;top:0;right:0;height:100%;width:min(560px,94vw);background:var(--surface);border-left:1px solid var(--border);box-shadow:var(--shadow-lg);overflow-y:auto;transform:translateX(102%);' +
      (reduce() ? '' : 'transition:transform var(--dur-slow) var(--ease-out);');
    aside.innerHTML = '<div class="faint" style="padding:24px;">…</div>';
    root.appendChild(backdrop);
    root.appendChild(aside);
    document.body.appendChild(root);
    prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey);
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      backdrop.style.opacity = '1';
      aside.style.transform = 'translateX(0)';
    }); });
    fetch(url + (url.indexOf('?') >= 0 ? '&' : '?') + 'panel=1')
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (h) { if (root) aside.innerHTML = h; })
      .catch(function () { window.location.href = url; });
  }

  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-drawer-close]')) { close(); return; }
    var a = e.target.closest('a[data-drawer]');
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    open(a.getAttribute('href'));
  });
})();

// 6) Form movimento: "A (portafoglio)" compare solo per i trasferimenti; il
//    blocco della partita di giro (da chi + gamba del rimborso) solo per i
//    giri, e la casella "il rimborso arriverà dopo" nasconde la gamba.
document.addEventListener('change', function (e) {
  if (e.target && e.target.id === 'mov-tipo') {
    var box = document.getElementById('mov-wallet-to');
    if (box) box.style.display = e.target.value === 'trasferimento' ? '' : 'none';
    var giro = document.getElementById('mov-giro');
    if (giro) giro.style.display = e.target.value === 'giro' ? '' : 'none';
  }
  if (e.target && e.target.id === 'mov-giro-dopo') {
    var ric = document.getElementById('mov-giro-ricevuto');
    if (ric) ric.style.display = e.target.checked ? 'none' : '';
  }
});

// 7) Ordinamento tabelle: click su un'intestazione .sortable inverte/imposta
//    l'ordine della colonna (asc/desc). Il valore di confronto è data-s sul
//    <td> (numeri/ISO-date) o, in mancanza, il testo della cella; le celle
//    vuote ('' o '—') finiscono SEMPRE in fondo. Il tfoot non si tocca.
document.addEventListener('click', function (e) {
  var th = e.target.closest('th.sortable');
  if (!th) return;
  var table = th.closest('table');
  if (!table || !table.tBodies.length) return;
  var tbody = table.tBodies[0];
  var ths = Array.prototype.slice.call(th.parentNode.children);
  var idx = ths.indexOf(th);
  var dir = th.classList.contains('asc') ? 'desc' : 'asc';
  ths.forEach(function (h) { h.classList.remove('asc', 'desc'); });
  th.classList.add(dir);
  var num = th.dataset.type === 'num';
  function key(row) {
    var td = row.cells[idx];
    if (!td) return null;
    var v = (td.dataset.s !== undefined ? td.dataset.s : td.textContent).trim();
    if (v === '' || v === '—') return null;
    if (num) {
      var f = parseFloat(v.replace(',', '.'));
      return isNaN(f) ? null : f;
    }
    return v.toLowerCase();
  }
  var rows = Array.prototype.slice.call(tbody.rows)
    .filter(function (r) { return r.cells.length > 1; });
  rows.map(function (r, i) { return { r: r, k: key(r), i: i }; })
    .sort(function (a, b) {
      if (a.k === null && b.k === null) return a.i - b.i;
      if (a.k === null) return 1;
      if (b.k === null) return -1;
      if (a.k < b.k) return dir === 'asc' ? -1 : 1;
      if (a.k > b.k) return dir === 'asc' ? 1 : -1;
      return a.i - b.i;                              // stabile a parità di valore
    })
    .forEach(function (x) { tbody.appendChild(x.r); });
});

// 8) Tendina holdings degli ETF (fragment caricato al primo click).
document.addEventListener('click', function (e) {
  var btn = e.target.closest('[data-holdings]');
  if (!btn) return;
  var id = btn.getAttribute('data-holdings');
  var row = document.getElementById('hr-' + id);
  if (!row) return;
  var box = row.querySelector('.holdings-box');
  if (row.style.display === 'none' || row.style.display === '') {
    var opening = (row.style.display === 'none');
    row.style.display = opening ? 'table-row' : 'none';
    if (opening && box && box.dataset.loaded === '0') {
      box.dataset.loaded = '1';
      box.innerHTML = '<div class="faint" style="padding:12px 16px;">…</div>';
      fetch('/portafoglio/' + id + '/holdings')
        .then(function (r) { return r.text(); })
        .then(function (h) { box.innerHTML = h; })
        .catch(function () { box.dataset.loaded = '0'; box.innerHTML = '<div class="faint" style="padding:12px 16px;">—</div>'; });
    }
  } else {
    row.style.display = 'none';
  }
});
