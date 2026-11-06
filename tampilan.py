"""
tampilan.py
Tema tampilan (UI) ala dashboard untuk aplikasi Analisis Simpang APILL:
  - Sidebar hijau-biru tua dengan logo lampu lalu lintas
  - Header bar, kartu angka (KPI), judul bagian
  - Perapian warna grafik Plotly

Catatan: agar warna teks terbaca, aplikasi harus memakai tema TERANG.
Atur lewat file .streamlit/config.toml (sudah disediakan).
"""

import base64

import streamlit as st

NAMA_APLIKASI = "AA SIPIL"
SUB_NAMA = "Analisis dan Animasi Simpang APILL"

WARNA_SIDEBAR = "#3A6270"
WARNA_HEADER = "#2F5663"
WARNA_AKSEN = "#2E86AB"
PALET_GRAFIK = ["#3A6270", "#3FA7D6", "#F59E0B", "#7FB7A8"]

# Logo: lampu lalu lintas (merah, kuning, hijau)
_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect x="29" y="52" width="6" height="10" rx="2" fill="#E5E7EB"/>
<rect x="17" y="3" width="30" height="52" rx="9" fill="#14232A" stroke="#FFFFFF" stroke-width="2.5"/>
<circle cx="32" cy="16" r="6.5" fill="#EF4444"/>
<circle cx="32" cy="29" r="6.5" fill="#FBBF24"/>
<circle cx="32" cy="42" r="6.5" fill="#22C55E"/>
<circle cx="30" cy="14" r="1.8" fill="#FFFFFF" opacity=".6"/>
</svg>"""


def _logo_uri():
    """Logo sebagai data-URI supaya aman dipakai di st.markdown."""
    b64 = base64.b64encode(_LOGO_SVG.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _satu_baris(teks):
    """Hapus indentasi & baris kosong agar tidak dianggap blok kode oleh Markdown."""
    return "".join(baris.strip() for baris in teks.splitlines() if baris.strip())


def terapkan_tema():
    """Menyuntikkan CSS ke halaman. Panggil sekali, tepat setelah st.set_page_config()."""
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background: #E3E6E8; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 1.4rem; max-width: 1280px; }}

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {{ background: {WARNA_SIDEBAR}; }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] label p {{ color: #FFFFFF !important; }}
    .brand {{ display: flex; align-items: center; gap: 12px; padding: 6px 2px 14px 2px;
              border-bottom: 1px solid rgba(255,255,255,.25); margin-bottom: 10px; }}
    .brand img {{ width: 46px; height: 46px; }}
    .brand-name {{ color: #FFFFFF; font-size: 21px; font-weight: 800; line-height: 1.1; }}
    .brand-sub {{ color: #C8DCE3; font-size: 12px; }}

    /* ---------- Header ---------- */
    .app-header {{ background: {WARNA_HEADER}; border-radius: 14px; padding: 14px 20px;
                   display: flex; align-items: center; gap: 16px; margin-bottom: 14px; }}
    .app-header img {{ width: 50px; height: 50px; }}
    .app-header .ttl {{ color: #FFFFFF; font-size: 24px; font-weight: 800; line-height: 1.15; }}
    .app-header .sub {{ color: #C8DCE3; font-size: 13px; margin-top: 2px; }}
    .app-header .pill {{ margin-left: auto; background: #FFFFFF; color: {WARNA_HEADER};
                         font-weight: 700; font-size: 12px; padding: 6px 12px; border-radius: 999px; }}

    /* ---------- Judul bagian ---------- */
    .sec-title {{ background: {WARNA_HEADER}; color: #FFFFFF; font-weight: 700; font-size: 16px;
                  padding: 9px 16px; border-radius: 10px; margin: 18px 0 10px 0; }}

    /* ---------- Kartu angka (KPI) ---------- */
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                 gap: 16px; margin: 6px 0 16px 0; }}
    .kpi {{ background: #FFFFFF; border-radius: 14px; padding: 16px 18px; display: flex;
            align-items: center; gap: 14px; box-shadow: 0 1px 5px rgba(0,0,0,.14); }}
    .kpi .ic {{ width: 48px; height: 48px; border-radius: 50%; background: {WARNA_SIDEBAR};
                display: flex; align-items: center; justify-content: center; font-size: 22px; flex: none; }}
    .kpi .val {{ color: #1F2D3A; font-size: 30px; font-weight: 800; line-height: 1.05; }}
    .kpi .lab {{ color: #51606E; font-size: 13px; margin-top: 2px; }}
    .kpi.bad .val {{ color: #D64545; }}
    .kpi.bad .ic {{ background: #D64545; }}

    /* ---------- Grafik, tabel, tombol ---------- */
    [data-testid="stPlotlyChart"] {{ background: #FFFFFF; border-radius: 14px; padding: 8px;
                                      box-shadow: 0 1px 5px rgba(0,0,0,.14); }}
    [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden;
                                   box-shadow: 0 1px 5px rgba(0,0,0,.14); }}
    .stButton > button[kind="primary"], [data-testid="stBaseButton-primary"],
    [data-testid="stDownloadButton"] button {{ background: {WARNA_AKSEN}; color: #FFFFFF;
                                               border: 0; border-radius: 8px; font-weight: 600; }}
    .stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stDownloadButton"] button:hover {{ background: #256F8E; color: #FFFFFF; }}
    </style>
    """
    st.markdown(_satu_baris(css), unsafe_allow_html=True)


def sidebar_brand():
    """Logo + nama aplikasi di bagian atas sidebar."""
    html = (
        f'<div class="brand"><img src="{_logo_uri()}" alt="logo">'
        f'<div><div class="brand-name">{NAMA_APLIKASI}</div>'
        f'<div class="brand-sub">{SUB_NAMA}</div></div></div>'
    )
    st.sidebar.markdown(html, unsafe_allow_html=True)


def header_halaman(judul, subjudul="", label_kanan="PKJI 2023"):
    """Bar judul di bagian atas halaman (dengan logo lampu lalu lintas)."""
    pill = f'<div class="pill">{label_kanan}</div>' if label_kanan else ""
    html = (
        f'<div class="app-header"><img src="{_logo_uri()}" alt="logo">'
        f'<div><div class="ttl">{judul}</div><div class="sub">{subjudul}</div></div>{pill}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def judul_bagian(teks):
    """Judul bagian berupa strip warna (pengganti st.subheader)."""
    st.markdown(f'<div class="sec-title">{teks}</div>', unsafe_allow_html=True)


def kartu_kpi(daftar):
    """
    Deretan kartu angka.
    Param : daftar -> list dict, tiap dict: {"ikon": "🚗", "nilai": "1.940", "label": "Total Volume", "bahaya": False}
    """
    kartu = ""
    for k in daftar:
        kelas = "kpi bad" if k.get("bahaya") else "kpi"
        kartu += (
            f'<div class="{kelas}"><div class="ic">{k.get("ikon", "")}</div>'
            f'<div><div class="val">{k["nilai"]}</div><div class="lab">{k["label"]}</div></div></div>'
        )
    st.markdown(f'<div class="kpi-grid">{kartu}</div>', unsafe_allow_html=True)


def rapikan_grafik(fig, tinggi=360):
    """Menyeragamkan warna dan margin grafik Plotly dengan tema aplikasi."""
    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#1F2D3A"),
        margin=dict(l=20, r=20, t=55, b=20),
        height=tinggi,
        title_font=dict(size=16),
    )
    return fig
