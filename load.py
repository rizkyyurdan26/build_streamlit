import streamlit as st
import numpy as np
import pandas as pd
import os
import json
import time
from ahp_function import ahp_rumus
from pm_function import profile_matching_with_ranges

# Fungsi untuk membersihkan dan mengonversi data agar kompatibel dengan JSON
def clean_session_state(state):
    clean_data = {}
    for key, value in state.items():
        try:
            # Coba serialisasi ke JSON langsung
            json.dumps(value)
            clean_data[key] = value
        except TypeError:
            # Konversi tipe data yang tidak didukung
            if isinstance(value, np.ndarray):  # Konversi numpy array ke list
                clean_data[key] = value.tolist()
            elif isinstance(value, dict):  # Rekursif untuk dictionary
                clean_data[key] = clean_session_state(value)
            else:
                st.warning(f"Tidak dapat menyimpan '{key}' karena tipe datanya tidak didukung.")
    return clean_data

def save_to_json(file_name):
    file_path = os.path.join("data", file_name)

    data_to_save = {
        "ahp_results": st.session_state.get("ahp_results", None),
        "pm_results": st.session_state.get("pm_results", None),
        "form_data": {
            "num_criteria": st.session_state.get("num_criteria", 0),
            "criteria_labels": [c for c in st.session_state.get("criteria_labels", []) if c.strip()],  # Pastikan nama kriteria tidak kosong
            "sub_criteria_dict": {
                k: v for k, v in st.session_state.get("sub_criteria_dict", {}).items() if k.strip()  # Pastikan nama kriteria tidak kosong
            },
            "num_alternatives": st.session_state.get("num_alternatives", 0),
            "alternatives": {
                alt: values for alt, values in st.session_state.get("alternatives", {}).items() if alt.strip()  # Pastikan nama alternatif tidak kosong
            },
        },
    }


    for key in st.session_state.keys():
        if key not in ["ahp_results", "pm_results"]:
            if key == "criteria_labels":
                # Simpan hanya kriteria dengan nama valid
                data_to_save["form_data"][key] = [c for c in st.session_state[key] if c.strip()]
            elif key == "alternatives":
                # Simpan hanya alternatif dengan nama valid
                data_to_save["form_data"][key] = {
                    alt: values for alt, values in st.session_state[key].items() if alt.strip()
                }
            elif key == "sub_criteria_dict":
                # Simpan hanya sub-kriteria dari kriteria valid
                data_to_save["form_data"][key] = {
                    k: v for k, v in st.session_state[key].items() if k.strip()
                }
            else:
                data_to_save["form_data"][key] = st.session_state[key]


    # Konversi semua NumPy array ke list agar bisa disimpan
    if data_to_save["ahp_results"]:
        if "sub_matrices" in data_to_save["ahp_results"]:
            data_to_save["ahp_results"]["sub_matrices"] = {
                key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in data_to_save["ahp_results"]["sub_matrices"].items()
            }

        # Pastikan bobot dan matriks lainnya juga diubah ke list
        if "weights_main" in data_to_save["ahp_results"]:
            data_to_save["ahp_results"]["weights_main"] = (
                data_to_save["ahp_results"]["weights_main"].tolist()
                if isinstance(data_to_save["ahp_results"]["weights_main"], np.ndarray)
                else data_to_save["ahp_results"]["weights_main"]
            )

        if "sub_results" in data_to_save["ahp_results"]:
            for key, sub_result in data_to_save["ahp_results"]["sub_results"].items():
                if "weights_sub" in sub_result:
                    sub_result["weights_sub"] = (
                        sub_result["weights_sub"].tolist()
                        if isinstance(sub_result["weights_sub"], np.ndarray)
                        else sub_result["weights_sub"]
                    )

    # Konversi hasil perangkingan PM jika ada NumPy array
    if data_to_save["pm_results"] and isinstance(data_to_save["pm_results"], np.ndarray):
        data_to_save["pm_results"] = data_to_save["pm_results"].tolist()

     # Tempat untuk menampilkan pesan sementara
    message_placeholder = st.empty()
    try:
        with open(file_path, "w") as file:
            json.dump(data_to_save, file)  # Simpan ke JSON tanpa error
        
        # Tampilkan sukses dan hilangkan setelah 1 detik
        message_placeholder.success(f"Data berhasil disimpan ke: '{file_name}'")
        time.sleep(1)  # Menunggu selama 1 detik
        message_placeholder.empty()  # Menghapus pesan
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")


def load_from_json(file_name):
    file_path = os.path.join("data", file_name)
    message_placeholder = st.empty()
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)

            # Kembalikan hasil AHP dan PM ke session state
            st.session_state["ahp_results"] = data.get("ahp_results", None)
            st.session_state["pm_results"] = data.get("pm_results", None)

            # Kembalikan sub_matrices ke numpy array agar tetap bisa digunakan
            if st.session_state["ahp_results"] and "sub_matrices" in st.session_state["ahp_results"]:
                st.session_state["ahp_results"]["sub_matrices"] = {
                    key: np.array(value) if isinstance(value, list) else value
                    for key, value in st.session_state["ahp_results"]["sub_matrices"].items()
                }

            # Kembalikan bobot hasil perhitungan ke numpy array
            if "weights_main" in st.session_state["ahp_results"]:
                st.session_state["ahp_results"]["weights_main"] = np.array(st.session_state["ahp_results"]["weights_main"])

            if "sub_results" in st.session_state["ahp_results"]:
                for key, sub_result in st.session_state["ahp_results"]["sub_results"].items():
                    if "weights_sub" in sub_result:
                        sub_result["weights_sub"] = np.array(sub_result["weights_sub"])

            # Kembalikan Form Data ke session state agar form tetap terisi saat dimuat
            form_data = data.get("form_data", {})
            for key, value in form_data.items():
                if key == "criteria_labels":
                    # Muat hanya kriteria yang memiliki nama valid
                    st.session_state[key] = [c for c in value if c.strip()]
                elif key == "sub_criteria_dict":
                    # Muat hanya sub-kriteria untuk kriteria yang valid
                    st.session_state[key] = {k: v for k, v in value.items() if k.strip()}
                elif key == "alternatives":
                    # Muat hanya alternatif yang memiliki nama valid
                    st.session_state[key] = {alt: vals for alt, vals in value.items() if alt.strip()}
                else:
                    st.session_state[key] = value  # Muat data lain seperti biasa


         # Tampilkan sukses dan hilangkan setelah 1 detik
        message_placeholder.success(f"Data berhasil dimuat dari '{file_name}'")
        time.sleep(1)  # Menunggu selama 1 detik
        message_placeholder.empty()  # Menghapus pesan

    else:
        # Jika file tidak ditemukan, tampilkan error dan hilangkan setelah 1 detik
        message_placeholder.error(f"File '{file_name}' tidak ditemukan.")
        time.sleep(1)  # Menunggu selama 1 detik
        message_placeholder.empty()  # Menghapus pesan


# Bagian Simpan dan Muat Data
st.subheader("Load Data")
col1, col2 = st.columns([1, 3])

with col1:
    # Dropdown untuk memilih file yang akan dimuat
    existing_files = [f for f in os.listdir("data") if f.endswith(".json")]
    load_file_name = st.selectbox(
        "Pilih File untuk Dimuat",
        options=["Pilih data"] + existing_files if existing_files else ["Pilih data", "Tidak ada file"],
        index=0
    )

    # Tombol untuk memuat data
    if st.button("Muat Data"):
        if load_file_name and load_file_name != "Pilih data" and load_file_name != "Tidak ada file":
            load_from_json(load_file_name)
        elif load_file_name == "Pilih data":
            st.warning("Silakan pilih file terlebih dahulu.")
        else:
            st.error("Tidak ada file yang dapat dimuat.")


st.write("---") 


st.title("Sistem Pendukung Keputusan AHP dan Profile Matching")

# Tab untuk AHP dan Profile Matching
tabs = st.tabs(["AHP - Pembobotan", "Profile Matching - Perangkingan"])

# Variabel global untuk menyimpan data
if "ahp_results" not in st.session_state:
    st.session_state.ahp_results = None

# ----------------- TAB 1: AHP -----------------
with tabs[0]:
    st.header("Analytic Hierarchy Process (AHP)")
    
    # Pastikan nilai 'num_criteria' diinisialisasi hanya jika belum ada di session_state
    if "num_criteria" not in st.session_state:
        st.session_state.num_criteria = 0  # Nilai default

    # Gunakan widget input untuk jumlah kriteria utama tanpa mengatur 'value'
    num_criteria = st.number_input(
        "Jumlah Kriteria Utama",
        min_value=0,  # Minimal 1 kriteria utama
        step=1,
        key="num_criteria"  # Key otomatis menghubungkan nilai ke st.session_state
    )

    # Sinkronkan nilai widget dengan session_state jika diperlukan
    if st.session_state.num_criteria != num_criteria:
        st.session_state.num_criteria = num_criteria

    criteria_labels = []
    sub_criteria_dict = {}

    # Input kriteria utama dan sub-kriteria
    # Input kriteria utama dan sub-kriteria
    if num_criteria >= 1:
        for i in range(num_criteria):
            with st.expander(f"Kriteria {i+1}"):
                # Input nama kriteria utama
                criteria_name = st.text_input(f"Nama Kriteria {i+1}", value=f"K{i+1}", key=f"criteria_{i}")

                # Validasi nama kriteria utama
                if criteria_name.strip():
                    criteria_labels.append(criteria_name)

                    # Input jumlah sub-kriteria
                    num_sub = st.number_input(
                        f"Jumlah Sub-Kriteria untuk {criteria_name}",
                        min_value=0,
                        step=1,
                        value=0,
                        key=f"num_sub_{i}"
                    )

                    # Pastikan sub_labels hanya digunakan jika num_sub > 0
                    if num_sub > 0:
                        sub_labels = []
                        for j in range(num_sub):
                            sub_name = st.text_input(
                                f"Nama Sub-Kriteria {j+1} untuk {criteria_name}",
                                value=f"{criteria_name}_S{j+1}",
                                key=f"sub_{i}_{j}"
                            )
                            sub_labels.append(sub_name)

                        # Masukkan ke dictionary hanya jika ada sub_labels
                        sub_criteria_dict[criteria_name] = sub_labels
                    else:
                        # Jika tidak ada sub-kriteria, masukkan daftar kosong
                        sub_criteria_dict[criteria_name] = []

    st.session_state.sub_criteria = sub_criteria_dict

    st.write(f'### Matriks Perbandingan')

    # Matriks perbandingan untuk kriteria utama
    with st.expander("Matriks Perbandingan Kriteria Utama"):
        st.write("### Matriks Perbandingan Kriteria Utama")
        matrix_main = []
        for i in range(len(criteria_labels)):
            row = []
            for j in range(len(criteria_labels)):
                if i == j:
                    row.append(1.0)
                elif i < j:
                    val = st.number_input(
                        f"Perbandingan {criteria_labels[i]} vs {criteria_labels[j]}",
                        min_value=0.1,
                        value=1.0,
                        key=f"matrix_main_{i}_{j}",
                        format="%.3f"
                    )
                    row.append(val)
                else:
                    row.append(1 / matrix_main[j][i])
            matrix_main.append(row)
        matrix_main = np.array(matrix_main)

    # Matriks perbandingan untuk masing-masing sub-kriteria
    sub_matrices = {}
    for criteria, sub_labels in sub_criteria_dict.items():
        if len(sub_labels) > 0:
            with st.expander(f"Matriks Perbandingan Sub-Kriteria untuk {criteria}"):
                st.write(f"### Matriks Perbandingan Sub-Kriteria untuk {criteria}")
                matrix_sub = []
                for i in range(len(sub_labels)):
                    row = []
                    for j in range(len(sub_labels)):
                        if i == j:
                            row.append(1.0)
                        elif i < j:
                            val = st.number_input(
                                f"Perbandingan {sub_labels[i]} vs {sub_labels[j]} ",
                                min_value=0.1,
                                value=1.0,
                                key=f"matrix_sub_{criteria}_{i}_{j}",
                                format="%.3f"
                            )
                            row.append(val)
                        else:
                            row.append(1 / matrix_sub[j][i])
                    matrix_sub.append(row)
                sub_matrices[criteria] = np.array(matrix_sub)

    # Tombol untuk menghitung semua bobot
    if st.button("Hitung Bobot Prioritas"):
        # start_time = time.time()

        # Perhitungan bobot untuk kriteria utama
        df_main, weights_main, lambda_max_main, CI_main, CR_main, RI_main = ahp_rumus(matrix_main, criteria_labels)

        # Simpan hasil ke session state
        st.session_state.ahp_results = {
            "criteria_labels": criteria_labels,
            "weights_main": weights_main,
            "sub_criteria_dict": sub_criteria_dict,
            "sub_matrices": sub_matrices,
            "df_main": df_main.to_dict()
        }

        # Tampilkan hasil kriteria utama
        st.write("### Hasil Perhitungan Bobot Kriteria Utama")
        st.dataframe(df_main.round(3))
        st.write(f"**Lambda Max**: {lambda_max_main:.3f}")
        st.write(f"**CI**: {CI_main:.3f}")
        st.write(f"**RI**: {RI_main:.3f}")
        st.write(f"**CR**: {CR_main:.3f}")
        if CR_main < 0.1:
            st.success("Matriks kriteria utama konsisten.")
            st.session_state.is_consistent = True
        else:
            st.error("Matriks kriteria utama tidak konsisten, silakan perbaiki nilai perbandingan.")
            st.session_state.is_consistent = False
            # st.session_state.ahp_results = None

        # Perhitungan bobot untuk sub-kriteria
        sub_results = {}
        for criteria, sub_labels in sub_criteria_dict.items():
            if len(sub_labels) > 0:
                matrix_sub = sub_matrices[criteria]
                df_sub, weights_sub, lambda_max_sub, CI_sub, CR_sub, RI_sub = ahp_rumus(matrix_sub, sub_labels)

                # Tampilkan hasil perhitungan
                st.write(f"### Hasil Perhitungan Bobot Sub-Kriteria untuk {criteria}")
                st.dataframe(df_sub.round(3))
                st.write(f"**Lambda Max**: {lambda_max_sub:.3f}")
                st.write(f"**CI**: {CI_sub:.3f}")
                st.write(f"**RI**: {RI_sub:.3f}")
                st.write(f"**CR**: {CR_sub:.3f}")

                # Tambahkan hasil bobot sub-kriteria ke dalam sub_results
                sub_results[criteria] = {
                    "df_sub": df_sub.to_dict(),  # Konversi DataFrame ke dictionary agar bisa disimpan ke JSON
                    "weights_sub": weights_sub.tolist(),  # Konversi numpy array ke list
                    "lambda_max_sub": lambda_max_sub,
                    "CI_sub": CI_sub,
                    "CR_sub": CR_sub,
                    "RI_sub": RI_sub
                }

                # Periksa konsistensi matriks
                if CR_sub < 0.1:
                    st.success(f"Matriks sub-kriteria untuk {criteria} konsisten.")
                    st.session_state.is_consistent = True
                else:
                    st.error(f"Matriks sub-kriteria untuk {criteria} tidak konsisten, silakan perbaiki nilai perbandingan.")
                    st.session_state.is_consistent = False
                    # st.session_state.ahp_results = None

        # end_time = time.time()
        # computation_time = end_time - start_time
        # st.write(f"### Waktu Komputasi: {computation_time:.4f} detik")

        # Simpan semua hasil bobot sub-kriteria ke dalam st.session_state
        st.session_state["ahp_results"]["sub_results"] = sub_results

# ----------------- TAB 2: Profile Matching -----------------
with tabs[1]:
    st.header("Profile Matching")

    # Pemeriksaan ketidaksesuaian kriteria dengan sub-kriteria
    incompatible_criteria = [
        criteria for criteria in criteria_labels 
        if len(sub_criteria_dict.get(criteria, [])) == 0  # Mengecek jika kriteria tidak memiliki sub-kriteria
    ]
    
    if incompatible_criteria:
        st.error(f"Perhatian: Kriteria {', '.join(incompatible_criteria)} tidak memiliki sub-kriteria. Perbaiki Kriteria dan parameter")
        st.stop()  


    # Pastikan hasil AHP sudah ada
    if st.session_state.ahp_results is None:
        st.warning("Silakan lakukan perhitungan AHP di tab sebelumnya terlebih dahulu!")
    elif not st.session_state.get('is_consistent', True):  # Cek konsistensi matriks
        st.warning("Matriks tidak konsisten. Perbaiki matriks terlebih dahulu.")
    else:
        ahp_results = st.session_state.ahp_results
        criteria_labels = ahp_results["criteria_labels"]
        weights_main = ahp_results["weights_main"]
        sub_criteria_dict = ahp_results["sub_criteria_dict"]
        sub_matrices = ahp_results["sub_matrices"]

        # Tampilkan form input untuk Profile Matching
        st.write("### Input Nilai Profil Ideal")
        sub_criteria_config = {}
        sub_criteria_weights = {}
        criteria_groups = {}

        for i, criteria in enumerate(criteria_labels):
            # Tampilkan kriteria utama hanya dengan nama dan bobot AHP
            st.write(f"**{criteria}** (Bobot AHP: {weights_main[i]:.3f})")

            # Jika kriteria memiliki sub-kriteria, tampilkan dropdown
            if len(sub_criteria_dict[criteria]) > 0:
                with st.expander(f"Sub-Kriteria untuk {criteria}"):
                    # Ambil bobot sub-kriteria dari hasil AHP
                    df_sub, weights_sub, _, _, _, _ = ahp_rumus(sub_matrices[criteria], sub_criteria_dict[criteria])

                    # Buat daftar sub-kriteria untuk setiap kriteria utama
                    criteria_groups[criteria] = []

                    for j, sub_criteria in enumerate(sub_criteria_dict[criteria]):
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            st.selectbox(
                                f"{sub_criteria} - Jenis Data",
                                ["Numerik", "Kategorikal"],
                                key=f"data_type_{sub_criteria}"
                            )
                        with col2:
                            data_type = st.session_state.get(f"data_type_{sub_criteria}", "Numerik")
                            if data_type == "Numerik":
                                is_range = st.checkbox(
                                    f"{sub_criteria} - Rentang Nilai?",
                                    key=f"is_range_{sub_criteria}"
                                )
                                if is_range:
                                    st.number_input(
                                        f"Nilai Minimum {sub_criteria}",
                                        value=0.0,
                                        format="%.3f",
                                        key=f"min_value_{sub_criteria}"
                                    )
                                    st.number_input(
                                        f"Nilai Maksimum {sub_criteria}",
                                        value=5.0,
                                        format="%.3f",
                                        key=f"max_value_{sub_criteria}"
                                    )
                                else:
                                    st.number_input(
                                        f"Nilai Ideal {sub_criteria}",
                                        value=5.0,
                                        format="%.3f",
                                        key=f"ideal_value_{sub_criteria}"
                                    )
                            else:
                                st.text_input(
                                    f"Nilai Ideal {sub_criteria} (Pisahkan dengan koma jika lebih dari satu)",
                                    value="",
                                    key=f"ideal_value_{sub_criteria}"
                                )
                        with col3:
                            weight = weights_sub[j]
                            st.write(f"Bobot AHP: {weight:.3f}")

                            # Simpan bobot ke dictionary
                            sub_criteria_weights[sub_criteria] = weight
                            criteria_groups[criteria].append(sub_criteria)

                        # Simpan konfigurasi sub-kriteria
                        ideal_value = st.session_state.get(f"ideal_value_{sub_criteria}", "")
                        if data_type == "Kategorikal" and isinstance(ideal_value, str):
                            ideal_value = [v.strip() for v in ideal_value.split(",") if v.strip()]
                        sub_criteria_config[sub_criteria] = {
                            "data_type": data_type,
                            "ideal_value": (
                                [st.session_state.get(f"min_value_{sub_criteria}", 0.0),
                                 st.session_state.get(f"max_value_{sub_criteria}", 5.0)]
                                if st.session_state.get(f"is_range_{sub_criteria}", False)
                                else ideal_value
                            ),
                        }

        # Input alternatif
        st.write("### Input Nilai Alternatif")
        num_alternatives = st.number_input("Jumlah Alternatif", min_value=1, step=1, value=3, key="num_alternatives")
        alternatives = {}

        for i in range(num_alternatives):
            with st.expander(f"Alternatif {i+1}"):
                alt_name = st.text_input(f"Nama Alternatif {i+1}", value=f"A{i+1}", key=f"alt_name_{i}")
                alt_values = {}
                for criteria in criteria_labels:
                    if len(sub_criteria_dict[criteria]) > 0:
                        for sub_criteria in sub_criteria_dict[criteria]:
                            if sub_criteria_config[sub_criteria]["data_type"] == "Numerik":
                                if isinstance(sub_criteria_config[sub_criteria]["ideal_value"], list):
                                    val = st.number_input(
                                        f"Nilai {sub_criteria} untuk {alt_name}",
                                        value=0.0,
                                        format="%.3f",
                                        key=f"value_{alt_name}_{sub_criteria}"
                                    )
                                    alt_values[sub_criteria] = val
                                else:
                                    val = st.number_input(
                                        f"Nilai {sub_criteria} untuk {alt_name}",
                                        value=0.0,
                                        format="%.3f",
                                        key=f"value_{alt_name}_{sub_criteria}"
                                    )
                                    alt_values[sub_criteria] = val
                            else:  # Jika data kategorikal
                                val = st.text_input(
                                    f"Nilai {sub_criteria} untuk {alt_name}",
                                    value="",
                                    key=f"value_{alt_name}_{sub_criteria}"
                                )
                                alt_values[sub_criteria] = val
                    else:
                        val = st.text_input(
                            f"Nilai {criteria} untuk {alt_name}",
                            value="",
                            key=f"value_{alt_name}_{criteria}"
                        )
                        alt_values[criteria] = val
                # Hanya tambahkan alternatif jika nama alternatif tidak kosong
                if alt_name.strip():
                    alternatives[alt_name] = alt_values
                else:
                    st.warning(f"Alternatif {i+1} tidak dimasukkan karena nama kosong.")



        # Tombol hitung perangkingan
        if st.button("Hitung Perangkingan"):
            # start_time1 = time.time()

            # Ideal values sesuai jenis data
            ideal_values = {
                key: val["ideal_value"] for key, val in sub_criteria_config.items()
            }

            # Perhitungan Profile Matching
            results = profile_matching_with_ranges(
                alternatives,
                ideal_values,
                criteria_groups,
                sub_criteria_weights,
                dict(zip(criteria_labels, weights_main))
            )

            # Simpan hasil perangkingan ke session state
            st.session_state["pm_results"] = results

            # Tampilkan hasil perangkingan
            st.write("### Hasil Perangkingan")
            st.dataframe(pd.DataFrame(results).round(3))

            # end_time1 = time.time()
            # computation_time1 = end_time1 - start_time1
            # st.write(f"### Waktu Komputasi: {computation_time1:.4f} detik")

    st.write("---")
    st.subheader("Simpan Data Perhitungan AHP dan Profile Matching")
    # Input nama file untuk menyimpan
    st.text_input("Nama File Simpan (contoh: data.json)", value="data.json", key="save_file_name")
    if st.button("Simpan Data"):
        save_to_json(st.session_state.save_file_name)
