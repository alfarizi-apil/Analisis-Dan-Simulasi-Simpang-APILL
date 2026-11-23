"""
langkah.py
Menyusun rincian langkah perhitungan (rumus, substitusi angka, hasil) untuk satu pendekat,
agar pengguna dapat memeriksa perhitungan satu per satu.

Seluruh angka diambil dari hasil analisis_simpang() di kalkulasi.py, sehingga tampilan
langkah selalu sama dengan hasil yang ditampilkan di tabel.
"""

from kalkulasi import BATAS_DS, HIJAU_MINIMUM, konversi_ke_smp


def _n(x, nd=1):
    """Format angka dengan pemisah ribuan."""
    return f"{x:,.{nd}f}"


def langkah_perhitungan(hs, kode, skenario="Eksisting"):
    """
    Rincian langkah perhitungan satu pendekat.

    Param : hs       -> dict hasil (kunci: analisis, data, Fuk, urutan)
            kode     -> kode pendekat ("U", "T", "S", "B")
            skenario -> "Eksisting" atau "Usulan PKJI"
    Return: list dict {"no", "besaran", "rumus", "substitusi", "hasil"}
    """
    an = hs["analisis"]
    eks, usl = an["eksisting"], an["usulan"]
    d = hs["data"][kode]
    Fuk = hs["Fuk"]
    b = next(x for x in eks["pendekat"] if x["kode"] == kode)
    emp_mc, emp_lv, emp_hv = konversi_ke_smp(1, 0, 0), konversi_ke_smp(0, 1, 0), konversi_ke_smp(0, 0, 1)

    langkah = []

    def tambah(besaran, rumus, substitusi, hasil):
        langkah.append({"no": len(langkah) + 1, "besaran": besaran, "rumus": rumus,
                        "substitusi": substitusi, "hasil": hasil})

    # ---------- Bagian dasar (sama untuk eksisting dan usulan) ----------
    tambah("Arus lalu lintas Q",
           "Q = MC x EMP_MC + LV x EMP_LV + HV x EMP_HV",
           f"{d['MC']:.0f} x {emp_mc:.2f} + {d['LV']:.0f} x {emp_lv:.2f} + {d['HV']:.0f} x {emp_hv:.2f}",
           f"{_n(b['Q'])} smp/jam")
    tambah("Arus jenuh dasar J0", "J0 = 600 x We", f"600 x {d['We']:.1f}", f"{_n(b['So'], 0)} smp/jam hijau")
    tambah("Faktor belok kiri FBKi", "FBKi = 1.0 - RBKi x 0.16",
           f"1.0 - {d['p_kiri'] / 100:.2f} x 0.16", f"{b['FBKi']:.3f}")
    tambah("Faktor belok kanan FBKa", "FBKa = 1.0 + RBKa x 0.26",
           f"1.0 + {d['p_kanan'] / 100:.2f} x 0.26", f"{b['FBKa']:.3f}")
    tambah("Arus jenuh J", "J = J0 x Fsf x Fuk x Fg x Fp x FBKi x FBKa",
           f"{_n(b['So'], 0)} x {d['Fsf']:.2f} x {Fuk:.2f} x {d['Fg']:.2f} x {d['Fp']:.2f} x {b['FBKi']:.3f} x {b['FBKa']:.3f}",
           f"{_n(b['J'], 0)} smp/jam hijau")
    tambah("Rasio arus Rq/J", "Rq/J = Q / J", f"{_n(b['Q'])} / {_n(b['J'], 0)}", f"{b['RqJ']:.3f}")

    if skenario == "Eksisting":
        whh_txt = " + ".join(f"({x['kuning']:.0f} + {x['ms']:.0f})" for x in eks["pendekat"])
        g_txt = " + ".join(f"{x['g']:.0f}" for x in eks["pendekat"])
        tambah("Waktu hijau hilang WHH", "WHH = jumlah (kuning + semua merah) seluruh fase", whh_txt,
               f"{eks['WHH']:.1f} d")
        tambah("Waktu siklus Co", "Co = jumlah hijau seluruh fase + WHH", f"{g_txt} + {eks['WHH']:.0f}",
               f"{eks['Co']:.1f} d")
        tambah("Kapasitas C", "C = J x g / Co", f"{_n(b['J'], 0)} x {b['g']:.1f} / {eks['Co']:.1f}",
               f"{_n(b['C'], 0)} smp/jam")
        tambah("Derajat kejenuhan DS", "DS = Q / C", f"{_n(b['Q'])} / {_n(b['C'], 0)}", f"{b['DS']:.3f}")
        tambah("Status", f"DS < {BATAS_DS} = OK / IDEAL", f"{b['DS']:.3f} {'<' if b['DS'] < BATAS_DS else '>='} {BATAS_DS}",
               b["status"])
        return langkah

    # ---------- Usulan PKJI ----------
    if not usl or not usl["layak"]:
        tambah("Usulan PKJI", "-", "-", "Tidak dapat dihitung (lihat peringatan pada halaman hasil)")
        return langkah

    u = next(x for x in usl["pendekat"] if x["kode"] == kode)
    ifr_txt = " + ".join(f"{x['RqJ']:.3f}" for x in usl["pendekat"])
    tambah("Waktu hijau hilang WHH", "WHH = jumlah (kuning + semua merah) seluruh fase",
           " + ".join(f"({x['kuning']:.0f} + {x['ms']:.0f})" for x in usl["pendekat"]), f"{usl['WHH']:.1f} d")
    tambah("Rasio arus simpang IFR", "IFR = jumlah Rq/J seluruh fase", ifr_txt, f"{usl['IFR']:.3f}")
    tambah("Siklus pra-penyesuaian s", "s = (1.5 x WHH + 5) / (1 - IFR)",
           f"(1.5 x {usl['WHH']:.1f} + 5) / (1 - {usl['IFR']:.3f})", f"{usl['s_pra']:.1f} d")
    g_mentah = (usl["s_pra"] - usl["WHH"]) * u["RqJ"] / usl["IFR"]
    catatan_min = f" (dinaikkan ke minimum {HIJAU_MINIMUM} d)" if u["g"] > g_mentah + 1e-9 else ""
    tambah("Waktu hijau usulan g", f"g = (s - WHH) x Rq/J / IFR, minimum {HIJAU_MINIMUM} d",
           f"({usl['s_pra']:.1f} - {usl['WHH']:.1f}) x {u['RqJ']:.3f} / {usl['IFR']:.3f}", f"{u['g']:.1f} d{catatan_min}")
    tambah("Siklus disesuaikan Co", "Co = jumlah hijau usulan + WHH",
           " + ".join(f"{x['g']:.1f}" for x in usl["pendekat"]) + f" + {usl['WHH']:.1f}", f"{usl['Co']:.1f} d")
    tambah("Kapasitas C", "C = J x g / Co", f"{_n(u['J'], 0)} x {u['g']:.1f} / {usl['Co']:.1f}", f"{_n(u['C'], 0)} smp/jam")
    tambah("Derajat kejenuhan DS", "DS = Q / C", f"{_n(u['Q'])} / {_n(u['C'], 0)}", f"{u['DS']:.3f}")
    tambah("Status", f"DS < {BATAS_DS} = OK / IDEAL", f"{u['DS']:.3f} {'<' if u['DS'] < BATAS_DS else '>='} {BATAS_DS}",
           u["status"])
    return langkah
