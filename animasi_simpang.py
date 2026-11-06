"""
animasi_simpang.py
Membuat simulasi animasi Simpang APILL 4 fase (HTML + JavaScript Canvas)
untuk ditampilkan di Streamlit lewat components.html().

Fitur simulasi:
  - Lampu 3 warna (hijau, kuning, merah) bergantian: U -> T -> S -> B
  - Durasi hijau/kuning/semua-merah diambil dari parameter perhitungan
  - Kendaraan berhenti di garis stop saat merah/kuning, lalu jalan lagi saat hijau
  - Kendaraan bisa lurus, belok kiri, atau belok kanan (lajur kiri / left-hand traffic)
  - Laju kedatangan kendaraan mengikuti volume MC, LV, HV tiap pendekat
  - Antrean, jumlah kendaraan lolos, dan diagram waktu sinyal ditampilkan

Konvensi pendekat (sesuai PKJI):
  U = kaki simpang Utara  (kendaraan datang dari atas layar, bergerak ke bawah)
  T = kaki simpang Timur  (datang dari kanan layar, bergerak ke kiri)
  S = kaki simpang Selatan(datang dari bawah layar, bergerak ke atas)
  B = kaki simpang Barat  (datang dari kiri layar, bergerak ke kanan)
"""

import json

URUTAN_PENDEKAT = ["U", "T", "S", "B"]


def hitung_waktu_siklus(hijau, kuning, semua_merah):
    """
    Menghitung waktu siklus simulasi untuk 4 fase berurutan.

    Rumus : siklus = sum(hijau_i + kuning + semua_merah) untuk 4 pendekat
    Param : hijau       -> list 4 nilai waktu hijau (detik) urutan U, T, S, B
            kuning      -> waktu kuning tiap fase (detik)
            semua_merah -> waktu semua merah tiap fase (detik)
    Return: waktu siklus total (detik)
    """
    return sum(h + kuning + semua_merah for h in hijau)


def bangun_html_animasi(hijau, kuning, semua_merah, volume, p_kiri=0.25, p_kanan=0.25, aktif=None):
    """
    Membangun string HTML animasi simpang.

    Param : hijau       -> list waktu hijau (detik), satu nilai per pendekat AKTIF
                           (urutan U, T, S, B; jumlahnya sama dengan len(aktif))
            kuning      -> waktu kuning (detik)
            semua_merah -> waktu semua merah / all-red (detik)
            volume      -> dict {"U": {"MC":..,"LV":..,"HV":..}, ...} dalam kendaraan/jam
                           (cukup berisi pendekat aktif)
            p_kiri      -> proporsi kendaraan belok kiri (0-1)
            p_kanan     -> proporsi kendaraan belok kanan (0-1)
            aktif       -> list kode pendekat yang ada, mis. ["U", "S", "B"] untuk simpang 3
                           lengan. Default None = keempat lengan (U, T, S, B).
    Return: string HTML siap dipakai di streamlit.components.v1.html()
    """
    aktif = [k for k in URUTAN_PENDEKAT if (aktif is None or k in aktif)]
    if len(aktif) not in (3, 4):
        raise ValueError("Simpang harus memiliki 3 atau 4 lengan.")
    if len(hijau) != len(aktif):
        raise ValueError("Jumlah nilai waktu hijau harus sama dengan jumlah pendekat aktif.")
    if p_kiri < 0 or p_kanan < 0 or p_kiri + p_kanan > 1:
        raise ValueError("Proporsi belok kiri + kanan harus antara 0 dan 1.")

    hijau4, volume4 = [], []
    for k in URUTAN_PENDEKAT:                      # susun ulang ke 4 slot (lengan tak ada = 0)
        if k in aktif:
            hijau4.append(float(hijau[aktif.index(k)]))
            volume4.append({t: float(volume[k][t]) for t in ("MC", "LV", "HV")})
        else:
            hijau4.append(0.0)
            volume4.append({"MC": 0.0, "LV": 0.0, "HV": 0.0})

    config = {
        "aktif": [URUTAN_PENDEKAT.index(k) for k in aktif],
        "hijau": hijau4,
        "kuning": float(kuning),
        "semuaMerah": float(semua_merah),
        "volume": volume4,
        "pKiri": float(p_kiri),
        "pKanan": float(p_kanan),
    }
    return _TEMPLATE_HTML.replace("__CONFIG__", json.dumps(config))


_TEMPLATE_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; color: #e5e7eb; }
  .wrap { background: #111827; border-radius: 12px; padding: 12px; display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-start; }
  #sim { flex: 1 1 420px; max-width: 640px; width: 100%; height: auto; border-radius: 10px; display: block; }
  .panel { flex: 1 1 280px; min-width: 260px; }
  #status { font-size: 15px; font-weight: 600; padding: 8px 10px; border-radius: 8px; background: #1f2937; margin-bottom: 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 5px 6px; text-align: center; border-bottom: 1px solid #374151; }
  th { color: #9ca3af; font-weight: 500; font-size: 12px; }
  .dot { display: inline-block; width: 11px; height: 11px; border-radius: 50%; vertical-align: middle; }
  .ctrl { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 10px 0; }
  button, select { background: #374151; color: #f3f4f6; border: 1px solid #4b5563; border-radius: 6px; padding: 5px 10px; font-size: 13px; cursor: pointer; }
  button:hover { background: #4b5563; }
  .legend { display: flex; gap: 12px; font-size: 12px; color: #d1d5db; margin: 6px 0 10px; flex-wrap: wrap; }
  .legend i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 4px; vertical-align: middle; }
  .small { font-size: 12px; color: #9ca3af; margin-top: 8px; line-height: 1.5; }
  #tl { width: 100%; height: auto; border-radius: 6px; background: #1f2937; display: block; margin-top: 6px; }
  h4 { margin: 12px 0 2px; font-size: 13px; color: #d1d5db; font-weight: 600; }
</style>
</head>
<body>
<div class="wrap">
  <canvas id="sim" width="640" height="640"></canvas>
  <div class="panel">
    <div id="status">...</div>
    <table>
      <thead><tr><th>Pendekat</th><th>Lampu</th><th>Sisa (d)</th><th>Q (kend/jam)</th><th>Antrean</th><th>Lolos</th></tr></thead>
      <tbody id="tb"></tbody>
    </table>
    <div class="ctrl">
      <button id="btnPlay">Jeda</button>
      <button id="btnReset">Ulang</button>
      <label>Kecepatan
        <select id="selSpeed">
          <option value="1">1x</option>
          <option value="2">2x</option>
          <option value="3" selected>3x</option>
          <option value="5">5x</option>
          <option value="10">10x</option>
        </select>
      </label>
    </div>
    <div class="legend">
      <span><i style="background:#f59e0b"></i>Lurus</span>
      <span><i style="background:#ef4444"></i>Belok kiri</span>
      <span><i style="background:#22c55e"></i>Belok kanan</span>
    </div>
    <h4>Diagram waktu sinyal (1 siklus)</h4>
    <canvas id="tl" width="300" height="104"></canvas>
    <div class="small" id="info"></div>
  </div>
</div>

<script>
(function () {
  const CFG = __CONFIG__;

  // ---------------- Konstanta geometri & fisika ----------------
  const N = 640, C = 320;          // ukuran kanvas, titik pusat
  const HW = 48, LANE = 24;        // setengah lebar jalan, offset lajur dari garis tengah
  const SPAWN_D = 380, STOP_D = 70; // jarak spawn & garis stop dari pusat
  const VMAX = 90, ACC = 75, BRAKE = 170, DEC_COMF = 110, MINGAP = 7, DT_MAX = 0.05;
  const OUT = [[0, -1], [1, 0], [0, 1], [-1, 0]];   // arah keluar kaki U, T, S, B
  const LBL = ["U", "T", "S", "B"];
  const TYPES = {
    MC: { len: 14, wid: 7,  vf: 1.15, acc: 1.3 },
    LV: { len: 30, wid: 15, vf: 1.0,  acc: 1.0 },
    HV: { len: 46, wid: 18, vf: 0.78, acc: 0.7 }
  };
  const COL = { lurus: "#f59e0b", kiri: "#ef4444", kanan: "#22c55e" };

  // ---------------- Jadwal sinyal ----------------
  const ACT = CFG.aktif;                       // indeks lengan yang ada (0=U, 1=T, 2=S, 3=B)
  const ACTSET = new Set(ACT);
  const NP = ACT.length;                       // jumlah fase = jumlah lengan
  const G = ACT.map(k => CFG.hijau[k]), Y = CFG.kuning, AR = CFG.semuaMerah;   // hijau per fase
  const starts = []; let cyc = 0;
  for (let i = 0; i < NP; i++) { starts.push(cyc); cyc += G[i] + Y + AR; }

  function signal(t) {
    const tc = ((t % cyc) + cyc) % cyc;
    let p = 0;
    for (let i = NP - 1; i >= 0; i--) { if (tc >= starts[i]) { p = i; break; } }
    const off = tc - starts[p];
    let sub, rem;
    if (off < G[p]) { sub = "G"; rem = G[p] - off; }
    else if (off < G[p] + Y) { sub = "Y"; rem = G[p] + Y - off; }
    else { sub = "AR"; rem = G[p] + Y + AR - off; }
    const st = [], cd = [];
    for (let k = 0; k < 4; k++) {
      const pi = ACT.indexOf(k);
      if (pi < 0) { st.push("R"); cd.push(9999); continue; }       // lengan tidak ada
      if (pi === p && sub !== "AR") { st.push(sub); cd.push(rem); }
      else { st.push("R"); cd.push((starts[pi] - tc + cyc) % cyc); }
    }
    return { ph: ACT[p], sub, rem, st, cd, tc };
  }

  // ---------------- Lintasan kendaraan ----------------
  // k = pendekat asal, turn = 'lurus' | 'kiri' | 'kanan'
  function mkPath(k, turn) {
    const o = OUT[k], h = [-o[0], -o[1]], l = [h[1], -h[0]];   // l = sisi kiri pengemudi
    let m;
    if (turn === "lurus") m = (k + 2) % 4;
    else {
      const tg = turn === "kiri" ? l : [-l[0], -l[1]];
      m = OUT.findIndex(v => v[0] === tg[0] && v[1] === tg[1]);
    }
    const om = OUT[m], lm = [om[1], -om[0]];
    const P0 = [C + o[0] * SPAWN_D + l[0] * LANE, C + o[1] * SPAWN_D + l[1] * LANE];
    const A  = [C + o[0] * HW + l[0] * LANE,      C + o[1] * HW + l[1] * LANE];
    const B  = [C + om[0] * HW + lm[0] * LANE,    C + om[1] * HW + lm[1] * LANE];
    const L1 = SPAWN_D - HW;
    let L2, boxFn;
    if (turn === "lurus") {
      L2 = 2 * HW;
      boxFn = u => ({ x: A[0] + h[0] * u, y: A[1] + h[1] * u, hx: h[0], hy: h[1] });
    } else {
      const sg = turn === "kiri" ? 1 : -1;
      const Q = [C + o[0] * HW + sg * l[0] * HW, C + o[1] * HW + sg * l[1] * HW];
      const a = [A[0] - Q[0], A[1] - Q[1]], b = [B[0] - Q[0], B[1] - Q[1]];
      const r = Math.hypot(a[0], a[1]);
      L2 = r * Math.PI / 2;
      boxFn = u => {
        const f = u / r, c = Math.cos(f), s = Math.sin(f);
        return { x: Q[0] + a[0] * c + b[0] * s, y: Q[1] + a[1] * c + b[1] * s,
                 hx: (-a[0] * s + b[0] * c) / r, hy: (-a[1] * s + b[1] * c) / r };
      };
    }
    const L3 = SPAWN_D - HW, L = L1 + L2 + L3;
    return {
      k, m, turn, L1, L2, L, boxEnd: L1 + L2, stopS: SPAWN_D - STOP_D,
      pos(s) {
        if (s < L1) return { x: P0[0] + h[0] * s, y: P0[1] + h[1] * s, hx: h[0], hy: h[1] };
        if (s < L1 + L2) return boxFn(s - L1);
        const u = s - L1 - L2;
        return { x: B[0] + om[0] * u, y: B[1] + om[1] * u, hx: om[0], hy: om[1] };
      }
    };
  }
  const PATHS = [0, 1, 2, 3].map(k => ({ lurus: mkPath(k, "lurus"), kiri: mkPath(k, "kiri"), kanan: mkPath(k, "kanan") }));

  // ---------------- State simulasi ----------------
  let cars = [], pending = [[], [], [], []], passed = [0, 0, 0, 0], t = 0, uid = 0;

  // Pilih arah: hanya ke lengan tujuan yang ada (simpang 3 lengan: tidak ada belok ke lengan kosong)
  function pickTurn(k) {
    const opts = [["lurus", 1 - CFG.pKiri - CFG.pKanan], ["kiri", CFG.pKiri], ["kanan", CFG.pKanan]]
      .filter(o => ACTSET.has(PATHS[k][o[0]].m));
    let sum = 0; for (const o of opts) sum += o[1];
    if (sum <= 0) return opts[Math.floor(Math.random() * opts.length)][0];
    let r = Math.random() * sum;
    for (const o of opts) { r -= o[1]; if (r <= 0) return o[0]; }
    return opts[opts.length - 1][0];
  }

  function newCar(k, type) {
    const turn = pickTurn(k);
    const T = TYPES[type];
    const path = PATHS[k][turn];
    const p = path.pos(0);
    return { id: ++uid, k, type, turn, len: T.len, wid: T.wid, vmax: VMAX * T.vf, acc: ACC * T.acc,
             path, s: 0, v: 35, vN: 35, crossed: false, x: p.x, y: p.y, hx: p.hx, hy: p.hy };
  }

  function spawn(dt) {
    for (let k = 0; k < 4; k++) {
      for (const type of ["MC", "LV", "HV"]) {
        const rate = CFG.volume[k][type] / 3600;
        if (Math.random() < rate * dt) pending[k].push(type);
      }
      if (pending[k].length > 40) pending[k].length = 40;
      if (pending[k].length) {
        const T = TYPES[pending[k][0]];
        let ok = true;
        for (const c of cars) { if (c.k === k && (c.s - c.len / 2) < T.len / 2 + 8) { ok = false; break; } }
        if (ok) cars.push(newCar(k, pending[k].shift()));
      }
    }
  }

  // Apakah persimpangan (kotak tengah) sedang dilewati kendaraan dari pendekat lain?
  function boxBusy(c) {
    for (const o of cars) {
      if (o.k === c.k) continue;
      if (o.s + o.len / 2 > o.path.L1 - 4 && o.s - o.len / 2 < o.path.boxEnd) return true;
    }
    return false;
  }

  function speedFor(c, sg, dt) {
    const front = c.s + c.len / 2;
    let vT = c.vmax, cap = Infinity;
    const lim = (gap, vObs, buf) => {
      const d = Math.max(0, gap - buf - 0.25 * c.v);
      vT = Math.min(vT, Math.sqrt(vObs * vObs + 2 * BRAKE * d));
    };

    // 1) Lampu lalu lintas (hanya berlaku sebelum garis stop)
    if (front < c.path.stopS + 0.5) {
      const d = c.path.stopS - front, st = sg.st[c.k];
      let stop = false;
      if (st === "R") stop = true;
      else if (st === "Y") stop = d > (c.v * c.v) / (2 * DEC_COMF);   // kuning: berhenti jika masih sempat
      if (!stop && boxBusy(c)) stop = true;                            // jangan masuk simpang yang belum kosong
      if (stop) lim(d, 0, 1.5);
    }

    for (const o of cars) {
      if (o === c) continue;
      // 2) Mobil di depan pada pendekat yang sama (antrean)
      if (o.k === c.k && o.s > c.s && (o.s - o.len / 2) < o.path.boxEnd) {
        const gap = (o.s - o.len / 2) - front;
        lim(gap, o.v, MINGAP);
        cap = Math.min(cap, Math.max(0, gap - 1.5) / dt);
      }
      // 3) Kendaraan di depan secara fisik (di dalam simpang / lengan keluar)
      if (front > c.path.L1 - 20) {
        const dx = o.x - c.x, dy = o.y - c.y;
        const ah = dx * c.hx + dy * c.hy;
        if (ah > 0 && ah < 140) {
          const lat = Math.abs(dx * c.hy - dy * c.hx);
          if (lat < (c.wid + o.wid) / 2 + 5 && (c.hx * o.hx + c.hy * o.hy) > 0.5) {
            const gap = ah - (c.len + o.len) / 2;
            lim(gap, o.v, MINGAP);
            cap = Math.min(cap, Math.max(0, gap - 1.5) / dt);
          }
        }
      }
    }

    let v = c.v;
    if (v < vT) v = Math.min(vT, v + c.acc * dt);
    else v = Math.max(vT, v - BRAKE * dt);
    return Math.min(v, cap);
  }

  function step(dt) {
    t += dt;
    const sg = signal(t);
    spawn(dt);
    for (const c of cars) c.vN = speedFor(c, sg, dt);
    for (const c of cars) {
      c.v = c.vN;
      c.s += c.v * dt;
      const p = c.path.pos(c.s);
      c.x = p.x; c.y = p.y; c.hx = p.hx; c.hy = p.hy;
      if (!c.crossed && c.s + c.len / 2 >= c.path.stopS) { c.crossed = true; passed[c.k]++; }
    }
    cars = cars.filter(c => c.s < c.path.L + c.len);
  }

  function reset() {
    cars = []; pending = [[], [], [], []]; passed = [0, 0, 0, 0]; t = 0;
  }

  // ---------------- Menggambar ----------------
  const cv = document.getElementById("sim"), ctx = cv.getContext("2d");
  const tl = document.getElementById("tl"), tctx = tl.getContext("2d");

  function rr(x, y, w, h, r) {
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h);
  }

  function drawRoad() {
    ctx.fillStyle = "#2b3544"; ctx.fillRect(0, 0, N, N);
    ctx.fillStyle = "#4b5563";
    ctx.fillRect(C - HW, C - HW, 2 * HW, 2 * HW);                 // kotak simpang
    for (const k of ACT) {                                         // lengan jalan yang ada
      const o = OUT[k];
      if (o[1] !== 0) ctx.fillRect(C - HW, o[1] < 0 ? 0 : C, 2 * HW, C);
      else ctx.fillRect(o[0] < 0 ? 0 : C, C - HW, C, 2 * HW);
    }
    for (const k of ACT) {
      ctx.save(); ctx.translate(C, C); ctx.rotate(k * Math.PI / 2);
      ctx.fillStyle = "#fbbf24";                                   // garis tengah
      for (let y = -(STOP_D + 8); y > -C; y -= 18) ctx.fillRect(-1, y - 10, 2, 10);
      ctx.fillStyle = "rgba(255,255,255,.85)";                     // zebra cross
      for (let x = -HW + 6; x < HW - 4; x += 11) ctx.fillRect(x, -66, 6, 14);
      ctx.fillStyle = "#ffffff"; ctx.fillRect(0, -STOP_D - 2, HW, 4); // garis stop
      ctx.restore();
    }
    // label pendekat
    ctx.font = "bold 15px system-ui, sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (const k of ACT) {
      const o = OUT[k], h = [-o[0], -o[1]], l = [h[1], -h[0]];
      const x = C + o[0] * (C - 26) + l[0] * LANE, y = C + o[1] * (C - 26) + l[1] * LANE;
      ctx.fillStyle = "rgba(17,24,39,.75)"; ctx.beginPath(); ctx.arc(x, y, 12, 0, 6.2832); ctx.fill();
      ctx.fillStyle = "#e5e7eb"; ctx.fillText(LBL[k], x, y + 1);
    }
  }

  function drawSignal(k, state, cd) {
    const o = OUT[k], h = [-o[0], -o[1]], l = [h[1], -h[0]];
    const x = C + o[0] * (STOP_D + 18) + l[0] * (HW + 18), y = C + o[1] * (STOP_D + 18) + l[1] * (HW + 18);
    ctx.fillStyle = "#0b1220"; rr(x - 11, y - 29, 22, 58, 5); ctx.fill();
    const lamps = [["R", "#ef4444", "#4a1515", -18], ["Y", "#fbbf24", "#4a3a0c", 0], ["G", "#22c55e", "#0f3d1f", 18]];
    for (const [s, on, off, dy] of lamps) {
      const act = state === s;
      ctx.fillStyle = act ? on : off;
      ctx.shadowColor = act ? on : "transparent"; ctx.shadowBlur = act ? 12 : 0;
      ctx.beginPath(); ctx.arc(x, y + dy, 7, 0, 6.2832); ctx.fill();
    }
    ctx.shadowBlur = 0;
    ctx.font = "bold 13px system-ui, sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillStyle = state === "G" ? "#22c55e" : (state === "Y" ? "#fbbf24" : "#fca5a5");
    ctx.fillText(cd < 100 ? String(Math.ceil(cd)) : "--", x, y + 41);
  }

  function drawCar(c) {
    const ang = Math.atan2(c.hy, c.hx) + Math.PI / 2;
    const w = c.wid, L = c.len, hl = Math.max(2, w * 0.25);
    ctx.save(); ctx.translate(c.x, c.y); ctx.rotate(ang);
    ctx.fillStyle = COL[c.turn];
    if (c.type === "MC") {
      rr(-w / 2, -L / 2, w, L, 3); ctx.fill();
      ctx.fillStyle = "#111827"; ctx.beginPath(); ctx.arc(0, -1, 3.2, 0, 6.2832); ctx.fill();
    } else if (c.type === "LV") {
      rr(-w / 2, -L / 2, w, L, 4); ctx.fill();
      ctx.fillStyle = "rgba(15,23,42,.75)";
      ctx.fillRect(-w / 2 + 2, -L / 2 + 6, w - 4, 7); ctx.fillRect(-w / 2 + 2, L / 2 - 9, w - 4, 5);
    } else {
      rr(-w / 2, -L / 2, w, L, 3); ctx.fill();
      ctx.fillStyle = "rgba(15,23,42,.8)"; ctx.fillRect(-w / 2 + 2, -L / 2 + 3, w - 4, 8);
      ctx.strokeStyle = "rgba(0,0,0,.4)"; ctx.beginPath(); ctx.moveTo(-w / 2, -L / 2 + 16); ctx.lineTo(w / 2, -L / 2 + 16); ctx.stroke();
    }
    ctx.fillStyle = "#fef9c3";                                    // lampu depan
    ctx.fillRect(-w / 2 + 1, -L / 2, hl, 2); ctx.fillRect(w / 2 - 1 - hl, -L / 2, hl, 2);
    if (c.v < 5) {                                                // lampu rem
      ctx.fillStyle = "#ef4444";
      ctx.fillRect(-w / 2 + 1, L / 2 - 2, hl, 2); ctx.fillRect(w / 2 - 1 - hl, L / 2 - 2, hl, 2);
    }
    if (c.turn !== "lurus" && c.s < c.path.boxEnd && Math.floor(t * 2.5) % 2 === 0) {   // lampu sein
      const sx = c.turn === "kiri" ? -w / 2 - 2.5 : w / 2;
      ctx.fillStyle = "#fbbf24";
      ctx.fillRect(sx, -L / 2 + 1, 2.5, 3); ctx.fillRect(sx, L / 2 - 4, 2.5, 3);
    }
    ctx.restore();
  }

  function drawTimeline(tc) {
    const W = tl.width, Hh = tl.height, x0 = 22, rowH = 20, y0 = 6, sc = (W - x0 - 4) / cyc;
    tctx.clearRect(0, 0, W, Hh);
    tctx.font = "bold 11px system-ui, sans-serif"; tctx.textAlign = "left"; tctx.textBaseline = "middle";
    for (let i = 0; i < NP; i++) {
      const y = y0 + i * (rowH + 4);
      tctx.fillStyle = "#ef4444"; tctx.fillRect(x0, y, cyc * sc, rowH);
      tctx.fillStyle = "#22c55e"; tctx.fillRect(x0 + starts[i] * sc, y, G[i] * sc, rowH);
      tctx.fillStyle = "#fbbf24"; tctx.fillRect(x0 + (starts[i] + G[i]) * sc, y, Y * sc, rowH);
      tctx.fillStyle = "#e5e7eb"; tctx.fillText(LBL[ACT[i]], 5, y + rowH / 2);
    }
    tctx.fillStyle = "#ffffff"; tctx.fillRect(x0 + tc * sc - 1, 2, 2, Hh - 4);
  }

  function render() {
    const sg = signal(t);
    drawRoad();
    for (const c of cars) drawCar(c);
    for (const k of ACT) drawSignal(k, sg.st[k], sg.cd[k]);
    ctx.font = "12px system-ui, sans-serif"; ctx.textAlign = "left"; ctx.fillStyle = "#9ca3af";
    ctx.fillText("t = " + Math.floor(t) + " d", 10, 16);
    drawTimeline(sg.tc);
    return sg;
  }

  // ---------------- Panel info ----------------
  const tb = document.getElementById("tb");
  const rows = {};
  for (const k of ACT) {
    const tr = document.createElement("tr");
    const q = CFG.volume[k].MC + CFG.volume[k].LV + CFG.volume[k].HV;
    tr.innerHTML = "<td><b>" + LBL[k] + "</b></td><td><span class='dot'></span></td><td></td><td>" + Math.round(q) + "</td><td></td><td></td>";
    tb.appendChild(tr); rows[k] = tr.children;
  }
  document.getElementById("info").innerHTML =
    "Hijau tiap fase: " + G.map(v => Math.round(v * 10) / 10).join(" / ") + " d &middot; Kuning " + Y + " d &middot; Semua merah " + AR + " d<br>" +
    "<b>Siklus simulasi = " + Math.round(cyc * 10) / 10 + " detik</b> (" + NP + " fase berurutan " + ACT.map(k => LBL[k]).join(" &rarr; ") + ")";

  const SUBTXT = { G: "HIJAU", Y: "KUNING", AR: "SEMUA MERAH" };
  const DOTC = { G: "#22c55e", Y: "#fbbf24", R: "#ef4444" };
  function updateHud(sg) {
    document.getElementById("status").textContent =
      "Fase aktif: Pendekat " + LBL[sg.ph] + " - " + SUBTXT[sg.sub] + " (" + Math.ceil(sg.rem) + " d)";
    for (const k of ACT) {
      const cells = rows[k];
      cells[1].firstChild.style.background = DOTC[sg.st[k]];
      cells[2].textContent = sg.cd[k] < 1000 ? Math.ceil(sg.cd[k]) : "--";
      const q = cars.filter(c => c.k === k && !c.crossed && c.v < 6 && c.s > 5).length + pending[k].length;
      cells[4].textContent = q;
      cells[5].textContent = passed[k];
    }
  }

  // ---------------- Kontrol & loop ----------------
  let playing = true, speed = 3, last = performance.now(), lastHud = 0;
  document.getElementById("btnPlay").onclick = function () { playing = !playing; this.textContent = playing ? "Jeda" : "Lanjut"; };
  document.getElementById("btnReset").onclick = function () { reset(); };
  document.getElementById("selSpeed").onchange = function () { speed = parseFloat(this.value); };

  function frame(now) {
    const dtReal = Math.min((now - last) / 1000, 0.1); last = now;
    if (playing) {
      const sim = dtReal * speed, n = Math.max(1, Math.ceil(sim / DT_MAX)), d = sim / n;
      for (let i = 0; i < n; i++) step(d);
    }
    const sg = render();
    if (now - lastHud > 250) { updateHud(sg); lastHud = now; }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // Akses untuk pengujian
  window.__SIM = { step, reset, get cars() { return cars; }, get passed() { return passed; }, get t() { return t; }, signal, cyc };
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    # Uji cepat: simpan HTML ke file agar bisa dibuka di browser
    data = {k: {"MC": 800, "LV": 300, "HV": 50} for k in URUTAN_PENDEKAT}
    html = bangun_html_animasi([35, 35, 35, 35], 3, 2, data)
    with open("uji_animasi.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Tersimpan: uji_animasi.html | siklus =", hitung_waktu_siklus([35] * 4, 3, 2), "detik")
    