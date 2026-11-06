"""
app.py
Antarmuka Streamlit untuk Analisis dan Animasi Simpang APILL (PKJI 2023).
"""

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from animasi_simpang import bangun_html_animasi, hitung_waktu_siklus
from ekspor_excel import buat_excel
from tampilan import (
    terapkan_tema, sidebar_brand, header_halaman, judul_bagian, kartu_kpi, rapikan_grafik, PALET_GRAFIK,
)
from kalkulasi import (
    hitung_arus_jenuh_dasar,
    hitung_arus_jenuh,
    hitung_kapasitas,
    hitung_derajat_kejenuhan,
    tentukan_status,
    konversi_ke_smp, # Tambahan fungsi baru
)

st.set_page_config(page_title="Analisis dan Animasi Simpang APILL", page_icon="🚦", layout="wide")
terapkan_tema()

# ---------------------------------------------------------------
# 1. Judul
# ---------------------------------------------------------------
header_halaman("Analisis dan Animasi Simpang APILL", "Berdasarkan pedoman PKJI 2023 | Input Berbasis Jenis Kendaraan")

# ---------------------------------------------------------------
# 2. Sidebar: parameter umum
# ---------------------------------------------------------------
sidebar_brand()
st.sidebar.header("Parameter Umum")

Co = st.sidebar.number_input("Waktu Siklus, Co (detik)", min_value=1.0, value=100.0, step=1.0, key="co_in")
g = st.sidebar.number_input("Waktu Hijau, g (detik)", min_value=0.0, value=35.0, step=1.0, key="g_in")

st.sidebar.subheader("Faktor Koreksi")
Fsf = st.sidebar.number_input("Fsf (hambatan samping)", min_value=0.0, value=0.90, step=0.01, format="%.2f", key="fsf_in")
Fg = st.sidebar.number_input("Fg (kelandaian)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key="fg_in")
Fp = st.sidebar.number_input("Fp (parkir)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key="fp_in")
Fuk = st.sidebar.number_input("Fuk (ukuran kota)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key="fuk_in")

# ---------------------------------------------------------------
# 3. Jenis simpang (3 atau 4 lengan) dan input data pendekat
# ---------------------------------------------------------------
nama_pendekat = {"U": "Utara", "T": "Timur", "S": "Selatan", "B": "Barat"}
SEMUA_PENDEKAT = ["U", "T", "S", "B"]


def reset_hasil():
    """Hapus hasil lama saat jenis simpang diganti, agar tabel tidak membingungkan."""
    st.session_state.pop("hasil", None)


judul_bagian("Jenis Simpang")
jenis = st.radio(
    "Pilih jenis simpang",
    ["Simpang 4 lengan", "Simpang 3 lengan"],
    horizontal=True,
    key="jenis_simpang",
    on_change=reset_hasil,
)

if jenis == "Simpang 3 lengan":
    lengan_kosong = st.selectbox(
        "Lengan yang tidak ada",
        SEMUA_PENDEKAT,
        index=1,
        format_func=lambda k: f"{k} ({nama_pendekat[k]})",
        key="lengan_kosong",
        on_change=reset_hasil,
    )
    pendekat_aktif = [k for k in SEMUA_PENDEKAT if k != lengan_kosong]
    st.caption(f"Pendekat yang dianalisis: {', '.join(pendekat_aktif)} (3 fase sinyal)")
else:
    pendekat_aktif = list(SEMUA_PENDEKAT)
    st.caption("Pendekat yang dianalisis: U, T, S, B (4 fase sinyal)")

judul_bagian("Data Pendekat (dalam kendaraan/jam)")
st.info("Masukkan jumlah kendaraan asli. Sistem akan otomatis mengonversinya ke SMP menggunakan faktor EMP PKJI 2023.")

data_input = {}
kolom = st.columns(len(pendekat_aktif))

for col, kode in zip(kolom, pendekat_aktif):
    with col:
        st.markdown(f"**Pendekat {kode}** ({nama_pendekat[kode]})")
        
        mc = st.number_input(f"Motor (MC) - {kode}", min_value=0, value=800, step=50, key=f"mc_{kode}")
        lv = st.number_input(f"Mobil (LV) - {kode}", min_value=0, value=300, step=50, key=f"lv_{kode}")
        hv = st.number_input(f"Truk/Bus (HV) - {kode}", min_value=0, value=50, step=10, key=f"hv_{kode}")
        We = st.number_input(
            f"Lebar We - {kode} (m)",
            min_value=0.1,
            value=7.0,
            step=0.1,
            key=f"We_{kode}",
        )
        
        # Simpan data mentah ke dictionary
        data_input[kode] = {"MC": mc, "LV": lv, "HV": hv, "We": We}

# ---------------------------------------------------------------
# 4. Tombol hitung
# ---------------------------------------------------------------
hitung = st.button("Hitung Kinerja Simpang", type="primary", key="btn_hitung")

def warnai_status(nilai):
    if nilai == "MACET / JENUH":
        return "color: red; font-weight: bold"
    return ""

# ---------------------------------------------------------------
# 5. Proses perhitungan & tampilkan hasil
# ---------------------------------------------------------------
if hitung:
    if g > Co:
        st.error("Waktu hijau (g) tidak boleh lebih besar dari waktu siklus (Co).")
        st.session_state.pop("hasil", None)
    else:
        baris = []
        try:
            for kode, d in data_input.items():
                # 1. Konversi kendaraan ke SMP
                Q_smp = konversi_ke_smp(d["MC"], d["LV"], d["HV"])

                # 2. Hitung Kinerja
                So = hitung_arus_jenuh_dasar(d["We"])
                S = hitung_arus_jenuh(So, Fsf, Fg, Fp, Fuk)
                C = hitung_kapasitas(S, g, Co)
                DS = hitung_derajat_kejenuhan(Q_smp, C)
                status = tentukan_status(DS)

                baris.append(
                    {
                        "Pendekat": kode,
                        "Total Kendaraan": d["MC"] + d["LV"] + d["HV"],
                        "Volume (SMP)": Q_smp,
                        "We": d["We"],
                        "Kapasitas (C)": C,
                        "Derajat Kejenuhan (DS)": DS,
                        "Status": status,
                    }
                )
        except ValueError as e:
            st.error(f"Input tidak valid: {e}")
            baris = []

        if baris:
            # Simpan hasil di session_state supaya tidak hilang saat tombol unduh ditekan
            st.session_state["hasil"] = {
                "df": pd.DataFrame(baris),
                "excel": buat_excel(data_input, Co, g, Fsf, Fg, Fp, Fuk, jenis_simpang=jenis),
                "komposisi": {
                    "MC": sum(d["MC"] for d in data_input.values()),
                    "LV": sum(d["LV"] for d in data_input.values()),
                    "HV": sum(d["HV"] for d in data_input.values()),
                },
                "Co": Co,
                "g": g,
            }
        else:
            st.session_state.pop("hasil", None)

if "hasil" in st.session_state:
    hasil = st.session_state["hasil"]
    df = hasil["df"]
    jumlah_jenuh = int((df["Status"] == "MACET / JENUH").sum())
    baris_maks = df.loc[df["Derajat Kejenuhan (DS)"].idxmax()]

    # ---- Kartu ringkasan ----
    judul_bagian("Ringkasan Kinerja Simpang")
    kartu_kpi(
        [
            {"ikon": "🚗", "nilai": f"{df['Volume (SMP)'].sum():,.0f}", "label": "Total Volume (smp/jam)"},
            {
                "ikon": "📈",
                "nilai": f"{baris_maks['Derajat Kejenuhan (DS)']:.2f}",
                "label": f"DS tertinggi (Pendekat {baris_maks['Pendekat']})",
                "bahaya": baris_maks["Derajat Kejenuhan (DS)"] >= 0.85,
            },
            {
                "ikon": "⚠️",
                "nilai": f"{jumlah_jenuh} / {len(df)}",
                "label": "Pendekat MACET / JENUH",
                "bahaya": jumlah_jenuh > 0,
            },
            {"ikon": "⏱️", "nilai": f"{hasil['Co']:.0f} d", "label": f"Waktu siklus (hijau {hasil['g']:.0f} d)"},
        ]
    )

    # ---- Tabel hasil ----
    styler = df.style.format(
        {
            "Total Kendaraan": "{:.0f}",
            "Volume (SMP)": "{:.1f}",
            "We": "{:.1f}",
            "Kapasitas (C)": "{:.0f}",
            "Derajat Kejenuhan (DS)": "{:.3f}",
        }
    )
    terapkan = getattr(styler, "map", None) or styler.applymap
    styler = terapkan(warnai_status, subset=["Status"])

    judul_bagian("Hasil Analisis")
    st.caption("Hasil berdasarkan input saat tombol 'Hitung Kinerja Simpang' terakhir ditekan.")
    st.dataframe(styler, use_container_width=True, hide_index=True)

    # ---- Tombol unduh Excel ----
    st.download_button(
        label="Unduh Hasil (Excel)",
        data=hasil["excel"],
        file_name="hasil_analisis_simpang_apill.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_excel",
    )

    # ---- Grafik: batang DS (kiri) dan donat komposisi kendaraan (kanan) ----
    kol_grafik, kol_donat = st.columns([3, 2])

    with kol_grafik:
        fig = px.bar(
            df,
            x="Pendekat",
            y="Derajat Kejenuhan (DS)",
            title="Tingkat Kejenuhan Simpang Arteri Primer",
            labels={"Pendekat": "Pendekat", "Derajat Kejenuhan (DS)": "Nilai DS"},
            text_auto=".3f",
            color_discrete_sequence=[PALET_GRAFIK[0]],
        )
        fig.add_hline(
            y=0.85,
            line_dash="dash",
            line_color="red",
            annotation_text="Batas DS = 0.85",
            annotation_position="top left",
            annotation_font_color="red",
        )
        batas_atas = max(1.0, df["Derajat Kejenuhan (DS)"].max() * 1.15)
        fig.update_yaxes(range=[0, batas_atas])
        fig.update_xaxes(categoryorder="array", categoryarray=list(df["Pendekat"]))
        st.plotly_chart(rapikan_grafik(fig), use_container_width=True)

    with kol_donat:
        komp = hasil["komposisi"]
        fig_donat = px.pie(
            names=["Motor (MC)", "Mobil (LV)", "Truk/Bus (HV)"],
            values=[komp["MC"], komp["LV"], komp["HV"]],
            hole=0.55,
            title="Komposisi Kendaraan (kend/jam)",
            color_discrete_sequence=PALET_GRAFIK,
        )
        fig_donat.update_traces(textinfo="percent")
        st.plotly_chart(rapikan_grafik(fig_donat), use_container_width=True)

    if jumlah_jenuh:
        st.warning(f"{jumlah_jenuh} dari {len(df)} pendekat berstatus MACET / JENUH (DS ≥ 0.85).")
    else:
        st.success("Semua pendekat berstatus OK / IDEAL (DS < 0.85).")

# ==========================================
# BAGIAN ANIMASI SIMPANG APILL (3 ATAU 4 FASE)
# ==========================================
st.divider()
n_fase = len(pendekat_aktif)
judul_bagian(f"Simulasi Lalu Lintas {jenis} APILL ({n_fase} Fase, Lampu 3 Warna)")
st.write(
    f"Lampu menyala bergantian {' → '.join(pendekat_aktif)}. Kendaraan berhenti di garis stop saat merah/kuning, "
    "lalu jalan saat hijau, dan bisa lurus, belok kiri, atau belok kanan. "
    "Kedatangan kendaraan mengikuti volume MC, LV, dan HV yang Anda isi di atas."
)

with st.expander("Pengaturan simulasi", expanded=False):
    kol_a, kol_b = st.columns(2)
    kuning = kol_a.number_input(
        "Waktu kuning (detik)", min_value=1.0, max_value=10.0, value=3.0, step=0.5, key="anim_kuning"
    )
    semua_merah = kol_b.number_input(
        "Waktu semua merah (detik)", min_value=0.0, max_value=10.0, value=2.0, step=0.5, key="anim_ar"
    )
    persen_kiri = kol_a.slider("Kendaraan belok kiri (%)", 0, 50, 25, key="anim_kiri")
    persen_kanan = kol_b.slider("Kendaraan belok kanan (%)", 0, 50, 25, key="anim_kanan")
    sesuaikan_co = st.checkbox(
        "Sesuaikan waktu hijau agar total siklus = Co (sidebar)",
        value=False,
        key="anim_sesuai_co",
        help=f"Jika dimatikan, hijau tiap fase = g di sidebar, sehingga siklus = {n_fase} x (g + kuning + semua merah).",
    )

# Waktu hijau yang dipakai animasi
if sesuaikan_co:
    g_anim = Co / n_fase - kuning - semua_merah
else:
    g_anim = g

if g_anim < 3:
    st.error(
        "Waktu hijau untuk animasi terlalu kecil (< 3 detik). "
        "Perbesar Co, atau kurangi waktu kuning / semua merah."
    )
else:
    hijau_anim = [g_anim] * n_fase
    siklus_anim = hitung_waktu_siklus(hijau_anim, kuning, semua_merah)
    st.caption(
        f"Hijau tiap fase = {g_anim:.0f} d, kuning = {kuning:.1f} d, semua merah = {semua_merah:.1f} d "
        f"→ siklus simulasi = {siklus_anim:.0f} d (Co di sidebar = {Co:.0f} d)."
    )
    if not sesuaikan_co and abs(siklus_anim - Co) > 1:
        st.info(
            f"Pada {n_fase} fase berurutan, siklus = {n_fase} x (g + kuning + semua merah), sehingga berbeda dari Co di sidebar. "
            "Centang 'Sesuaikan waktu hijau agar total siklus = Co' jika ingin siklus simulasi sama dengan Co."
        )

    html_animasi = bangun_html_animasi(
        hijau=hijau_anim,
        kuning=kuning,
        semua_merah=semua_merah,
        volume=data_input,
        p_kiri=persen_kiri / 100,
        p_kanan=persen_kanan / 100,
        aktif=pendekat_aktif,
    )
    components.html(html_animasi, height=720, scrolling=True)
