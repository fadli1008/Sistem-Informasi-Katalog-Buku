import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import time
import base64

# ==========================================
# 1. KONFIGURASI HALAMAN & THEME
# ==========================================
st.set_page_config(
    page_title="Katalog Perpustakaan SMAN 7", 
    page_icon="📚", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# INJEKSI CUSTOM CSS UNTUK UI/UX MODERN & RESPONSIF
st.markdown("""
    <style>
    /* Import Font Modern (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Menyembunyikan elemen bawaan tanpa mengganggu tombol navigasi sidebar */
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}
    
    /* Custom Title - Responsif & Posisi Tengah */
    .main-title {
        font-size: clamp(1.8rem, 3.5vw, 2.8rem); 
        font-weight: 800;
        background: linear-gradient(90deg, #0284c7 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0.5rem;
        margin-top: 1rem;
        line-height: 1.3;
        word-wrap: break-word;
    }
    
    .sub-title {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 400;
        text-align: center;
        margin-bottom: 2.5rem;
    }
    
    /* Styling Tombol Primary */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(2, 132, 199, 0.25);
        background: linear-gradient(135deg, #0369a1 0%, #0f172a 100%);
    }
    
    /* Styling Container / Card */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
        padding: 1.5rem !important;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
    }
    
    /* Styling Metrik */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #64748b !important;
        font-weight: 600 !important;
    }
    
    /* Tabel Header */
    thead tr th {
        background-color: #f8fafc !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INISIALISASI DATABASE & STATE
# ==========================================
def init_db():
    conn = sqlite3.connect('perpustakaan.db', check_same_thread=False)
    c = conn.cursor()
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
    conn.commit()
    return conn

conn = init_db()

for key in ['role', 'username', 'nama']:
    if key not in st.session_state:
        st.session_state[key] = None

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
    st.markdown("<h2 style='text-align: center; color: #0284c7; font-weight: 800;'>🏫 SMAN 7</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; margin-top: -15px;'>Bengkulu Selatan</p>", unsafe_allow_html=True)
    st.divider()
    
    menu = st.radio(
        "Pilih Menu",
        ["🔍 Katalog Buku", "🧑 Area Siswa", "🔒 Area Petugas (Admin)"],
        label_visibility="collapsed"
    )
    
    st.divider()
    if st.session_state['role']:
        st.markdown(f"**👤 Sesi Aktif:**<br/>{st.session_state['nama']} ({st.session_state['role']})", unsafe_allow_html=True)
        st.write("")
        if st.button("🚪 Keluar Akun", use_container_width=True):
            st.session_state.update({'role': None, 'username': None, 'nama': None})
            st.rerun()

# Menampilkan Judul Utama (Posisi Tengah & Responsif)
st.markdown('<div class="main-title">Sistem Informasi Katalog & Peminjaman Buku</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Eksplorasi, pinjam, dan kelola literatur perpustakaan dengan mudah.</div>', unsafe_allow_html=True)

# ------------------------------------------
# MENU: PENCARIAN KATALOG (PUBLIK)
# ------------------------------------------
if menu == "🔍 Katalog Buku":
    with st.expander("🛠️ Buka Filter & Pencarian Lanjutan", expanded=False):
        c1, c2 = st.columns([3, 1])
        with c1:
            search_query = st.text_input("Pencarian", placeholder="Ketik judul buku atau nama pengarang...", label_visibility="collapsed")
        with c2:
            kategori_filter = st.selectbox("Filter Kategori", ["Semua Kategori", "Pelajaran", "Referensi", "Literatur Umum"], label_visibility="collapsed")
            
    query = "SELECT id_buku as ID, cover_url as 'Sampul', judul as 'Judul Buku', pengarang as 'Pengarang', kategori as 'Kategori', tahun as 'Tahun', status as 'Status' FROM buku WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (judul LIKE ? OR pengarang LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    if kategori_filter != "Semua Kategori":
        query += " AND kategori = ?"
        params.append(kategori_filter)
        
    df = pd.read_sql_query(query, conn, params=params)
    
    if df.empty:
        st.info("📚 Tidak ada buku yang cocok dengan kriteria pencarian.")
    else:
        st.write("") # Memberi jarak setelah filter
        # PERUBAHAN UTAMA: Mengganti st.dataframe menjadi Grid Layout (4 Kolom) layaknya E-Commerce
        cols = st.columns(4)
        
        for index, row in df.iterrows():
            col = cols[index % 4]
            with col:
                with st.container(border=True):
                    # Logika warna badge (label) status
                    status_val = row['Status']
                    if status_val == 'Tersedia':
                        badge_color = "#10b981" # Hijau
                        badge_text = "Tersedia"
                    elif status_val in ['Menunggu Approval', 'Menunggu Pengembalian']:
                        badge_color = "#f59e0b" # Kuning/Amber
                        badge_text = "Diproses"
                    else:
                        badge_color = "#ef4444" # Merah
                        badge_text = "Dipinjam"
                        
                    # Menggabungkan gambar dengan label mengambang (badge) di atasnya
                    html_card = f'''
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
                            <img src="{row['Sampul']}" style="width: 100%; height: 230px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <div style="position: absolute; top: 8px; right: 8px; background-color: {badge_color}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                {badge_text}
                            </div>
                        </div>
                    '''
                    st.markdown(html_card, unsafe_allow_html=True)
                    
                    # Judul dan pengarang dengan sistem pemotongan (ellipsis) agar layout tidak rusak jika teks kepanjangan
                    st.markdown(f"<div style='text-align: center; margin-top: 15px; margin-bottom: 2px;'><strong style='font-size: 1rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;' title='{row['Judul Buku']}'>{row['Judul Buku']}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 0.85rem; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{row['Pengarang']}'>✍️ {row['Pengarang']}</div>", unsafe_allow_html=True)
                    
                    # Tag Kategori & Tahun di bagian bawah kartu
                    st.markdown(f"<div style='text-align: center; font-size: 0.75rem; background-color: #f1f5f9; padding: 4px 8px; border-radius: 6px; color: #475569; border: 1px solid #e2e8f0;'>📚 {row['Kategori']} &nbsp;|&nbsp; 🗓️ {row['Tahun']}</div>", unsafe_allow_html=True)

# ------------------------------------------
# MENU: AREA SISWA
# ------------------------------------------
elif menu == "🧑 Area Siswa":
    if st.session_state['role'] != 'Siswa':
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            tab_login, tab_daftar = st.tabs(["🔐 Masuk Akun", "📝 Daftar Baru"])
            
            with tab_login:
                with st.container(border=True):
                    with st.form("form_login_siswa"):
                        st.markdown("<h4 style='text-align: center;'>Login Akun Siswa</h4>", unsafe_allow_html=True)
                        st.write("")
                        user_in = st.text_input("NISN / Username")
                        pass_in = st.text_input("Kata Sandi", type="password")
                        if st.form_submit_button("Masuk", use_container_width=True):
                            res = login_user('siswa', user_in, pass_in)
                            if res:
                                st.session_state.update({'role': 'Siswa', 'username': res[0], 'nama': res[1]})
                                st.rerun()
                            else:
                                st.error("❌ Username atau Kata Sandi salah.")
                                
            with tab_daftar:
                with st.container(border=True):
                    with st.form("form_daftar_siswa", clear_on_submit=True):
                        st.markdown("<h4 style='text-align: center;'>Buat Akun Baru</h4>", unsafe_allow_html=True)
                        st.write("")
                        reg_user = st.text_input("NISN / Username")
                        reg_nama = st.text_input("Nama Lengkap")
                        reg_pass = st.text_input("Kata Sandi", type="password")
                        if st.form_submit_button("Daftar Sekarang", use_container_width=True):
                            if not all([reg_user, reg_nama, reg_pass]):
                                st.warning("⚠️ Harap isi semua kolom!")
                            else:
                                try:
                                    c = conn.cursor()
                                    hashed = hashlib.sha256(reg_pass.encode()).hexdigest()
                                    c.execute("INSERT INTO siswa (username, nama, password) VALUES (?, ?, ?)", (reg_user, reg_nama, hashed))
                                    conn.commit()
                                    st.toast("✅ Akun berhasil dibuat! Silakan masuk pada tab Login.", icon="🎉")
                                except sqlite3.IntegrityError:
                                    st.error("❌ Username/NISN sudah terdaftar.")
                                    
    else:
        st.markdown(f"### 👋 Selamat Datang, {st.session_state['nama']}")
        st.write("Silakan kelola pengajuan peminjaman dan pengembalian buku Anda di bawah ini.")
        st.write("")
        
        t1, t2 = st.tabs(["📖 Pinjam Buku", "🕒 Pengembalian & Riwayat"])
        
        with t1:
            st.markdown("#### 📚 Etalase Buku Tersedia")
            st.markdown("Pilih dan klik tombol pinjam pada buku yang ingin Anda baca.")
            st.write("")
            
            df_ready = pd.read_sql_query("SELECT id_buku, cover_url, judul, pengarang FROM buku WHERE status='Tersedia'", conn)
            
            if df_ready.empty:
                st.info("Koleksi saat ini sedang kosong atau semua buku sedang dipinjam.")
            else:
                cols = st.columns(3)
                for index, row in df_ready.iterrows():
                    col = cols[index % 3]
                    with col:
                        with st.container(border=True):
                            img_html = f'''
                                <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                                    <img src="{row['cover_url']}" style="width: 100%; height: 260px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                </div>
                            '''
                            st.markdown(img_html, unsafe_allow_html=True)
                            
                            st.markdown(f"<div style='text-align: center; margin-bottom: 2px;'><strong style='font-size: 1.05rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;' title='{row['judul']}'>{row['judul']}</strong></div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 0.9rem; margin-bottom: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' title='{row['pengarang']}'>✍️ {row['pengarang']}</div>", unsafe_allow_html=True)
                            
                            if st.button("📌 Ajukan Pinjaman", key=f"pinjam_{row['id_buku']}", use_container_width=True):
                                tgl_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M")
                                c = conn.cursor()
                                c.execute("INSERT INTO peminjaman (id_buku, username_siswa, tanggal_pinjam, status_pinjam) VALUES (?, ?, ?, 'Menunggu Approval')", 
                                          (row['id_buku'], st.session_state['username'], tgl_sekarang))
                                c.execute("UPDATE buku SET status='Menunggu Approval' WHERE id_buku=?", (row['id_buku'],))
                                conn.commit()
                                st.toast(f"✅ Pengajuan '{row['judul']}' terkirim!", icon="🚀")
                                time.sleep(1.5)
                                st.rerun()
                        
        with t2:
            df_dipinjam = pd.read_sql_query("SELECT p.id_pinjam, b.judul, b.pengarang FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku WHERE p.username_siswa = ? AND p.status_pinjam = 'Dipinjam'", conn, params=[st.session_state['username']])
            
            if not df_dipinjam.empty:
                with st.container(border=True):
                    st.markdown("#### 🔄 Kembalikan Buku")
                    df_dipinjam['opsi'] = df_dipinjam['id_pinjam'].astype(str) + " - " + df_dipinjam['judul']
                    buku_kembali = st.selectbox("Pilih buku yang akan dikembalikan:", options=df_dipinjam['opsi'].tolist())
                    
                    if st.button("Ajukan Pengembalian Buku", use_container_width=True):
                        id_p_kembali = int(buku_kembali.split(" - ")[0])
                        c = conn.cursor()
                        c.execute("UPDATE peminjaman SET status_pinjam='Menunggu Pengembalian' WHERE id_pinjam=?", (id_p_kembali,))
                        conn.commit()
                        st.toast("✅ Pengembalian diajukan! Serahkan fisik buku ke petugas.", icon="📦")
                        time.sleep(1.5)
                        st.rerun()
            
            st.markdown("##### 📜 Riwayat Transaksi Anda")
            q_riwayat = '''
                SELECT b.judul as 'Judul Buku', p.tanggal_pinjam as 'Tanggal Pengajuan', p.status_pinjam as 'Status Transaksi'
                FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku
                WHERE p.username_siswa = ? ORDER BY p.id_pinjam DESC
            '''
            df_riwayat = pd.read_sql_query(q_riwayat, conn, params=[st.session_state['username']])
            st.dataframe(df_riwayat, use_container_width=True, hide_index=True)

# ------------------------------------------
# MENU: AREA PETUGAS (ADMIN)
# ------------------------------------------
elif menu == "🔒 Area Petugas (Admin)":
    if st.session_state['role'] != 'Admin':
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h3 style='text-align: center;'>🔐 Autentikasi Petugas Admin</h3>", unsafe_allow_html=True)
                st.write("")
                with st.form("login_form_admin", clear_on_submit=True):
                    admin_user = st.text_input("Username")
                    admin_pass = st.text_input("Kata Sandi", type="password")
                    if st.form_submit_button("Masuk Ke Sistem", use_container_width=True):
                        res = login_user('admin', admin_user, admin_pass)
                        if res:
                            st.session_state.update({'role': 'Admin', 'username': res[0], 'nama': "Petugas Perpus"})
                            st.rerun()
                        else:
                            st.error("❌ Kredensial tidak valid.")
                            
    else:
        total, tersedia, dipinjam = get_stats()
        c1, c2, c3 = st.columns(3)
        c1.metric(label="Total Koleksi", value=total, delta="Buku Terdaftar", delta_color="off")
        c2.metric(label="Siap Pinjam", value=tersedia, delta="Status Tersedia")
        c3.metric(label="Sedang Dipinjam", value=dipinjam, delta="Sirkulasi Aktif", delta_color="inverse")
                
        st.write("")
        tab1, tab2, tab3, tab4 = st.tabs([
            "📑 Persetujuan Transaksi", 
            "📥 Tambah Koleksi Buku", 
            "⚙️ Kelola Katalog DB",
            "📋 Log Transaksi"
        ])
        
        # TAB 1: Persetujuan
        with tab1:
            col_p, col_k = st.columns(2)
            with col_p:
                st.markdown("#### 📥 Validasi Peminjaman Baru")
                q_app_pinjam = "SELECT p.id_pinjam, p.id_buku, b.judul, s.nama as nama_siswa FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku JOIN siswa s ON p.username_siswa = s.username WHERE p.status_pinjam = 'Menunggu Approval'"
                df_app_p = pd.read_sql_query(q_app_pinjam, conn)
                
                if not df_app_p.empty:
                    st.dataframe(df_app_p[['id_pinjam', 'judul', 'nama_siswa']], use_container_width=True, hide_index=True, column_config={
                        "id_pinjam": "ID", "judul": "Judul Buku", "nama_siswa": "Nama Siswa"
                    })
                    
                    opsi_pinjam = (df_app_p['id_pinjam'].astype(str) + " - " + df_app_p['judul'] + " oleh " + df_app_p['nama_siswa']).tolist()
                    pilihan = st.selectbox("Pilih antrean pinjam:", options=opsi_pinjam, key="sb_pinjam")
                    
                    bp1, bp2 = st.columns(2)
                    id_p = int(pilihan.split(" - ")[0])
                    id_b = int(df_app_p[df_app_p['id_pinjam'] == id_p]['id_buku'].values[0])
                    
                    if bp1.button("✅ Setujui", use_container_width=True):
                        conn.execute("UPDATE peminjaman SET status_pinjam='Dipinjam' WHERE id_pinjam=?", (id_p,))
                        conn.execute("UPDATE buku SET status='Dipinjam' WHERE id_buku=?", (id_b,))
                        conn.commit()
                        st.toast("Pinjaman Disetujui!", icon="✅")
                        time.sleep(1)
                        st.rerun()
                    if bp2.button("❌ Tolak", use_container_width=True):
                        conn.execute("UPDATE peminjaman SET status_pinjam='Ditolak' WHERE id_pinjam=?", (id_p,))
                        conn.execute("UPDATE buku SET status='Tersedia' WHERE id_buku=?", (id_b,))
                        conn.commit()
                        st.toast("Pinjaman Ditolak!", icon="🗑️")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("Tidak ada pengajuan pinjam baru.")
                    
            with col_k:
                st.markdown("#### 📤 Validasi Pengembalian")
                q_app_kembali = "SELECT p.id_pinjam, p.id_buku, b.judul, s.nama as nama_siswa FROM peminjaman p JOIN buku b ON p.id_buku = b.id_buku JOIN siswa s ON p.username_siswa = s.username WHERE p.status_pinjam = 'Menunggu Pengembalian'"
                df_app_k = pd.read_sql_query(q_app_kembali, conn)
                
                if not df_app_k.empty:
                    st.dataframe(df_app_k[['id_pinjam', 'judul', 'nama_siswa']], use_container_width=True, hide_index=True, column_config={
                        "id_pinjam": "ID", "judul": "Judul Buku", "nama_siswa": "Nama Siswa"
                    })
                    
                    opsi_kembali = (df_app_k['id_pinjam'].astype(str) + " - " + df_app_k['judul'] + " oleh " + df_app_k['nama_siswa']).tolist()
                    pilihan_k = st.selectbox("Pilih antrean kembali:", options=opsi_kembali, key="sb_kembali")
                    
                    if st.button("✅ Konfirmasi Buku Diterima", use_container_width=True):
                        id_k = int(pilihan_k.split(" - ")[0])
                        id_bk = int(df_app_k[df_app_k['id_pinjam'] == id_k]['id_buku'].values[0])
                        conn.execute("UPDATE peminjaman SET status_pinjam='Selesai' WHERE id_pinjam=?", (id_k,))
                        conn.execute("UPDATE buku SET status='Tersedia' WHERE id_buku=?", (id_bk,))
                        conn.commit()
                        st.toast("Sukses: Buku telah kembali ke rak!", icon="📚")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("Tidak ada antrean pengembalian buku.")

        # TAB 2: Tambah Koleksi
        with tab2:
            with st.container(border=True):
                st.markdown("#### 📝 Formulir Entri Buku Baru")
                with st.form("form_tambah", clear_on_submit=True):
                    cx, cy = st.columns(2)
                    with cx:
                        input_judul = st.text_input("Judul Buku Lengkap")
                        input_kategori = st.selectbox("Kategori Buku", ["Pelajaran", "Referensi", "Literatur Umum"])
                        input_status = st.selectbox("Status Awal", ["Tersedia", "Dipinjam"])
                    with cy:
                        input_pengarang = st.text_input("Nama Pengarang/Penulis")
                        input_tahun = st.number_input("Tahun Terbit", min_value=1900, max_value=datetime.now().year, value=datetime.now().year, step=1)
                        input_file = st.file_uploader("Upload Sampul Gambar", type=['png', 'jpg', 'jpeg'])
                    
                    if st.form_submit_button("Simpan ke Katalog", use_container_width=True):
                        if not input_judul or not input_pengarang:
                            st.warning("⚠️ Judul dan pengarang wajib diisi!")
                        else:
                            final_cover = "https://via.placeholder.com/150x200.png?text=Buku"
                            if input_file:
                                b64_encoded = base64.b64encode(input_file.getvalue()).decode()
                                final_cover = f"data:{input_file.type};base64,{b64_encoded}"
                                
                            conn.execute("INSERT INTO buku (cover_url, judul, pengarang, kategori, tahun, status) VALUES (?, ?, ?, ?, ?, ?)",
                                      (final_cover, input_judul, input_pengarang, input_kategori, input_tahun, input_status))
                            conn.commit()
                            st.toast(f"Buku '{input_judul}' didaftarkan!", icon="🎉")
                            time.sleep(1.5)
                            st.rerun()

        # TAB 3: Kelola Katalog
        with tab3:
            st.markdown("#### 📊 Tabel Manajemen Database Utama")
            st.caption("Anda dapat mengubah data langsung pada tabel di bawah (kecuali ID & Base64 Sampul). Klik 'Simpan Perubahan' setelah selesai.")
            df_edit = pd.read_sql_query("SELECT id_buku, cover_url, judul, pengarang, kategori, tahun, status FROM buku", conn)
            
            edited_df = st.data_editor(
                df_edit,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id_buku": st.column_config.NumberColumn("ID Buku", disabled=True, width="small"),
                    "cover_url": st.column_config.TextColumn("Data Sampul (Base64)", disabled=True),
                    "judul": "Judul Buku",
                    "pengarang": "Pengarang",
                    "status": st.column_config.SelectboxColumn("Status", options=["Tersedia", "Dipinjam", "Menunggu Approval"], required=True)
                }
            )
            
            if st.button("💾 Sinkronisasi Perubahan Database", type="primary", use_container_width=True):
                c = conn.cursor()
                c.execute("DELETE FROM buku")
                for _, row in edited_df.iterrows():
                    c.execute("INSERT INTO buku (id_buku, cover_url, judul, pengarang, kategori, tahun, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (row['id_buku'], row['cover_url'], row['judul'], row['pengarang'], row['kategori'], row['tahun'], row['status']))
                conn.commit()
                st.toast("Basis data berhasil diperbarui!", icon="✅")
                time.sleep(1)
                st.rerun()

        # TAB 4: Log Transaksi
        with tab4:
            st.markdown("#### 📜 Riwayat Log Seluruh Transaksi")
            st.caption("Berikut adalah catatan riwayat aktivitas sirkulasi peminjaman dan pengembalian buku di perpustakaan.")
            
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
                def color_status_log(val):
                    if val == 'Selesai': color = '#10b981'
                    elif val in ['Menunggu Approval', 'Menunggu Pengembalian']: color = '#f59e0b'
                    else: color = '#ef4444'
                    return f'color: {color}; font-weight: 600;'
                    
                st.dataframe(
                    df_log.style.map(color_status_log, subset=['Status']),
                    use_container_width=True,
                    hide_index=True
                )