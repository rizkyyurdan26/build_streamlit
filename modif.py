import streamlit as st
import os
import time
import json
import runpy
import pandas as pd

# Atur lebar kolom agar lebih optimal
st.markdown(
    """
    <style>
    .streamlit-expanderHeader {
        font-size: 18px;
        font-weight: bold;
    }
    .dataframe-container {
        width: 100% !important;
        height: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True
)

# Fungsi untuk memuat data JSON
def load_json(file_name):
    file_path = os.path.join("data", file_name)
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return None

# Fungsi untuk menghapus file JSON
def delete_json(file_name):
    file_path = os.path.join("data", file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

# Inisialisasi session state untuk modal konfirmasi dan reload
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False

if "file_to_delete" not in st.session_state:
    st.session_state.file_to_delete = None

if "reload" not in st.session_state:
    st.session_state.reload = False

# Jika reload flag aktif, reload halaman menggunakan JavaScript
if st.session_state.reload:
    st.session_state.reload = False  # Reset state agar tidak reload terus-menerus
    st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)

# Mendapatkan daftar file JSON di folder 'data'
existing_files = [f for f in os.listdir("data") if f.endswith(".json")]

if existing_files:
    # Dropdown untuk memilih file
    selected_file_index = st.selectbox(
        "Pilih file data:", 
        range(len(existing_files)),
        format_func=lambda x: existing_files[x],  # Tampilkan nama file di dropdown
        key="selected_file_index"
    )

    selected_file = existing_files[selected_file_index]  # Ambil nama file berdasarkan indeks

    # Tombol untuk memuat data
    if st.button("Muat Data"):
        data = load_json(selected_file)

        if data:
            # Menampilkan hasil perhitungan AHP
            if "ahp_results" in data and data["ahp_results"]:
                st.subheader("Hasil Perhitungan Bobot AHP")

                # Tampilkan bobot utama
                if "weights_main" in data["ahp_results"]:
                    df_ahp = pd.DataFrame({
                        "Kriteria": data["ahp_results"]["criteria_labels"],
                        "Bobot": data["ahp_results"]["weights_main"]
                    })
                    st.dataframe(df_ahp)

                # Tampilkan bobot sub-kriteria
                if "sub_results" in data["ahp_results"]:
                    for key, sub_data in data["ahp_results"]["sub_results"].items():
                        st.subheader(f"Hasil Bobot Sub-Kriteria: {key}")
                        df_sub = pd.DataFrame(sub_data["df_sub"])
                        st.dataframe(df_sub)

            # Tampilkan dataframe
            if "pm_results" in data and data["pm_results"]:
                st.subheader("Hasil Perangkingan Profile Matching")
                df_pm = pd.DataFrame(data["pm_results"])
                st.table(df_pm)

    # Tombol untuk membuka konfirmasi hapus
    if st.button("Hapus Data Ini"):
        st.session_state.confirm_delete = True
        st.session_state.file_to_delete = selected_file

    # Jika tombol hapus diklik, tampilkan konfirmasi
    if st.session_state.confirm_delete and st.session_state.file_to_delete:
        st.warning(f"Apakah Anda yakin ingin menghapus file '{st.session_state.file_to_delete}'?")

        col1, col2 = st.columns(2)

        message_placeholder = st.empty()

        def confirm_delete():
            success = delete_json(st.session_state.file_to_delete)
            if success:
                 # Tampilkan sukses dan hilangkan setelah 1 detik
                message_placeholder.success(f"Data berhasil dihapus")
                time.sleep(1)  # Menunggu selama 1 detik
                message_placeholder.empty()  # Menghapus pesan
                
                st.session_state.confirm_delete = False
                st.session_state.file_to_delete = None
                st.session_state.reload = True  # Set flag untuk reload halaman

        def cancel_delete():
            st.session_state.confirm_delete = False
            st.session_state.file_to_delete = None

        with col1:
            st.button("Ya, Hapus", on_click=confirm_delete)

        with col2:
            st.button("Batal", on_click=cancel_delete)


    #   # Tombol untuk pergi ke halaman load.py (menggunakan runpy)
    # if st.button("Gunakan Data", key="use_data_button"):
    #     # Mengarahkan ke halaman load.py
    #     runpy.run_path("load.py")
else:
    st.warning("Tidak ada file data yang tersedia.")
