"""
ekspor_excel.py
Membuat file Excel (.xlsx) hasil analisis Simpang APILL (satu pendekat = satu fase)
untuk diunduh dari web Streamlit.

Isi file:
  1. Input         -> parameter umum + tabel data tiap pendekat (sel biru = input)
  2. Eksisting     -> kinerja dengan waktu hijau yang Anda isi (semua RUMUS Excel)
  3. Usulan PKJI   -> siklus dan hijau dihitung otomatis + perbandingan DS (rumus Excel)
  4. Catatan       -> rumus, asumsi, dan cakupan

Seluruh angka di sheet 2 dan 3 adalah rumus yang merujuk ke sheet 1, jadi jika input
diubah di Excel, hasilnya ikut berubah otomatis.
"""

import io

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from kalkulasi import BATAS_DS, HIJAU_MINIMUM, RENTANG_SIKLUS, konversi_ke_smp

# ---- Gaya ----
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
S_IN, S_EKS, S_USL, S_CAT = "1. Input", "2. Eksisting", "3. Usulan PKJI", "4. Catatan"
IN = f"'{S_IN}'!"
EKS = f"'{S_EKS}'!"


def _title(ws, text, last_col):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    c = ws.cell(row=1, column=1, value=text)
    c.font, c.fill, c.alignment = F_TITLE, FILL_TITLE, LEFT
    ws.row_dimensions[1].height = 24


def _section(ws, row, text, last_col):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    c = ws.cell(row=row, column=1, value=text)
    c.font, c.fill, c.alignment = F_SECTION, FILL_SECTION, LEFT


def _head(ws, row, labels, tinggi=42):
    for i, text in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=text)
        c.font, c.fill, c.alignment, c.border = F_HEAD, FILL_HEAD, CENTER, BORDER
    ws.row_dimensions[row].height = tinggi


def _cell(ws, ref, value, font=F_TEXT, fmt=None, fill=None, align=CENTER):
    c = ws[ref]
    c.value = value
    c.font, c.alignment, c.border = font, align, BORDER
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    return c


def _ringkas(ws, row, label, rumus, fmt, keterangan, last_col):
    """Satu baris ringkasan: label (A:C digabung), nilai di kolom D, keterangan (E sampai akhir)."""
    ws.merge_cells(f"A{row}:C{row}")
    _cell(ws, f"A{row}", label, F_LABEL, fill=FILL_LABEL, align=LEFT)
    _cell(ws, f"D{row}", rumus, F_TEXT, fmt)
    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=last_col)
    _cell(ws, f"E{row}", keterangan, F_NOTE, align=LEFT)


def _grafik_ds(ws_tujuan, anchor, seri, batas_ref, n):
    """
    Grafik batang DS + garis putus-putus merah batas DS.
    seri -> list (worksheet, nomor_kolom) untuk tiap seri batang (judul dari baris 3)
    batas_ref -> (worksheet, nomor_kolom) kolom batas DS
    """
    bar = BarChart()
    bar.type = "col"
    bar.grouping = "clustered"
    bar.title = "Tingkat Kejenuhan Simpang Arteri Primer"
    bar.x_axis.title = "Pendekat"
    bar.y_axis.title = "Nilai DS"
    for ws_s, kol in seri:
        bar.add_data(Reference(ws_s, min_col=kol, min_row=3, max_row=3 + n), titles_from_data=True)
    kat_ws = seri[0][0]
    bar.set_categories(Reference(kat_ws, min_col=1, min_row=4, max_row=3 + n))
    bar.y_axis.scaling.min = 0
    bar.y_axis.number_format = "0.00"
    bar.x_axis.delete = False
    bar.y_axis.delete = False
    bar.legend.position = "b"

    garis = LineChart()
    ws_b, kol_b = batas_ref
    garis.add_data(Reference(ws_b, min_col=kol_b, min_row=3, max_row=3 + n), titles_from_data=True)
    sg = garis.series[0]
    sg.graphicalProperties.line.solidFill = "FF0000"
    sg.graphicalProperties.line.dashStyle = "dash"
    sg.graphicalProperties.line.width = 22000
    sg.marker.symbol = "none"
    sg.smooth = False
    bar += garis
    bar.height, bar.width = 9, 17
    ws_tujuan.add_chart(bar, anchor)


def buat_excel(data, Fuk, jenis_simpang=None, sertakan_usulan=True, batas_ds=BATAS_DS):
    """
    Membuat file Excel hasil analisis dan mengembalikannya sebagai bytes.

    Param : data -> dict {kode: {"MC","LV","HV","We","Fsf","Fg","Fp",
                                  "p_kiri","p_kanan" (persen), "g","kuning","ms" (detik)}}
                    (hanya pendekat yang ada: 3 atau 4)
            Fuk  -> faktor ukuran kota
            jenis_simpang   -> teks, mis. "Simpang 4 lengan" (opsional)
            sertakan_usulan -> True: buat sheet usulan PKJI
    Return: bytes isi file .xlsx (siap dipakai st.download_button)
    """
    kode_aktif = [k for k in URUTAN if k in data]
    n = len(kode_aktif)
    jenis_simpang = jenis_simpang or f"Simpang {n} lengan"
    emp_mc, emp_lv, emp_hv = konversi_ke_smp(1, 0, 0), konversi_ke_smp(0, 1, 0), konversi_ke_smp(0, 0, 1)

    wb = Workbook()

    # ======================================================
    # Sheet 1 - Input
    # ======================================================
    ws = wb.active
    ws.title = S_IN
    kol_in = 14
    _title(ws, "INPUT ANALISIS SIMPANG APILL - JALAN ARTERI PRIMER (PKJI 2023)", kol_in)
    ws.merge_cells("A2:N2")
    ws["A2"].value = "Sel bertulisan BIRU = input yang boleh diubah. Sheet 2 dan 3 otomatis ikut berubah."
    ws["A2"].font, ws["A2"].fill, ws["A2"].alignment = F_NOTE, FILL_NOTE, LEFT
    ws.merge_cells("A3:N3")
    ws["A3"].value = f"Jenis simpang: {jenis_simpang}  |  Pendekat: {', '.join(kode_aktif)}  |  Satu pendekat = satu fase (terlindung)"
    ws["A3"].font, ws["A3"].alignment = F_LABEL, LEFT

    _section(ws, 4, "A. PARAMETER UMUM", kol_in)
    umum = [
        (5, "Fuk (ukuran kota)", Fuk, "0.00", "Faktor penyesuaian ukuran kota (satu nilai untuk seluruh simpang)"),
        (6, "Batas DS", batas_ds, "0.00", "DS < batas = OK / IDEAL; DS >= batas = MACET / JENUH"),
        (7, "EMP MC (smp/kend)", emp_mc, "0.00", "Dari konversi_ke_smp di kalkulasi.py (pendekat terlindung)"),
        (8, "EMP LV (smp/kend)", emp_lv, "0.00", "Dari konversi_ke_smp di kalkulasi.py"),
        (9, "EMP HV (smp/kend)", emp_hv, "0.00", "Dari konversi_ke_smp di kalkulasi.py"),
    ]
    for r, label, nilai, fmt, ket in umum:
        ws.merge_cells(f"A{r}:B{r}")
        _cell(ws, f"A{r}", label, F_LABEL, fill=FILL_LABEL, align=LEFT)
        _cell(ws, f"C{r}", nilai, F_INPUT, fmt)
        ws.merge_cells(f"D{r}:N{r}")
        _cell(ws, f"D{r}", ket, F_TEXT, align=LEFT)
    # Catatan: nilai Fuk di C5, Batas DS di C6, EMP di C7:C9 (sel gabungan A:B untuk label)

    _section(ws, 11, "B. DATA TIAP PENDEKAT / FASE", kol_in)
    _head(ws, 12, ["Pendekat", "Nama", "MC\n(kend/jam)", "LV\n(kend/jam)", "HV\n(kend/jam)", "Lebar We\n(m)",
                   "Fsf\n(FHS)", "Fg", "Fp", "Belok kiri\n(%)", "Belok kanan\n(%)",
                   "Hijau g\n(detik)", "Kuning\n(detik)", "Semua merah\n(detik)"], tinggi=34)
    for i, kode in enumerate(kode_aktif):
        r = 13 + i
        d = data[kode]
        _cell(ws, f"A{r}", kode, F_LABEL, fill=FILL_LABEL)
        _cell(ws, f"B{r}", NAMA_PENDEKAT[kode], F_TEXT)
        for kol, kunci, fmt in [("C", "MC", "#,##0"), ("D", "LV", "#,##0"), ("E", "HV", "#,##0"),
                                ("F", "We", "0.0"), ("G", "Fsf", "0.00"), ("H", "Fg", "0.00"), ("I", "Fp", "0.00"),
                                ("J", "p_kiri", "0.0"), ("K", "p_kanan", "0.0"),
                                ("L", "g", "0.0"), ("M", "kuning", "0.0"), ("N", "ms", "0.0")]:
            _cell(ws, f"{kol}{r}", d[kunci], F_INPUT, fmt)
    ws.column_dimensions["A"].width = 13
    ws.column_dimensions["B"].width = 11
    for col in "CDEFGHIJKLMN":
        ws.column_dimensions[col].width = 12

    # Referensi sel parameter umum
    REF_FUK, REF_BATAS = f"{IN}$C$5", f"{IN}$C$6"
    REF_EMP = (f"{IN}$C$7", f"{IN}$C$8", f"{IN}$C$9")

    # ======================================================
    # Sheet 2 - Eksisting
    # ======================================================
    we = wb.create_sheet(S_EKS)
    kol_e = 14
    _title(we, "KINERJA SIMPANG KONDISI EKSISTING (HIJAU DIISI PENGGUNA) - PKJI 2023", kol_e)
    we.merge_cells("A2:N2")
    we["A2"].value = "Seluruh angka adalah rumus yang merujuk ke sheet '1. Input'."
    we["A2"].font, we["A2"].fill, we["A2"].alignment = F_NOTE, FILL_NOTE, LEFT
    _head(we, 3, ["Pendekat", "Volume Q\n(smp/jam)", "Lebar We\n(m)", "J0 = 600 x We\n(smp/jam)",
                  "FBKi", "FBKa", "J = J0 x Fsf x Fg x Fp\nx Fuk x FBKi x FBKa",
                  "Rq/J = Q / J", "Hijau g\n(d)", "Kuning\n(d)", "Semua merah\n(d)",
                  "C = J x g / Co\n(smp/jam)", "DS Eksisting\n(Q / C)", "Status"])
    akhir = 3 + n
    r_whh, r_co, r_ifr, r_jenuh, r_rentang = n + 5, n + 6, n + 7, n + 8, n + 9
    CO = f"$D${r_co}"
    for i in range(n):
        r, s = 4 + i, 13 + i
        _cell(we, f"A{r}", f"={IN}A{s}", F_LABEL, fill=FILL_LABEL)
        _cell(we, f"B{r}", f"={IN}C{s}*{REF_EMP[0]}+{IN}D{s}*{REF_EMP[1]}+{IN}E{s}*{REF_EMP[2]}", F_TEXT, "#,##0.0")
        _cell(we, f"C{r}", f"={IN}F{s}", F_TEXT, "0.0")
        _cell(we, f"D{r}", f"=600*C{r}", F_TEXT, "#,##0")
        _cell(we, f"E{r}", f"=1-{IN}J{s}/100*0.16", F_TEXT, "0.000")
        _cell(we, f"F{r}", f"=1+{IN}K{s}/100*0.26", F_TEXT, "0.000")
        _cell(we, f"G{r}", f"=D{r}*{IN}G{s}*{IN}H{s}*{IN}I{s}*{REF_FUK}*E{r}*F{r}", F_TEXT, "#,##0")
        _cell(we, f"H{r}", f"=IF(G{r}>0,B{r}/G{r},0)", F_TEXT, "0.000")
        _cell(we, f"I{r}", f"={IN}L{s}", F_TEXT, "0.0")
        _cell(we, f"J{r}", f"={IN}M{s}", F_TEXT, "0.0")
        _cell(we, f"K{r}", f"={IN}N{s}", F_TEXT, "0.0")
        _cell(we, f"L{r}", f"=G{r}*I{r}/{CO}", F_TEXT, "#,##0")
        _cell(we, f"M{r}", f"=IF(L{r}>0,B{r}/L{r},0)", F_TEXT, "0.000")
        _cell(we, f"N{r}", f'=IF(M{r}<{REF_BATAS},"OK / IDEAL","MACET / JENUH")', F_TEXT)
    we.conditional_formatting.add(
        f"N4:N{akhir}",
        CellIsRule(operator="equal", formula=['"MACET / JENUH"'], font=Font(name=FONT, size=9, bold=True, color="FF0000")),
    )

    lo, hi = RENTANG_SIKLUS.get(n, (None, None))
    _ringkas(we, r_whh, "Waktu hijau hilang WHH (d)", f"=SUM(J4:J{akhir})+SUM(K4:K{akhir})", "0.0",
             "WHH = jumlah (kuning + semua merah) seluruh fase", kol_e)
    _ringkas(we, r_co, "Waktu siklus Co (d)", f"=SUM(I4:I{akhir})+D{r_whh}", "0.0",
             "Co = jumlah hijau seluruh fase + WHH (dihitung, bukan diisi)", kol_e)
    _ringkas(we, r_ifr, "Rasio arus simpang IFR", f"=SUM(H4:H{akhir})", "0.000",
             "IFR = jumlah Rq/J kritis (satu pendekat = satu fase)", kol_e)
    _ringkas(we, r_jenuh, "Pendekat jenuh", f'=COUNTIF(N4:N{akhir},"MACET / JENUH")', "0",
             f"Jumlah pendekat (dari {n}) berstatus MACET / JENUH", kol_e)
    _ringkas(we, r_rentang, "Cek rentang siklus",
             f'=IF(AND(D{r_co}>={lo},D{r_co}<={hi}),"Dalam rentang layak","Di luar rentang layak")' if lo else "-",
             "General", f"Rentang siklus layak untuk {n} fase: {lo}-{hi} detik (PKJI 2023)", kol_e)

    we.column_dimensions["A"].width = 14
    for col, w in zip("BCDEFGHIJKLMN", [13, 10, 14, 9, 9, 22, 12, 9, 9, 12, 15, 14, 16]):
        we.column_dimensions[col].width = w
    we.freeze_panes = "B4"

    # ======================================================
    # Sheet 3 - Usulan PKJI
    # ======================================================
    if sertakan_usulan:
        wu = wb.create_sheet(S_USL)
        kol_u = 11
        _title(wu, "USULAN WAKTU SINYAL BERDASARKAN PKJI 2023 (SIKLUS DAN HIJAU DIHITUNG OTOMATIS)", kol_u)
        wu.merge_cells("A2:K2")
        wu["A2"].value = "Rumus: s = (1,5 x WHH + 5) / (1 - IFR);  WHi = (s - WHH) x Rq/J_i / IFR;  hijau minimum 10 d."
        wu["A2"].font, wu["A2"].fill, wu["A2"].alignment = F_NOTE, FILL_NOTE, LEFT
        _head(wu, 3, ["Pendekat", "Rq/J", "Rasio fase\n(Rq/J / IFR)", "Hijau usulan\n(d)", "Kuning\n(d)",
                      "Semua merah\n(d)", "J\n(smp/jam hijau)", "C = J x g / Co\n(smp/jam)",
                      "DS Usulan\n(Q / C)", "Status", "Batas DS"])
        u_whh, u_ifr, u_spra, u_co, u_rentang = n + 5, n + 6, n + 7, n + 8, n + 9
        for i in range(n):
            r, e = 4 + i, 4 + i
            _cell(wu, f"A{r}", f"={EKS}A{e}", F_LABEL, fill=FILL_LABEL)
            _cell(wu, f"B{r}", f"={EKS}H{e}", F_TEXT, "0.000")
            _cell(wu, f"C{r}", f"=IF($D${u_ifr}>0,B{r}/$D${u_ifr},0)", F_TEXT, "0.000")
            _cell(wu, f"D{r}", f'=IF(ISNUMBER($D${u_spra}),MAX({HIJAU_MINIMUM},($D${u_spra}-$D${u_whh})*C{r}),"-")', F_TEXT, "0.0")
            _cell(wu, f"E{r}", f"={EKS}J{e}", F_TEXT, "0.0")
            _cell(wu, f"F{r}", f"={EKS}K{e}", F_TEXT, "0.0")
            _cell(wu, f"G{r}", f"={EKS}G{e}", F_TEXT, "#,##0")
            _cell(wu, f"H{r}", f'=IF(ISNUMBER(D{r}),G{r}*D{r}/$D${u_co},"-")', F_TEXT, "#,##0")
            _cell(wu, f"I{r}", f'=IF(ISNUMBER(H{r}),{EKS}B{e}/H{r},"-")', F_TEXT, "0.000")
            _cell(wu, f"J{r}", f'=IF(ISNUMBER(I{r}),IF(I{r}<{REF_BATAS},"OK / IDEAL","MACET / JENUH"),"-")', F_TEXT)
            _cell(wu, f"K{r}", f"={REF_BATAS}", F_TEXT, "0.00")
        wu.conditional_formatting.add(
            f"J4:J{akhir}",
            CellIsRule(operator="equal", formula=['"MACET / JENUH"'], font=Font(name=FONT, size=9, bold=True, color="FF0000")),
        )
        _ringkas(wu, u_whh, "Waktu hijau hilang WHH (d)", f"={EKS}D{r_whh}", "0.0", "Sama dengan sheet 2", kol_u)
        _ringkas(wu, u_ifr, "Rasio arus simpang IFR", f"={EKS}D{r_ifr}", "0.000", "Sama dengan sheet 2", kol_u)
        _ringkas(wu, u_spra, "Siklus pra-penyesuaian s (d)",
                 f'=IF(AND(D{u_ifr}>0,D{u_ifr}<1),(1.5*D{u_whh}+5)/(1-D{u_ifr}),"tidak dapat dihitung")', "0.0",
                 "s = (1,5 x WHH + 5) / (1 - IFR). Jika IFR >= 1, siklus tidak dapat dihitung", kol_u)
        _ringkas(wu, u_co, "Siklus disesuaikan Co (d)",
                 f'=IF(ISNUMBER(D{u_spra}),SUM(D4:D{akhir})+D{u_whh},"-")', "0.0",
                 "Co = jumlah hijau usulan + WHH", kol_u)
        _ringkas(wu, u_rentang, "Cek rentang siklus",
                 f'=IF(ISNUMBER(D{u_co}),IF(AND(D{u_co}>={lo},D{u_co}<={hi}),"Dalam rentang layak","Di luar rentang layak"),"-")' if lo else "-",
                 "General", f"Rentang siklus layak untuk {n} fase: {lo}-{hi} detik (PKJI 2023)", kol_u)
        wu.column_dimensions["A"].width = 14
        for col, w in zip("BCDEFGHIJK", [10, 14, 14, 10, 14, 16, 16, 14, 16, 10]):
            wu.column_dimensions[col].width = w
        wu.freeze_panes = "B4"
        _grafik_ds(wu, f"A{n + 11}", [(we, 13), (wu, 9)], (wu, 11), n)
    else:
        # Tanpa usulan: grafik DS eksisting ditaruh di sheet 2 (kolom batas DS memakai kolom P)
        we["P3"].value = "Batas DS"
        we["P3"].font = F_HEAD
        we["P3"].fill = FILL_HEAD
        for i in range(n):
            we[f"P{4 + i}"].value = f"={REF_BATAS}"
            we[f"P{4 + i}"].number_format = "0.00"
        _grafik_ds(we, f"A{n + 11}", [(we, 13)], (we, 16), n)

    # ======================================================
    # Sheet 4 - Catatan
    # ======================================================
    wc = wb.create_sheet(S_CAT)
    _title(wc, "CATATAN RUMUS, ASUMSI, DAN CAKUPAN", 2)
    catatan = [
        ("Volume Q (smp/jam)", "Q = MC x EMP_MC + LV x EMP_LV + HV x EMP_HV (EMP pendekat terlindung, sheet 1)"),
        ("Arus jenuh dasar", "J0 = 600 x We (pendekat terlindung)"),
        ("Faktor belok", "FBKi = 1,0 - RBKi x 0,16;  FBKa = 1,0 + RBKa x 0,26 (RBKi, RBKa = proporsi belok kiri/kanan)"),
        ("Arus jenuh", "J = J0 x Fsf(FHS) x Fuk x Fg x Fp x FBKi x FBKa"),
        ("Rasio arus", "Rq/J = Q / J;  IFR = jumlah Rq/J kritis seluruh fase (satu pendekat = satu fase)"),
        ("Waktu hijau hilang", "WHH = jumlah (kuning + semua merah) seluruh fase"),
        ("Eksisting", "Co = jumlah hijau + WHH;  C = J x g / Co;  DS = Q / C"),
        ("Usulan PKJI", "s = (1,5 x WHH + 5) / (1 - IFR);  WHi = (s - WHH) x Rq/J_i / IFR;  hijau minimum 10 d; Co = jumlah hijau + WHH"),
        ("Rentang siklus layak", "2 fase: 40-80 d;  3 fase: 50-100 d;  4 fase: 80-130 d"),
        ("Status", f"DS < {batas_ds} = OK / IDEAL;  DS >= {batas_ds} = MACET / JENUH"),
        ("Jenis simpang", f"{jenis_simpang} (pendekat: {', '.join(kode_aktif)})"),
        ("Asumsi", "Satu pendekat = satu fase sehingga semua pendekat bertipe terlindung. Belok kiri langsung (LTOR) tidak dimodelkan."),
        ("Cakupan", "Belum termasuk tundaan, panjang antrian, dan rasio kendaraan henti."),
        ("Sumber", "Pedoman Kapasitas Jalan Indonesia (PKJI) 2023 - Kapasitas Simpang APILL. Cek ulang pada dokumen asli."),
    ]
    _head(wc, 3, ["Butir", "Keterangan"], tinggi=20)
    for i, (k, v) in enumerate(catatan):
        r = 4 + i
        _cell(wc, f"A{r}", k, F_LABEL, fill=FILL_LABEL, align=LEFT)
        _cell(wc, f"B{r}", v, F_TEXT, align=LEFT)
        wc.row_dimensions[r].height = 28
    wc.column_dimensions["A"].width = 24
    wc.column_dimensions["B"].width = 110

    for sheet in wb.worksheets:
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
    wb.calculation.fullCalcOnLoad = True

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


if __name__ == "__main__":
    dasar = dict(We=7.0, Fsf=0.9, Fg=1.0, Fp=1.0, p_kiri=0, p_kanan=0, g=20, kuning=3, ms=2)
    contoh = {
        "U": dict(MC=1600, LV=700, HV=150, **dasar), "T": dict(MC=800, LV=300, HV=50, **dasar),
        "S": dict(MC=1200, LV=500, HV=80, **dasar), "B": dict(MC=800, LV=300, HV=50, **dasar),
    }
    with open("contoh_hasil.xlsx", "wb") as f:
        f.write(buat_excel(contoh, 1.0))
    print("Tersimpan: contoh_hasil.xlsx")
