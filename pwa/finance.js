/* MyMoney PWA — logica finanziaria (v2 Fase 3). Trasposizione in JS del calcolo
   del PC (finance/service.py): saldi dei portafogli e sintesi del mese, incluse
   le partite di giro. Deve dare gli STESSI numeri del PC. */
window.FIN = (function () {
  "use strict";
  function r2(n) { return Math.round((Number(n) + Number.EPSILON) * 100) / 100; }

  // saldo di ogni wallet (per uid): apertura + effetti dei movimenti.
  // Giro: la spesa esce da wallet_uid; il rimborso (importo_ricevuto) entra in wallet_to_uid.
  function saldi(wallets, movimenti) {
    var s = {};
    wallets.forEach(function (w) { s[w.uid] = w.saldo_iniziale || 0; });
    movimenti.forEach(function (m) {
      if (m.deleted) return;
      if (m.tipo === "entrata") { if (m.wallet_uid in s) s[m.wallet_uid] += m.importo || 0; }
      else if (m.tipo === "uscita") { if (m.wallet_uid in s) s[m.wallet_uid] -= m.importo || 0; }
      else if (m.tipo === "trasferimento") {
        if (m.wallet_uid in s) s[m.wallet_uid] -= m.importo || 0;
        if (m.wallet_to_uid in s) s[m.wallet_to_uid] += m.importo || 0;
      } else if (m.tipo === "giro") {
        if ((m.importo || 0) > 0 && m.wallet_uid in s) s[m.wallet_uid] -= m.importo;
        if (m.importo_ricevuto != null && m.wallet_to_uid in s) s[m.wallet_to_uid] += m.importo_ricevuto;
      }
    });
    Object.keys(s).forEach(function (k) { s[k] = r2(s[k]); });
    return s;
  }

  function totale(wallets, saldoMap) {
    return r2(wallets.filter(function (w) { return !w.archiviato && !w.deleted; })
      .reduce(function (acc, w) { return acc + (saldoMap[w.uid] || 0); }, 0));
  }

  function _ym(iso) { var d = new Date(iso); return [d.getFullYear(), d.getMonth() + 1]; }
  function _inMese(iso, anno, mese) { if (!iso) return false; var ym = _ym(iso); return ym[0] === anno && ym[1] === mese; }

  // sintesi del mese: entrate/uscite. Le partite di giro CHIUSE contano SOLO il
  // netto (Σ rientri − Σ spese): >0 entrata all'ultimo rientro, <0 uscita all'ultima spesa.
  function riepilogoMese(movimenti, anno, mese) {
    var entrate = 0, uscite = 0, gruppi = {};
    movimenti.forEach(function (m) {
      if (m.deleted) return;
      if (m.tipo === "entrata" && _inMese(m.data, anno, mese)) entrate += m.importo || 0;
      else if (m.tipo === "uscita" && _inMese(m.data, anno, mese)) uscite += m.importo || 0;
      else if (m.tipo === "giro") {
        var g = m.giro_id || ("_" + m.uid);
        (gruppi[g] = gruppi[g] || []).push(m);
      }
    });
    Object.keys(gruppi).forEach(function (g) {
      var rows = gruppi[g];
      if (rows.some(function (r) { return r.giro_aperta; })) return;   // aperta = neutra
      var speso = 0, ricevuto = 0, ultimaSpesa = null, ultimoRientro = null;
      rows.forEach(function (r) {
        speso += r.importo || 0;
        if (r.importo_ricevuto != null) ricevuto += r.importo_ricevuto;
        if ((r.importo || 0) > 0 && r.data) { var d = new Date(r.data); if (!ultimaSpesa || d > ultimaSpesa) ultimaSpesa = d; }
        if (r.importo_ricevuto != null && r.data_ricevuto) { var d2 = new Date(r.data_ricevuto); if (!ultimoRientro || d2 > ultimoRientro) ultimoRientro = d2; }
      });
      var netto = ricevuto - speso;
      if (netto > 0 && ultimoRientro && ultimoRientro.getFullYear() === anno && ultimoRientro.getMonth() + 1 === mese) entrate += netto;
      else if (netto < 0 && ultimaSpesa && ultimaSpesa.getFullYear() === anno && ultimaSpesa.getMonth() + 1 === mese) uscite += -netto;
    });
    return { entrate: r2(entrate), uscite: r2(uscite), saldo: r2(entrate - uscite) };
  }

  // importo con segno da mostrare nel registro per una riga (mirror di giro_importo_display)
  function giroDisplay(m) {
    var haSpesa = (m.importo || 0) > 0, haRientro = m.importo_ricevuto != null;
    if (haSpesa && haRientro) return r2((m.importo_ricevuto || 0) - (m.importo || 0)); // combo
    if (haRientro) return r2(m.importo_ricevuto || 0);
    return r2(-(m.importo || 0));
  }

  return { r2: r2, saldi: saldi, totale: totale, riepilogoMese: riepilogoMese, giroDisplay: giroDisplay };
})();
