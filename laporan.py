"""
laporan.py
Membuat kesimpulan otomatis dan berkas laporan hasil analisis:
  - susun_kesimpulan()     : teks ringkasan, temuan, rekomendasi, catatan
  - buat_laporan_pdf()     : laporan PDF
  - buat_laporan_docx()    : laporan Word (.docx)
  - buat_csv()             : tabel hasil dalam CSV

Seluruh angka diambil dari hasil analisis_simpang() di kalkulasi.py.
Kesimpulan dibuat berdasarkan aturan sederhana (bukan penilaian ahli), sehingga tetap
perlu ditinjau oleh perencana sebelum dipakai.
"""

import csv
import datetime
import io
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

from kalkulasi import BATAS_DS, RENTANG_SIKLUS  # noqa: E402

NAMA_APLIKASI = "AA SIPIL"
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
         "September", "Oktober", "November", "Desember"]

CATATAN_KETERBATASAN = [
    "Satu pendekat = satu fase (semua pendekat terlindung). Fase gabungan dan pendekat terlawan belum dimodelkan.",
    "Faktor Fsf, Fg, Fp, dan Fuk diisi pengguna; nilainya harus diambil dari tabel PKJI 2023 sesuai kondisi lokasi.",
    "Tundaan, panjang antrian, dan rasio kendaraan henti belum dihitung.",
    "Rumus mengacu pada PKJI 2023 melalui sumber sekunder; periksa kembali pada dokumen pedoman asli.",
    "Hasil adalah alat bantu analisis dan perlu ditinjau oleh perencana lalu lintas sebelum dijadikan dasar keputusan.",
]


# ----------------------------------------------------------------------
# Pengambilan data berurutan fase
# ----------------------------------------------------------------------
def _tanggal():
    now = datetime.datetime.now()
    return f"{now.day} {BULAN[now.month - 1]} {now.year}"


def _baris_eks(hs):
    peta = {b["kode"]: b for b in hs["analisis"]["eksisting"]["pendekat"]}
    return [peta[k] for k in hs["urutan"]]


def _baris_usl(hs):
    usl = hs["analisis"]["usulan"]
    if not usl or not usl["layak"]:
        return None
    peta = {b["kode"]: b for b in usl["pendekat"]}
    return [peta[k] for k in hs["urutan"]]


# ----------------------------------------------------------------------
# Kesimpulan otomatis
# ----------------------------------------------------------------------
def susun_kesimpulan(hs):
    """
    Menyusun teks kesimpulan dari hasil analisis.

    Param : hs -> dict hasil (kunci: analisis, data, jenis, Fuk, urutan)
    Return: dict {"ringkasan": [...], "temuan": [...], "rekomendasi": [...], "catatan": [...]}
    """
    an = hs["analisis"]
    eks, usl = an["eksisting"], an["usulan"]
    be, bu = _baris_eks(hs), _baris_usl(hs)
    n = len(be)
    jenuh = [b for b in be if b["DS"] >= BATAS_DS]
    lewat = [b for b in be if b["DS"] > 1.0]
    maks = max(be, key=lambda b: b["DS"])
    hijau_e = ", ".join(f"{b['kode']} {b['g']:.0f} d" for b in be)

    ringkasan = [
        f"Analisis dilakukan pada {hs['jenis'].lower()} dengan pendekat {', '.join(hs['urutan'])} "
        f"(urutan fase {' - '.join(hs['urutan'])}; satu pendekat = satu fase) memakai metode PKJI 2023 untuk simpang bersinyal.",
        f"Waktu sinyal eksisting: hijau {hijau_e}; waktu hijau hilang {eks['WHH']:.0f} d, sehingga waktu siklus "
        f"{eks['Co']:.0f} d. Faktor ukuran kota Fuk = {hs['Fuk']:.2f}.",
    ]

    temuan = []
    if not jenuh:
        temuan.append(
            f"Kondisi eksisting: seluruh pendekat memiliki DS di bawah batas {BATAS_DS:.2f}. DS tertinggi "
            f"{maks['DS']:.2f} pada pendekat {maks['kode']}; kinerja eksisting memenuhi batas yang dipakai."
        )
    else:
        daftar = ", ".join(f"{b['kode']} (DS {b['DS']:.2f})" for b in jenuh)
        temuan.append(
            f"Kondisi eksisting: {len(jenuh)} dari {n} pendekat mencapai atau melampaui batas DS {BATAS_DS:.2f}, "
            f"yaitu {daftar}. DS tertinggi {maks['DS']:.2f} pada pendekat {maks['kode']}."
        )
        if lewat:
            temuan.append(
                "Pendekat " + ", ".join(b["kode"] for b in lewat) + " memiliki DS lebih dari 1.00; arus melebihi "
                "kapasitas pendekat sehingga antrean cenderung terus bertambah selama arus tersebut berlangsung."
            )

    jenuh_u, maks_u = [], None
    if usl is None:
        temuan.append("Waktu sinyal usulan PKJI tidak dihitung pada analisis ini.")
    elif bu is None:
        temuan.append(usl["pesan"])
    else:
        maks_u = max(bu, key=lambda b: b["DS"])
        jenuh_u = [b for b in bu if b["DS"] >= BATAS_DS]
        hijau_u = ", ".join(f"{b['kode']} {b['g']:.1f} d" for b in bu)
        temuan.append(
            f"Usulan PKJI: waktu siklus {usl['Co']:.0f} d dengan hijau {hijau_u}; DS tertinggi {maks_u['DS']:.2f} "
            f"pada pendekat {maks_u['kode']}; {len(jenuh_u)} dari {n} pendekat berstatus jenuh."
        )
        if maks_u["DS"] < maks["DS"] - 0.005:
            temuan.append(f"Dibanding eksisting, DS tertinggi turun dari {maks['DS']:.2f} menjadi {maks_u['DS']:.2f}.")
        elif maks_u["DS"] > maks["DS"] + 0.005:
            tambahan = " (masih di bawah batas)" if maks_u["DS"] < BATAS_DS else ""
            temuan.append(
                f"Dibanding eksisting, DS tertinggi usulan ({maks_u['DS']:.2f}{tambahan}) lebih tinggi daripada "
                f"eksisting ({maks['DS']:.2f}). Rumus usulan memilih siklus yang relatif pendek dan membagi hijau "
                "menurut rasio arus, sehingga pada volume rendah DS bisa lebih tinggi daripada pengaturan eksisting."
            )
        else:
            temuan.append("DS tertinggi usulan relatif sama dengan eksisting.")
        sebaran_e = max(b["DS"] for b in be) - min(b["DS"] for b in be)
        sebaran_u = max(b["DS"] for b in bu) - min(b["DS"] for b in bu)
        if sebaran_u < sebaran_e - 0.02:
            temuan.append(f"DS antar pendekat pada usulan lebih merata (selisih DS tertinggi dan terendah "
                          f"{sebaran_e:.2f} menjadi {sebaran_u:.2f}).")
    for pesan in an["peringatan"]:
        temuan.append("Catatan: " + pesan)

    rekomendasi = []
    if jenuh and bu is not None and maks_u["DS"] < maks["DS"] - 0.005:
        kalimat = ("Pertimbangkan menerapkan waktu hijau usulan PKJI ("
                   + ", ".join(f"{b['kode']} {b['g']:.1f} d" for b in bu) + ") karena menurunkan DS tertinggi.")
        if jenuh_u:
            kalimat += " Namun masih ada pendekat yang jenuh sehingga diperlukan langkah tambahan."
        rekomendasi.append(kalimat)
    if jenuh and (bu is None or jenuh_u):
        rekomendasi.append(
            "Pengaturan waktu sinyal saja belum cukup menurunkan seluruh DS di bawah batas. Pertimbangkan menambah "
            "lebar efektif atau jumlah lajur pada pendekat kritis, mengurangi hambatan samping dan parkir di pendekat, "
            "atau meninjau pola fase."
        )
    if jenuh and bu is not None and maks_u["DS"] >= maks["DS"] - 0.005 and not rekomendasi:
        rekomendasi.append("Waktu sinyal usulan tidak memperbaiki DS tertinggi; kaji ulang pengaturan eksisting dan data volume.")
    if not jenuh:
        rekomendasi.append("Pertahankan pengaturan sinyal eksisting dan lakukan pemantauan berkala, terutama bila volume lalu lintas meningkat.")
    if an["peringatan"]:
        rekomendasi.append("Tinjau waktu siklus atau hijau yang diberi peringatan sebelum diterapkan di lapangan.")

    return {"ringkasan": ringkasan, "temuan": temuan, "rekomendasi": rekomendasi, "catatan": list(CATATAN_KETERBATASAN)}


# ----------------------------------------------------------------------
# Tabel
# ----------------------------------------------------------------------
def _tabel_input(hs):
    kepala = ["Pendekat", "MC", "LV", "HV", "We (m)", "Fsf", "Fg", "Fp", "Kiri (%)", "Kanan (%)"]
    baris = [[k, f"{d['MC']:.0f}", f"{d['LV']:.0f}", f"{d['HV']:.0f}", f"{d['We']:.1f}", f"{d['Fsf']:.2f}",
              f"{d['Fg']:.2f}", f"{d['Fp']:.2f}", f"{d['p_kiri']:.0f}", f"{d['p_kanan']:.0f}"]
             for k in hs["urutan"] for d in [hs["data"][k]]]
    return kepala, baris


def _tabel_sinyal(hs):
    kepala = ["Fase", "Pendekat", "Hijau (d)", "Kuning (d)", "Semua merah (d)"]
    baris = [[str(i + 1), k, f"{d['g']:.1f}", f"{d['kuning']:.1f}", f"{d['ms']:.1f}"]
             for i, k in enumerate(hs["urutan"]) for d in [hs["data"][k]]]
    return kepala, baris


def _tabel_kinerja(baris_hasil, dengan_hijau=True):
    kepala = ["Pendekat", "Q (smp/jam)", "J (smp/jam hijau)", "Rq/J", "Hijau (d)", "C (smp/jam)", "DS", "Status"]
    baris = [[b["kode"], f"{b['Q']:.1f}", f"{b['J']:.0f}", f"{b['RqJ']:.3f}", f"{b['g']:.1f}", f"{b['C']:.0f}",
              f"{b['DS']:.3f}", b["status"]] for b in baris_hasil]
    return kepala, baris


def _ringkasan_simpang(hs):
    an = hs["analisis"]
    eks, usl = an["eksisting"], an["usulan"]
    ok = bool(usl and usl["layak"])
    n = len(hs["urutan"])
    lo, hi = RENTANG_SIKLUS.get(n, (0, 0))

    def rentang(co):
        return "Dalam rentang" if lo <= co <= hi else "Di luar rentang"

    kepala = ["Parameter", "Eksisting", "Usulan PKJI"]
    baris = [
        ["Waktu hijau hilang WHH (d)", f"{eks['WHH']:.1f}", f"{usl['WHH']:.1f}" if ok else "-"],
        ["Rasio arus simpang IFR", f"{eks['IFR']:.3f}", f"{usl['IFR']:.3f}" if ok else "-"],
        ["Waktu siklus (d)", f"{eks['Co']:.1f}", f"{usl['Co']:.1f}" if ok else "-"],
        [f"Rentang layak {n} fase ({lo}-{hi} d)", rentang(eks["Co"]), rentang(usl["Co"]) if ok else "-"],
    ]
    return kepala, baris


# ----------------------------------------------------------------------
# Grafik (PNG) untuk PDF dan Word
# ----------------------------------------------------------------------
def buat_grafik_ds(hs):
    """Grafik batang DS eksisting dan usulan dengan garis batas DS. Mengembalikan bytes PNG."""
    be, bu = _baris_eks(hs), _baris_usl(hs)
    kode = [b["kode"] for b in be]
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=170)
    x = list(range(len(kode)))
    lebar = 0.38 if bu else 0.55
    geser = lebar / 2 if bu else 0
    seri = [("Eksisting", [b["DS"] for b in be], "#3A6270", -geser)]
    if bu:
        seri.append(("Usulan PKJI", [b["DS"] for b in bu], "#3FA7D6", geser))
    for nama, nilai, warna, g in seri:
        batang = ax.bar([i + g for i in x], nilai, lebar, label=nama, color=warna)
        for r, v in zip(batang, nilai):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    ax.axhline(BATAS_DS, color="red", linestyle="--", linewidth=1.4, label=f"Batas DS = {BATAS_DS:.2f}")
    ax.set_xticks(x)
    ax.set_xticklabels(kode)
    ax.set_xlabel("Pendekat")
    ax.set_ylabel("Nilai DS")
    semua = [v for _, nilai, _, _ in seri for v in nilai]
    ax.set_ylim(0, max(1.0, max(semua) * 1.18))
    ax.set_title("Tingkat Kejenuhan Simpang Arteri Primer", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


# ----------------------------------------------------------------------
# CSV
# ----------------------------------------------------------------------
def buat_csv(hs):
    """Tabel hasil eksisting dan usulan dalam satu CSV (UTF-8 dengan BOM agar terbaca Excel)."""
    keluar = io.StringIO()
    w = csv.writer(keluar)
    w.writerow(["Skenario", "Fase_ke", "Pendekat", "Q_smp_jam", "We_m", "J_smp_jam_hijau", "Rq_per_J",
                "Hijau_d", "Kuning_d", "Semua_merah_d", "Kapasitas_C_smp_jam", "DS", "Status"])
    for skenario, baris in (("Eksisting", _baris_eks(hs)), ("Usulan PKJI", _baris_usl(hs))):
        if baris is None:
            continue
        for i, b in enumerate(baris, start=1):
            w.writerow([skenario, i, b["kode"], round(b["Q"], 2), b["We"], round(b["J"], 1), round(b["RqJ"], 4),
                        round(b["g"], 2), b["kuning"], b["ms"], round(b["C"], 1), round(b["DS"], 4), b["status"]])
    return keluar.getvalue().encode("utf-8-sig")


# ----------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------
def _daftarkan_font():
    """Memakai DejaVu Sans (ikut terpasang bersama matplotlib) agar simbol tampil benar."""
    folder = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    reg, bold = os.path.join(folder, "DejaVuSans.ttf"), os.path.join(folder, "DejaVuSans-Bold.ttf")
    if os.path.exists(reg) and os.path.exists(bold):
        if "DejaVu" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("DejaVu", reg))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
        return "DejaVu", "DejaVu-Bold"
    return "Helvetica", "Helvetica-Bold"


def buat_laporan_pdf(hs):
    """Membuat laporan PDF. Return: bytes."""
    font, font_tebal = _daftarkan_font()
    st_judul = ParagraphStyle("judul", fontName=font_tebal, fontSize=17, leading=21, textColor=colors.HexColor("#2F5663"))
    st_sub = ParagraphStyle("sub", fontName=font, fontSize=9.5, leading=13, textColor=colors.HexColor("#51606E"))
    st_h = ParagraphStyle("h", fontName=font_tebal, fontSize=11.5, leading=15, textColor=colors.HexColor("#2F5663"),
                          spaceBefore=12, spaceAfter=5)
    st_isi = ParagraphStyle("isi", fontName=font, fontSize=9.2, leading=13.2, spaceAfter=3.5)
    st_butir = ParagraphStyle("butir", parent=st_isi, leftIndent=12, bulletIndent=2)
    st_sel = ParagraphStyle("sel", fontName=font, fontSize=8, leading=10, alignment=1)
    st_sel_t = ParagraphStyle("selt", parent=st_sel, fontName=font_tebal, textColor=colors.white)
    st_merah = ParagraphStyle("merah", parent=st_sel, fontName=font_tebal, textColor=colors.HexColor("#DC2626"))

    def tabel(kepala, baris, lebar_kolom=None, kolom_status=None):
        data = [[Paragraph(h, st_sel_t) for h in kepala]]
        for r in baris:
            sel = []
            for j, v in enumerate(r):
                gaya = st_merah if (v == "MACET / JENUH") else st_sel
                sel.append(Paragraph(str(v), gaya))
            data.append(sel)
        t = Table(data, colWidths=lebar_kolom, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5663")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6F8")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    def halaman(canvas, doc):
        canvas.saveState()
        canvas.setFont(font, 7.5)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(2 * cm, 1.1 * cm, f"{NAMA_APLIKASI} - Laporan Analisis Simpang APILL (PKJI 2023)")
        canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Halaman {doc.page}")
        canvas.restoreState()

    kes = susun_kesimpulan(hs)
    be, bu = _baris_eks(hs), _baris_usl(hs)
    lebar = A4[0] - 4 * cm
    cerita = [
        Paragraph("Laporan Analisis Kinerja Simpang APILL", st_judul),
        Paragraph(f"{hs['jenis']} - Jalan Arteri Primer | Berdasarkan PKJI 2023 | Dibuat {_tanggal()} oleh {NAMA_APLIKASI}", st_sub),
        Spacer(1, 6),
        Paragraph("1. Data Masukan", st_h),
        Paragraph("Data lalu lintas dan geometri tiap pendekat (MC, LV, HV dalam kend/jam):", st_isi),
    ]
    kepala, baris = _tabel_input(hs)
    cerita.append(tabel(kepala, baris, [lebar * f for f in (0.14, 0.09, 0.09, 0.08, 0.10, 0.09, 0.08, 0.08, 0.125, 0.125)]))
    cerita.append(Spacer(1, 6))
    cerita.append(Paragraph("Pengaturan sinyal tiap fase:", st_isi))
    kepala, baris = _tabel_sinyal(hs)
    cerita.append(tabel(kepala, baris, [lebar * f for f in (0.12, 0.16, 0.22, 0.22, 0.28)]))

    cerita.append(Paragraph("2. Hasil Kondisi Eksisting", st_h))
    kepala, baris = _tabel_kinerja(be)
    anchos = [lebar * f for f in (0.13, 0.12, 0.15, 0.09, 0.10, 0.12, 0.09, 0.20)]
    cerita.append(tabel(kepala, baris, anchos))
    if bu is not None:
        cerita.append(Paragraph("3. Usulan Waktu Sinyal Menurut PKJI 2023", st_h))
        kepala, baris = _tabel_kinerja(bu)
        cerita.append(tabel(kepala, baris, anchos))
    cerita.append(Paragraph("4. Ringkasan Simpang", st_h))
    kepala, baris = _ringkasan_simpang(hs)
    cerita.append(tabel(kepala, baris, [lebar * f for f in (0.50, 0.25, 0.25)]))

    cerita.append(KeepTogether([
        Paragraph("5. Grafik Derajat Kejenuhan", st_h),
        Image(io.BytesIO(buat_grafik_ds(hs)), width=lebar, height=lebar * 3.4 / 7.2),
    ]))

    cerita.append(Paragraph("6. Kesimpulan", st_h))
    for t in kes["ringkasan"] + kes["temuan"]:
        cerita.append(Paragraph(t, st_butir, bulletText="•"))
    cerita.append(Paragraph("7. Rekomendasi", st_h))
    for t in kes["rekomendasi"]:
        cerita.append(Paragraph(t, st_butir, bulletText="•"))
    cerita.append(Paragraph("8. Asumsi dan Keterbatasan", st_h))
    for t in kes["catatan"]:
        cerita.append(Paragraph(t, st_butir, bulletText="•"))

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                      title="Laporan Analisis Simpang APILL", author=NAMA_APLIKASI).build(cerita, onFirstPage=halaman, onLaterPages=halaman)
    return buf.getvalue()


# ----------------------------------------------------------------------
# Word (.docx)
# ----------------------------------------------------------------------
def _warna_sel(sel, hex_warna):
    tc_pr = sel._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_warna)
    tc_pr.append(shd)


def _nomor_halaman(paragraf):
    """Menyisipkan kolom nomor halaman (PAGE) pada paragraf footer."""
    run = paragraf.add_run()
    for tipe, teks in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipe:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tipe)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = teks
        run._r.append(el)
    run.font.size = Pt(8)


def buat_laporan_docx(hs):
    """Membuat laporan Word. Return: bytes."""
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    normal.font.size = Pt(10)
    for nama, ukuran in (("Title", 20), ("Heading 1", 13)):
        gaya = doc.styles[nama]
        gaya.font.name = "Arial"
        fonts = gaya.element.rPr.rFonts
        for atribut in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            fonts.attrib.pop(qn(atribut), None)          # lepas font tema agar Arial dipakai
        fonts.set(qn("w:ascii"), "Arial")
        fonts.set(qn("w:hAnsi"), "Arial")
        gaya.font.size = Pt(ukuran)
        gaya.font.bold = True
        gaya.font.color.rgb = RGBColor(0x2F, 0x56, 0x63)
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(14)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(5)

    def tabel(kepala, baris, lebar_cm):
        t = doc.add_table(rows=1, cols=len(kepala))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for j, h in enumerate(kepala):
            sel = t.rows[0].cells[j]
            sel.text = ""
            p = sel.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h)
            r.bold, r.font.size, r.font.color.rgb = True, Pt(8.5), RGBColor(255, 255, 255)
            _warna_sel(sel, "2F5663")
        for i, baris_i in enumerate(baris):
            sel_baris = t.add_row().cells
            for j, v in enumerate(baris_i):
                sel_baris[j].text = ""
                p = sel_baris[j].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(str(v))
                r.font.size = Pt(8.5)
                if v == "MACET / JENUH":
                    r.bold, r.font.color.rgb = True, RGBColor(0xDC, 0x26, 0x26)
                if i % 2 == 1:
                    _warna_sel(sel_baris[j], "F3F6F8")
        for j, kolom in enumerate(t.columns):
            kolom.width = Cm(lebar_cm[j])                 # lebar kolom (gridCol)
        for baris_t in t.rows:
            for j, sel in enumerate(baris_t.cells):
                sel.width = Cm(lebar_cm[j])
        doc.add_paragraph()
        return t

    kes = susun_kesimpulan(hs)
    be, bu = _baris_eks(hs), _baris_usl(hs)

    doc.add_paragraph("Laporan Analisis Kinerja Simpang APILL", style="Title")
    p = doc.add_paragraph(f"{hs['jenis']} - Jalan Arteri Primer | Berdasarkan PKJI 2023 | Dibuat {_tanggal()} oleh {NAMA_APLIKASI}")
    p.runs[0].font.size, p.runs[0].font.color.rgb = Pt(9), RGBColor(0x51, 0x60, 0x6E)

    doc.add_heading("1. Data Masukan", level=1)
    doc.add_paragraph("Data lalu lintas dan geometri tiap pendekat (MC, LV, HV dalam kend/jam):")
    kepala, baris = _tabel_input(hs)
    tabel(kepala, baris, [2.3, 1.6, 1.6, 1.4, 1.7, 1.5, 1.4, 1.4, 2.0, 2.0])
    doc.add_paragraph("Pengaturan sinyal tiap fase:")
    kepala, baris = _tabel_sinyal(hs)
    tabel(kepala, baris, [2.0, 3.0, 3.5, 3.5, 4.5])

    doc.add_heading("2. Hasil Kondisi Eksisting", level=1)
    kepala, baris = _tabel_kinerja(be)
    lebar_kinerja = [2.2, 2.0, 2.6, 1.5, 1.6, 2.0, 1.5, 3.6]
    tabel(kepala, baris, lebar_kinerja)
    nomor = 3
    if bu is not None:
        doc.add_heading("3. Usulan Waktu Sinyal Menurut PKJI 2023", level=1)
        kepala, baris = _tabel_kinerja(bu)
        tabel(kepala, baris, lebar_kinerja)
        nomor = 4
    doc.add_heading(f"{nomor}. Ringkasan Simpang", level=1)
    kepala, baris = _ringkasan_simpang(hs)
    tabel(kepala, baris, [8.5, 4.2, 4.2])

    doc.add_heading(f"{nomor + 1}. Grafik Derajat Kejenuhan", level=1)
    doc.add_picture(io.BytesIO(buat_grafik_ds(hs)), width=Cm(16.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading(f"{nomor + 2}. Kesimpulan", level=1)
    for t in kes["ringkasan"] + kes["temuan"]:
        doc.add_paragraph(t, style="List Bullet")
    doc.add_heading(f"{nomor + 3}. Rekomendasi", level=1)
    for t in kes["rekomendasi"]:
        doc.add_paragraph(t, style="List Bullet")
    doc.add_heading(f"{nomor + 4}. Asumsi dan Keterbatasan", level=1)
    for t in kes["catatan"]:
        doc.add_paragraph(t, style="List Bullet")

    pie = sec.footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = pie.add_run(f"{NAMA_APLIKASI} - Laporan Analisis Simpang APILL (PKJI 2023) | Halaman ")
    r.font.size = Pt(8)
    _nomor_halaman(pie)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
