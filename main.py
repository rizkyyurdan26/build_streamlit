import streamlit as st
import runpy

# Set konfigurasi halaman di awal aplikasi (hanya sekali)
st.set_page_config(layout="wide", page_title="Aplikasi Pendukung Keputusan")

# Sidebar untuk navigasi
st.sidebar.title("Navigasi")
page = st.sidebar.radio("Pilih Jenis Data", ("New Data", "Load Data", "View Data"))

# Jalankan halaman yang dipilih
if page == "New Data":
    runpy.run_path("app.py")
elif page == "Load Data":
    runpy.run_path("load.py")
elif page == "View Data":
    runpy.run_path("modif.py")

