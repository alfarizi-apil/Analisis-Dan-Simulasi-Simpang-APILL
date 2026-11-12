"""
kalkulasi.py
Fungsi-fungsi murni (pure functions, tanpa UI) untuk analisis Simpang APILL
berdasarkan pedoman PKJI 2023 - studi kasus Jalan Arteri Primer.

Satuan yang dipakai:
    We  : meter (lebar efektif pendekat)
    S   : smp/jam hijau
    C   : smp/jam
    Q   : smp/jam
    g   : detik (waktu hijau)
    Co  : detik (waktu siklus)
"""


def hitung_arus_jenuh_dasar(We):
    """
    Menghitung arus jenuh dasar (So).

    Rumus : So = 600 * We
    Param : We -> lebar efektif pendekat (meter)
    Return: So -> arus jenuh dasar (smp/jam hijau)
    """
    if We <= 0:
        raise ValueError("Lebar efektif (We) harus lebih besar dari 0.")
    return 600 * We


def hitung_arus_jenuh(So, Fsf, Fg, Fp, Fuk):
    """
    Menghitung arus jenuh terkoreksi (S).

    Rumus : S = So * Fsf * Fg * Fp * Fuk
    Param : So  -> arus jenuh dasar (smp/jam hijau)
            Fsf -> faktor koreksi hambatan samping
            Fg  -> faktor koreksi kelandaian
            Fp  -> faktor koreksi parkir
            Fuk -> faktor koreksi ukuran kota
    Return: S   -> arus jenuh setelah koreksi (smp/jam hijau)
    """
    return So * Fsf * Fg * Fp * Fuk


def hitung_kapasitas(S, g, Co):
    """
    Menghitung kapasitas pendekat (C).

    Rumus : C = S * (g / Co)
    Param : S  -> arus jenuh terkoreksi (smp/jam hijau)
            g  -> waktu hijau (detik)
            Co -> waktu siklus (detik)
    Return: C  -> kapasitas pendekat (smp/jam)
    """
    if Co <= 0:
        raise ValueError("Waktu siklus (Co) harus lebih besar dari 0.")
    return S * (g / Co)


def hitung_derajat_kejenuhan(Q, C):
    """
    Menghitung derajat kejenuhan (DS).

    Rumus : DS = Q / C
    Param : Q  -> volume arus lalu lintas (smp/jam)
            C  -> kapasitas pendekat (smp/jam)
    Return: DS -> derajat kejenuhan (tanpa satuan)
    """
    if C <= 0:
        raise ValueError("Kapasitas (C) harus lebih besar dari 0.")
    return Q / C


def tentukan_status(DS):
    """
    Menentukan status kinerja simpang berdasarkan nilai DS.

    Aturan: DS <  0.85 -> "OK / IDEAL"
            DS >= 0.85 -> "MACET / JENUH"
    Param : DS -> derajat kejenuhan
    Return: string status kinerja
    """
    if DS < 0.85:
        return "OK / IDEAL"
    return "MACET / JENUH"

# Ekivalen mobil penumpang (EMP) untuk pendekat terlindung
EMP_MC = 0.15
EMP_LV = 1.00
EMP_HV = 1.30


def konversi_ke_smp(mc, lv, hv):
    """
    Mengonversi jumlah kendaraan mentah (kend/jam) ke Satuan Mobil Penumpang (smp/jam).

    Rumus : Q = MC x EMP_MC + LV x EMP_LV + HV x EMP_HV
    """
    return mc * EMP_MC + lv * EMP_LV + hv * EMP_HV


# ======================================================================
# PERHITUNGAN PER FASE - SATU PENDEKAT = SATU FASE (PENDEKAT TERLINDUNG)
# Rumus mengacu pada PKJI 2023 (simpang APILL).
# ======================================================================

BATAS_DS = 0.85                                   # batas derajat kejenuhan
HIJAU_MINIMUM = 10                                # waktu hijau minimum (detik)
RENTANG_SIKLUS = {2: (40, 80), 3: (50, 100), 4: (80, 130)}   # siklus layak menurut jumlah fase

_URUTAN_PENDEKAT = ["U", "T", "S", "B"]
_ARAH_KELUAR = {"U": (0, -1), "T": (1, 0), "S": (0, 1), "B": (-1, 0)}   # arah keluar tiap kaki (layar)


def hitung_faktor_belok_kiri(persen_kiri):
    """
    Faktor penyesuaian belok kiri.

    Rumus : FBKi = 1,0 - RBKi x 0,16
    Param : persen_kiri -> persentase kendaraan belok kiri (0-100)
    Return: FBKi
    """
    return 1.0 - (persen_kiri / 100.0) * 0.16


def hitung_faktor_belok_kanan(persen_kanan):
    """
    Faktor penyesuaian belok kanan.

    Rumus : FBKa = 1,0 + RBKa x 0,26
    Param : persen_kanan -> persentase kendaraan belok kanan (0-100)
    Return: FBKa
    """
    return 1.0 + (persen_kanan / 100.0) * 0.26


def hitung_arus_jenuh_lengkap(We, Fsf, Fg, Fp, Fuk, persen_kiri, persen_kanan):
    """
    Arus jenuh lengkap: J = J0 x FHS x FUK x FG x FP x FBKi x FBKa.

    Return: (So, FBKi, FBKa, J)
    """
    So = hitung_arus_jenuh_dasar(We)
    FBKi = hitung_faktor_belok_kiri(persen_kiri)
    FBKa = hitung_faktor_belok_kanan(persen_kanan)
    J = hitung_arus_jenuh(So, Fsf, Fg, Fp, Fuk) * FBKi * FBKa
    return So, FBKi, FBKa, J


def hitung_rasio_arus(Q, J):
    """
    Rasio arus.

    Rumus : Rq/J = Q / J
    Return: Rq/J (0 jika J <= 0)
    """
    return Q / J if J > 0 else 0.0


def hitung_waktu_hijau_hilang(daftar_kuning, daftar_semua_merah):
    """
    Waktu hijau hilang per siklus (WHH) = jumlah (kuning + semua merah) seluruh fase.

    Param : daftar_kuning, daftar_semua_merah -> list waktu (detik) tiap fase
    Return: WHH (detik)
    """
    return sum(daftar_kuning) + sum(daftar_semua_merah)


def hitung_siklus_pra_penyesuaian(WHH, IFR):
    """
    Waktu siklus pra-penyesuaian (rumus Webster yang dipakai PKJI).

    Rumus : s = (1,5 x WHH + 5) / (1 - IFR)
    Param : WHH -> waktu hijau hilang per siklus (detik)
            IFR -> rasio arus simpang = jumlah Rq/J kritis seluruh fase
    Return: s (detik). Error jika IFR >= 1 (simpang melebihi kapasitas).
    """
    if IFR >= 1:
        raise ValueError("Rasio arus simpang (IFR) >= 1, waktu siklus tidak dapat dihitung.")
    return (1.5 * WHH + 5) / (1 - IFR)


def hitung_waktu_hijau_usulan(s, WHH, daftar_rq_j_kritis, hijau_min=HIJAU_MINIMUM):
    """
    Waktu hijau tiap fase.

    Rumus : WHi = (s - WHH) x Rq/J_kritis_i / IFR
            (hijau yang kurang dari hijau_min dinaikkan menjadi hijau_min)
    Return: (daftar_hijau, ada_koreksi)
    """
    ifr = sum(daftar_rq_j_kritis)
    mentah = [(s - WHH) * r / ifr for r in daftar_rq_j_kritis]
    hasil = [max(hijau_min, g) for g in mentah]
    return hasil, any(h > m + 1e-9 for h, m in zip(hasil, mentah))


def tujuan_belok(kode, aktif):
    """
    Menentukan gerakan yang mungkin dari suatu pendekat pada simpang 3 atau 4 lengan.

    Param : kode  -> "U", "T", "S", atau "B"
            aktif -> list kode lengan yang ada
    Return: dict {"lurus": bool, "kiri": bool, "kanan": bool}
    """
    o = _ARAH_KELUAR[kode]
    h = (-o[0], -o[1])                 # arah gerak kendaraan masuk simpang
    kiri_vec = (h[1], -h[0])           # sisi kiri pengemudi (lalu lintas lajur kiri)

    def kode_dari(vec):
        for k, v in _ARAH_KELUAR.items():
            if v == vec:
                return k

    return {
        "lurus": kode_dari(h) in aktif,
        "kiri": kode_dari(kiri_vec) in aktif,
        "kanan": kode_dari((-kiri_vec[0], -kiri_vec[1])) in aktif,
    }


def _baris_kinerja(b, C):
    """Melengkapi satu baris hasil dengan kapasitas, DS, dan status."""
    DS = hitung_derajat_kejenuhan(b["Q"], C)
    b["C"] = C
    b["DS"] = DS
    b["status"] = tentukan_status(DS)
    return b


def analisis_simpang(data, Fuk, hitung_usulan=True):
    """
    Analisis kinerja simpang APILL, satu pendekat = satu fase (semua terlindung).

    Param : data -> dict {kode: {"MC","LV","HV","We","Fsf","Fg","Fp",
                                  "p_kiri","p_kanan"(%), "g","kuning","ms"(detik)}}
            Fuk  -> faktor ukuran kota (satu nilai untuk seluruh simpang)
            hitung_usulan -> True: hitung juga waktu siklus dan hijau usulan PKJI
    Return: dict berisi
            "eksisting": {"pendekat": [...], "WHH", "Co", "IFR"}
            "usulan"   : None, atau {"layak", "pesan", "pendekat", "s_pra", "Co", "WHH", "IFR", ...}
            "peringatan": list teks peringatan
    """
    kode_list = [k for k in _URUTAN_PENDEKAT if k in data]
    n = len(kode_list)
    peringatan = []

    dasar = []
    for k in kode_list:
        d = data[k]
        Q = konversi_ke_smp(d["MC"], d["LV"], d["HV"])
        So, FBKi, FBKa, J = hitung_arus_jenuh_lengkap(
            d["We"], d["Fsf"], d["Fg"], d["Fp"], Fuk, d["p_kiri"], d["p_kanan"]
        )
        dasar.append({"kode": k, "Q": Q, "We": d["We"], "So": So, "FBKi": FBKi, "FBKa": FBKa,
                      "J": J, "RqJ": hitung_rasio_arus(Q, J)})

    WHH = hitung_waktu_hijau_hilang([data[k]["kuning"] for k in kode_list], [data[k]["ms"] for k in kode_list])
    IFR = sum(b["RqJ"] for b in dasar)

    # ---------- Kondisi eksisting: hijau diisi pengguna ----------
    eks = []
    Co = sum(data[k]["g"] for k in kode_list) + WHH
    for b in dasar:
        d = data[b["kode"]]
        e = dict(b, g=d["g"], kuning=d["kuning"], ms=d["ms"])
        eks.append(_baris_kinerja(e, hitung_kapasitas(e["J"], e["g"], Co)))

    if n in RENTANG_SIKLUS:
        lo, hi = RENTANG_SIKLUS[n]
        if not lo <= Co <= hi:
            peringatan.append(f"Eksisting: waktu siklus {Co:.0f} d di luar rentang layak {lo}-{hi} d untuk {n} fase.")
    for e in eks:
        if e["g"] < HIJAU_MINIMUM:
            peringatan.append(f"Eksisting: hijau pendekat {e['kode']} ({e['g']:.0f} d) kurang dari {HIJAU_MINIMUM} d.")

    # ---------- Usulan PKJI: siklus & hijau dihitung otomatis ----------
    usulan = None
    if hitung_usulan:
        if IFR >= 1:
            usulan = {"layak": False, "IFR": IFR, "WHH": WHH,
                      "pesan": f"Usulan tidak dapat dihitung: rasio arus simpang (IFR) = {IFR:.2f} >= 1 "
                               "(arus melebihi arus jenuh). Perlu tambah lebar/lajur atau ubah pola fase."}
        elif IFR <= 0:
            usulan = {"layak": False, "IFR": IFR, "WHH": WHH,
                      "pesan": "Usulan tidak dapat dihitung karena seluruh volume bernilai 0."}
        else:
            s_pra = hitung_siklus_pra_penyesuaian(WHH, IFR)
            hijau, dikoreksi = hitung_waktu_hijau_usulan(s_pra, WHH, [b["RqJ"] for b in dasar])
            Co_adj = sum(hijau) + WHH
            usl = []
            for b, g_u in zip(dasar, hijau):
                d = data[b["kode"]]
                u = dict(b, g=g_u, kuning=d["kuning"], ms=d["ms"], RF=b["RqJ"] / IFR)
                usl.append(_baris_kinerja(u, hitung_kapasitas(u["J"], g_u, Co_adj)))
            usulan = {"layak": True, "pendekat": usl, "s_pra": s_pra, "Co": Co_adj, "WHH": WHH,
                      "IFR": IFR, "dikoreksi": dikoreksi}
            if n in RENTANG_SIKLUS:
                lo, hi = RENTANG_SIKLUS[n]
                if not lo <= Co_adj <= hi:
                    peringatan.append(f"Usulan: waktu siklus {Co_adj:.0f} d di luar rentang layak {lo}-{hi} d untuk {n} fase.")
            if dikoreksi:
                peringatan.append(f"Usulan: ada hijau < {HIJAU_MINIMUM} d yang dinaikkan menjadi {HIJAU_MINIMUM} d, "
                                  "sehingga siklus disesuaikan = jumlah hijau + WHH.")

    return {"eksisting": {"pendekat": eks, "WHH": WHH, "Co": Co, "IFR": IFR},
            "usulan": usulan, "peringatan": peringatan}



if __name__ == "__main__":
    # Contoh pemakaian: simpang 4 lengan, satu pendekat = satu fase
    contoh = {k: {"MC": 800, "LV": 300, "HV": 50, "We": 7.0, "Fsf": 0.90, "Fg": 1.0, "Fp": 1.0,
                  "p_kiri": 25, "p_kanan": 25, "g": 20, "kuning": 3, "ms": 2}
              for k in ["U", "T", "S", "B"]}
    hasil = analisis_simpang(contoh, Fuk=1.0)
    print("=== AA SIPIL - CONTOH ANALISIS SIMPANG APILL (PKJI 2023) ===")
    print(f"Eksisting: Co = {hasil['eksisting']['Co']:.0f} d, IFR = {hasil['eksisting']['IFR']:.3f}")
    for b in hasil["eksisting"]["pendekat"]:
        print(f"  Pendekat {b['kode']}: Q={b['Q']:.0f} C={b['C']:.0f} DS={b['DS']:.3f} -> {b['status']}")
    u = hasil["usulan"]
    if u and u["layak"]:
        print(f"Usulan   : Co = {u['Co']:.0f} d")
        for b in u["pendekat"]:
            print(f"  Pendekat {b['kode']}: g={b['g']:.1f} d, DS={b['DS']:.3f} -> {b['status']}")
