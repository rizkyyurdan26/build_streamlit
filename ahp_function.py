import numpy as np

# Fungsi untuk menghitung bobot
def ahp_weights(matrix_comparism):
    # Pastikan matrix_comparism berupa numpy.ndarray
    if not isinstance(matrix_comparism, np.ndarray):
        matrix_comparism = np.array(matrix_comparism)

    n = matrix_comparism.shape[0]
    M_I = np.prod(matrix_comparism, axis=1)
    W_bar_I = np.power(M_I, 1/n)
    W_I = W_bar_I / np.sum(W_bar_I)
    return W_I, W_bar_I

# Dictionary Random Index (RI)
Dict_RI = {
    1: 0.00, 
    2: 0.00, 
    3: 0.58, 
    4: 0.90, 
    5: 1.12, 
    6: 1.24, 
    7: 1.32, 
    8: 1.41, 
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.48,
    13: 1.56,
    14: 1.57,
    15: 1.58,
}

# Fungsi untuk menghitung konsistensi
def consistency(matrix_comparism, W_I):
    # Pastikan matrix_comparism berupa numpy.ndarray
    if not isinstance(matrix_comparism, np.ndarray):
        matrix_comparism = np.array(matrix_comparism)

    n = matrix_comparism.shape[0]
    AW = np.dot(matrix_comparism, W_I)
    lambda_max = np.sum(AW / (n * W_I))
    CI = (lambda_max - n) / (n - 1) if n > 1 else 0  # CI dihitung hanya jika n > 1
    RI = Dict_RI.get(n, 0)  # Ambil nilai RI dari Dict_RI, default ke 0
    CR = CI / RI if RI != 0 else 0  # Hindari pembagian dengan nol
    return lambda_max, CI, CR, RI

# Fungsi utama untuk AHP
def ahp_rumus(matrix_comparism, labels):
    # Pastikan matrix_comparism berupa numpy.ndarray
    if not isinstance(matrix_comparism, np.ndarray):
        matrix_comparism = np.array(matrix_comparism)

    if matrix_comparism.shape[0] == 0:  # Matriks kosong
        raise ValueError("Matrix is empty. Please provide a valid comparison matrix.")

    W_I, W_bar_I = ahp_weights(matrix_comparism)
    lambda_max, CI, CR, RI = consistency(matrix_comparism, W_I)
    
    # Buat DataFrame hasil
    import pandas as pd
    df = pd.DataFrame(matrix_comparism, index=labels, columns=labels)
    df['Weight'] = W_I

    return df, W_I, lambda_max, CI, CR, RI
