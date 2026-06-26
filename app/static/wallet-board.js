/* =========================================================================
   Board dei portafogli: treemap (tessere grandi quanto pesano) + scene vive.
   Filosofia "esuberante ma leggera": a riposo è un quadro fermo; all'evento
   (tocco / anteprima / movimento reale) esplode 2-3 secondi e si calma.
   Nessuna libreria esterna: gira nel browser, anche offline. Vedi CLAUDE.md.
   ========================================================================= */
(function () {
  "use strict";
  var board = document.getElementById("wboard");
  var dataEl = document.getElementById("wboard-data");
  if (!board || !dataEl) return;

  var DATA;
  try { DATA = JSON.parse(dataEl.textContent || "[]"); } catch (e) { DATA = []; }
  if (!DATA.length) return;

  var L = {
    shareOf: board.getAttribute("data-share-of") || "",
    inLbl: board.getAttribute("data-in") || "in",
    outLbl: board.getAttribute("data-out") || "out"
  };

  // Modalità animazioni, con rispetto del "riduci animazioni" di sistema.
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function mode() {
    var m = document.documentElement.getAttribute("data-anim") || "piene";
    if (reduce && m === "piene") m = "leggere"; // accessibilità: niente tempesta
    return m;
  }

  // ----------------------------- treemap squarified -----------------------------
  function squarify(items, X, Y, W, H) {
    var out = [], nodes = items.map(function (it) { return { ref: it.ref, area: 0, v: it.value }; });
    var totV = nodes.reduce(function (s, n) { return s + n.v; }, 0) || 1;
    var totA = W * H;
    nodes.forEach(function (n) { n.area = n.v / totV * totA; });
    var x = X, y = Y, w = W, h = H, row = [];
    function worst(r, len) {
      var s = 0, mx = -1e9, mn = 1e9;
      for (var i = 0; i < r.length; i++) { s += r[i].area; if (r[i].area > mx) mx = r[i].area; if (r[i].area < mn) mn = r[i].area; }
      if (s <= 0) return 1e9;
      return Math.max(len * len * mx / (s * s), s * s / (len * len * mn));
    }
    function commit() {
      var s = row.reduce(function (a, n) { return a + n.area; }, 0);
      if (w >= h) {
        var rw = s / h, yy = y;
        for (var i = 0; i < row.length; i++) { var nh = row[i].area / rw; out.push({ ref: row[i].ref, x: x, y: yy, w: rw, h: nh }); yy += nh; }
        x += rw; w -= rw;
      } else {
        var rh = s / w, xx = x;
        for (var j = 0; j < row.length; j++) { var nw = row[j].area / rh; out.push({ ref: row[j].ref, x: xx, y: y, w: nw, h: rh }); xx += nw; }
        y += rh; h -= rh;
      }
      row = [];
    }
    for (var i = 0; i < nodes.length; i++) {
      var len = Math.min(w, h);
      var cur = worst(row, len), nxt = worst(row.concat([nodes[i]]), len);
      if (row.length && cur < nxt) commit();
      row.push(nodes[i]);
    }
    if (row.length) commit();
    return out;
  }

  // ----------------------------- helpers di disegno -----------------------------
  function rr(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function rand(a, b) { return a + Math.random() * (b - a); }
  function fireColor(t, a) {
    var c;
    if (t < 0.18) c = [255, 248, 214];
    else if (t < 0.42) c = [255, 206, 84];
    else if (t < 0.68) c = [255, 120, 42];
    else c = [206, 44, 32];
    return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")";
  }

  // ----------------------------- scena di una tessera -----------------------------
  function Scene(canvas, type) {
    this.cv = canvas; this.ctx = canvas.getContext("2d"); this.type = type;
    this.parts = []; this.pile = 0.18; this.running = false; this.emitUntil = 0;
    this.cw = 0; this.ch = 0;
  }
  Scene.prototype.resize = function () {
    var r = this.cv.getBoundingClientRect();
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    this.cw = Math.max(1, r.width); this.ch = Math.max(1, r.height);
    this.cv.width = Math.round(this.cw * dpr); this.cv.height = Math.round(this.ch * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.drawStatic();
  };
  Scene.prototype.sky = function (top, bot) {
    var ctx = this.ctx, W = this.cw, H = this.ch;
    var g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, top); g.addColorStop(1, bot);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  };
  Scene.prototype.hillTop = function () { return this.ch - (0.24 + 0.5 * this.pile) * this.ch; };

  Scene.prototype.drawStatic = function () {
    var ctx = this.ctx, W = this.cw, H = this.ch, t = this.type;
    ctx.clearRect(0, 0, W, H);
    if (t === "contanti") {
      this.sky("#0d2440", "#061226");
      this.moneyHill();
    } else if (t === "conto") {
      this.sky("#10233f", "#070f1d");
      this.vault();
    } else if (t === "investimento") {
      this.sky("#0c2233", "#06131d");
      this.plant();
    } else if (t === "carta") {
      this.sky("#161033", "#0a0820");
      this.cardWave();
    } else {
      this.sky("#101826", "#070b12");
      this.coinPile("#9fb0c6", "#5d6b80");
    }
  };

  Scene.prototype.moneyHill = function () {
    var ctx = this.ctx, W = this.cw, H = this.ch, top = this.hillTop();
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(0, H); ctx.lineTo(0, H * 0.9);
    ctx.quadraticCurveTo(W * 0.26, top + 12, W * 0.5, top);
    ctx.quadraticCurveTo(W * 0.74, top + 14, W, H * 0.88);
    ctx.lineTo(W, H); ctx.closePath();
    var g = ctx.createLinearGradient(0, top, 0, H);
    g.addColorStop(0, "#3aa05a"); g.addColorStop(1, "#175c33");
    ctx.fillStyle = g; ctx.fill();
    ctx.clip();
    // texture: piccole banconote impilate
    ctx.globalAlpha = 0.9;
    for (var yy = top + 6; yy < H; yy += 9) {
      for (var xx = ((yy / 9) % 2) * 13 - 6; xx < W; xx += 26) {
        ctx.fillStyle = "#2f8f4e";
        rr(ctx, xx, yy, 22, 7, 2); ctx.fill();
        ctx.fillStyle = "rgba(255,255,255,.14)";
        ctx.fillRect(xx + 9, yy + 2, 4, 3);
      }
    }
    ctx.restore();
  };
  Scene.prototype.coinPile = function (c1, c2) {
    var ctx = this.ctx, W = this.cw, H = this.ch, top = this.hillTop();
    for (var i = 0; i < 60; i++) {
      var px = (i * 53 % 100) / 100 * W;
      var py = lerp(H, top, (i % 12) / 12) + ((i * 17) % 9);
      var rad = 6 + (i % 3);
      ctx.fillStyle = (i % 2) ? c1 : c2;
      ctx.beginPath(); ctx.ellipse(px, py, rad, rad * 0.45, 0, 0, 7); ctx.fill();
    }
  };
  Scene.prototype.vault = function () {
    var ctx = this.ctx, W = this.cw, H = this.ch, top = this.hillTop();
    var bw = 30, gap = 6, rows = Math.ceil((H - top) / 13);
    for (var r = 0; r < rows; r++) {
      var yy = H - 12 - r * 13;
      var off = (r % 2) * (bw / 2);
      for (var x = -off; x < W; x += bw + gap) {
        var g = ctx.createLinearGradient(0, yy, 0, yy + 11);
        g.addColorStop(0, "#f0cf6a"); g.addColorStop(1, "#b98a2c");
        ctx.fillStyle = g; rr(ctx, x, yy, bw, 11, 2); ctx.fill();
        ctx.fillStyle = "rgba(255,255,255,.25)"; ctx.fillRect(x + 3, yy + 2, bw - 6, 2);
      }
    }
  };
  Scene.prototype.plant = function () {
    var ctx = this.ctx, W = this.cw, H = this.ch, cx = W / 2;
    // vaso
    ctx.fillStyle = "#7a4a2b"; rr(ctx, cx - 22, H - 26, 44, 22, 4); ctx.fill();
    ctx.fillStyle = "#5d3720"; ctx.fillRect(cx - 24, H - 28, 48, 5);
    // stelo + foglie, altezza in base al "pile"
    var hgt = (0.34 + 0.5 * this.pile) * H;
    ctx.strokeStyle = "#3f9d54"; ctx.lineWidth = 4; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(cx, H - 26); ctx.lineTo(cx, H - 26 - hgt); ctx.stroke();
    var leaves = Math.max(2, Math.round(this.pile * 7));
    for (var i = 1; i <= leaves; i++) {
      var ly = H - 26 - (i / (leaves + 1)) * hgt, side = i % 2 ? 1 : -1;
      ctx.fillStyle = i % 2 ? "#4caf50" : "#3c9a45";
      ctx.save(); ctx.translate(cx, ly); ctx.rotate(side * 0.6);
      ctx.beginPath(); ctx.ellipse(side * 12, 0, 14, 6, 0, 0, 7); ctx.fill(); ctx.restore();
    }
  };
  Scene.prototype.cardWave = function () {
    var ctx = this.ctx, W = this.cw, H = this.ch;
    // carta
    var cw = Math.min(W * 0.6, 150), ch = cw * 0.62, cx = W / 2 - cw / 2, cy = H * 0.5 - ch / 2;
    var g = ctx.createLinearGradient(cx, cy, cx + cw, cy + ch);
    g.addColorStop(0, "#6d5bd0"); g.addColorStop(1, "#3a2f7a");
    ctx.fillStyle = g; rr(ctx, cx, cy, cw, ch, 10); ctx.fill();
    ctx.fillStyle = "#e8c14a"; rr(ctx, cx + 12, cy + ch * 0.34, 22, 16, 3); ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,.5)"; ctx.fillRect(cx + 12, cy + ch - 16, cw - 24, 5);
    // onde alla base
    ctx.strokeStyle = "rgba(150,130,240,.5)"; ctx.lineWidth = 2;
    for (var k = 0; k < 3; k++) {
      ctx.beginPath();
      for (var x = 0; x <= W; x += 6) {
        var yy = H - 14 - k * 9 + Math.sin((x / 26) + k) * 4;
        x === 0 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy);
      }
      ctx.stroke();
    }
  };

  // ----------------------------- particelle -----------------------------
  Scene.prototype.spawnNote = function (i, n, mag) {
    var W = this.cw, cx = W / 2;
    this.parts.push({
      kind: "note", x: cx + rand(-W * 0.22, W * 0.22), y: rand(-40, -8),
      vx: rand(-0.5, 0.5), vy: rand(0.5, 1.5), ang: rand(-0.5, 0.5), vang: rand(-0.08, 0.08),
      w: rand(20, 30), h: rand(10, 14), grav: 0.16, floor: this.hillTop() + rand(-6, 10), rest: 0,
      hue: this.type === "conto" ? "gold" : "green"
    });
  };
  Scene.prototype.spawnBurningNote = function () {
    var W = this.cw;
    this.parts.push({
      kind: "burn", x: W / 2 + rand(-W * 0.12, W * 0.12), y: this.hillTop() - rand(2, 16),
      w: 34, h: 18, ang: rand(-0.2, 0.2), burn: 0, life: 0, maxlife: 140
    });
  };
  Scene.prototype.spawnFire = function () {
    var W = this.cw, base = this.hillTop();
    var blue = Math.random() < 0.16;
    this.parts.push({
      kind: "fire", x: W / 2 + rand(-W * 0.16, W * 0.16), y: base + rand(-2, 10),
      vx: rand(-0.4, 0.4), vy: rand(-1.8, -0.9), grav: -0.012, r: rand(7, 14),
      life: 0, maxlife: rand(34, 58), blue: blue
    });
    if (Math.random() < 0.4)
      this.parts.push({ kind: "ember", x: W / 2 + rand(-W * 0.2, W * 0.2), y: base, vx: rand(-0.5, 0.5), vy: rand(-2.4, -1.4), grav: -0.02, life: 0, maxlife: rand(30, 50), r: rand(1, 2.2) });
  };
  Scene.prototype.spawnEffect = function (i, n, mag) {
    // entrate per tipi non-contanti: monete/foglie che cadono
    var W = this.cw, cx = W / 2;
    var kind = this.type === "investimento" ? "leaf" : "coin";
    this.parts.push({
      kind: kind, x: cx + rand(-W * 0.25, W * 0.25), y: rand(-30, -6),
      vx: rand(-0.4, 0.4), vy: rand(0.6, 1.4), ang: rand(-1, 1), vang: rand(-0.1, 0.1),
      w: rand(8, 13), grav: 0.15, floor: this.hillTop() + rand(-4, 12), rest: 0
    });
  };

  Scene.prototype.update = function (p) {
    if (p.kind === "fire" || p.kind === "ember") {
      p.x += p.vx; p.y += p.vy; p.vy += p.grav; p.vx *= 0.99; p.life++;
      if (p.life >= p.maxlife) p.dead = true;
    } else if (p.kind === "burn") {
      p.life++; p.burn = Math.min(1, p.life / p.maxlife);
      if (p.life >= p.maxlife) p.dead = true;
    } else { // note / coin / leaf con gravità e atterraggio
      p.vy += p.grav; p.x += p.vx; p.y += p.vy; p.ang += p.vang;
      if (p.y >= p.floor) {
        p.y = p.floor;
        if (Math.abs(p.vy) > 0.7) { p.vy *= -0.3; p.vx *= 0.6; p.vang *= 0.5; }
        else { p.vy = 0; p.vx *= 0.7; p.vang *= 0.5; p.rest++; if (p.rest > 8) { p.dead = true; this.pile = Math.min(1, this.pile + 0.012); } }
      }
    }
  };
  Scene.prototype.draw = function (p) {
    var ctx = this.ctx;
    if (p.kind === "note") {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.ang);
      var w = p.w, h = p.h, gold = p.hue === "gold";
      // mazzetta: pila di 3 banconote leggermente sfalsate
      for (var s = 2; s >= 0; s--) {
        ctx.fillStyle = gold ? (s === 0 ? "#e8c14a" : "#c9a52c") : (s === 0 ? "#2f9150" : "#246f3f");
        rr(ctx, -w / 2 + s * 1.3, -h / 2 - s * 1.6, w, h, 2.5); ctx.fill();
      }
      ctx.fillStyle = "rgba(255,255,255,.16)"; ctx.fillRect(-w / 2, -h * 0.16, w, h * 0.3);
      ctx.fillStyle = "rgba(255,255,255,.42)"; ctx.beginPath(); ctx.arc(0, -h * 0.02, h * 0.2, 0, 7); ctx.fill();
      // fascetta di carta della mazzetta
      ctx.fillStyle = gold ? "#9a6b12" : "#15532c";
      ctx.fillRect(-w * 0.13, -h / 2 - 5, w * 0.26, h + 7);
      ctx.restore();
    } else if (p.kind === "coin") {
      ctx.save(); ctx.fillStyle = "#e8c14a"; ctx.beginPath();
      ctx.ellipse(p.x, p.y, p.w, p.w * 0.9, 0, 0, 7); ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,.35)"; ctx.beginPath(); ctx.ellipse(p.x - p.w * 0.3, p.y - p.w * 0.3, p.w * 0.3, p.w * 0.25, 0, 0, 7); ctx.fill();
      ctx.restore();
    } else if (p.kind === "leaf") {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.ang);
      ctx.fillStyle = "#4caf50"; ctx.beginPath(); ctx.ellipse(0, 0, p.w, p.w * 0.5, 0, 0, 7); ctx.fill();
      ctx.restore();
    } else if (p.kind === "burn") {
      // banconota che brucia: parte verde residua in alto, cenere nera che sale
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.ang);
      var bw = p.w, bh = p.h, remain = 1 - p.burn;
      if (remain > 0.02) { ctx.fillStyle = "#2f9150"; rr(ctx, -bw / 2, -bh / 2, bw, bh * remain, 2); ctx.fill(); }
      ctx.fillStyle = "rgba(22,16,12,.92)"; rr(ctx, -bw / 2, -bh / 2 + bh * remain, bw, bh * p.burn, 2); ctx.fill();
      ctx.fillStyle = "rgba(255,150,40,.9)"; ctx.fillRect(-bw / 2, -bh / 2 + bh * remain - 1, bw, 2);
      ctx.restore();
    } else if (p.kind === "fire") {
      var tt = p.life / p.maxlife, a = (1 - tt) * 0.85, R = p.r * (1 - tt * 0.35);
      ctx.globalCompositeOperation = "lighter";
      var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, R * 2.1);
      g.addColorStop(0, p.blue && tt < 0.3 ? "rgba(120,170,255," + a + ")" : fireColor(tt, a));
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, R * 2.1, 0, 7); ctx.fill();
      ctx.globalCompositeOperation = "source-over";
    } else if (p.kind === "ember") {
      var ea = 1 - p.life / p.maxlife;
      ctx.fillStyle = "rgba(255,200,90," + ea + ")";
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill();
    }
  };

  Scene.prototype.drawFlames = function (level) {
    // corpo del fuoco: lingue di fiamma sovrapposte (rosso->arancio->giallo->bianco)
    // che ondeggiano: dà il senso di un fuoco vero, oltre alle scintille.
    var ctx = this.ctx, W = this.cw, baseY = this.hillTop(), cx = W / 2;
    var tn = performance.now() / 90;
    var bw = Math.min(W * 0.46, 110) * (0.7 + 0.3 * level);
    var layers = [["206,44,32", 1.0, 1.0], ["255,120,42", 0.8, 1.35], ["255,206,84", 0.6, 1.7], ["255,248,214", 0.45, 2.3]];
    ctx.globalCompositeOperation = "lighter";
    for (var i = 0; i < layers.length; i++) {
      var a = layers[i][1] * (0.5 + 0.5 * level), spd = layers[i][2];
      var w = bw * (1 - i * 0.16), hgt = (26 + 34 * level) * (1 - i * 0.12);
      var wob = Math.sin(tn * spd + i) * (4 + i * 2);
      ctx.fillStyle = "rgba(" + layers[i][0] + "," + a + ")";
      ctx.beginPath();
      ctx.moveTo(cx - w / 2, baseY);
      ctx.quadraticCurveTo(cx - w / 4 + wob, baseY - hgt * 0.6, cx + wob * 0.6, baseY - hgt);
      ctx.quadraticCurveTo(cx + w / 4 + wob, baseY - hgt * 0.6, cx + w / 2, baseY);
      ctx.closePath(); ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
  };
  Scene.prototype.burst = function (dir, mag) {
    var m = mode(); if (m === "spente") return;
    mag = mag || 1;
    if (dir === "in") {
      var n = m === "leggere" ? 5 : 14;
      for (var i = 0; i < n; i++) {
        if (this.type === "contanti" || this.type === "conto") this.spawnNote(i, n, mag);
        else this.spawnEffect(i, n, mag);
      }
    } else { // uscita -> fuoco
      this.emitUntil = performance.now() + (m === "leggere" ? 700 : 1500) * mag;
      if (m !== "leggere") this.spawnBurningNote();
      this.pile = Math.max(0.05, this.pile - 0.07 * mag);
    }
    this.loop();
  };
  Scene.prototype.loop = function () {
    if (this.running) return; this.running = true;
    var self = this, light = mode() === "leggere";
    function step() {
      self.drawStatic();
      var now = performance.now(), ctx = self.ctx;
      if (now < self.emitUntil) {
        var rate = light ? 1 : 3;
        for (var k = 0; k < rate; k++) self.spawnFire();
        self.drawFlames(light ? 0.55 : 1);
      }
      var alive = 0;
      for (var i = 0; i < self.parts.length; i++) {
        var p = self.parts[i]; if (p.dead) continue;
        self.update(p); self.draw(p); if (!p.dead) alive++;
      }
      if (alive > 0 || now < self.emitUntil) { self.raf = requestAnimationFrame(step); }
      else { self.parts = []; self.running = false; self.drawStatic(); }
    }
    self.raf = requestAnimationFrame(step);
  };

  // ----------------------------- costruzione del board -----------------------------
  var tiles = []; // {el, scene, ref}
  function buildTiles() {
    board.innerHTML = "";
    tiles = [];
    var maxAbs = DATA.reduce(function (m, d) { return Math.max(m, Math.abs(d.saldo)); }, 0);
    var floor = Math.max(maxAbs * 0.07, 1);
    var items = DATA.map(function (d) { return { ref: d, value: Math.max(Math.abs(d.saldo), floor) }; });
    var sumV = items.reduce(function (s, it) { return s + it.value; }, 0) || 1;

    DATA.forEach(function (d) {
      var el = document.createElement("div");
      el.className = "wtile"; el.tabIndex = 0;
      el.setAttribute("role", "button");
      var share = Math.round(Math.max(Math.abs(d.saldo), floor) / sumV * 100);
      var cv = document.createElement("canvas");
      var scrim = document.createElement("div"); scrim.className = "scrim";
      var shareEl = document.createElement("div"); shareEl.className = "wshare";
      shareEl.textContent = share + "% " + L.shareOf;
      var info = document.createElement("div"); info.className = "info";
      info.innerHTML = '<div class="wtype"></div><div class="wname"></div>' +
        '<div class="wbal' + (d.saldo < 0 ? " neg" : "") + '"></div>';
      info.querySelector(".wtype").textContent = d.tlabel || "";
      info.querySelector(".wname").textContent = d.nome || "";
      info.querySelector(".wbal").textContent = d.eur || "";
      var btns = document.createElement("div"); btns.className = "wbtns";
      var bin = document.createElement("button"); bin.className = "pin"; bin.type = "button";
      bin.textContent = "+"; bin.setAttribute("aria-label", L.inLbl);
      var bout = document.createElement("button"); bout.className = "pout"; bout.type = "button";
      bout.textContent = "−"; bout.setAttribute("aria-label", L.outLbl);
      btns.appendChild(bin); btns.appendChild(bout);

      el.appendChild(cv); el.appendChild(scrim); el.appendChild(shareEl); el.appendChild(info); el.appendChild(btns);
      board.appendChild(el);

      var scene = new Scene(cv, d.tipo);
      // riempimento a riposo proporzionale al peso: chi ha più soldi ha la
      // montagna/caveau/pianta più alta (le tessere grandi non restano vuote).
      scene.pile = maxAbs > 0 ? Math.min(0.92, 0.28 + 0.6 * (Math.abs(d.saldo) / maxAbs)) : 0.3;
      var t = { el: el, scene: scene, ref: d };
      tiles.push(t);

      bin.addEventListener("click", function (e) { e.stopPropagation(); scene.burst("in", 1); });
      bout.addEventListener("click", function (e) { e.stopPropagation(); scene.burst("out", 1); });
      el.addEventListener("click", function () { scene.burst("in", 1); });
      el.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); scene.burst("in", 1); }
      });
    });
  }

  function layout() {
    var W = board.clientWidth, H = board.clientHeight, G = 4;
    // se il board non ha ancora dimensioni (CSS non pronto, tab nascosta…),
    // riprova invece di collassare le tessere a 0.
    if (W < 40 || H < 40) { setTimeout(layout, 150); return; }
    var maxAbs = DATA.reduce(function (m, d) { return Math.max(m, Math.abs(d.saldo)); }, 0);
    var floor = Math.max(maxAbs * 0.08, 1);
    var items = tiles.map(function (t) { return { ref: t, value: Math.max(Math.abs(t.ref.saldo), floor) }; });
    // squarified vuole i valori dal più grande al più piccolo: così le tessere
    // restano quadrate invece di diventare strisce sottili.
    items.sort(function (a, b) { return b.value - a.value; });
    var rects = squarify(items, 0, 0, W, H);
    rects.forEach(function (rc) {
      var t = rc.ref, el = t.el;
      var x = rc.x + G, y = rc.y + G, w = Math.max(8, rc.w - 2 * G), h = Math.max(8, rc.h - 2 * G);
      el.style.left = x + "px"; el.style.top = y + "px";
      el.style.width = w + "px"; el.style.height = h + "px";
      el.classList.toggle("tiny", h < 84 || w < 110);
      t.scene.resize();
    });
  }

  buildTiles();
  layout();

  // ricalcolo su ridimensionamento (con piccolo debounce)
  var rt;
  function onResize() { clearTimeout(rt); rt = setTimeout(layout, 120); }
  if (window.ResizeObserver) { new ResizeObserver(onResize).observe(board); }
  else { window.addEventListener("resize", onResize); }

  // autoplay dopo un movimento reale: ?play=<id>&dir=in|out
  try {
    var qp = new URLSearchParams(window.location.search);
    var pid = qp.get("play"), pdir = qp.get("dir") === "out" ? "out" : "in";
    if (pid) {
      var hit = tiles.filter(function (t) { return String(t.ref.id) === String(pid); })[0];
      if (hit) setTimeout(function () { hit.scene.burst(pdir, 1); }, 350);
    }
  } catch (e) { }
})();
