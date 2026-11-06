"""
ekspor_excel.py
Membuat file Excel (.xlsx) hasil analisis Simpang APILL untuk diunduh dari web Streamlit.

Isi file:
  1. Input            -> parameter umum, faktor EMP, dan data pendekat (sel biru = input)
  2. Hasil Analisis   -> Q (smp/jam), So, S, C, DS, Status (semua memakai RUMUS Excel) + grafik DS
  3. Catatan          -> rumus dan asumsi yang dipakai

Semua angka di sheet 2 adalah rumus yang merujuk ke sheet 1, jadi jika Anda mengubah
input di Excel, hasilnya ikut berubah otomatis.
"""

import io

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from kalkulasi import konversi_ke_smp

# ---- Gaya (mengikuti file Excel survei Anda) ----
FONT = "Arial"
F_TITLE = Font(name=FONT, size=12, bold=True, color="FFFFFF")
F_HEAD = Font(name=FONT, size=9, bold=True, color="FFFFFF")
F_SECTION = Font(name=FONT, size=10, bold=True, color="1F3864")
F_LABEL = Font(name=FONT, size=9, bold=True, color="1F3864")
F_TEXT = Font(name=FONT, size=9, color="000000")
F_INPUT = Font(name=FONT, size=9, color="0000FF")       # biru = input
F_NOTE = Font(name=FONT, size=8, color="7F3E00")
FILL_TITLE = PatternFill("solid", fgColor="1F4E79")
FILL_HEAD = PatternFill("solid", fgColor="2E75B6")
FILL_SECTION = PatternFill("solid", fgColor="D6E4F0")
FILL_LABEL = PatternFill("solid", fgColor="F2F2F2")
FILL_NOTE = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)

NAMA_PENDEKAT = {"U": "Utara", "T": "Timur", "S": "Selatan", "B": "Barat"}
URUTAN = ["U", "T", "S", "B"]
SHEET_IN = "1. Input"
SHEET_HASIL = "2. Hasil Analisis"
SHEET_CATATAN = "3. Catatan"


def _title(ws, text, last_col):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    c = ws.cell(row=1, column=1, value=text)
    c.font, c.fill, c.alignment = F_TITLE, FILL_TITLE, LEFT
    ws.row_dimensions[1].height = 24


def _section(ws, row, text, last_col):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    c = ws.cell(row=row, column=1, value=text)
    c.font, c.fill, c.alignment = F_SECTION, FILL_SECTION, LEFT


def _head(ws, row, labels):
    for i, text in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=text)
        c.font, c.fill, c.alignment, c.border = F_HEAD, FILL_HEAD, CENTER, BORDER
    ws.row_dimensions[row].height = 30


def _cell(ws, ref, value, font=F_TEXT, fmt=None, fill=None, align=CENTER):
    c = ws[ref]
    c.value = value
    c.font, c.alignment, c.border = font, align, BORDER
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    return c


def buat_excel(data_input, Co, g, Fsf, Fg, Fp, Fuk, batas_ds=0.85, jenis_simpang=None):
    """
    Membuat file Excel hasil analisis dan mengembalikannya sebagai bytes.

    Param : data_input -> dict {"U": {"MC":..,"LV":..,"HV":..,"We":..}, "T": ..., "S": ..., "B": ...}
            Co, g      -> waktu siklus dan waktu hijau (detik)
            Fsf, Fg, Fp, Fuk -> faktor koreksi arus jenuh
            batas_ds   -> batas derajat kejenuhan (default 0.85)
            jenis_simpang -> teks jenis simpang, mis. "Simpang 3 lengan" (opsional)
            (data_input boleh berisi 3 atau 4 pendekat; hanya yang ada yang ditulis)
    Return: bytes isi file .xlsx (siap dipakai st.download_button)
    """
    # Faktor EMP diambil dari kalkulasi.py supaya selalu sama dengan perhitungan di web
    emp_mc = konversi_ke_smp(1, 0, 0)
    emp_lv = konversi_ke_smp(0, 1, 0)
    emp_hv = konversi_ke_smp(0, 0, 1)

    kode_aktif = [k for k in URUTAN if k in data_input]
    n = len(kode_aktif)                      # jumlah pendekat (3 atau 4)
    jenis_simpang = jenis_simpang or f"Simpang {n} lengan"

    wb = Workbook()

    # ======================================================
    # Sheet 1 - Input
    # ======================================================
    ws = wb.active
    ws.title = SHEET_IN
    _title(ws, "INPUT ANALISIS SIMPANG APILL - JALAN ARTERI PRIMER (PKJI 2023)", 6)
    ws.merge_cells("A2:F2")
    ws["A2"].value = "Sel bertulisan BIRU = input yang boleh diubah. Semua hasil di sheet 2 otomatis ikut berubah."
    ws["A2"].font, ws["A2"].fill, ws["A2"].alignment = F_NOTE, FILL_NOTE, LEFT

    ws.merge_cells("A3:F3")
    ws["A3"].value = f"Jenis simpang: {jenis_simpang}  |  Pendekat: {', '.join(kode_aktif)}"
    ws["A3"].font, ws["A3"].alignment = F_LABEL, LEFT

    _section(ws, 4, "A. PARAMETER UMUM", 6)
    parameter = [
        (5, "Waktu Siklus, Co", Co, "detik", "0.0", "Dari sidebar web"),
        (6, "Waktu Hijau, g", g, "detik", "0.0", "Dari sidebar web (sama untuk semua pendekat)"),
        (7, "Fsf (hambatan samping)", Fsf, "-", "0.00", "Faktor koreksi arus jenuh"),
        (8, "Fg (kelandaian)", Fg, "-", "0.00", "Faktor koreksi arus jenuh"),
        (9, "Fp (parkir)", Fp, "-", "0.00", "Faktor koreksi arus jenuh"),
        (10, "Fuk (ukuran kota)", Fuk, "-", "0.00", "Faktor koreksi arus jenuh"),
        (11, "Batas DS", batas_ds, "-", "0.00", "DS < batas = OK / IDEAL; DS >= batas = MACET / JENUH"),
    ]
    for r, label, nilai, sat, fmt, ket in parameter:
        _cell(ws, f"A{r}", label, F_LABEL, fill=FILL_LABEL, align=LEFT)
        _cell(ws, f"B{r}", nilai, F_INPUT, fmt)
        _cell(ws, f"C{r}", sat, F_TEXT)
        ws.merge_cells(f"D{r}:F{r}")
        _cell(ws, f"D{r}", ket, F_TEXT, align=LEFT)

    _section(ws, 13, "B. FAKTOR EMP (smp/kendaraan)", 6)
    emp = [(14, "MC (sepeda motor)", emp_mc), (15, "LV (kendaraan ringan)", emp_lv), (16, "HV (kendaraan berat)", emp_hv)]
    for r, label, nilai in emp:
        _cell(ws, f"A{r}", label, F_LABEL, fill=FILL_LABEL, align=LEFT)
        _cell(ws, f"B{r}", nilai, F_INPUT, "0.00")
        _cell(ws, f"C{r}", "smp/kend", F_TEXT)
        ws.merge_cells(f"D{r}:F{r}")
        _cell(ws, f"D{r}", "Diambil dari fungsi konversi_ke_smp di kalkulasi.py", F_TEXT, align=LEFT)

    _section(ws, 18, "C. DATA PENDEKAT (kendaraan/jam)", 6)
    _head(ws, 19, ["Pendekat", "Nama", "MC (kend/jam)", "LV (kend/jam)", "HV (kend/jam)", "Lebar We (m)"])
    for i, kode in enumerate(kode_aktif):
        r = 20 + i
        d = data_input[kode]
        _cell(ws, f"A{r}", kode, F_LABEL, fill=FILL_LABEL)
        _cell(ws, f"B{r}", NAMA_PENDEKAT[kode], F_TEXT)
        _cell(ws, f"C{r}", d["MC"], F_INPUT, "#,##0")
        _cell(ws, f"D{r}", d["LV"], F_INPUT, "#,##0")
        _cell(ws, f"E{r}", d["HV"], F_INPUT, "#,##0")
        _cell(ws, f"F{r}", d["We"], F_INPUT, "0.0")

    ws.column_dimensions["A"].width = 28
    for col, w in zip("BCDEF", [14, 14, 14, 14, 14]):
        ws.column_dimensions[col].width = w

    # ======================================================
    # Sheet 2 - Hasil Analisis (semua rumus)
    # ======================================================
    wh = wb.create_sheet(SHEET_HASIL)
    _title(wh, "HASIL ANALISIS KINERJA SIMPANG APILL - PKJI 2023", 10)
    wh.merge_cells("A2:J2")
    wh["A2"].value = "Seluruh angka pada tabel ini adalah rumus yang merujuk ke sheet '1. Input'."
    wh["A2"].font, wh["A2"].fill, wh["A2"].alignment = F_NOTE, FILL_NOTE, LEFT

    _head(wh, 3, ["Pendekat", "Total Kendaraan\n(kend/jam)", "Volume Q\n(smp/jam)", "Lebar We\n(m)",
                  "So = 600 x We\n(smp/jam hijau)", "S = So x Fsf x Fg x Fp x Fuk\n(smp/jam hijau)",
                  "C = S x g / Co\n(smp/jam)", "DS = Q / C", "Status", "Batas DS"])
    wh.row_dimensions[3].height = 42
    i_ = f"'{SHEET_IN}'!"
    for i in range(n):
        r = 4 + i          # baris hasil
        s = 20 + i         # baris data di sheet input
        _cell(wh, f"A{r}", f"={i_}A{s}", F_LABEL, fill=FILL_LABEL)
        _cell(wh, f"B{r}", f"=SUM({i_}C{s}:E{s})", F_TEXT, "#,##0")
        _cell(wh, f"C{r}", f"={i_}C{s}*{i_}$B$14+{i_}D{s}*{i_}$B$15+{i_}E{s}*{i_}$B$16", F_TEXT, "#,##0.0")
        _cell(wh, f"D{r}", f"={i_}F{s}", F_TEXT, "0.0")
        _cell(wh, f"E{r}", f"=600*D{r}", F_TEXT, "#,##0")
        _cell(wh, f"F{r}", f"=E{r}*{i_}$B$7*{i_}$B$8*{i_}$B$9*{i_}$B$10", F_TEXT, "#,##0")
        _cell(wh, f"G{r}", f"=F{r}*{i_}$B$6/{i_}$B$5", F_TEXT, "#,##0")
        _cell(wh, f"H{r}", f"=IF(G{r}>0,C{r}/G{r},0)", F_TEXT, "0.000")
        _cell(wh, f"I{r}", f'=IF(H{r}<{i_}$B$11,"OK / IDEAL","MACET / JENUH")', F_TEXT)
        _cell(wh, f"J{r}", f"={i_}$B$11", F_TEXT, "0.00")

    akhir = 3 + n                  # baris terakhir tabel hasil
    r_sum = akhir + 2              # baris ringkasan
    _cell(wh, f"A{r_sum}", "Pendekat jenuh", F_LABEL, fill=FILL_LABEL, align=LEFT)
    _cell(wh, f"B{r_sum}", f'=COUNTIF(I4:I{akhir},"MACET / JENUH")', F_TEXT, "0")
    wh.merge_cells(f"C{r_sum}:J{r_sum}")
    _cell(wh, f"C{r_sum}", f"Jumlah pendekat (dari {n}) yang berstatus MACET / JENUH", F_TEXT, align=LEFT)

    # Teks status MACET / JENUH berwarna merah
    wh.conditional_formatting.add(
        f"I4:I{akhir}",
        CellIsRule(operator="equal", formula=['"MACET / JENUH"'], font=Font(name=FONT, size=9, bold=True, color="FF0000")),
    )

    # Grafik: batang DS + garis putus-putus merah batas DS
    bar = BarChart()
    bar.type = "col"
    bar.title = "Tingkat Kejenuhan Simpang Arteri Primer"
    bar.x_axis.title = "Pendekat"
    bar.y_axis.title = "Nilai DS"
    bar.add_data(Reference(wh, min_col=8, min_row=3, max_row=akhir), titles_from_data=True)
    bar.set_categories(Reference(wh, min_col=1, min_row=4, max_row=akhir))
    bar.y_axis.scaling.min = 0
    bar.y_axis.number_format = "0.00"
    bar.x_axis.delete = False
    bar.y_axis.delete = False
    bar.legend.position = "b"

    garis = LineChart()
    garis.add_data(Reference(wh, min_col=10, min_row=3, max_row=akhir), titles_from_data=True)
    s_garis = garis.series[0]
    s_garis.graphicalProperties.line.solidFill = "FF0000"
    s_garis.graphicalProperties.line.dashStyle = "dash"
    s_garis.graphicalProperties.line.width = 22000
    s_garis.marker.symbol = "none"
    s_garis.smooth = False
    bar += garis

    bar.height, bar.width = 9, 16
    wh.add_chart(bar, f"A{r_sum + 2}")

    wh.column_dimensions["A"].width = 14
    for col, w in zip("BCDEFGHIJ", [16, 14, 11, 17, 24, 16, 12, 17, 11]):
        wh.column_dimensions[col].width = w
    wh.freeze_panes = "B4"

    # ======================================================
    # Sheet 3 - Catatan
    # ======================================================
    wc = wb.create_sheet(SHEET_CATATAN)
    _title(wc, "CATATAN RUMUS DAN ASUMSI", 2)
    catatan = [
        ("Volume Q (smp/jam)", "Q = MC x EMP_MC + LV x EMP_LV + HV x EMP_HV (EMP dari sheet 1)"),
        ("Arus jenuh dasar", "So = 600 x We"),
        ("Arus jenuh terkoreksi", "S = So x Fsf x Fg x Fp x Fuk"),
        ("Kapasitas", "C = S x (g / Co)"),
        ("Derajat kejenuhan", "DS = Q / C"),
        ("Status", "DS < 0.85 = OK / IDEAL; DS >= 0.85 = MACET / JENUH"),
        ("Jenis simpang", f"{jenis_simpang} (pendekat: {', '.join(kode_aktif)})"),
        ("Waktu hijau", "Satu nilai g dipakai untuk semua pendekat (sesuai input di web)"),
        ("Sumber input", "Seluruh nilai input (volume, lebar, faktor koreksi, Co, g) berasal dari isian pengguna di web"),
        ("Cakupan", "File ini hanya memuat yang dihitung web: Q, So, S, C, DS, status. "
                    "Waktu siklus optimum, tundaan, dan panjang antrian belum termasuk."),
    ]
    _head(wc, 3, ["Butir", "Keterangan"])
    wc.row_dimensions[3].height = 20
    for i, (k, v) in enumerate(catatan):
        r = 4 + i
        _cell(wc, f"A{r}", k, F_LABEL, fill=FILL_LABEL, align=LEFT)
        _cell(wc, f"B{r}", v, F_TEXT, align=LEFT)
        wc.row_dimensions[r].height = 28
    wc.column_dimensions["A"].width = 26
    wc.column_dimensions["B"].width = 95

    # Cetak: landscape dan muat 1 halaman lebar
    for sheet in wb.worksheets:
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True

    # Hitung ulang rumus saat file dibuka
    wb.calculation.fullCalcOnLoad = True

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    contoh = {k: {"MC": 800, "LV": 300, "HV": 50, "We": 7.0} for k in URUTAN}
    with open("contoh_hasil.xlsx", "wb") as f:
        f.write(buat_excel(contoh, 100, 35, 0.9, 1.0, 1.0, 1.0))
    print("Tersimpan: contoh_hasil.xlsx")
    