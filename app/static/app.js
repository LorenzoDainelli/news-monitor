// JS minimo dell'app.
// 1) Conferme di eliminazione: il testo è tradotto e passato via data-msg,
//    così niente problemi di virgolette/lingua.
document.addEventListener('submit', function (e) {
  var f = e.target;
  if (f.classList && f.classList.contains('js-confirm')) {
    if (!window.confirm(f.dataset.msg || 'OK?')) {
      e.preventDefault();
    }
  }
});

// 2) Tendina holdings degli ETF: al primo click carica le holdings dal server.
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
