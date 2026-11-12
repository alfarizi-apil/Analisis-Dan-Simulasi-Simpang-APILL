import pytest
from kalkulasi import *

def test_smp():
    assert konversi_ke_smp(100, 100, 100) == pytest.approx(15 + 100 + 130)

def test_arus_jenuh_dasar():
    assert hitung_arus_jenuh_dasar(7) == 4200
    with pytest.raises(ValueError):
        hitung_arus_jenuh_dasar(0)

def test_faktor_belok():
    assert hitung_faktor_belok_kiri(100) == pytest.approx(0.84)
    assert hitung_faktor_belok_kanan(100) == pytest.approx(1.26)

def test_kapasitas_dan_ds():
    C = hitung_kapasitas(4000, 20, 100)
    assert C == 800
    assert hitung_derajat_kejenuhan(400, C) == 0.5
    assert tentukan_status(0.85) == "MACET / JENUH"
    assert tentukan_status(0.84) == "OK / IDEAL"

def test_webster():
    assert hitung_siklus_pra_penyesuaian(20, 0.5) == pytest.approx(70)
    with pytest.raises(ValueError):
        hitung_siklus_pra_penyesuaian(20, 1)

def test_hijau_proporsional():
    g, koreksi = hitung_waktu_hijau_usulan(70, 20, [0.2, 0.3])
    assert g == pytest.approx([20, 30]) and not koreksi

def test_tujuan_belok_3_lengan():
    # simpang 4 lengan: semua gerakan tersedia
    assert all(tujuan_belok("U", ["U", "T", "S", "B"]).values())
    # simpang 3 lengan tanpa T: pendekat dari lengan buntu tidak punya arah lurus
    kosong = [k for k in "UTSB" if not tujuan_belok(k, ["U", "S", "B"])["lurus"]]
    assert len(kosong) == 1

def test_analisis_4_lengan():
    d = {k: dict(MC=800, LV=300, HV=50, We=7, Fsf=.9, Fg=1, Fp=1, p_kiri=25, p_kanan=25, g=20, kuning=3, ms=2)
         for k in "UTSB"}
    h = analisis_simpang(d, 1.0)
    assert h["eksisting"]["Co"] == pytest.approx(80 + 20)
    assert h["usulan"]["layak"]
    for b in h["usulan"]["pendekat"]:
        assert b["DS"] > 0
