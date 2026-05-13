import streamlit as st
from datetime import datetime
import pandas as pd
from st_supabase_connection import SupabaseConnection

# ====================== KONEKSI SUPABASE ======================
conn = st.connection("supabase", type=SupabaseConnection)

# ====================== CONFIG ======================
st.set_page_config(page_title="Laporan Puskesmas", layout="wide")
st.title("📊 Sistem Laporan Puskesmas")

# Sidebar Menu
menu = st.sidebar.selectbox("Menu", ["Upload Laporan Baru", "Daftar Semua Laporan"])

# ====================== UPLOAD LAPORAN ======================
if menu == "Upload Laporan Baru":
    st.subheader("Upload Laporan Baru")
    
    puskesmas = st.text_input("Nama Puskesmas *", placeholder="contoh: Puskesmas Kecamatan X")
    jenis = st.selectbox("Jenis Laporan *", 
                        ["Bulanan", "Mingguan", "Triwulan", "Kejadian Khusus", "Lainnya"])
    keterangan = st.text_area("Keterangan (opsional)")
    
    uploaded_file = st.file_uploader("Pilih File Laporan", 
                                   type=["pdf", "xlsx", "xls", "docx", "jpg", "png", "jpeg"])
    
    if st.button("Simpan Laporan", type="primary", use_container_width=True):
        if not puskesmas or not uploaded_file:
            st.error("❌ Nama Puskesmas dan File wajib diisi!")
        else:
            with st.spinner("Menyimpan laporan ke Supabase..."):
                try:
                    # Buat nama file unik
                    waktu = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_path = f"{puskesmas}/{waktu}_{uploaded_file.name}"
                    
                    # Upload file ke Storage
                    bucket_name = "laporan"   # ← Ganti kalau bucket kamu beda nama
                    
                    conn.storage.from_(bucket_name).upload(
                        file_path, 
                        uploaded_file.getvalue(),
                        {"content-type": uploaded_file.type}
                    )
                    
                    # Dapatkan URL
                    file_url = conn.storage.from_(bucket_name).get_public_url(file_path)
                    
                    # Simpan data ke tabel
                    data = {
                        "tanggal": datetime.now().date().isoformat(),
                        "puskesmas": puskesmas,
                        "jenis_laporan": jenis,
                        "nama_file": uploaded_file.name,
                        "file_url": file_url,
                        "keterangan": keterangan,
                        "status": "Tersimpan"
                    }
                    
                    conn.table("laporan").insert(data).execute()
                    
                    st.success("✅ Laporan berhasil disimpan permanen!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {str(e)}")

# ====================== DAFTAR LAPORAN ======================
elif menu == "Daftar Semua Laporan":
    st.subheader("Daftar Semua Laporan")
    
    # Ambil data dari Supabase
    response = conn.table("laporan").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(response.data)
    
    if df.empty:
        st.info("Belum ada laporan yang diupload.")
    else:
        # Filter
        filter_puskesmas = st.multiselect("Filter Puskesmas", options=df["puskesmas"].unique())
        
        if filter_puskesmas:
            df = df[df["puskesmas"].isin(filter_puskesmas)]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Tombol download tiap file
        st.subheader("Download Laporan")
        for index, row in df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{row['puskesmas']}** - {row['jenis_laporan']}")
            with col2:
                st.caption(row['tanggal'])
            with col3:
                if st.button("Download", key=f"dl_{index}"):
                    st.link_button("Download File", row['file_url'])