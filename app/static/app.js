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
