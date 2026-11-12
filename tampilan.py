"""
tampilan.py
Tema tampilan (UI) gelap bergaya dashboard untuk aplikasi AA SIPIL:
  - Latar gelap, kartu dengan garis tipis, aksen oranye
  - Logo AA SIPIL (assets/logo_kecil.png) di sidebar dan header
  - Header (hero), judul bagian, kartu angka (KPI), kartu keterangan
  - Perapian warna grafik Plotly

Tema dasar diatur lewat .streamlit/config.toml (base = "dark").
"""

import base64
from pathlib import Path

import streamlit as st

NAMA_APLIKASI = "AA SIPIL"
SUB_NAMA = "Analisis dan Animasi Simpang APILL"

WARNA_LATAR = "#0B1014"
WARNA_KARTU = "#111B21"
WARNA_GARIS = "#1F2D36"
WARNA_AKSEN = "#FF7A2B"
WARNA_AKSEN_GELAP = "#E8631A"
WARNA_TEKS = "#F1F5F9"
WARNA_REDUP = "#8FA1AE"
PALET_GRAFIK = ["#FF7A2B", "#3FA7D6", "#F5B041", "#7FB7A8"]

_FILE_LOGO = Path(__file__).parent / "assets" / "logo_kecil.png"

_LOGO_CADANGAN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect x="29" y="52" width="6" height="10" rx="2" fill="#E5E7EB"/>
<rect x="17" y="3" width="30" height="52" rx="9" fill="#14232A" stroke="#FFFFFF" stroke-width="2.5"/>
<circle cx="32" cy="16" r="6.5" fill="#EF4444"/><circle cx="32" cy="29" r="6.5" fill="#FBBF24"/>
<circle cx="32" cy="42" r="6.5" fill="#22C55E"/></svg>"""


def _logo_uri():
    """Logo sebagai data-URI (PNG dari assets/, atau SVG cadangan bila file tidak ada)."""
    if _FILE_LOGO.exists():
        return "data:image/png;base64," + base64.b64encode(_FILE_LOGO.read_bytes()).decode("ascii")
    return "data:image/svg+xml;base64," + base64.b64encode(_LOGO_CADANGAN.encode("utf-8")).decode("ascii")


def _satu_baris(teks):
    """Hapus indentasi & baris kosong agar tidak dianggap blok kode oleh Markdown."""
    return "".join(baris.strip() for baris in teks.splitlines() if baris.strip())


def terapkan_tema():
    """Menyuntikkan CSS ke halaman. Panggil sekali, tepat setelah st.set_page_config()."""
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background: {WARNA_LATAR}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 1.2rem; max-width: 1280px; }}
    h1, h2, h3, p, label, span {{ color: {WARNA_TEKS}; }}
    [data-testid="stCaptionContainer"] p {{ color: {WARNA_REDUP}; }}

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {{ background: #0E161B; border-right: 1px solid {WARNA_GARIS}; }}
    .brand {{ display: flex; align-items: center; gap: 12px; padding: 4px 2px 14px 2px;
              border-bottom: 1px solid {WARNA_GARIS}; margin-bottom: 12px; }}
    .brand img {{ width: 46px; height: 46px; border-radius: 10px; }}
    .brand-name {{ color: #FFFFFF; font-size: 21px; font-weight: 800; line-height: 1.1; }}
    .brand-sub {{ color: {WARNA_REDUP}; font-size: 12px; }}

    /* ---------- Header (hero) ---------- */
    .hero {{ background: radial-gradient(circle at 85% 20%, rgba(255,122,43,.18), transparent 45%),
                         linear-gradient(135deg, #131F26 0%, #0E161B 100%);
             border: 1px solid {WARNA_GARIS}; border-radius: 18px; padding: 22px 26px; margin-bottom: 16px; }}
    .hero-top {{ display: flex; align-items: center; gap: 18px; }}
    .hero img {{ width: 78px; height: 78px; border-radius: 14px; }}
    .hero .tag {{ display: inline-block; border: 1px solid {WARNA_GARIS}; color: {WARNA_REDUP};
                  font-size: 12px; padding: 3px 12px; border-radius: 999px; margin-bottom: 6px; }}
    .hero .ttl {{ color: #FFFFFF; font-size: 30px; font-weight: 800; line-height: 1.15; }}
    .hero .ttl b {{ color: {WARNA_AKSEN}; font-weight: 800; }}
    .hero .sub {{ color: {WARNA_REDUP}; font-size: 14px; margin-top: 4px; }}
    .hero .pill {{ margin-left: auto; background: {WARNA_AKSEN}; color: #FFFFFF; font-weight: 700;
                   font-size: 12px; padding: 7px 14px; border-radius: 999px; white-space: nowrap; }}
    .hero-fitur {{ display: flex; flex-wrap: wrap; gap: 22px; margin-top: 18px; padding-top: 14px;
                   border-top: 1px solid {WARNA_GARIS}; }}
    .hero-fitur div {{ color: {WARNA_REDUP}; font-size: 13px; display: flex; align-items: center; gap: 8px; }}
    .hero-fitur i {{ font-style: normal; width: 28px; height: 28px; border-radius: 50%;
                     border: 1px solid {WARNA_GARIS}; display: inline-flex; align-items: center;
                     justify-content: center; font-size: 13px; }}

    /* ---------- Judul bagian ---------- */
    .sec-title {{ color: #FFFFFF; font-weight: 800; font-size: 20px; margin: 26px 0 10px 0;
                  padding-left: 12px; border-left: 4px solid {WARNA_AKSEN}; }}

    /* ---------- Kartu angka (KPI) ---------- */
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                 gap: 14px; margin: 6px 0 16px 0; }}
    .kpi {{ background: {WARNA_KARTU}; border: 1px solid {WARNA_GARIS}; border-radius: 16px;
            padding: 16px 18px; display: flex; align-items: center; gap: 14px; }}
    .kpi .ic {{ width: 46px; height: 46px; border-radius: 50%; background: rgba(255,122,43,.15);
                border: 1px solid rgba(255,122,43,.5); display: flex; align-items: center;
                justify-content: center; font-size: 21px; flex: none; }}
    .kpi .val {{ color: #FFFFFF; font-size: 28px; font-weight: 800; line-height: 1.05; }}
    .kpi .lab {{ color: {WARNA_REDUP}; font-size: 13px; margin-top: 2px; }}
    .kpi.bad {{ border-color: rgba(239,68,68,.55); }}
    .kpi.bad .val {{ color: #F87171; }}
    .kpi.bad .ic {{ background: rgba(239,68,68,.15); border-color: rgba(239,68,68,.6); }}

    /* ---------- Kartu keterangan ---------- */
    .kartu-info {{ background: {WARNA_KARTU}; border: 1px solid {WARNA_GARIS}; border-radius: 16px;
                   padding: 14px 18px; color: {WARNA_REDUP}; font-size: 14px; margin: 6px 0 12px 0; }}
    .kartu-info b {{ color: {WARNA_TEKS}; }}

    /* ---------- Grafik, tabel, tombol ---------- */
    [data-testid="stPlotlyChart"] {{ background: {WARNA_KARTU}; border: 1px solid {WARNA_GARIS};
                                      border-radius: 16px; padding: 8px; }}
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{ border: 1px solid {WARNA_GARIS};
                                      border-radius: 14px; overflow: hidden; }}
    [data-testid="stTabs"] button[role="tab"] p {{ font-weight: 700; }}
    .stButton > button[kind="primary"], [data-testid="stBaseButton-primary"],
    [data-testid="stDownloadButton"] button {{ background: {WARNA_AKSEN}; color: #FFFFFF; border: 0;
                                               border-radius: 999px; font-weight: 700; padding: 8px 26px; }}
    [data-testid="stBaseButton-primary"] p::after {{ content: "  →"; }}
    .stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stDownloadButton"] button:hover {{ background: {WARNA_AKSEN_GELAP}; color: #FFFFFF; }}
    [data-testid="stBaseButton-secondary"] {{ border-radius: 999px; border: 1px solid {WARNA_GARIS}; }}
    iframe {{ border-radius: 16px; }}
    </style>
    """
    st.markdown(_satu_baris(css), unsafe_allow_html=True)


def sidebar_brand():
    """Logo + nama aplikasi di bagian atas sidebar."""
    html = (
        f'<div class="brand"><img src="{_logo_uri()}" alt="logo AA SIPIL">'
        f'<div><div class="brand-name">{NAMA_APLIKASI}</div>'
        f'<div class="brand-sub">{SUB_NAMA}</div></div></div>'
    )
    st.sidebar.markdown(html, unsafe_allow_html=True)


def header_halaman(judul, subjudul="", label_kanan="PKJI 2023", fitur=None):
    """
    Header besar di bagian atas halaman.
    Param : fitur -> list tuple (ikon, teks) untuk deretan keunggulan di bawah judul.
    """
    pill = f'<div class="pill">{label_kanan}</div>' if label_kanan else ""
    deret = ""
    if fitur:
        deret = '<div class="hero-fitur">' + "".join(f"<div><i>{i}</i>{t}</div>" for i, t in fitur) + "</div>"
    html = (
        f'<div class="hero"><div class="hero-top"><img src="{_logo_uri()}" alt="logo AA SIPIL">'
        f'<div><span class="tag">{SUB_NAMA}</span>'
        f'<div class="ttl">{judul}</div><div class="sub">{subjudul}</div></div>{pill}</div>{deret}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def judul_bagian(teks):
    """Judul bagian dengan garis aksen oranye (pengganti st.subheader)."""
    st.markdown(f'<div class="sec-title">{teks}</div>', unsafe_allow_html=True)


def kartu_info(teks):
    """Kotak keterangan bergaya kartu (pengganti st.info)."""
    st.markdown(f'<div class="kartu-info">{teks}</div>', unsafe_allow_html=True)


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
    """Menyeragamkan warna dan margin grafik Plotly dengan tema gelap aplikasi."""
    fig.update_layout(
        paper_bgcolor=WARNA_KARTU,
        plot_bgcolor=WARNA_KARTU,
        font=dict(color=WARNA_TEKS),
        margin=dict(l=20, r=20, t=55, b=20),
        height=tinggi,
        title_font=dict(size=16, color="#FFFFFF"),
        legend=dict(font=dict(color=WARNA_TEKS)),
    )
    fig.update_xaxes(gridcolor=WARNA_GARIS, zerolinecolor=WARNA_GARIS)
    fig.update_yaxes(gridcolor=WARNA_GARIS, zerolinecolor=WARNA_GARIS)
    return fig
