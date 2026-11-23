"""
komponen_ui.py
Komponen tampilan tambahan untuk alur bertahap (wizard) aplikasi AA SIPIL:
  - stepper          : penanda langkah 1 sampai 5
  - kartu_fitur      : kartu keunggulan di halaman awal
  - tampil_ilustrasi : gambar denah simpang 3 atau 4 lengan (SVG)
  - bar_kejenuhan    : visualisasi derajat kejenuhan (DS) tiap pendekat

Semua HTML ditulis tanpa baris kosong agar tidak dianggap blok kode oleh Markdown.
"""

import base64

import streamlit as st

URUTAN_PENDEKAT = ["U", "T", "S", "B"]


def _satu_baris(teks):
    """Hapus indentasi dan baris kosong."""
    return "".join(baris.strip() for baris in teks.splitlines() if baris.strip())


def terapkan_css_komponen():
    """Menyuntikkan CSS komponen. Panggil sekali setelah terapkan_tema()."""
    css = """
    <style>
    .aa-stepper { display: flex; align-items: center; gap: 6px; margin: 6px 0 20px 0; flex-wrap: wrap; }
    .aa-step { display: flex; align-items: center; gap: 8px; flex: 0 0 auto; }
    .aa-dot { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center;
              justify-content: center; font-weight: 800; font-size: 15px; flex: none;
              border: 2px solid #9CA3AF; color: #6B7280; background: #FFFFFF; }
    .aa-step.aktif .aa-dot { background: #2E86AB; border-color: #2E86AB; color: #FFFFFF;
                             box-shadow: 0 0 0 4px rgba(46,134,171,.25); }
    .aa-step.selesai .aa-dot { background: #22C55E; border-color: #22C55E; color: #FFFFFF; }
    .aa-label { font-size: 13px; font-weight: 600; color: inherit; opacity: .6; line-height: 1.15; }
    .aa-step.aktif .aa-label, .aa-step.selesai .aa-label { opacity: 1; }
    .aa-bar { flex: 1 1 16px; height: 3px; background: #9CA3AF; opacity: .45; border-radius: 2px; min-width: 14px; }
    .aa-bar.selesai { background: #22C55E; opacity: 1; }

    .aa-fitur-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
                     gap: 14px; margin: 6px 0 12px 0; }
    .aa-fitur { background: #FFFFFF; border-radius: 14px; padding: 14px 16px; box-shadow: 0 1px 5px rgba(0,0,0,.14); }
    .aa-fitur .ic { font-size: 26px; line-height: 1; }
    .aa-fitur .jd { font-weight: 700; color: #1F2D3A; margin-top: 6px; font-size: 15px; }
    .aa-fitur .tx { font-size: 12.5px; color: #51606E; margin-top: 2px; }

    .aa-gauge { background: #FFFFFF; border-radius: 14px; padding: 12px 16px 10px 16px;
                box-shadow: 0 1px 5px rgba(0,0,0,.14); margin-bottom: 8px; }
    .aa-g-judul { font-weight: 700; color: #1F2D3A; font-size: 14px; margin-bottom: 8px; }
    .aa-g-row { display: flex; align-items: center; gap: 10px; margin: 7px 0; }
    .aa-g-nama { width: 26px; font-weight: 800; color: #1F2D3A; text-align: center; }
    .aa-g-track { position: relative; flex: 1; height: 20px; background: #E5E7EB; border-radius: 10px; overflow: visible; }
    .aa-g-fill { height: 100%; border-radius: 10px; }
    .aa-g-mark { position: absolute; top: -4px; bottom: -4px; width: 0; border-left: 2px dashed #DC2626; }
    .aa-g-mark.satu { border-left-color: #7F1D1D; border-left-style: dotted; }
    .aa-g-nilai { width: 150px; font-size: 12.5px; color: #1F2D3A; font-weight: 600; }
    .aa-g-skala { font-size: 11px; color: #6B7280; margin-top: 2px; }
    .aa-legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; margin: 2px 0 10px 0; color: inherit; }
    .aa-legend i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 5px; vertical-align: middle; }

    .aa-ilustrasi { text-align: center; }
    .aa-ilustrasi img { width: 100%; max-width: 330px; border-radius: 14px; box-shadow: 0 1px 5px rgba(0,0,0,.14); }
    </style>
    """
    st.markdown(_satu_baris(css), unsafe_allow_html=True)


def stepper(langkah_aktif, nama_langkah):
    """Penanda langkah: selesai (hijau), aktif (biru), belum (abu-abu)."""
    html = ""
    for i, nama in enumerate(nama_langkah, start=1):
        if i < langkah_aktif:
            kelas, isi = "selesai", "✓"
        elif i == langkah_aktif:
            kelas, isi = "aktif", str(i)
        else:
            kelas, isi = "", str(i)
        html += f'<div class="aa-step {kelas}"><div class="aa-dot">{isi}</div><div class="aa-label">{nama}</div></div>'
        if i < len(nama_langkah):
            html += f'<div class="aa-bar {"selesai" if i < langkah_aktif else ""}"></div>'
    st.markdown(f'<div class="aa-stepper">{html}</div>', unsafe_allow_html=True)


def kartu_fitur(daftar):
    """
    Kartu keunggulan.
    Param : daftar -> list dict {"ikon": "📐", "judul": "...", "teks": "..."}
    """
    isi = "".join(
        f'<div class="aa-fitur"><div class="ic">{d["ikon"]}</div>'
        f'<div class="jd">{d["judul"]}</div><div class="tx">{d["teks"]}</div></div>'
        for d in daftar
    )
    st.markdown(f'<div class="aa-fitur-grid">{isi}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Ilustrasi denah simpang (SVG)
# ----------------------------------------------------------------------
def ilustrasi_simpang_svg(aktif, urutan=None):
    """
    Membuat SVG denah simpang (lalu lintas lajur kiri).

    Param : aktif  -> list kode lengan yang ada, mis. ["U", "S", "B"]
            urutan -> list kode sesuai urutan fase (opsional); jika diisi, nomor fase ditampilkan
    Return: string SVG
    """
    c, jalan = 160, "#4B5563"
    kotak = {"U": (124, 0, 72, 124), "T": (196, 124, 124, 72), "S": (124, 196, 72, 124), "B": (0, 124, 124, 72)}
    label_pos = {"U": (160, 22), "T": (298, 160), "S": (160, 298), "B": (22, 160)}
    badge_pos = {"U": (194, 22), "T": (298, 126), "S": (126, 298), "B": (22, 194)}
    garis_tengah = {"U": (160, 8, 160, 118), "T": (202, 160, 312, 160), "S": (160, 202, 160, 312), "B": (8, 160, 118, 160)}
    garis_stop = {"U": (160, 112, 196, 112), "T": (208, 160, 208, 196), "S": (124, 208, 160, 208), "B": (112, 124, 112, 160)}
    panah = {"U": "178,82 171,66 185,66", "T": "238,178 254,171 254,185",
             "S": "142,238 135,254 149,254", "B": "82,142 66,135 66,149"}

    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 320" font-family="Arial, sans-serif">',
         '<rect width="320" height="320" rx="18" fill="#E9EDF0"/>']
    for k in URUTAN_PENDEKAT:
        x, y, w, h = kotak[k]
        if k in aktif:
            p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{jalan}"/>')
        else:
            p.append(f'<rect x="{x + 2}" y="{y + 2}" width="{w - 4}" height="{h - 4}" fill="none" '
                     f'stroke="#9CA3AF" stroke-width="2" stroke-dasharray="6 5" rx="6"/>')
            p.append(f'<text x="{(x + w / 2):.0f}" y="{(y + h / 2 + 4):.0f}" text-anchor="middle" '
                     f'font-size="11" fill="#9CA3AF">tidak ada</text>')
    p.append(f'<rect x="124" y="124" width="72" height="72" fill="{jalan}"/>')
    for k in URUTAN_PENDEKAT:
        if k not in aktif:
            continue
        x1, y1, x2, y2 = garis_tengah[k]
        p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#FBBF24" stroke-width="2" stroke-dasharray="8 6"/>')
        x1, y1, x2, y2 = garis_stop[k]
        p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#FFFFFF" stroke-width="4"/>')
        p.append(f'<polygon points="{panah[k]}" fill="#E5E7EB"/>')
    for k in URUTAN_PENDEKAT:
        lx, ly = label_pos[k]
        if k in aktif:
            p.append(f'<circle cx="{lx}" cy="{ly}" r="15" fill="#1F2937"/>')
            p.append(f'<text x="{lx}" y="{ly + 5}" text-anchor="middle" font-size="15" font-weight="bold" fill="#FFFFFF">{k}</text>')
            if urutan and k in urutan:
                bx, by = badge_pos[k]
                p.append(f'<circle cx="{bx}" cy="{by}" r="10" fill="#F59E0B"/>')
                p.append(f'<text x="{bx}" y="{by + 4}" text-anchor="middle" font-size="12" font-weight="bold" fill="#1F2937">{urutan.index(k) + 1}</text>')
        else:
            p.append(f'<circle cx="{lx}" cy="{ly}" r="15" fill="none" stroke="#9CA3AF" stroke-width="2" stroke-dasharray="4 3"/>')
            p.append(f'<text x="{lx}" y="{ly + 5}" text-anchor="middle" font-size="15" font-weight="bold" fill="#9CA3AF">{k}</text>')
    p.append("</svg>")
    return "".join(p)


def tampil_ilustrasi(aktif, urutan=None):
    """Menampilkan ilustrasi simpang (SVG sebagai data-URI agar aman di Markdown)."""
    b64 = base64.b64encode(ilustrasi_simpang_svg(aktif, urutan).encode("utf-8")).decode("ascii")
    st.markdown(
        f'<div class="aa-ilustrasi"><img src="data:image/svg+xml;base64,{b64}" alt="Ilustrasi simpang"></div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Visualisasi kejenuhan
# ----------------------------------------------------------------------
SKALA_MAKS = 1.2          # DS 1.2 = ujung batang
BATAS_HIJAU = 0.70        # batas visual (bukan dari PKJI) untuk membedakan "aman" dan "mendekati batas"


def warna_ds(ds, batas=0.85):
    """Warna batang menurut nilai DS."""
    if ds > 1.0:
        return "#B91C1C"
    if ds >= batas:
        return "#EF4444"
    if ds >= BATAS_HIJAU:
        return "#F59E0B"
    return "#22C55E"


def bar_kejenuhan(judul, daftar, batas=0.85):
    """
    Batang kejenuhan tiap pendekat.

    Param : judul  -> judul kartu
            daftar -> list dict {"kode": "U", "ds": 0.63, "status": "OK / IDEAL"}
            batas  -> batas DS (garis putus-putus merah)
    """
    pos_batas = batas / SKALA_MAKS * 100
    pos_satu = 1.0 / SKALA_MAKS * 100
    baris = ""
    for d in daftar:
        lebar = min(d["ds"], SKALA_MAKS) / SKALA_MAKS * 100
        baris += (
            f'<div class="aa-g-row"><div class="aa-g-nama">{d["kode"]}</div>'
            f'<div class="aa-g-track"><div class="aa-g-fill" style="width:{lebar:.1f}%;background:{warna_ds(d["ds"], batas)}"></div>'
            f'<div class="aa-g-mark" style="left:{pos_batas:.1f}%"></div>'
            f'<div class="aa-g-mark satu" style="left:{pos_satu:.1f}%"></div></div>'
            f'<div class="aa-g-nilai">DS {d["ds"]:.2f} · {d["status"]}</div></div>'
        )
    html = (
        f'<div class="aa-gauge"><div class="aa-g-judul">{judul}</div>{baris}'
        f'<div class="aa-g-skala">Garis putus-putus merah = batas DS {batas:.2f}; garis titik-titik = DS 1.00 (kapasitas penuh)</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def legenda_kejenuhan(batas=0.85):
    """Keterangan warna batang kejenuhan."""
    isi = (
        f'<span><i style="background:#22C55E"></i>DS &lt; {BATAS_HIJAU:.2f} (aman)</span>'
        f'<span><i style="background:#F59E0B"></i>{BATAS_HIJAU:.2f} - {batas:.2f} (mendekati batas)</span>'
        f'<span><i style="background:#EF4444"></i>{batas:.2f} - 1.00 (melewati batas)</span>'
        f'<span><i style="background:#B91C1C"></i>&gt; 1.00 (melebihi kapasitas)</span>'
    )
    st.markdown(f'<div class="aa-legend">{isi}</div>', unsafe_allow_html=True)
