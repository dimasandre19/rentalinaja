import streamlit as st
import mysql.connector
import pandas as pd

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Rentalinaja - Car Rental System",
    layout="wide"
)

# Fungsi Koneksi Database MySQL
def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  
            database="rentalinaja"
        )
    except mysql.connector.Error as err:
        st.error(f"Gagal terhubung ke Database MySQL: {err}")
        return None

# Sidebar Navigasi
st.sidebar.title("Rentalinaja")
st.sidebar.subheader("Sistem Manajemen Rental Mobil")
menu = st.sidebar.selectbox(
    "Pilih Menu",
    ["Kelola Penyewa", "Kelola Mobil", "Transaksi Rental"]
)

# ---------------------------------------------------------
# MENU 1: KELOLA PENYEWA
# ---------------------------------------------------------
if menu == "Kelola Penyewa":
    st.header("Data Penyewa")
    
    # Form Tambah Penyewa (Parameterized Query - Safe against SQL Injection)
    with st.expander("Tambah Penyewa Baru"):
        with st.form("form_tambah_penyewa", clear_on_submit=True):
            nama = st.text_input("Nama Lengkap")
            no_hp = st.text_input("Nomor HP / WhatsApp")
            alamat = st.text_area("Alamat Lengkap")
            submit = st.form_submit_button("Simpan Penyewa")
            
            if submit:
                if nama and no_hp:
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        # Parameterized Query menggunakan placeholder %s
                        query = "INSERT INTO penyewa (nama, no_hp, alamat) VALUES (%s, %s, %s)"
                        try:
                            cursor.execute(query, (nama, no_hp, alamat))
                            conn.commit()
                            st.success(f"Berhasil menambahkan penyewa: {nama}")
                        except mysql.connector.Error as err:
                            st.error(f"Gagal menyimpan data: {err}")
                        finally:
                            cursor.close()
                            conn.close()
                else:
                    st.warning("Nama dan Nomor HP wajib diisi!")

    # Tampilkan Daftar Penyewa
    st.subheader("Daftar Penyewa Terdaftar")
    conn = get_connection()
    if conn:
        df_penyewa = pd.read_sql("SELECT * FROM penyewa ORDER BY id_penyewa DESC", conn)
        st.dataframe(df_penyewa, use_container_width=True)
        
        # Form Hapus Penyewa
        if not df_penyewa.empty:
            with st.expander("Hapus Data Penyewa"):
                penyewa_opt = {f"{row['id_penyewa']} - {row['nama']}": row['id_penyewa'] for _, row in df_penyewa.iterrows()}
                pilihan_hapus = st.selectbox("Pilih Penyewa yang Ingin Dihapus", list(penyewa_opt.keys()))
                if st.button("Hapus Penyewa", type="primary"):
                    id_to_delete = penyewa_opt[pilihan_hapus]
                    cursor = conn.cursor()
                    try:
                        cursor.execute("DELETE FROM penyewa WHERE id_penyewa = %s", (id_to_delete,))
                        conn.commit()
                        st.success("Data penyewa berhasil dihapus!")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Gagal menghapus! Data ini mungkin terkait dengan transaksi lain: {err}")
                    finally:
                        cursor.close()
        conn.close()

# ---------------------------------------------------------
# MENU 2: KELOLA MOBIL
# ---------------------------------------------------------
elif menu == "Kelola Mobil":
    st.header("Data Armada Mobil")
    
    # Form Tambah Mobil
    with st.expander("Tambah Mobil Baru"):
        with st.form("form_tambah_mobil", clear_on_submit=True):
            merk = st.text_input("Merk / Model Mobil (misal: Toyota Avanza)")
            nopol = st.text_input("Nomor Polisi (Plat Nomor)")
            harga_sewa = st.number_input("Harga Sewa per Hari (Rp)", min_value=0, step=50000)
            status = st.selectbox("Status Mobil", ["Tersedia", "Disewa"])
            submit_mobil = st.form_submit_button("Simpan Mobil")
            
            if submit_mobil:
                if merk and nopol:
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        query = "INSERT INTO mobil (merk_mobil, nopol, harga_sewa_per_hari, status) VALUES (%s, %s, %s, %s)"
                        try:
                            cursor.execute(query, (merk, nopol, harga_sewa, status))
                            conn.commit()
                            st.success(f"Berhasil menambahkan mobil: {merk} ({nopol})")
                        except mysql.connector.Error as err:
                            st.error(f"Gagal menyimpan data: {err}")
                        finally:
                            cursor.close()
                            conn.close()
                else:
                    st.warning("Merk dan Plat Nomor wajib diisi!")

    # Tampilkan Daftar Mobil
    st.subheader("Daftar Armada Mobil")
    conn = get_connection()
    if conn:
        df_mobil = pd.read_sql("SELECT * FROM mobil ORDER BY id_mobil DESC", conn)
        st.dataframe(df_mobil, use_container_width=True)
        conn.close()

# ---------------------------------------------------------
# MENU 3: TRANSAKSI RENTAL
# ---------------------------------------------------------
elif menu == "Transaksi Rental":
    st.header("Transaksi Rental Mobil")
    
    conn = get_connection()
    if conn:
        df_penyewa = pd.read_sql("SELECT id_penyewa, nama FROM penyewa", conn)
        df_mobil = pd.read_sql("SELECT id_mobil, merk_mobil, harga_sewa_per_hari FROM mobil WHERE status = 'Tersedia'", conn)
        
        with st.expander("Buat Transaksi Rental Baru"):
            if df_penyewa.empty or df_mobil.empty:
                st.info("Pastikan data Penyewa dan Mobil (status 'Tersedia') sudah diisi terlebih dahulu.")
            else:
                with st.form("form_transaksi", clear_on_submit=True):
                    dict_penyewa = {f"{row['id_penyewa']} - {row['nama']}": row['id_penyewa'] for _, row in df_penyewa.iterrows()}
                    pilihan_penyewa = st.selectbox("Pilih Penyewa", list(dict_penyewa.keys()))
                    
                    dict_mobil = {f"{row['id_mobil']} - {row['merk_mobil']} (Rp {row['harga_sewa_per_hari']:,}/hari)": (row['id_mobil'], row['harga_sewa_per_hari']) for _, row in df_mobil.iterrows()}
                    pilihan_mobil = st.selectbox("Pilih Mobil", list(dict_mobil.keys()))
                    
                    tgl_sewa = st.date_input("Tanggal Sewa")
                    lama_sewa = st.number_input("Lama Sewa (Hari)", min_value=1, value=1)
                    submit_trx = st.form_submit_button("Proses Transaksi")
                    
                    if submit_trx:
                        id_penyewa_selected = dict_penyewa[pilihan_penyewa]
                        id_mobil_selected, harga_per_hari = dict_mobil[pilihan_mobil]
                        total_harga = harga_per_hari * lama_sewa
                        
                        cursor = conn.cursor()
                        try:
                            # 1. Insert ke tabel transaksi
                            query_trx = """
                                INSERT INTO transaksi (id_penyewa, id_mobil, tgl_sewa, lama_sewa, total_biaya)
                                VALUES (%s, %s, %s, %s, %s)
                            """
                            cursor.execute(query_trx, (id_penyewa_selected, id_mobil_selected, tgl_sewa, lama_sewa, total_harga))
                            
                            # 2. Update status mobil jadi 'Disewa'
                            cursor.execute("UPDATE mobil SET status = 'Disewa' WHERE id_mobil = %s", (id_mobil_selected,))
                            
                            conn.commit()
                            st.success(f"Transaksi Berhasil! Total Biaya: Rp {total_harga:,.0f}")
                            st.rerun()
                        except mysql.connector.Error as err:
                            conn.rollback()
                            st.error(f"Gagal memproses transaksi: {err}")
                        finally:
                            cursor.close()

        # Tampilkan Riwayat Transaksi Menggunakan SQL JOIN
        st.subheader("Riwayat Transaksi Rental (SQL JOIN)")
        query_join = """
            SELECT 
                t.id_transaksi,
                p.nama AS nama_penyewa,
                p.no_hp,
                m.merk_mobil,
                m.nopol,
                t.tgl_sewa,
                t.lama_sewa,
                t.total_biaya
            FROM transaksi t
            JOIN penyewa p ON t.id_penyewa = p.id_penyewa
            JOIN mobil m ON t.id_mobil = m.id_mobil
            ORDER BY t.id_transaksi DESC
        """
        try:
            df_trx = pd.read_sql(query_join, conn)
            st.dataframe(df_trx, use_container_width=True)
        except Exception as e:
            st.error(f"Gagal memuat riwayat transaksi: {e}")
        finally:
            conn.close()