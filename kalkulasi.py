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

def konversi_ke_smp(mc, lv, hv):
    """
    Mengonversi jumlah kendaraan mentah (kend/jam) ke Satuan Mobil Penumpang (SMP/jam).
    """
    emp_mc = 0.15
    emp_lv = 1.00
    emp_hv = 1.30
    
    q_smp = (mc * emp_mc) + (lv * emp_lv) + (hv * emp_hv)
    return q_smp


if __name__ == "__main__":
    # ---- Data dummy Jalan Arteri Primer ----
    Q = 1200      # Volume (smp/jam)
    We = 7.0      # Lebar efektif (meter)
    Fsf = 0.90    # Faktor hambatan samping
    Fg = 1.0      # Faktor kelandaian
    Fp = 1.0      # Faktor parkir
    Fuk = 1.00    # Faktor ukuran kota
    Co = 100      # Waktu siklus (detik)
    g = 35        # Waktu hijau (detik)

    # ---- Alur perhitungan ----
    So = hitung_arus_jenuh_dasar(We)
    S = hitung_arus_jenuh(So, Fsf, Fg, Fp, Fuk)
    C = hitung_kapasitas(S, g, Co)
    DS = hitung_derajat_kejenuhan(Q, C)
    status = tentukan_status(DS)

    # ---- Tampilkan hasil ----
    print("=== SIMULASI APILL - JALAN ARTERI PRIMER (PKJI 2023) ===")
    print(f"Arus jenuh dasar (So)       : {So:.2f} smp/jam hijau")
    print(f"Arus jenuh (S)              : {S:.2f} smp/jam hijau")
    print(f"Kapasitas (C)               : {C:.2f} smp/jam")
    print(f"Derajat kejenuhan (DS)      : {DS:.3f}")
    print(f"Status                      : {status}")
   