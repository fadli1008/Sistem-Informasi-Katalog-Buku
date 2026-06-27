import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import time
import base64 # TAMBAHAN: Untuk konversi gambar ke Base64

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME
# ==========================================
st.set_page_config(
    page_title="Katalog Perpustakaan SMAN 7", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    
    div.stButton > button:first-child {
        background-color: #0284c7;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        background-color: #0369a1;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0284c7 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INISIALISASI DATABASE & STATE
# ==========================================
def init_db():
    conn = sqlite3.connect('perpustakaan.db', check_same_thread=False)
    c = conn.cursor()
    
    # Kolom cover_url akan digunakan untuk menyimpan string Base64 gambar
    c.execute('''
        CREATE TABLE IF NOT EXISTS buku (
            id_buku INTEGER PRIMARY KEY AUTOINCREMENT,
            cover_url TEXT,
            judul TEXT NOT NULL,
            pengarang TEXT NOT NULL,
            kategori TEXT NOT NULL,
            tahun INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS siswa (
            username TEXT PRIMARY KEY,
            nama TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS peminjaman (
            id_pinjam INTEGER PRIMARY KEY AUTOINCREMENT,
            id_buku INTEGER,
            username_siswa TEXT,
            tanggal_pinjam TEXT,
            status_pinjam TEXT,
            FOREIGN KEY(id_buku) REFERENCES buku(id_buku),
            FOREIGN KEY(username_siswa) REFERENCES siswa(username)
        )
    ''')
    
    c.execute("SELECT * FROM admin WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = hashlib.sha256("password123".encode()).hexdigest()
        c.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', hashed_pw))
        
    c.execute("SELECT * FROM siswa WHERE username='siswa'")
    if not c.fetchone():
        hashed_pw_siswa = hashlib.sha256("password123".encode()).hexdigest()
        c.execute("INSERT INTO siswa (username, nama, password) VALUES (?, ?, ?)", ('siswa', 'Sandi Perdana Putra', hashed_pw_siswa))
        
    conn.commit()
    return conn

conn = init_db()

if 'role' not in st.session_state:
    st.session_state['role'] = None  
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'nama' not in st.session_state:
    st.session_state['nama'] = None

# ==========================================
# 3. FUNGSI LOGIKA SISTEM
# ==========================================
def login_user(table, username, password):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} WHERE username=? AND password=?", (username, hashed_pw))
    return c.fetchone()

def get_stats():
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM buku")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM buku WHERE status='Tersedia'")
    tersedia = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM buku WHERE status='Dipinjam'")
    dipinjam = c.fetchone()[0]
    return total, tersedia, dipinjam

# ==========================================
# 4. STRUKTUR NAVIGASI UTAMA
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #0284c7;'>🏫 SMAN 7</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.9rem; color: #64748b;'>Bengkulu Selatan</p>", unsafe_allow_html=True)
    st.divider()
    
    menu = st.radio(
        "PILIH NAVIGASI",
        ["🔍 Pencarian Katalog", "🧑 Area Siswa (User)", "🔒 Area Petugas (Admin)"],
        index=0
    )
    st.divider()
    
    if st.session_state['role']:
        st.write(f"🟢 **Sesi Aktif: {st.session_state['role']}**")
        st.write(f"Nama: {st.session_state['nama']}")
        if st.button("Keluar Sistem", use_container_width=True):
            st.session_state['role'] = None
            st.session_state['username'] = None
            st.session_state['nama'] = None
            st.rerun()

st.markdown('<h1 class="main-title">Sistem Informasi Katalog & Peminjaman Buku</h1>', unsafe_allow_html=True)
st.divider()

# ------------------------------------------
# MENU: PENCARIAN KATALOG (PUBLIK)
# ------------------------------------------
if menu == "🔍 Pencarian Katalog":
    with st.container(border=True):
        st.markdown("##### 🛠️ Panel Penyaringan Informasi")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("Cari Judul Buku atau Pengarang", placeholder="Ketik kata kunci...", label_visibility="collapsed")
        with col2:
            kategori_filter = st.selectbox("Kategori Buku", ["Semua Kategori", "Pelajaran", "Referensi", "Literatur Umum"], label_visibility="collapsed")
            
    query = "SELECT id_buku as ID, cover_url as 'Sampul', judul as 'Judul Buku', pengarang as 'Pengarang', kategori as 'Kategori', tahun as 'Tahun Terbit', status as 'Status' FROM buku WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (judul LIKE ? OR pengarang LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    if kategori_filter != "Semua Kategori":
        query += " AND kategori = ?"
        params.append(kategori_filter)
        
    df = pd.read_sql_query(query, conn, params=params)
    
    if df.empty:
        st.info("Koleksi buku tidak ditemukan atau belum terdata dalam sistem.")
    else:
        def color_status(val):
            if val == 'Tersedia': color = '#28a745'
            elif val in ['Menunggu Approval', 'Menunggu Pengembalian']: color = '#ffc107'
            else: color = '#dc3545'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(
            df.style.map(color_status, subset=['Status']), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Sampul": st.column_config.ImageColumn("Sampul Buku", help="Tampilan fisik buku")
            }
        )

# ------------------------------------------
# MENU: AREA SISWA (USER INTERACTION)
# ------------------------------------------
elif menu == "🧑 Area Siswa (User)":
    
    if st.session_state['role'] != 'Siswa':
        tab_login, tab_daftar = st.tabs(["🔐 Login Siswa", "📝 Registrasi Akun Baru"])
        
        with tab_login:
            col1, col2, col3 = st.columns([1, 1.5, 1])
            with col2:
                with st.container(border=True):
                    with st.form("form_login_siswa"):
                        st.markdown("##### Login Akun Siswa")
                        user_in = st.text_input("Username / NISN")
                        pass_in = st.text_input("Password", type="password")
                        if st.form_submit_button("Masuk", use_container_width=True):
                            res = login_user('siswa', user_in, pass_in)
                            if res:
                                st.session_state['role'] = 'Siswa'
                                st.session_state['username'] = res[0]
                                st.session_state['nama'] = res[1]
                                st.success("Login Berhasil!")
                                st.rerun()
                            else:
                                st.error("Username atau Password salah!")
                                
        with tab_daftar:
            col1, col2, col3 = st.columns([1, 1.5, 1])
            with col2:
                with st.container(border=True):
                    with st.form("form_daftar_siswa", clear_on_submit=True):
                        st.markdown("##### Pendaftaran Akun Siswa Baru")
                        reg_user = st.text_input("Buat Username / NISN")
                        reg_nama = st.text_input("Nama Lengkap Anda")
                        reg_pass = st.text_input("Buat Password", type="password")
                        
                        if st.form_submit_button("Daftar Sekarang", use_container_width=True):
                            if not reg_user or not reg_nama or not reg_pass:
                                st.error("Semua kolom registrasi wajib diisi!")
                            else:
                                try:
                                    c = conn.cursor()
                                    hashed = hashlib.sha256(reg_pass.encode()).hexdigest()
                                    c.execute("INSERT INTO siswa (username, nama, password) VALUES (?, ?, ?)", (reg_user, reg_nama, hashed))
                                    conn.commit()
                                    st.success("Akun berhasil dibuat! Silakan pindah ke tab Login.")
                                except sqlite3.IntegrityError:
                                    st.error("Username sudah terdaftar, gunakan username lain.")
                                    
    else:
        st.markdown(f"### Halo, {st.session_state['nama']} 👋")
        t1, t2 = st.tabs(["📖 Ajukan Peminjaman", "🕒 Status & Pengembalian"])
        
        with t1:
            with st.container(border=True):
                st.markdown("##### Formulir Pengajuan Pinjam Buku")
                df_ready = pd.read_sql_query("SELECT id_buku, judul, pengarang FROM buku WHERE status='Tersedia'", conn)
                
                if df_ready.empty:
                    st.warning("Maaf, saat ini tidak ada buku yang siap dipinjam.")
                else:
                    df_ready['opsi'] = df_ready['id_buku'].astype(str) + " - " + df_ready['judul'] + " (" + df_ready['pengarang'] + ")"
                    pilihan_buku = st.selectbox("Pilih Buku yang Ingin Anda Pinjam", options=df_ready['opsi'].tolist())
                    
                    if st.button("Kirim Pengajuan ke Petugas", use_container_width=True):
                        with st.spinner("Memproses pengajuan Anda..."):
                            id_terpilih = int(pilihan_buku.split(" - ")[0])
                            tgl_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            c = conn.cursor()
                            c.execute("INSERT INTO peminjaman (id_buku, username_siswa, tanggal_pinjam, status_pinjam) VALUES (?, ?, ?, 'Menunggu Approval')", 
                                      (id_terpilih, st.session_state['username'], tgl_sekarang))
                            c.execute("UPDATE buku SET status='Menunggu Approval' WHERE id_buku=?", (id_terpilih,))
                            conn.commit()
                            time.sleep(1)
                            
                        st.success("✅ Pengajuan berhasil dikirim! Menunggu konfirmasi petugas...")
                        time.sleep(2)
                        st.rerun()
                        
        with t2:
            df_dipinjam = pd.read_sql_query("SELECT p.id_pinjam, b.judul, b.pengarang FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku WHERE p.username_siswa = ? AND p.status_pinjam = 'Dipinjam'", conn, params=[st.session_state['username']])
            
            if not df_dipinjam.empty:
                with st.container(border=True):
                    st.markdown("##### 🔄 Kembalikan Buku")
                    df_dipinjam['opsi'] = df_dipinjam['id_pinjam'].astype(str) + " - " + df_dipinjam['judul']
                    buku_kembali = st.selectbox("Pilih buku yang ingin Anda kembalikan ke perpustakaan:", options=df_dipinjam['opsi'].tolist())
                    
                    if st.button("Ajukan Pengembalian Buku", use_container_width=True):
                        with st.spinner("Mengirim pengajuan pengembalian..."):
                            id_p_kembali = int(buku_kembali.split(" - ")[0])
                            c = conn.cursor()
                            c.execute("UPDATE peminjaman SET status_pinjam='Menunggu Pengembalian' WHERE id_pinjam=?", (id_p_kembali,))
                            conn.commit()
                            time.sleep(1)
                        st.success("✅ Berhasil diajukan! Silakan serahkan fisik buku ke petugas untuk diselesaikan.")
                        time.sleep(2)
                        st.rerun()
                        
            st.markdown("##### Riwayat Status Transaksi Anda")
            q_riwayat = '''
                SELECT p.id_pinjam as 'ID Transaksi', b.judul as 'Judul Buku', b.pengarang as 'Pengarang', p.tanggal_pinjam as 'Waktu Pengajuan', p.status_pinjam as 'Status Transaksi'
                FROM peminjaman p 
                JOIN buku b ON p.id_buku = b.id_buku
                WHERE p.username_siswa = ?
                ORDER BY p.id_pinjam DESC
            '''
            df_riwayat = pd.read_sql_query(q_riwayat, conn, params=[st.session_state['username']])
            
            if df_riwayat.empty:
                st.info("Anda belum memiliki riwayat pengajuan.")
            else:
                st.dataframe(df_riwayat, use_container_width=True, hide_index=True)

# ------------------------------------------
# MENU: AREA PETUGAS (ADMIN)
# ------------------------------------------
elif menu == "🔒 Area Petugas (Admin)":
    
    if st.session_state['role'] != 'Admin':
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>🔐 Autentikasi Petugas Admin</h4>", unsafe_allow_html=True)
                with st.form("login_form_admin", clear_on_submit=True):
                    admin_user = st.text_input("Username")
                    admin_pass = st.text_input("Password", type="password")
                    if st.form_submit_button("Masuk Ke Sistem", use_container_width=True):
                        res = login_user('admin', admin_user, admin_pass)
                        if res:
                            st.session_state['role'] = 'Admin'
                            st.session_state['username'] = res[0]
                            st.session_state['nama'] = "Petugas Perpustakaan"
                            st.rerun()
                        else:
                            st.error("Akses Ditolak: Kredensial Admin tidak valid!")
                            
    else:
        total, tersedia, dipinjam = get_stats()
        c1, c2, c3 = st.columns(3)
        with c1: st.container(border=True).metric(label="📘 Total Koleksi Buku", value=total)
        with c2: st.container(border=True).metric(label="🟢 Koleksi Tersedia", value=tersedia)
        with c3: st.container(border=True).metric(label="🔴 Sedang Dipinjam", value=dipinjam)
                
        st.write("")
        tab1, tab2, tab3, tab4 = st.tabs([
            "📥 Tambah Buku", 
            "📑 Proses Approval", 
            "⚙️ Kelola Katalog", 
            "📋 Log Transaksi"
        ])
        
        # TAB 1: Tambah Buku
        with tab1:
            with st.container(border=True):
                st.markdown("##### 📝 Formulir Entri Buku Baru")
                with st.form("form_tambah", clear_on_submit=True):
                    cx, cy = st.columns(2)
                    with cx:
                        input_judul = st.text_input("Judul Buku Lengkap")
                        input_kategori = st.selectbox("Kategori Buku", ["Pelajaran", "Referensi", "Literatur Umum"])
                        input_status = st.selectbox("Status Awal", ["Tersedia", "Dipinjam"])
                    with cy:
                        input_pengarang = st.text_input("Nama Pengarang/Penulis")
                        input_tahun = st.number_input("Tahun Terbit", min_value=1900, max_value=2030, value=2026, step=1)
                        # PERUBAHAN: Mengganti text input menjadi File Uploader
                        input_file = st.file_uploader("Upload Gambar Sampul", type=['png', 'jpg', 'jpeg'])
                    
                    if st.form_submit_button("Simpan ke Katalog"):
                        if not input_judul or not input_pengarang:
                            st.error("Peringatan: Judul buku dan nama pengarang wajib diisi!")
                        else:
                            # Logika Konversi File Upload ke Base64 Data URI
                            if input_file is not None:
                                bytes_data = input_file.getvalue()
                                b64_encoded = base64.b64encode(bytes_data).decode()
                                mime_type = input_file.type
                                final_cover = f"data:{mime_type};base64,{b64_encoded}"
                            else:
                                final_cover = "https://via.placeholder.com/150x200.png?text=Buku" # Default
                                
                            c = conn.cursor()
                            c.execute("INSERT INTO buku (cover_url, judul, pengarang, kategori, tahun, status) VALUES (?, ?, ?, ?, ?, ?)",
                                      (final_cover, input_judul, input_pengarang, input_kategori, input_tahun, input_status))
                            conn.commit()
                            st.success(f"Sukses: Buku '{input_judul}' didaftarkan.")
                            st.rerun()
                            
        # TAB 2: SISTEM APPROVAL (PINJAM DAN KEMBALI)
        with tab2:
            st.markdown("##### 📥 Approval Pengajuan PEMINJAMAN Baru")
            q_app_pinjam = '''
                SELECT p.id_pinjam as 'ID Transaksi', p.id_buku, b.judul as 'Judul Buku', s.nama as 'Nama Siswa', p.tanggal_pinjam as 'Waktu Pengajuan'
                FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku JOIN siswa s ON p.username_siswa = s.username
                WHERE p.status_pinjam = 'Menunggu Approval'
            '''
            df_app_p = pd.read_sql_query(q_app_pinjam, conn)
            if df_app_p.empty:
                st.info("Tidak ada pengajuan pinjam baru.")
            else:
                st.dataframe(df_app_p.drop(columns=['id_buku']), use_container_width=True, hide_index=True)
                app_pil_p = st.selectbox("Pilih transaksi peminjaman untuk disetujui:", options=(df_app_p['ID Transaksi'].astype(str) + " - " + df_app_p['Judul Buku']).tolist())
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✅ Setujui Pinjaman", key="acc_pinjam", use_container_width=True):
                        with st.spinner("Memproses..."):
                            id_p = int(app_pil_p.split(" - ")[0])
                            id_b = int(df_app_p[df_app_p['ID Transaksi'] == id_p]['id_buku'].values[0])
                            c = conn.cursor()
                            c.execute("UPDATE peminjaman SET status_pinjam='Dipinjam' WHERE id_pinjam=?", (id_p,))
                            c.execute("UPDATE buku SET status='Dipinjam' WHERE id_buku=?", (id_b,))
                            conn.commit()
                            time.sleep(1)
                        st.success("Disetujui!")
                        time.sleep(1)
                        st.rerun()
                with b2:
                    if st.button("❌ Tolak Pinjaman", key="tolak_pinjam", use_container_width=True):
                        with st.spinner("Memproses penolakan..."):
                            id_p = int(app_pil_p.split(" - ")[0])
                            id_b = int(df_app_p[df_app_p['ID Transaksi'] == id_p]['id_buku'].values[0])
                            c = conn.cursor()
                            c.execute("UPDATE peminjaman SET status_pinjam='Ditolak' WHERE id_pinjam=?", (id_p,))
                            c.execute("UPDATE buku SET status='Tersedia' WHERE id_buku=?", (id_b,))
                            conn.commit()
                            time.sleep(1)
                        st.error("Ditolak dan dikembalikan ke rak.")
                        time.sleep(1)
                        st.rerun()
                        
            st.divider()
            
            st.markdown("##### 📤 Approval PENGEMBALIAN Buku")
            q_app_kembali = '''
                SELECT p.id_pinjam as 'ID Transaksi', p.id_buku, b.judul as 'Judul Buku', s.nama as 'Nama Siswa'
                FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku JOIN siswa s ON p.username_siswa = s.username
                WHERE p.status_pinjam = 'Menunggu Pengembalian'
            '''
            df_app_k = pd.read_sql_query(q_app_kembali, conn)
            if df_app_k.empty:
                st.info("Tidak ada siswa yang sedang mengajukan pengembalian buku.")
            else:
                st.dataframe(df_app_k.drop(columns=['id_buku']), use_container_width=True, hide_index=True)
                app_pil_k = st.selectbox("Pilih transaksi pengembalian untuk diverifikasi:", options=(df_app_k['ID Transaksi'].astype(str) + " - " + df_app_k['Judul Buku']).tolist())
                if st.button("✅ Verifikasi Buku Diterima (Selesai)", key="acc_kembali", use_container_width=True):
                    with st.spinner("Memproses penyelesaian..."):
                        id_k = int(app_pil_k.split(" - ")[0])
                        id_bk = int(df_app_k[df_app_k['ID Transaksi'] == id_k]['id_buku'].values[0])
                        c = conn.cursor()
                        c.execute("UPDATE peminjaman SET status_pinjam='Selesai' WHERE id_pinjam=?", (id_k,))
                        c.execute("UPDATE buku SET status='Tersedia' WHERE id_buku=?", (id_bk,))
                        conn.commit()
                        time.sleep(1)
                    st.success("Buku telah diterima dan berstatus Tersedia kembali di katalog!")
                    time.sleep(1.5)
                    st.rerun()

        # TAB 3: Edit & Hapus Katalog
        with tab3:
            with st.container(border=True):
                st.markdown("##### 📊 Tabel Manajemen Data Utama (CRUD)")
                df_edit = pd.read_sql_query("SELECT id_buku, cover_url, judul, pengarang, kategori, tahun, status FROM buku", conn)
                
                edited_df = st.data_editor(
                    df_edit,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id_buku": st.column_config.NumberColumn("ID Buku", disabled=True),
                        # PERUBAHAN: Teks cover_url dinonaktifkan di editor agar string base64 yang panjang tidak membuat tabel lagging.
                        "cover_url": st.column_config.TextColumn("Data Sampul (Base64)", disabled=True),
                        "status": st.column_config.SelectboxColumn("Status", options=["Tersedia", "Dipinjam", "Menunggu Approval"], required=True)
                    }
                )
                
                if st.button("Sinkronisasi Perubahan Database", type="primary", use_container_width=True):
                    c = conn.cursor()
                    c.execute("DELETE FROM buku")
                    for index, row in edited_df.iterrows():
                        c.execute("INSERT INTO buku (id_buku, cover_url, judul, pengarang, kategori, tahun, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (row['id_buku'], row['cover_url'], row['judul'], row['pengarang'], row['kategori'], row['tahun'], row['status']))
                    conn.commit()
                    st.success("Basis data diperbarui.")
                    time.sleep(1)
                    st.rerun()
                    
        # TAB 4: Log Transaksi Lengkap
        with tab4:
            st.markdown("##### 📜 Riwayat Log Seluruh Transaksi")
            q_log = '''
                SELECT p.id_pinjam as 'ID Transaksi', b.judul as 'Judul Buku', s.nama as 'Nama Peminjam', s.username as 'NISN', p.tanggal_pinjam as 'Waktu Aktivitas', p.status_pinjam as 'Status'
                FROM peminjaman p
                JOIN buku b ON p.id_buku = b.id_buku
                JOIN siswa s ON p.username_siswa = s.username
                ORDER BY p.id_pinjam DESC
            '''
            df_log = pd.read_sql_query(q_log, conn)
            
            if df_log.empty:
                st.info("Belum ada data transaksi aktivitas perpustakaan.")
            else:
                st.dataframe(df_log, use_container_width=True, hide_index=True)