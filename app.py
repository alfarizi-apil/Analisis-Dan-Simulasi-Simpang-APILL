"""
app.py
Antarmuka Streamlit untuk Analisis Dan Simulasi Simpang APILL.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from animasi_simpang import bangun_html_animasi, hitung_waktu_siklus
from kalkulasi import (
    hitung_arus_jenuh_dasar,
    hitung_arus_jenuh,
    hitung_kapasitas,
    hitung_derajat_kejenuhan,
    tentukan_status,
    konversi_ke_smp, # Tambahan fungsi baru
)

st.set_page_config(page_title="Analisis Dan Simulasi Simpang APILL", layout="wide")

# ---------------------------------------------------------------
# 1. Judul
# ---------------------------------------------------------------
st.title("Analisis Dan Simulasi Simpang APILL")
st.caption("Berdasarkan pedoman PKJI 2023 | Input Berbasis Jenis Kendaraan")

# ---------------------------------------------------------------
# 2. Sidebar: parameter umum
# ---------------------------------------------------------------
st.sidebar.header("Parameter Umum")

Co = st.sidebar.number_input("Waktu Siklus, Co (detik)", min_value=1.0, value=100.0, step=1.0, key="co_in")
g = st.sidebar.number_input("Waktu Hijau, g (detik)", min_value=0.0, value=35.0, step=1.0, key="g_in")

st.sidebar.subheader("Faktor Koreksi")
Fsf = st.sidebar.number_input("Fsf (hambatan samping)", min_value=0.0, value=0.90, step=0.01, format="%.2f", key="fsf_in")
Fg = st.sidebar.number_input("Fg (kelandaian)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key="fg_in")
Fp = st.sidebar.number_input("Fp (parkir)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key="fp_in")
Fuk = st.sidebar.number_input("Fuk (ukuran kota)", min_value=0.0, value=1.00, step=0.01, format="%.2f", key="fuk_in")

# ---------------------------------------------------------------
# 3. Input data pendekat (4 kolom: U, T, S, B)
# ---------------------------------------------------------------
st.subheader("Data Pendekat (dalam kendaraan/jam)")
st.info("Masukkan jumlah kendaraan asli. Sistem akan otomatis mengonversinya ke SMP menggunakan faktor EMP PKJI 2023.")

nama_pendekat = {"U": "Utara", "T": "Timur", "S": "Selatan", "B": "Barat"}

data_input = {}
kolom = st.columns(4)

for col, kode in zip(kolom, ["U", "T", "S", "B"]):
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
            df = pd.DataFrame(baris)

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

            st.subheader("Hasil Analisis")
            st.dataframe(styler, use_container_width=True, hide_index=True)

            # ---- Grafik batang DS per pendekat ----
            fig = px.bar(
                df,
                x="Pendekat",
                y="Derajat Kejenuhan (DS)",
                title="Tingkat Kejenuhan Simpang Arteri Primer",
                labels={"Pendekat": "Pendekat", "Derajat Kejenuhan (DS)": "Nilai DS"},
                text_auto=".3f",
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
            fig.update_xaxes(categoryorder="array", categoryarray=["U", "T", "S", "B"])

            st.plotly_chart(fig, use_container_width=True)

            jumlah_jenuh = (df["Status"] == "MACET / JENUH").sum()
            if jumlah_jenuh:
                st.warning(f"{jumlah_jenuh} dari 4 pendekat berstatus MACET / JENUH (DS ≥ 0.85).")
            else:
                st.success("Semua pendekat berstatus OK / IDEAL (DS < 0.85).")

# ==========================================
# BAGIAN ANIMASI SIMPANG APILL (4 FASE)
# ==========================================
st.divider()
st.subheader("Simulasi Lalu Lintas Simpang APILL (4 Fase, Lampu 3 Warna)")
st.write(
    "Lampu menyala bergantian U → T → S → B. Kendaraan berhenti di garis stop saat merah/kuning, "
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
        help="Jika dimatikan, hijau tiap fase = g di sidebar, sehingga siklus = 4 x (g + kuning + semua merah).",
    )

# Waktu hijau yang dipakai animasi
if sesuaikan_co:
    g_anim = Co / 4 - kuning - semua_merah
else:
    g_anim = g

if g_anim < 3:
    st.error(
        "Waktu hijau untuk animasi terlalu kecil (< 3 detik). "
        "Perbesar Co, atau kurangi waktu kuning / semua merah."
    )
else:
    hijau_anim = [g_anim] * 4
    siklus_anim = hitung_waktu_siklus(hijau_anim, kuning, semua_merah)
    st.caption(
        f"Hijau tiap fase = {g_anim:.0f} d, kuning = {kuning:.1f} d, semua merah = {semua_merah:.1f} d "
        f"→ siklus simulasi = {siklus_anim:.0f} d (Co di sidebar = {Co:.0f} d)."
    )
    if not sesuaikan_co and abs(siklus_anim - Co) > 1:
        st.info(
            "Pada 4 fase berurutan, siklus = 4 x (g + kuning + semua merah), sehingga berbeda dari Co di sidebar. "
            "Centang 'Sesuaikan waktu hijau agar total siklus = Co' jika ingin siklus simulasi sama dengan Co."
        )

    html_animasi = bangun_html_animasi(
        hijau=hijau_anim,
        kuning=kuning,
        semua_merah=semua_merah,
        volume=data_input,
        p_kiri=persen_kiri / 100,
        p_kanan=persen_kanan / 100,
    )
    components.html(html_animasi, height=720, scrolling=True)
