import numpy as np

# Fungsi untuk menghitung GAP
def calculate_gap(candidate_value, ideal_value):
    """Menghitung GAP antara nilai kandidat dan nilai ideal."""
    
    # Jika ideal_value berupa range numerik (min, max), pastikan isinya angka
    if (
        isinstance(ideal_value, (list, tuple)) and 
        len(ideal_value) == 2 and 
        all(isinstance(v, (int, float)) for v in ideal_value)
    ):
        min_val, max_val = ideal_value
        return interpolasi(candidate_value, min_val, max_val)

    # Jika ideal_value berupa string (kategorikal)
    elif isinstance(candidate_value, str):
        if isinstance(ideal_value, str):  
            # Jika ideal_value hanya satu teks, ubah menjadi list
            ideal_value = [ideal_value.strip()]  
        elif isinstance(ideal_value, list):  
            # Bersihkan elemen ideal_value untuk memastikan tidak ada whitespace berlebih
            ideal_value = [val.strip() for val in ideal_value]  

        # Pastikan ideal_value benar-benar daftar string sebelum membandingkan
        if all(isinstance(v, str) for v in ideal_value):
            return 5 if candidate_value.strip() in ideal_value else 1
        else:
            raise TypeError(f"Ideal value untuk '{candidate_value}' harus berupa string atau daftar string.")

    # Jika ideal_value berupa angka tunggal
    elif isinstance(candidate_value, (int, float)) and isinstance(ideal_value, (int, float)):
        gap = candidate_value - ideal_value
        return gap_weight(gap)

    else:
        # Jika tipe data tidak cocok
        raise TypeError(f"Data ideal dan kandidat tidak cocok: {candidate_value} ({type(candidate_value)}) vs {ideal_value} ({type(ideal_value)})")

# Fungsi interpolasi untuk range numerik
def interpolasi(x, min_val, max_val):
    """Interpolasi nilai kandidat terhadap rentang ideal."""
    if not isinstance(x, (int, float)) or not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
        raise TypeError(f"Data numerik diperlukan untuk interpolasi, tetapi mendapatkan: {type(x)}")
    
    if min_val <= x <= max_val:
        return 5
    elif 0 <= x < min_val:
        return 1 + ((x - 0) / (min_val - 0)) * (5 - 1)
    elif max_val < x <= (min_val + max_val):
        return 5 + ((x - max_val) / ((min_val + max_val) - max_val)) * (1 - 5)
    else:
        return 1

# Fungsi untuk menentukan bobot GAP berdasarkan aturan Profile Matching
def gap_weight(gap):
    """Menghitung bobot GAP berdasarkan aturan gap profile matching."""
    gap_weights = {
        0: 5,
        1: 4.5,
        -1: 4,
        2: 3.5,
        -2: 3,
        3: 2.5,
        -3: 2,
        4: 1.5,
        -4: 1
    }
    return gap_weights.get(gap, 1)  # Default bobot adalah 1 jika GAP lebih dari ±4

# Fungsi utama Profile Matching
def profile_matching_with_ranges(alternatives, ideal_values, criteria_groups, sub_criteria_weights, criteria_weights):
    results = []

    for name, candidate in alternatives.items():
        weights = {}
        for key in candidate:
            try:
                # Periksa apakah ideal_value berupa rentang numerik
                if isinstance(ideal_values[key], (list, tuple)) and len(ideal_values[key]) == 2:
                    # Pastikan semua elemen dalam ideal_value adalah angka sebelum menggunakannya sebagai range
                    if all(isinstance(v, (int, float)) for v in ideal_values[key]):
                        min_val, max_val = ideal_values[key]
                        weights[key] = interpolasi(candidate[key], min_val, max_val)
                    else:
                        weights[key] = calculate_gap(candidate[key], ideal_values[key])

                # Jika ideal_value berupa string atau list string
                else:
                    weights[key] = calculate_gap(candidate[key], ideal_values[key])

            except Exception as e:
                raise TypeError(f"Error in processing key '{key}': {e}")

        # Hitung nilai kriteria utama berdasarkan sub-kriteria
        criteria_scores = {}
        for criteria, sub_criteria in criteria_groups.items():
            nk = sum(weights[sub] * sub_criteria_weights[sub] for sub in sub_criteria)
            criteria_scores[criteria] = nk

        # Hitung Final Score
        final_score = sum(criteria_scores[criteria] * criteria_weights[criteria] for criteria in criteria_scores)

        results.append({
            "Alternatif": name,
            **weights,  # Tambahkan bobot GAP untuk tiap sub-kriteria
            **criteria_scores,  # Tambahkan nilai kriteria utama
            "Final Score": final_score,
        })

    # Urutkan hasil berdasarkan Final Score (tertinggi ke terendah)
    results = sorted(results, key=lambda x: x["Final Score"], reverse=True)
    for i, result in enumerate(results, start=1):
        result["Ranking"] = i

    return results
