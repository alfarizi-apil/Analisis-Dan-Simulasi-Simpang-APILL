"""
app.py
AA SIPIL - Analisis dan Animasi Simpang APILL (PKJI 2023).
Antarmuka Streamlit.

Fitur:
  - Pilihan simpang 3 lengan atau 4 lengan
  - Satu pendekat = satu fase; waktu hijau, kuning, dan semua merah BOLEH BERBEDA tiap fase
  - Data tiap pendekat diisi lewat tabel (volume MC/LV/HV, lebar, Fsf, Fg, Fp, % belok kiri/kanan)
  - Hasil kondisi EKSISTING (hijau diisi) dan USULAN PKJI (siklus dan hijau dihitung otomatis)
  - Animasi lalu lintas, grafik DS, dan unduh hasil dalam Excel
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from animasi_simpang import bangun_html_animasi, hitung_waktu_siklus
from ekspor_excel import buat_excel
from kalkulasi import BATAS_DS, RENTANG_SIKLUS, analisis_simpang, tujuan_belok
from tampilan import (
    PALET_GRAFIK,
    header_halaman,
    judul_bagian,
    kartu_info,
    kartu_kpi,
    rapikan_grafik,
    sidebar_brand,
    terapkan_tema,
)

_IKON = Path(__file__).parent / "assets" / "logo_kecil.png"
st.set_page_config(
    page_title="AA SIPIL - Analisis dan Animasi Simpang APILL",
    page_icon=str(_IKON) if _IKON.exists() else "🚦",
    layout="wide",
)
terapkan_tema()

header_halaman(
    "Analisis Simpang <b>APILL</b> Jalan Arteri Primer",
    "Berdasarkan pedoman PKJI 2023. Satu pendekat = satu fase, waktu sinyal boleh berbeda tiap fase.",
    fitur=[
        ("📐", "Sesuai rumus PKJI 2023"),
        ("⏱️", "Kondisi eksisting dan usulan"),
        ("🎬", "Animasi lalu lintas"),
        ("📊", "Unduh hasil ke Excel"),
    ],
)

# ---------------------------------------------------------------
# Sidebar: parameter umum
# ---------------------------------------------------------------
sidebar_brand()
st.sidebar.header("Parameter Umum")
Fuk = st.sidebar.number_input(
    "Fuk (ukuran kota)", min_value=0.5, max_value=1.5, value=1.00, step=0.01, format="%.2f", key="fuk_in"
)
hitung_usulan = st.sidebar.checkbox("Hitung juga waktu sinyal usulan PKJI", value=True, key="usulan_in")
st.sidebar.caption(
    "Fsf, Fg, Fp, persentase belok, serta waktu hijau, kuning, dan semua merah "
    "diisi per pendekat pada tabel di halaman utama."
)

# ---------------------------------------------------------------
# Jenis simpang
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
    kunci_tabel = "3" + lengan_kosong
    st.caption(f"Pendekat yang dianalisis: {', '.join(pendekat_aktif)} (3 fase sinyal)")
else:
    pendekat_aktif = list(SEMUA_PENDEKAT)
    kunci_tabel = "4"
    st.caption("Pendekat yang dianalisis: U, T, S, B (4 fase sinyal)")

# ---------------------------------------------------------------
# Tabel input per pendekat
# ---------------------------------------------------------------
HIJAU_DEFAULT, KUNING_DEFAULT, MERAH_SEMUA_DEFAULT = 20, 3, 2


def tabel_awal(aktif):
    """Nilai awal kedua tabel; persentase belok disesuaikan dengan lengan yang ada."""
    data_a, data_b = [], []
    for k in aktif:
        t = tujuan_belok(k, aktif)
        if t["lurus"]:
            kiri, kanan = (25 if t["kiri"] else 0), (25 if t["kanan"] else 0)
        else:                                  # lengan buntu: hanya bisa belok kiri atau kanan
            kiri, kanan = 50, 50
        data_a.append({
            "Pendekat": k, "Motor (MC)": 800, "Mobil (LV)": 300, "Truk/Bus (HV)": 50,
            "We (m)": 7.0, "Fsf": 0.90, "Fg": 1.00, "Fp": 1.00,
            "Belok kiri (%)": float(kiri), "Belok kanan (%)": float(kanan),
        })
        data_b.append({
            "Pendekat": k, "Hijau g (d)": float(HIJAU_DEFAULT),
            "Kuning (d)": float(KUNING_DEFAULT), "Semua merah (d)": float(MERAH_SEMUA_DEFAULT),
        })
    return pd.DataFrame(data_a), pd.DataFrame(data_b)


df_a0, df_b0 = tabel_awal(pendekat_aktif)
angka = st.column_config.NumberColumn

judul_bagian("Data Lalu Lintas dan Geometri Tiap Pendekat")
kartu_info(
    "Isi <b>jumlah kendaraan asli (kend/jam)</b>; sistem mengonversinya ke smp. Klik sel untuk mengubah nilai. "
    "Faktor Fsf, Fg, dan Fp serta persentase belok boleh berbeda untuk tiap pendekat. "
    "Pastikan nilai faktor diambil dari tabel PKJI 2023 sesuai kondisi lokasi."
)
df_a = st.data_editor(
    df_a0,
    key=f"tbl_a_{kunci_tabel}",
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    disabled=["Pendekat"],
    column_config={
        "Motor (MC)": angka("Motor (MC)", min_value=0, step=10, format="%d"),
        "Mobil (LV)": angka("Mobil (LV)", min_value=0, step=10, format="%d"),
        "Truk/Bus (HV)": angka("Truk/Bus (HV)", min_value=0, step=5, format="%d"),
        "We (m)": angka("We (m)", help="Lebar efektif pendekat", min_value=0.5, max_value=30.0, step=0.1, format="%.1f"),
        "Fsf": angka("Fsf", help="Faktor hambatan samping (FHS)", min_value=0.1, max_value=1.5, step=0.01, format="%.2f"),
        "Fg": angka("Fg", help="Faktor kelandaian", min_value=0.1, max_value=1.5, step=0.01, format="%.2f"),
        "Fp": angka("Fp", help="Faktor parkir", min_value=0.1, max_value=1.5, step=0.01, format="%.2f"),
        "Belok kiri (%)": angka("Belok kiri (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.0f"),
        "Belok kanan (%)": angka("Belok kanan (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.0f"),
    },
)

judul_bagian("Pengaturan Sinyal Tiap Fase")
st.caption(
    "Satu pendekat = satu fase. Waktu hijau, kuning, dan semua merah boleh berbeda untuk tiap fase. "
    "Waktu siklus (Co) tidak diisi: dihitung otomatis = jumlah hijau + kuning + semua merah seluruh fase."
)
df_b = st.data_editor(
    df_b0,
    key=f"tbl_b_{kunci_tabel}",
    hide_index=True,
    use_container_width=True,
    num_rows="fixed",
    disabled=["Pendekat"],
    column_config={
        "Hijau g (d)": angka("Hijau g (d)", min_value=1.0, max_value=200.0, step=1.0, format="%.1f"),
        "Kuning (d)": angka("Kuning (d)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
        "Semua merah (d)": angka("Semua merah (d)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
    },
)


def susun_data(tabel_a, tabel_b):
    """Gabungkan dua tabel menjadi dict data per pendekat, sekaligus memvalidasi isiannya."""
    kesalahan, catatan = [], []
    if tabel_a.isna().any().any() or tabel_b.isna().any().any():
        return None, ["Ada sel yang kosong pada tabel. Lengkapi semua sel terlebih dahulu."], []

    baris_a = {r["Pendekat"]: r for r in tabel_a.to_dict("records")}
    baris_b = {r["Pendekat"]: r for r in tabel_b.to_dict("records")}
    data = {}
    for k in pendekat_aktif:
        a, b = baris_a[k], baris_b[k]
        kiri, kanan = float(a["Belok kiri (%)"]), float(a["Belok kanan (%)"])
        t = tujuan_belok(k, pendekat_aktif)
        if kiri + kanan > 100:
            kesalahan.append(f"Pendekat {k}: belok kiri + belok kanan tidak boleh lebih dari 100%.")
        if kiri > 0 and not t["kiri"]:
            kesalahan.append(f"Pendekat {k}: tidak ada lengan tujuan untuk belok kiri pada simpang ini (isi 0).")
        if kanan > 0 and not t["kanan"]:
            kesalahan.append(f"Pendekat {k}: tidak ada lengan tujuan untuk belok kanan pada simpang ini (isi 0).")
        if not t["lurus"] and abs(kiri + kanan - 100) > 0.5:
            catatan.append(f"Pendekat {k} tidak punya arah lurus; belok kiri + kanan sebaiknya 100%.")
        data[k] = {
            "MC": float(a["Motor (MC)"]), "LV": float(a["Mobil (LV)"]), "HV": float(a["Truk/Bus (HV)"]),
            "We": float(a["We (m)"]), "Fsf": float(a["Fsf"]), "Fg": float(a["Fg"]), "Fp": float(a["Fp"]),
            "p_kiri": kiri, "p_kanan": kanan,
            "g": float(b["Hijau g (d)"]), "kuning": float(b["Kuning (d)"]), "ms": float(b["Semua merah (d)"]),
        }
    return (None if kesalahan else data), kesalahan, catatan


hitung = st.button("Hitung Kinerja Simpang", type="primary")


def tanda_input():
    """Sidik jari seluruh input; dipakai untuk mendeteksi hasil yang sudah tidak sesuai isian."""
    return repr((df_a.round(6).to_dict("records"), df_b.round(6).to_dict("records"),
                 Fuk, hitung_usulan, jenis, tuple(pendekat_aktif)))


def warnai_status(nilai):
    """Teks merah tebal untuk status MACET / JENUH."""
    if nilai == "MACET / JENUH":
        return "color: red; font-weight: bold"
    return ""


def gaya_tabel(df, format_kolom):
    """Tabel Pandas dengan format angka dan status berwarna merah."""
    styler = df.style.format(format_kolom)
    terapkan = getattr(styler, "map", None) or styler.applymap
    return terapkan(warnai_status, subset=["Status"])


# ---------------------------------------------------------------
# Proses perhitungan
# ---------------------------------------------------------------
if hitung:
    data_hitung, kesalahan, catatan_input = susun_data(df_a, df_b)
    if kesalahan:
        for pesan in kesalahan:
            st.error(pesan)
        st.session_state.pop("hasil", None)
    else:
        try:
            hasil_analisis = analisis_simpang(data_hitung, Fuk, hitung_usulan)
        except ValueError as e:
            st.error(f"Input tidak valid: {e}")
            st.session_state.pop("hasil", None)
        else:
            st.session_state["hasil"] = {
                "analisis": hasil_analisis,
                "data": data_hitung,
                "aktif": list(pendekat_aktif),
                "jenis": jenis,
                "tanda": tanda_input(),
                "catatan_input": catatan_input,
                "excel": buat_excel(data_hitung, Fuk, jenis_simpang=jenis, sertakan_usulan=hitung_usulan),
                "komposisi": {
                    "MC": sum(d["MC"] for d in data_hitung.values()),
                    "LV": sum(d["LV"] for d in data_hitung.values()),
                    "HV": sum(d["HV"] for d in data_hitung.values()),
                },
            }

# ---------------------------------------------------------------
# Tampilan hasil
# ---------------------------------------------------------------
if "hasil" in st.session_state:
    hs = st.session_state["hasil"]
    an = hs["analisis"]
    eks = an["eksisting"]
    usl = an["usulan"]
    usl_ok = bool(usl and usl["layak"])

    if hs.get("tanda") != tanda_input():
        st.warning("Isian di atas sudah berubah sejak perhitungan terakhir. "
                   "Tekan 'Hitung Kinerja Simpang' agar hasil di bawah sesuai isian terbaru.")

    df_eks = pd.DataFrame(
        [
            {
                "Pendekat": b["kode"], "Q (smp/jam)": b["Q"], "We (m)": b["We"], "J (smp/jam hijau)": b["J"],
                "Rq/J": b["RqJ"], "Hijau g (d)": b["g"], "Kuning (d)": b["kuning"], "Semua merah (d)": b["ms"],
                "Kapasitas C": b["C"], "DS": b["DS"], "Status": b["status"],
            }
            for b in eks["pendekat"]
        ]
    )
    jumlah_jenuh = int((df_eks["Status"] == "MACET / JENUH").sum())
    baris_maks = df_eks.loc[df_eks["DS"].idxmax()]

    # ---- Kartu ringkasan ----
    judul_bagian("Ringkasan Kinerja Simpang")
    kartu = [
        {"ikon": "🚗", "nilai": f"{df_eks['Q (smp/jam)'].sum():,.0f}", "label": "Total Volume (smp/jam)"},
        {
            "ikon": "📈",
            "nilai": f"{baris_maks['DS']:.2f}",
            "label": f"DS tertinggi eksisting (Pendekat {baris_maks['Pendekat']})",
            "bahaya": baris_maks["DS"] >= BATAS_DS,
        },
        {
            "ikon": "⚠️",
            "nilai": f"{jumlah_jenuh} / {len(df_eks)}",
            "label": "Pendekat MACET / JENUH (eksisting)",
            "bahaya": jumlah_jenuh > 0,
        },
        {"ikon": "⏱️", "nilai": f"{eks['Co']:.0f} d", "label": "Siklus eksisting (hijau + WHH)"},
    ]
    if usl_ok:
        kartu.append({"ikon": "🧮", "nilai": f"{usl['Co']:.0f} d", "label": "Siklus usulan PKJI"})
    kartu_kpi(kartu)

    # ---- Peringatan ----
    for pesan in hs["catatan_input"] + an["peringatan"]:
        st.warning(pesan)
    if usl and not usl_ok:
        st.error(usl["pesan"])

    # ---- Tabel eksisting ----
    judul_bagian("Hasil Kondisi Eksisting (Waktu Hijau Sesuai Isian)")
    st.caption("Hasil berdasarkan input saat tombol 'Hitung Kinerja Simpang' terakhir ditekan.")
    st.dataframe(
        gaya_tabel(
            df_eks,
            {
                "Q (smp/jam)": "{:.1f}", "We (m)": "{:.1f}", "J (smp/jam hijau)": "{:.0f}", "Rq/J": "{:.3f}",
                "Hijau g (d)": "{:.1f}", "Kuning (d)": "{:.1f}", "Semua merah (d)": "{:.1f}",
                "Kapasitas C": "{:.0f}", "DS": "{:.3f}",
            },
        ),
        use_container_width=True,
        hide_index=True,
    )

    # ---- Tabel usulan ----
    df_usl = None
    if usl_ok:
        judul_bagian("Usulan Waktu Sinyal Menurut PKJI 2023")
        df_usl = pd.DataFrame(
            [
                {
                    "Pendekat": b["kode"], "Rq/J": b["RqJ"], "Rasio fase": b["RF"],
                    "Hijau eksisting (d)": e["g"], "Hijau usulan (d)": b["g"],
                    "Kapasitas C": b["C"], "DS": b["DS"], "Status": b["status"],
                }
                for b, e in zip(usl["pendekat"], eks["pendekat"])
            ]
        )
        st.dataframe(
            gaya_tabel(
                df_usl,
                {"Rq/J": "{:.3f}", "Rasio fase": "{:.3f}", "Hijau eksisting (d)": "{:.1f}",
                 "Hijau usulan (d)": "{:.1f}", "Kapasitas C": "{:.0f}", "DS": "{:.3f}"},
            ),
            use_container_width=True,
            hide_index=True,
        )

    # ---- Ringkasan simpang: eksisting vs usulan ----
    n_fase = len(hs["aktif"])
    lo, hi = RENTANG_SIKLUS.get(n_fase, (None, None))

    def teks_rentang(co):
        return "Dalam rentang" if lo <= co <= hi else "Di luar rentang"

    ring = [
        ("Waktu hijau hilang WHH (d)", f"{eks['WHH']:.1f}", f"{usl['WHH']:.1f}" if usl_ok else "-"),
        ("Rasio arus simpang IFR", f"{eks['IFR']:.3f}", f"{usl['IFR']:.3f}" if usl_ok else "-"),
        ("Waktu siklus (d)", f"{eks['Co']:.1f}", f"{usl['Co']:.1f}" if usl_ok else "-"),
        (f"Rentang layak {n_fase} fase ({lo}-{hi} d)", teks_rentang(eks["Co"]), teks_rentang(usl["Co"]) if usl_ok else "-"),
    ]
    judul_bagian("Ringkasan Simpang")
    st.dataframe(
        pd.DataFrame(ring, columns=["Parameter", "Eksisting", "Usulan PKJI"]),
        use_container_width=True,
        hide_index=True,
    )

    # ---- Tombol unduh Excel ----
    st.download_button(
        label="Unduh Hasil (Excel)",
        data=hs["excel"],
        file_name="hasil_analisis_simpang_apill.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_excel",
    )

    # ---- Grafik: DS eksisting vs usulan (kiri), komposisi kendaraan (kanan) ----
    kol_grafik, kol_donat = st.columns([3, 2])

    with kol_grafik:
        baris_grafik = [{"Pendekat": r["Pendekat"], "Skenario": "Eksisting", "DS": r["DS"]} for _, r in df_eks.iterrows()]
        if df_usl is not None:
            baris_grafik += [{"Pendekat": r["Pendekat"], "Skenario": "Usulan PKJI", "DS": r["DS"]} for _, r in df_usl.iterrows()]
        df_grafik = pd.DataFrame(baris_grafik)
        fig = px.bar(
            df_grafik,
            x="Pendekat",
            y="DS",
            color="Skenario",
            barmode="group",
            title="Tingkat Kejenuhan Simpang Arteri Primer",
            labels={"Pendekat": "Pendekat", "DS": "Nilai DS"},
            text_auto=".2f",
            color_discrete_sequence=PALET_GRAFIK,
        )
        fig.add_hline(
            y=BATAS_DS,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Batas DS = {BATAS_DS}",
            annotation_position="top left",
            annotation_font_color="red",
        )
        fig.update_yaxes(range=[0, max(1.0, df_grafik["DS"].max() * 1.15)])
        fig.update_xaxes(categoryorder="array", categoryarray=list(hs["aktif"]))
        st.plotly_chart(rapikan_grafik(fig), use_container_width=True)

    with kol_donat:
        komp = hs["komposisi"]
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
        st.warning(f"Kondisi eksisting: {jumlah_jenuh} dari {len(df_eks)} pendekat berstatus MACET / JENUH (DS ≥ {BATAS_DS}).")
    else:
        st.success(f"Kondisi eksisting: semua pendekat berstatus OK / IDEAL (DS < {BATAS_DS}).")

    # ===========================================================
    # ANIMASI SIMPANG APILL
    # ===========================================================
    judul_bagian(f"Animasi Lalu Lintas {hs['jenis']} APILL ({n_fase} Fase, Lampu 3 Warna)")
    st.write(
        f"Lampu menyala bergantian {' → '.join(hs['aktif'])} dengan waktu hijau, kuning, dan semua merah "
        "sesuai tabel di atas. Kendaraan berhenti di garis stop saat merah/kuning, lalu jalan saat hijau, "
        "dan bisa lurus, belok kiri, atau belok kanan sesuai persentase belok tiap pendekat."
    )
    opsi_anim = ["Eksisting"] + (["Usulan PKJI"] if usl_ok else [])
    pilihan_anim = st.radio(
        "Waktu sinyal yang disimulasikan",
        opsi_anim,
        horizontal=True,
        key=f"anim_sumber_{len(opsi_anim)}",
    )
    sumber = eks["pendekat"] if pilihan_anim == "Eksisting" else usl["pendekat"]
    hijau_anim = [b["g"] for b in sumber]
    kuning_anim = [b["kuning"] for b in sumber]
    merah_anim = [b["ms"] for b in sumber]
    siklus_anim = hitung_waktu_siklus(hijau_anim, kuning_anim, merah_anim)
    st.caption(
        f"Hijau tiap fase ({'/'.join(hs['aktif'])}): {' / '.join(f'{g:.0f}' for g in hijau_anim)} d "
        f"→ siklus simulasi = {siklus_anim:.0f} d."
    )

    html_animasi = bangun_html_animasi(
        hijau=hijau_anim,
        kuning=kuning_anim,
        semua_merah=merah_anim,
        volume=hs["data"],
        p_kiri=[hs["data"][k]["p_kiri"] / 100 for k in hs["aktif"]],
        p_kanan=[hs["data"][k]["p_kanan"] / 100 for k in hs["aktif"]],
        aktif=hs["aktif"],
    )
    components.html(html_animasi, height=720, scrolling=True)
else:
    st.caption("Isi tabel di atas, lalu tekan 'Hitung Kinerja Simpang' untuk melihat hasil, grafik, dan simulasi.")
