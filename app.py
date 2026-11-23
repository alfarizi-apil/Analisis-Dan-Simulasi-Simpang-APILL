"""
app.py
AA SIPIL - Analisis dan Animasi Simpang APILL (PKJI 2023), Jalan Arteri Primer.

Alur bertahap (lima halaman):
  1. Mulai    : panduan pemakai, pilih jenis simpang (3 atau 4 lengan), Fuk, opsi usulan
  2. Data     : tabel lalu lintas dan geometri, pengaturan sinyal tiap fase (termasuk urutan fase)
  3. Hasil    : kartu ringkasan, tabel, grafik, batang kejenuhan, langkah perhitungan
  4. Animasi  : simulasi lalu lintas (waktu sinyal eksisting atau usulan)
  5. Unduh    : kesimpulan otomatis, Excel, PDF, Word, CSV

Cara menjalankan:  streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from animasi_simpang import bangun_html_animasi, hitung_waktu_siklus
from ekspor_excel import buat_excel
from kalkulasi import BATAS_DS, RENTANG_SIKLUS, analisis_simpang, tujuan_belok
from komponen_ui import (
    bar_kejenuhan,
    kartu_fitur,
    legenda_kejenuhan,
    stepper,
    tampil_ilustrasi,
    terapkan_css_komponen,
)
from langkah import langkah_perhitungan
from laporan import buat_csv, buat_laporan_docx, buat_laporan_pdf, susun_kesimpulan
from panduan import tampilkan_panduan
from tampilan import (
    PALET_GRAFIK,
    header_halaman,
    judul_bagian,
    kartu_kpi,
    rapikan_grafik,
    sidebar_brand,
    terapkan_tema,
)

st.set_page_config(page_title="AA SIPIL - Analisis Simpang APILL", page_icon="🚦", layout="wide")
terapkan_tema()
terapkan_css_komponen()

NAMA_PENDEKAT = {"U": "Utara", "T": "Timur", "S": "Selatan", "B": "Barat"}
SEMUA_PENDEKAT = ["U", "T", "S", "B"]
NAMA_LANGKAH = ["Mulai", "Data", "Hasil Analisis", "Animasi", "Unduh"]
HIJAU_DEFAULT, KUNING_DEFAULT, MERAH_SEMUA_DEFAULT = 20, 3, 2

ss = st.session_state
ss.setdefault("langkah", 1)
ss.setdefault("visit", 0)
ss.setdefault("cfg", {"jenis": "Simpang 4 lengan", "lengan_kosong": "T", "Fuk": 1.00, "usulan": True})


# ======================================================================
# Fungsi bantu
# ======================================================================
def aktif_dari(jenis, lengan_kosong):
    """Daftar pendekat yang ada menurut jenis simpang."""
    if jenis == "Simpang 3 lengan":
        return [k for k in SEMUA_PENDEKAT if k != lengan_kosong]
    return list(SEMUA_PENDEKAT)


ss.setdefault("aktif", aktif_dari(ss["cfg"]["jenis"], ss["cfg"]["lengan_kosong"]))


def pindah(n):
    """Pindah ke halaman n lalu muat ulang."""
    if n == 2:
        ss["visit"] += 1            # editor tabel dibuat ulang dari data tersimpan
    ss["langkah"] = n
    st.rerun()


def mulai_ulang():
    """Hapus seluruh isian dan kembali ke halaman 1."""
    for kunci in list(ss.keys()):
        del ss[kunci]
    st.rerun()


def tombol_nav(label_kembali, label_lanjut, kunci):
    """Tombol Kembali dan Lanjut di bagian bawah halaman. Return: (klik_kembali, klik_lanjut)."""
    st.divider()
    kol_k, kol_tengah, kol_l = st.columns([2, 3, 2])
    kembali = lanjut = False
    if label_kembali:
        with kol_k:
            kembali = st.button(label_kembali, key=f"kembali_{kunci}")
    if label_lanjut:
        with kol_l:
            lanjut = st.button(label_lanjut, key=f"lanjut_{kunci}", type="primary")
    return kembali, lanjut


def tabel_awal(aktif):
    """Nilai awal kedua tabel; persentase belok disesuaikan dengan lengan yang ada."""
    data_a, data_b = [], []
    for i, k in enumerate(aktif, start=1):
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
            "Pendekat": k, "Fase ke-": i, "Hijau g (d)": float(HIJAU_DEFAULT),
            "Kuning (d)": float(KUNING_DEFAULT), "Semua merah (d)": float(MERAH_SEMUA_DEFAULT),
        })
    return pd.DataFrame(data_a), pd.DataFrame(data_b)


def urutan_dari_tabel(tabel_b):
    """Urutan pendekat menurut kolom 'Fase ke-'; None jika nomor fase tidak valid."""
    try:
        nomor = [float(v) for v in tabel_b["Fase ke-"]]
    except (TypeError, ValueError):
        return None
    n = len(nomor)
    if any(v != v for v in nomor) or any(abs(v - round(v)) > 1e-9 for v in nomor):
        return None
    nomor = [int(round(v)) for v in nomor]
    if sorted(nomor) != list(range(1, n + 1)):
        return None
    return [k for _, k in sorted(zip(nomor, list(tabel_b["Pendekat"])))]


def susun_data(tabel_a, tabel_b, aktif):
    """
    Gabungkan dua tabel menjadi dict data per pendekat dan validasi isiannya.
    Return: (data, urutan, daftar_kesalahan, daftar_catatan)
    """
    kesalahan, catatan = [], []
    if tabel_a.isna().any().any() or tabel_b.isna().any().any():
        return None, None, ["Ada sel yang kosong pada tabel. Lengkapi semua sel terlebih dahulu."], []

    urutan = urutan_dari_tabel(tabel_b)
    if urutan is None:
        kesalahan.append(f"Kolom 'Fase ke-' harus berisi bilangan bulat 1 sampai {len(aktif)} tanpa nomor yang sama.")

    baris_a = {r["Pendekat"]: r for r in tabel_a.to_dict("records")}
    baris_b = {r["Pendekat"]: r for r in tabel_b.to_dict("records")}
    data = {}
    for k in aktif:
        a, b = baris_a[k], baris_b[k]
        kiri, kanan = float(a["Belok kiri (%)"]), float(a["Belok kanan (%)"])
        t = tujuan_belok(k, aktif)
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
    return (None if kesalahan else data), urutan, kesalahan, catatan


def urut_baris(daftar, urutan):
    """Susun ulang daftar hasil (dict dengan kunci 'kode') sesuai urutan fase."""
    peta = {b["kode"]: b for b in daftar}
    return [peta[k] for k in urutan]


def warnai_status(nilai):
    """Teks merah tebal untuk status MACET / JENUH."""
    return "color: red; font-weight: bold" if nilai == "MACET / JENUH" else ""


def gaya_tabel(df, format_kolom):
    """Tabel Pandas dengan format angka dan status berwarna merah."""
    styler = df.style.format(format_kolom)
    terapkan = getattr(styler, "map", None) or styler.applymap
    return terapkan(warnai_status, subset=["Status"])


# ======================================================================
# Halaman 1 - Mulai (panduan + jenis simpang)
# ======================================================================
def halaman_mulai():
    cfg = ss["cfg"]
    tab_mulai, tab_panduan = st.tabs(["🚦 Mulai Analisis", "📖 Panduan Pemakai"])

    with tab_mulai:
        kartu_fitur([
            {"ikon": "📐", "judul": "Rumus PKJI 2023", "teks": "Kapasitas, DS, dan status tiap pendekat."},
            {"ikon": "⚖️", "judul": "Eksisting dan Usulan", "teks": "Bandingkan sinyal lapangan dengan hijau usulan."},
            {"ikon": "🎬", "judul": "Animasi Lalu Lintas", "teks": "Lihat antrean dan arus kendaraan secara visual."},
            {"ikon": "📄", "judul": "Unduh Laporan", "teks": "Excel, PDF, Word, dan CSV dengan kesimpulan."},
        ])
        judul_bagian("Langkah 1 dari 5 - Pilih Jenis Simpang")
        kiri, kanan = st.columns([3, 2])
        with kiri:
            opsi = ["Simpang 4 lengan", "Simpang 3 lengan"]
            jenis = st.radio("Pilih jenis simpang", opsi, index=opsi.index(cfg["jenis"]), horizontal=True, key="w_jenis")
            if jenis == "Simpang 3 lengan":
                lengan_kosong = st.selectbox(
                    "Lengan yang tidak ada",
                    SEMUA_PENDEKAT,
                    index=SEMUA_PENDEKAT.index(cfg["lengan_kosong"]),
                    format_func=lambda k: f"{k} ({NAMA_PENDEKAT[k]})",
                    key="w_lengan",
                )
            else:
                lengan_kosong = cfg["lengan_kosong"]
            aktif = aktif_dari(jenis, lengan_kosong)
            st.caption(f"Pendekat yang dianalisis: {', '.join(aktif)} ({len(aktif)} fase sinyal)")
            fuk = st.number_input(
                "Fuk (faktor ukuran kota)",
                min_value=0.5,
                max_value=1.5,
                value=float(cfg["Fuk"]),
                step=0.01,
                format="%.2f",
                key="w_fuk",
                help="Ambil dari tabel PKJI 2023 sesuai jumlah penduduk kota lokasi studi.",
            )
            usulan = st.checkbox(
                "Hitung juga waktu sinyal usulan PKJI",
                value=bool(cfg["usulan"]),
                key="w_usulan",
                help="Jika dicentang, siklus dan hijau dihitung otomatis dan dibandingkan dengan kondisi eksisting.",
            )
        with kanan:
            tampil_ilustrasi(aktif)
            st.caption("Huruf = kode pendekat. Garis putus-putus abu-abu = lengan yang tidak ada. Lalu lintas lajur kiri.")

        _, lanjut = tombol_nav(None, "Lanjut: Isi Data ›", "1")
        if lanjut:
            if aktif != ss.get("aktif"):               # jenis simpang berubah: siapkan tabel baru
                for kunci in ("df_a", "df_b", "df_aktif", "hasil"):
                    ss.pop(kunci, None)
            ss["cfg"] = {"jenis": jenis, "lengan_kosong": lengan_kosong, "Fuk": float(fuk), "usulan": bool(usulan)}
            ss["aktif"] = aktif
            pindah(2)

    with tab_panduan:
        tampilkan_panduan()


# ======================================================================
# Halaman 2 - Data
# ======================================================================
def halaman_data():
    cfg, aktif = ss["cfg"], ss["aktif"]
    if "df_a" not in ss or ss.get("df_aktif") != aktif:
        ss["df_a"], ss["df_b"] = tabel_awal(aktif)
        ss["df_aktif"] = list(aktif)

    angka = st.column_config.NumberColumn
    judul_bagian(f"Langkah 2 dari 5 - Data Lalu Lintas dan Geometri ({cfg['jenis']})")
    st.info(
        "Isi jumlah kendaraan asli (kend/jam); sistem mengonversinya ke SMP. Klik sel untuk mengubah nilai. "
        "Faktor Fsf, Fg, Fp dan persentase belok boleh berbeda tiap pendekat."
    )
    df_a = st.data_editor(
        ss["df_a"],
        key=f"tbl_a_{ss['visit']}",
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
        "Satu pendekat = satu fase. Ubah kolom 'Fase ke-' untuk mengatur urutan nyala lampu. Hijau, kuning, dan "
        "semua merah boleh berbeda tiap fase. Waktu siklus (Co) dihitung otomatis = jumlah hijau + kuning + semua merah."
    )
    df_b = st.data_editor(
        ss["df_b"],
        key=f"tbl_b_{ss['visit']}",
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Pendekat"],
        column_config={
            "Fase ke-": angka("Fase ke-", help="Urutan nyala hijau: 1 = pertama", min_value=1, max_value=4, step=1, format="%d"),
            "Hijau g (d)": angka("Hijau g (d)", min_value=1.0, max_value=200.0, step=1.0, format="%.1f"),
            "Kuning (d)": angka("Kuning (d)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
            "Semua merah (d)": angka("Semua merah (d)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
        },
    )

    urutan_kini = urutan_dari_tabel(df_b)
    with st.expander("Lihat urutan fase pada denah simpang"):
        if urutan_kini:
            tampil_ilustrasi(aktif, urutan_kini)
            st.caption("Lingkaran oranye = nomor fase. Urutan: " + " → ".join(urutan_kini))
        else:
            st.warning("Nomor 'Fase ke-' belum valid (harus 1 sampai jumlah lengan tanpa nomor yang sama).")

    kembali, lanjut = tombol_nav("‹ Kembali", "Hitung dan Lihat Hasil ›", "2")
    if kembali:
        ss["df_a"], ss["df_b"] = df_a, df_b          # simpan isian sebelum pindah
        pindah(1)
    if lanjut:
        ss["df_a"], ss["df_b"] = df_a, df_b
        data, urutan, kesalahan, catatan = susun_data(df_a, df_b, aktif)
        if kesalahan:
            for pesan in kesalahan:
                st.error(pesan)
            return
        try:
            analisis = analisis_simpang(data, cfg["Fuk"], cfg["usulan"])
        except ValueError as e:
            st.error(f"Input tidak valid: {e}")
            return
        ss["hasil"] = {
            "analisis": analisis,
            "data": data,
            "aktif": list(aktif),
            "urutan": urutan,
            "jenis": cfg["jenis"],
            "Fuk": cfg["Fuk"],
            "catatan_input": catatan,
            "excel": buat_excel(data, cfg["Fuk"], jenis_simpang=cfg["jenis"], sertakan_usulan=cfg["usulan"]),
            "komposisi": {
                "MC": sum(d["MC"] for d in data.values()),
                "LV": sum(d["LV"] for d in data.values()),
                "HV": sum(d["HV"] for d in data.values()),
            },
        }
        pindah(3)


# ======================================================================
# Halaman 3 - Hasil Analisis
# ======================================================================
def halaman_hasil():
    hs = ss["hasil"]
    an = hs["analisis"]
    eks, usl = an["eksisting"], an["usulan"]
    usl_ok = bool(usl and usl["layak"])
    urutan = hs["urutan"]
    n_fase = len(urutan)
    be = urut_baris(eks["pendekat"], urutan)
    bu = urut_baris(usl["pendekat"], urutan) if usl_ok else None

    df_eks = pd.DataFrame([
        {"Fase": i, "Pendekat": b["kode"], "Q (smp/jam)": b["Q"], "We (m)": b["We"], "J (smp/jam hijau)": b["J"],
         "Rq/J": b["RqJ"], "Hijau g (d)": b["g"], "Kuning (d)": b["kuning"], "Semua merah (d)": b["ms"],
         "Kapasitas C": b["C"], "DS": b["DS"], "Status": b["status"]}
        for i, b in enumerate(be, start=1)
    ])
    jumlah_jenuh = int((df_eks["Status"] == "MACET / JENUH").sum())
    baris_maks = df_eks.loc[df_eks["DS"].idxmax()]

    judul_bagian("Langkah 3 dari 5 - Hasil Analisis")
    kartu = [
        {"ikon": "🚗", "nilai": f"{df_eks['Q (smp/jam)'].sum():,.0f}", "label": "Total Volume (smp/jam)"},
        {"ikon": "📈", "nilai": f"{baris_maks['DS']:.2f}",
         "label": f"DS tertinggi eksisting (Pendekat {baris_maks['Pendekat']})", "bahaya": baris_maks["DS"] >= BATAS_DS},
        {"ikon": "⚠️", "nilai": f"{jumlah_jenuh} / {len(df_eks)}", "label": "Pendekat MACET / JENUH (eksisting)",
         "bahaya": jumlah_jenuh > 0},
        {"ikon": "⏱️", "nilai": f"{eks['Co']:.0f} d", "label": "Siklus eksisting (hijau + WHH)"},
    ]
    if usl_ok:
        kartu.append({"ikon": "🧮", "nilai": f"{usl['Co']:.0f} d", "label": "Siklus usulan PKJI"})
    kartu_kpi(kartu)

    for pesan in hs["catatan_input"] + an["peringatan"]:
        st.warning(pesan)
    if usl and not usl_ok:
        st.error(usl["pesan"])

    tab_tabel, tab_grafik, tab_langkah = st.tabs(["📋 Tabel dan Ringkasan", "📊 Grafik dan Kejenuhan", "🧮 Langkah Perhitungan"])

    # ---------------- Tab 1: tabel ----------------
    with tab_tabel:
        judul_bagian("Hasil Kondisi Eksisting (Waktu Hijau Sesuai Isian)")
        st.dataframe(
            gaya_tabel(df_eks, {
                "Q (smp/jam)": "{:.1f}", "We (m)": "{:.1f}", "J (smp/jam hijau)": "{:.0f}", "Rq/J": "{:.3f}",
                "Hijau g (d)": "{:.1f}", "Kuning (d)": "{:.1f}", "Semua merah (d)": "{:.1f}",
                "Kapasitas C": "{:.0f}", "DS": "{:.3f}",
            }),
            use_container_width=True, hide_index=True,
        )
        df_usl = None
        if usl_ok:
            judul_bagian("Usulan Waktu Sinyal Menurut PKJI 2023")
            df_usl = pd.DataFrame([
                {"Fase": i, "Pendekat": b["kode"], "Rq/J": b["RqJ"], "Rasio fase": b["RF"],
                 "Hijau eksisting (d)": e["g"], "Hijau usulan (d)": b["g"],
                 "Kapasitas C": b["C"], "DS": b["DS"], "Status": b["status"]}
                for i, (b, e) in enumerate(zip(bu, be), start=1)
            ])
            st.dataframe(
                gaya_tabel(df_usl, {"Rq/J": "{:.3f}", "Rasio fase": "{:.3f}", "Hijau eksisting (d)": "{:.1f}",
                                    "Hijau usulan (d)": "{:.1f}", "Kapasitas C": "{:.0f}", "DS": "{:.3f}"}),
                use_container_width=True, hide_index=True,
            )
        lo, hi = RENTANG_SIKLUS.get(n_fase, (0, 0))

        def teks_rentang(co):
            return "Dalam rentang" if lo <= co <= hi else "Di luar rentang"

        judul_bagian("Ringkasan Simpang")
        st.dataframe(
            pd.DataFrame([
                ("Waktu hijau hilang WHH (d)", f"{eks['WHH']:.1f}", f"{usl['WHH']:.1f}" if usl_ok else "-"),
                ("Rasio arus simpang IFR", f"{eks['IFR']:.3f}", f"{usl['IFR']:.3f}" if usl_ok else "-"),
                ("Waktu siklus (d)", f"{eks['Co']:.1f}", f"{usl['Co']:.1f}" if usl_ok else "-"),
                (f"Rentang layak {n_fase} fase ({lo}-{hi} d)", teks_rentang(eks["Co"]),
                 teks_rentang(usl["Co"]) if usl_ok else "-"),
            ], columns=["Parameter", "Eksisting", "Usulan PKJI"]),
            use_container_width=True, hide_index=True,
        )

    # ---------------- Tab 2: grafik dan kejenuhan ----------------
    with tab_grafik:
        judul_bagian("Visualisasi Kejenuhan Tiap Pendekat")
        legenda_kejenuhan(BATAS_DS)
        kol_e, kol_u = st.columns(2)
        with kol_e:
            bar_kejenuhan("Kondisi Eksisting", [{"kode": b["kode"], "ds": b["DS"], "status": b["status"]} for b in be], BATAS_DS)
        with kol_u:
            if usl_ok:
                bar_kejenuhan("Usulan PKJI", [{"kode": b["kode"], "ds": b["DS"], "status": b["status"]} for b in bu], BATAS_DS)
            else:
                st.info("Usulan PKJI tidak tersedia (tidak dipilih atau tidak dapat dihitung).")

        kol_grafik, kol_donat = st.columns([3, 2])
        with kol_grafik:
            baris_grafik = [{"Pendekat": b["kode"], "Skenario": "Eksisting", "DS": b["DS"]} for b in be]
            if usl_ok:
                baris_grafik += [{"Pendekat": b["kode"], "Skenario": "Usulan PKJI", "DS": b["DS"]} for b in bu]
            df_grafik = pd.DataFrame(baris_grafik)
            fig = px.bar(
                df_grafik, x="Pendekat", y="DS", color="Skenario", barmode="group",
                title="Tingkat Kejenuhan Simpang Arteri Primer",
                labels={"Pendekat": "Pendekat", "DS": "Nilai DS"}, text_auto=".2f",
                color_discrete_sequence=PALET_GRAFIK,
            )
            fig.add_hline(y=BATAS_DS, line_dash="dash", line_color="red", annotation_text=f"Batas DS = {BATAS_DS}",
                          annotation_position="top left", annotation_font_color="red")
            fig.update_yaxes(range=[0, max(1.0, df_grafik["DS"].max() * 1.15)])
            fig.update_xaxes(categoryorder="array", categoryarray=list(urutan))
            st.plotly_chart(rapikan_grafik(fig), use_container_width=True)
        with kol_donat:
            komp = hs["komposisi"]
            fig_donat = px.pie(
                names=["Motor (MC)", "Mobil (LV)", "Truk/Bus (HV)"], values=[komp["MC"], komp["LV"], komp["HV"]],
                hole=0.55, title="Komposisi Kendaraan (kend/jam)", color_discrete_sequence=PALET_GRAFIK,
            )
            fig_donat.update_traces(textinfo="percent")
            st.plotly_chart(rapikan_grafik(fig_donat), use_container_width=True)

        if jumlah_jenuh:
            st.warning(f"Kondisi eksisting: {jumlah_jenuh} dari {len(df_eks)} pendekat berstatus MACET / JENUH (DS ≥ {BATAS_DS}).")
        else:
            st.success(f"Kondisi eksisting: semua pendekat berstatus OK / IDEAL (DS < {BATAS_DS}).")

    # ---------------- Tab 3: langkah perhitungan ----------------
    with tab_langkah:
        judul_bagian("Langkah Perhitungan dengan Angka")
        st.caption("Pilih pendekat dan skenario untuk melihat setiap rumus beserta angka yang dimasukkan.")
        kol_p, kol_s = st.columns(2)
        with kol_p:
            pilih_kode = st.selectbox("Pendekat", urutan, key="lg_pendekat",
                                      format_func=lambda k: f"{k} ({NAMA_PENDEKAT[k]})")
        with kol_s:
            opsi_skenario = ["Eksisting"] + (["Usulan PKJI"] if usl_ok else [])
            pilih_skenario = st.radio("Skenario", opsi_skenario, horizontal=True, key=f"lg_skenario_{len(opsi_skenario)}")
        rincian = langkah_perhitungan(hs, pilih_kode, pilih_skenario)
        st.table(pd.DataFrame([
            {"No": r["no"], "Besaran": r["besaran"], "Rumus": r["rumus"], "Substitusi": r["substitusi"], "Hasil": r["hasil"]}
            for r in rincian
        ]).set_index("No"))

    kembali, lanjut = tombol_nav("‹ Kembali ke Data", "Lanjut: Animasi ›", "3")
    if kembali:
        pindah(2)
    if lanjut:
        pindah(4)


# ======================================================================
# Halaman 4 - Animasi
# ======================================================================
def halaman_animasi():
    hs = ss["hasil"]
    an = hs["analisis"]
    eks, usl = an["eksisting"], an["usulan"]
    usl_ok = bool(usl and usl["layak"])
    urutan = hs["urutan"]

    judul_bagian(f"Langkah 4 dari 5 - Simulasi Lalu Lintas {hs['jenis']} ({len(urutan)} Fase)")
    st.write(
        f"Lampu menyala bergantian {' → '.join(urutan)} dengan waktu hijau, kuning, dan semua merah sesuai tabel. "
        "Kendaraan berhenti di garis stop saat merah atau kuning, lalu jalan saat hijau, dan bisa lurus, belok kiri, "
        "atau belok kanan sesuai persentase belok tiap pendekat. Antrean panjang menandakan DS tinggi."
    )
    opsi = ["Eksisting"] + (["Usulan PKJI"] if usl_ok else [])
    pilihan = st.radio("Waktu sinyal yang disimulasikan", opsi, horizontal=True, key=f"anim_sumber_{len(opsi)}")
    sumber = urut_baris(eks["pendekat"] if pilihan == "Eksisting" else usl["pendekat"], urutan)
    hijau = [b["g"] for b in sumber]
    kuning = [b["kuning"] for b in sumber]
    merah = [b["ms"] for b in sumber]
    siklus = hitung_waktu_siklus(hijau, kuning, merah)
    st.caption(
        f"Hijau tiap fase ({'/'.join(urutan)}): {' / '.join(f'{g:.0f}' for g in hijau)} d → siklus simulasi = {siklus:.0f} d."
    )
    html = bangun_html_animasi(
        hijau=hijau,
        kuning=kuning,
        semua_merah=merah,
        volume=hs["data"],
        p_kiri=[hs["data"][k]["p_kiri"] / 100 for k in urutan],
        p_kanan=[hs["data"][k]["p_kanan"] / 100 for k in urutan],
        aktif=urutan,
    )
    components.html(html, height=720, scrolling=True)

    kembali, lanjut = tombol_nav("‹ Kembali ke Hasil", "Lanjut: Unduh Hasil ›", "4")
    if kembali:
        pindah(3)
    if lanjut:
        pindah(5)


# ======================================================================
# Halaman 5 - Unduh
# ======================================================================
def halaman_unduh():
    hs = ss["hasil"]
    kes = susun_kesimpulan(hs)

    judul_bagian("Langkah 5 dari 5 - Kesimpulan dan Unduh Hasil")
    st.markdown("**Ringkasan**")
    for t in kes["ringkasan"]:
        st.markdown(f"- {t}")
    st.markdown("**Temuan**")
    for t in kes["temuan"]:
        st.markdown(f"- {t}")
    st.markdown("**Rekomendasi**")
    for t in kes["rekomendasi"]:
        st.markdown(f"- {t}")
    with st.expander("Asumsi dan keterbatasan"):
        for t in kes["catatan"]:
            st.markdown(f"- {t}")
    st.caption("Kesimpulan dibuat otomatis dengan aturan sederhana dan tetap perlu ditinjau oleh perencana lalu lintas.")

    judul_bagian("Unduh Hasil")
    if "pdf" not in hs or "docx" not in hs or "csv" not in hs:
        with st.spinner("Menyusun laporan..."):
            hs["pdf"] = buat_laporan_pdf(hs)
            hs["docx"] = buat_laporan_docx(hs)
            hs["csv"] = buat_csv(hs)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.download_button("📄 Laporan PDF", data=hs["pdf"], file_name="laporan_simpang_apill.pdf",
                           mime="application/pdf", key="dl_pdf")
    with k2:
        st.download_button("📝 Laporan Word", data=hs["docx"], file_name="laporan_simpang_apill.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_docx")
    with k3:
        st.download_button("📊 Excel (rumus hidup)", data=hs["excel"], file_name="hasil_analisis_simpang_apill.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_excel")
    with k4:
        st.download_button("🗂️ Data CSV", data=hs["csv"], file_name="hasil_analisis_simpang_apill.csv",
                           mime="text/csv", key="dl_csv")

    kembali, baru = tombol_nav("‹ Kembali ke Animasi", "Mulai Analisis Baru", "5")
    if kembali:
        pindah(4)
    if baru:
        mulai_ulang()


# ======================================================================
# Sidebar dan pengatur halaman
# ======================================================================
sidebar_brand()
st.sidebar.markdown("**Ringkasan Pilihan**")
st.sidebar.caption(f"Langkah {ss['langkah']} dari 5: {NAMA_LANGKAH[ss['langkah'] - 1]}")
st.sidebar.caption(f"{ss['cfg']['jenis']} | Pendekat: {', '.join(ss['aktif'])}")
st.sidebar.caption(f"Fuk = {ss['cfg']['Fuk']:.2f}")
if st.sidebar.button("Mulai ulang", key="btn_reset"):
    mulai_ulang()

if ss["langkah"] >= 3 and "hasil" not in ss:
    ss["langkah"] = 2                      # hasil belum ada: kembali ke halaman Data

header_halaman(
    "Analisis dan Animasi Simpang APILL",
    "Berdasarkan pedoman PKJI 2023 | Satu pendekat = satu fase, waktu sinyal bisa berbeda tiap fase",
)
stepper(ss["langkah"], NAMA_LANGKAH)

{1: halaman_mulai, 2: halaman_data, 3: halaman_hasil, 4: halaman_animasi, 5: halaman_unduh}[ss["langkah"]]()
