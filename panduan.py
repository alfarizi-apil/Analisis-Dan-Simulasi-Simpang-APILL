"""
panduan.py
Buku panduan pemakai AA SIPIL yang ditampilkan di halaman awal (dalam bentuk tab).
Isinya disesuaikan dengan alur lima halaman: Mulai, Data, Hasil, Animasi, Unduh.
"""

from textwrap import dedent

import streamlit as st

PENGANTAR = dedent("""
    **AA SIPIL** adalah aplikasi web untuk menganalisis kinerja simpang bersinyal (APILL) pada Jalan Arteri Primer
    dan menampilkannya dalam bentuk animasi lalu lintas. Perhitungan mengacu pada Pedoman Kapasitas Jalan
    Indonesia (PKJI) 2023.

    **Tujuan aplikasi**

    - Menghitung kapasitas, derajat kejenuhan (DS), dan status kinerja tiap pendekat simpang.
    - Membandingkan **kondisi eksisting** (waktu sinyal dari lapangan) dengan **usulan PKJI** (waktu siklus dan hijau
      dihitung otomatis).
    - Memperlihatkan hasil secara visual lewat grafik, batang kejenuhan, dan animasi, sehingga mudah dipahami orang non-teknis.
    - Menampilkan **langkah perhitungan** lengkap dengan angka, agar hasil bisa diperiksa satu per satu.
    - Menyimpan hasil dalam **Excel** (rumus hidup), **laporan PDF**, **laporan Word**, dan **CSV**.

    **Cakupan:** simpang 3 lengan dan 4 lengan, dengan prinsip satu pendekat = satu fase (semua pendekat terlindung).
    Urutan fase dapat diubah pada halaman Data.
""")

ALUR = dedent("""
    Aplikasi dibagi menjadi **lima halaman bertahap**. Tekan tombol **Lanjut** untuk berpindah, dan **Kembali**
    untuk memperbaiki isian. Isian Anda tetap tersimpan selama halaman tidak ditutup.

    | Halaman | Kegiatan | Tujuan |
    |---|---|---|
    | 1. Mulai | Pilih jenis simpang, isi Fuk, pilih opsi usulan, baca panduan | Menentukan jumlah lengan dan fase |
    | 2. Data | Isi tabel lalu lintas dan geometri, lalu pengaturan sinyal tiap fase | Memberi data masukan |
    | 3. Hasil | Baca kartu ringkasan, tabel, grafik, batang kejenuhan, dan langkah perhitungan | Menilai kinerja eksisting dan usulan |
    | 4. Animasi | Jalankan simulasi lalu lintas (eksisting atau usulan) | Melihat perilaku lalu lintas secara visual |
    | 5. Unduh | Baca kesimpulan, unduh Excel, PDF, Word, atau CSV | Menyimpan hasil untuk laporan |

    Penanda langkah di bagian atas menunjukkan posisi Anda: hijau = selesai, biru = sedang dikerjakan, abu-abu = belum.
""")

MENGISI_DATA = dedent("""
    **Halaman 1 - Mulai**

    | Isian | Arti |
    |---|---|
    | Jenis simpang | Simpang 4 lengan atau 3 lengan. Ilustrasi di sebelah kanan ikut berubah |
    | Lengan yang tidak ada | Muncul untuk simpang 3 lengan (U, T, S, atau B). Nilai awal: Timur |
    | Fuk (ukuran kota) | Faktor ukuran kota, rentang 0,5 sampai 1,5. Ambil dari tabel PKJI 2023 sesuai jumlah penduduk kota |
    | Hitung juga waktu sinyal usulan | Jika dicentang, aplikasi juga menghitung siklus dan hijau usulan PKJI |

    Kode pendekat: **U** = Utara, **T** = Timur, **S** = Selatan, **B** = Barat.

    **Halaman 2 - Data.** Klik sel untuk mengubah nilai.

    | Kolom | Arti | Satuan |
    |---|---|---|
    | Motor (MC), Mobil (LV), Truk/Bus (HV) | Jumlah kendaraan hasil survei | kend/jam |
    | We (m) | Lebar efektif pendekat (0,5 sampai 30) | meter |
    | Fsf, Fg, Fp | Faktor hambatan samping, kelandaian, dan parkir | tanpa satuan |
    | Belok kiri (%), Belok kanan (%) | Persentase kendaraan yang berbelok | % |
    | Fase ke- | Urutan fase (1 sampai jumlah lengan, tidak boleh sama) | - |
    | Hijau g, Kuning, Semua merah | Waktu sinyal tiap fase (hijau 1-200 d, kuning dan semua merah 0-10 d) | detik |

    Faktor konversi kendaraan (EMP): motor 0,15, mobil 1,00, truk/bus 1,30.

    **Waktu siklus (Co) tidak diisi.** Aplikasi menghitungnya: Co = jumlah (hijau + kuning + semua merah) seluruh fase.
    Hijau, kuning, dan semua merah boleh **berbeda tiap fase**. Mengubah kolom *Fase ke-* mengubah urutan nyala lampu
    pada simulasi dan urutan penyajian hasil.

    **Validasi saat menekan "Hitung".** Tidak boleh ada sel kosong; belok kiri + kanan tidak boleh lebih dari 100%;
    belok tidak boleh diisi jika lengan tujuannya tidak ada (mis. belok kiri dari U pada simpang tanpa lengan T);
    nomor fase harus lengkap dan tidak kembar. Jika ada yang salah, pesan kesalahan muncul dan Anda tetap di halaman Data.
""")

MEMBACA_HASIL = dedent("""
    **Kartu ringkasan** - total volume, DS tertinggi (merah bila 0,85 atau lebih), jumlah pendekat jenuh, siklus eksisting,
    dan siklus usulan.

    **Status kinerja**

    | Nilai DS | Status |
    |---|---|
    | kurang dari 0,85 | OK / IDEAL |
    | 0,85 atau lebih | MACET / JENUH (ditulis merah) |

    **Peringatan** muncul, misalnya, jika siklus berada di luar rentang layak (2 fase 40-80 d, 3 fase 50-100 d,
    4 fase 80-130 d), ada hijau kurang dari 10 detik, atau rasio arus simpang (IFR) mencapai 1 atau lebih sehingga
    usulan tidak dapat dihitung.

    **Halaman Hasil dibagi tiga tab**

    - **Tabel dan ringkasan:** tabel kondisi eksisting, tabel usulan PKJI, dan ringkasan simpang (WHH, IFR, siklus).
    - **Grafik dan kejenuhan:** grafik batang DS (eksisting vs usulan) dengan garis batas 0,85, grafik donat komposisi
      kendaraan, dan **batang kejenuhan** berwarna: hijau (DS < 0,70), kuning (0,70-0,85), merah (0,85-1,00),
      merah tua (> 1,00). Batas 0,70 hanya pembantu visual, bukan ketentuan PKJI.
    - **Langkah perhitungan:** pilih pendekat dan skenario, lalu lihat setiap rumus beserta angka yang dimasukkan.

    **Halaman Animasi.** Lampu menyala bergiliran sesuai urutan fase dengan hijau, kuning, dan semua merah dari tabel.
    Kendaraan berhenti di garis stop saat merah atau kuning, berjalan saat hijau, dan dapat lurus, belok kiri, atau belok
    kanan sesuai persentase belok (lalu lintas lajur kiri). Warna kendaraan: kuning = lurus, merah = belok kiri,
    hijau = belok kanan. Panel menampilkan status lampu, antrean, jumlah kendaraan lolos, dan diagram waktu sinyal.
    Animasi adalah ilustrasi perilaku lalu lintas, bukan simulasi mikroskopik yang dikalibrasi.

    **Halaman Unduh.** Tersedia *Kesimpulan* otomatis dan empat berkas: Excel (4 lembar, rumus hidup), laporan PDF,
    laporan Word, dan CSV.
""")

RUMUS = dedent("""
    | No | Besaran | Rumus |
    |---|---|---|
    | 1 | Arus lalu lintas | Q = MC x 0,15 + LV x 1,00 + HV x 1,30 (smp/jam) |
    | 2 | Arus jenuh dasar | J0 = 600 x We |
    | 3 | Faktor belok kiri | FBKi = 1,0 - RBKi x 0,16 |
    | 4 | Faktor belok kanan | FBKa = 1,0 + RBKa x 0,26 |
    | 5 | Arus jenuh | J = J0 x Fsf x Fuk x Fg x Fp x FBKi x FBKa |
    | 6 | Rasio arus | Rq/J = Q / J |
    | 7 | Waktu hijau hilang | WHH = jumlah (kuning + semua merah) seluruh fase |
    | 8 | Rasio arus simpang | IFR = jumlah Rq/J seluruh fase |
    | 9 | Siklus pra-penyesuaian | s = (1,5 x WHH + 5) / (1 - IFR) |
    | 10 | Hijau usulan | g = (s - WHH) x (Rq/J fase) / IFR, minimum 10 detik |
    | 11 | Kapasitas | C = J x (g / Co) |
    | 12 | Derajat kejenuhan | DS = Q / C |

    Jika ada hijau yang dinaikkan ke 10 detik, siklus usulan disesuaikan menjadi jumlah hijau ditambah WHH.
    Rumus mengacu pada PKJI 2023 melalui sumber sekunder; periksa kembali pada dokumen pedoman asli.
""")

CONTOH = dedent("""
    Data awal aplikasi (simpang 4 lengan): tiap pendekat motor 800, mobil 300, truk/bus 50, We 7 m, Fsf 0,90,
    belok kiri dan kanan masing-masing 25%, hijau 20 d, kuning 3 d, semua merah 2 d.

    | Besaran | Eksisting | Usulan PKJI |
    |---|---|---|
    | Q tiap pendekat | sekitar 485 smp/jam | sama |
    | Waktu siklus | 100 d | 70 d |
    | Hijau tiap fase | 20 d | sekitar 12,6 d |
    | IFR | 0,502 | 0,502 |
    | DS tiap pendekat | sekitar 0,63 | sekitar 0,70 |
    | Status | OK / IDEAL | OK / IDEAL |

    **Cara membaca:** semua pendekat masih di bawah 0,85, jadi simpang tidak jenuh. Siklus usulan 70 detik berada di
    bawah rentang layak untuk 4 fase (80-130 d), sehingga aplikasi memberi peringatan. Ini contoh yang baik untuk
    menjelaskan bahwa hasil hitungan tetap harus dinilai dengan pertimbangan teknis.

    **Contoh jam sibuk.** Motor/mobil/truk: U 1600/700/150, T 800/300/50, S 1200/500/80, B 800/300/50, belok kiri dan
    kanan 0%, hijau 20 d untuk semua fase. Eksisting: DS U sekitar 1,50 dan S sekitar 1,04 (melebihi kapasitas).
    Usulan: siklus sekitar 148 d dan DS sekitar 0,88 untuk semua pendekat. Hasilnya lebih merata, tetapi siklus melewati
    rentang layak dan DS masih di atas 0,85, sehingga perlu langkah lain seperti penambahan lebar atau lajur.
""")

BATASAN = dedent("""
    **Asumsi dan keterbatasan**

    - Satu pendekat = satu fase (semua pendekat terlindung). Fase gabungan dan pendekat terlawan belum didukung.
    - Faktor Fsf, Fg, Fp, dan Fuk diisi manual; ambil dari tabel dan grafik PKJI 2023 sesuai kondisi lokasi.
    - Tundaan, panjang antrian, rasio kendaraan henti, dan analisis kecelakaan belum tersedia.
    - Animasi adalah ilustrasi, bukan simulasi mikroskopik yang dikalibrasi.
    - Kesimpulan di halaman Unduh dibuat otomatis dengan aturan sederhana; tetap perlu ditinjau perencana lalu lintas.

    **Pertanyaan yang sering muncul**

    - *Mengapa batas DS 0,85?* Itu batas kinerja yang dipakai aplikasi (sesuai PKJI 2023). Di atasnya simpang dianggap
      mendekati atau melewati jenuh.
    - *Mengapa waktu siklus tidak diisi?* Karena siklus adalah jumlah hijau, kuning, dan semua merah seluruh fase.
    - *Apa bedanya eksisting dan usulan?* Eksisting memakai waktu sinyal lapangan. Usulan menghitung siklus dan hijau
      dari rasio arus.
    - *Dari mana nilai Fsf, Fg, Fp, dan Fuk?* Dari tabel dan grafik PKJI 2023 sesuai kondisi lokasi.
    - *Apakah hasil Excel bisa diubah?* Bisa. Ubah sel biru di lembar Input dan hasil ikut berubah.
    - *Apakah ada tundaan dan antrian?* Belum. Itu rencana pengembangan.
    - *Bagaimana jika ingin mengganti jenis simpang?* Kembali ke halaman 1, pilih jenis lain; tabel data akan disiapkan ulang.
""")


def tampilkan_panduan():
    """Menampilkan buku panduan dalam beberapa tab."""
    tab = st.tabs(["Pengantar", "Alur 5 Halaman", "Mengisi Data", "Membaca Hasil", "Rumus", "Contoh", "Batasan dan FAQ"])
    for t, isi in zip(tab, [PENGANTAR, ALUR, MENGISI_DATA, MEMBACA_HASIL, RUMUS, CONTOH, BATASAN]):
        with t:
            st.markdown(isi)
