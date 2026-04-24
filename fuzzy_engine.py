# ──────────────────────────────────────────────────────────────
# BAGIAN 1: FUNGSI KEANGGOTAAN (Membership Functions)
# ──────────────────────────────────────────────────────────────

def mf_trapezoid(x: float, a: float, b: float, c: float, d: float) -> float:   
    if x <= a or x >= d:
        return 0.0
    elif b <= x <= c:
        return 1.0
    elif a < x < b:
        return (x - a) / (b - a)
    else:  # c < x < d
        return (d - x) / (d - c)


def mf_triangle(x: float, a: float, b: float, c: float) -> float:   
    if x <= a or x >= c:
        return 0.0
    elif x == b:
        return 1.0
    elif a < x <= b:
        return (x - a) / (b - a)
    else:  # b < x < c
        return (c - x) / (c - b)


def mf_shoulder_left(x: float, a: float, b: float) -> float:
    """
    Fungsi keanggotaan bahu kiri (untuk nilai sangat rendah).
    µ = 1.0 jika x <= a, turun linear hingga 0 di x = b.
    """
    if x <= a:
        return 1.0
    elif x >= b:
        return 0.0
    else:
        return (b - x) / (b - a)


def mf_shoulder_right(x: float, a: float, b: float) -> float:
    """
    Fungsi keanggotaan bahu kanan (untuk nilai sangat tinggi).
    µ = 0.0 jika x <= a, naik linear hingga 1.0 di x = b.
    """
    if x <= a:
        return 0.0
    elif x >= b:
        return 1.0
    else:
        return (x - a) / (b - a)


# ──────────────────────────────────────────────────────────────
# BAGIAN 2: FUZZIFIKASI INPUT
# ──────────────────────────────────────────────────────────────

class FuzzySuhu:
    """
    Himpunan fuzzy untuk variabel Suhu (0°C – 50°C).
    Tiga himpunan: DINGIN | NORMAL | PANAS
    """
    @staticmethod
    def dingin(s: float) -> float:
        # µ = 1 jika s <= 8, turun ke 0 di s = 18
        return mf_shoulder_left(s, 8, 18)

    @staticmethod
    def normal(s: float) -> float:
        # µ puncak di 15–22, transisi di 10 dan 28
        return mf_trapezoid(s, 10, 15, 22, 28)

    @staticmethod
    def panas(s: float) -> float:
        # µ = 0 di s = 26, naik ke 1 di s = 35+
        return mf_shoulder_right(s, 26, 35)


class FuzzyHumid:
    """
    Himpunan fuzzy untuk variabel Kelembapan (0% – 100%).
    Tiga himpunan: KERING | OPTIMAL | LEMBAP
    """
    @staticmethod
    def kering(h: float) -> float:
        return mf_shoulder_left(h, 25, 38)

    @staticmethod
    def optimal(h: float) -> float:
        return mf_trapezoid(h, 35, 42, 56, 65)

    @staticmethod
    def lembap(h: float) -> float:
        return mf_shoulder_right(h, 60, 75)


# ──────────────────────────────────────────────────────────────
# BAGIAN 3: RULE BASE (Basis Aturan Mamdani)
# ──────────────────────────────────────────────────────────────

# Output fuzzy set mapping → skor numerik (untuk defuzzifikasi)
OUTPUT_SETS = {
    "IDEAL":    90,   # kondisi terbaik
    "OK":       60,   # dapat diterima
    "WASPADA":  35,   # perlu perhatian
    "BAHAYA":   10,   # kondisi berbahaya
}

def evaluate_rules(mu_suhu: dict, mu_humid: dict) -> dict:
    """
    Evaluasi semua rule fuzzy dengan operator Mamdani.
    Setiap rule: IF (kondisi suhu) AND (kondisi humid) THEN output
    Operator AND  = MIN
    Operator OR   = MAX (untuk agregasi rule dengan output sama)
    
    Args:
        mu_suhu  : dict derajat keanggotaan suhu   {dingin, normal, panas}
        mu_humid : dict derajat keanggotaan humid  {kering, optimal, lembap}
    Returns:
        dict output fuzzy dengan firing strength tiap himpunan output
    """
    rules = {
        # [R1] IF suhu NORMAL AND humid OPTIMAL  THEN IDEAL
        "IDEAL":   max([
            min(mu_suhu["normal"],  mu_humid["optimal"]),   # R1
        ]),
        # [R2] IF suhu DINGIN AND humid OPTIMAL  THEN OK
        # [R3] IF suhu PANAS  AND humid OPTIMAL  THEN OK
        # [R4] IF suhu NORMAL AND humid KERING   THEN OK
        # [R5] IF suhu NORMAL AND humid LEMBAP   THEN OK
        "OK":      max([
            min(mu_suhu["dingin"],  mu_humid["optimal"]),   # R2
            min(mu_suhu["panas"],   mu_humid["optimal"]),   # R3
            min(mu_suhu["normal"],  mu_humid["kering"]),    # R4
            min(mu_suhu["normal"],  mu_humid["lembap"]),    # R5
        ]),
        # [R6] IF suhu DINGIN AND humid KERING   THEN WASPADA
        # [R7] IF suhu PANAS  AND humid KERING   THEN WASPADA
        # [R8] IF suhu DINGIN AND humid LEMBAP   THEN WASPADA
        "WASPADA": max([
            min(mu_suhu["dingin"],  mu_humid["kering"]),    # R6
            min(mu_suhu["panas"],   mu_humid["kering"]),    # R7
            min(mu_suhu["dingin"],  mu_humid["lembap"]),    # R8
        ]),
        # [R9]  IF suhu PANAS  AND humid LEMBAP  THEN BAHAYA
        "BAHAYA":  max([
            min(mu_suhu["panas"],   mu_humid["lembap"]),    # R9
        ]),
    }
    return rules


# ──────────────────────────────────────────────────────────────
# BAGIAN 4: DEFUZZIFIKASI (Metode Weighted Average / Centroid)
# ──────────────────────────────────────────────────────────────

def defuzzify(fired_rules: dict) -> float:
    """
    Defuzzifikasi menggunakan Weighted Average (approx. Centroid).
    
    Formula:
        z* = Σ(µi × zi) / Σ(µi)
        
    dimana:
        µi = firing strength rule ke-i
        zi = nilai representatif output set ke-i
    
    Args:
        fired_rules: {nama_set: firing_strength}
    Returns:
        nilai crisp output [0..100]
    """
    numerator   = sum(fired_rules[name] * OUTPUT_SETS[name] for name in fired_rules)
    denominator = sum(fired_rules[name] for name in fired_rules)

    if denominator == 0:
        return 0.0

    return round(numerator / denominator, 2)


# ──────────────────────────────────────────────────────────────
# BAGIAN 5: FAKTOR KOREKSI PER JENIS JAM & DURASI
# ──────────────────────────────────────────────────────────────

JENIS_FACTOR = {
    # Mechanical paling sensitif terhadap suhu & kelembapan
    "mechanical": 1.00,
    # Quartz sedikit lebih toleran
    "quartz":     0.95,
    # Smart luxury — baterai sensitif suhu, tapi seal lebih baik
    "smartlux":   0.90,
}

DURASI_PENALTY = {
    # Dipakai harian — paparan minimal
    "short":  0.00,
    # Rotasi mingguan — risiko sedang
    "medium": 5.00,
    # Simpan lama — akumulasi risiko
    "long":   12.00,
}


# ──────────────────────────────────────────────────────────────
# BAGIAN 6: FUNGSI UTAMA SISTEM FUZZY
# ──────────────────────────────────────────────────────────────

def run_fuzzy(suhu: float, humid: float,
              jenis: str = "mechanical",
              durasi: str = "short") -> dict:
    """
    Jalankan seluruh pipeline Sistem Fuzzy Mamdani.
    
    Pipeline:
      Input → Fuzzifikasi → Rule Evaluation → Agregasi → Defuzzifikasi → Output
    
    Args:
        suhu   : suhu ruangan dalam °C
        humid  : kelembapan relatif dalam %
        jenis  : jenis jam ('mechanical' | 'quartz' | 'smartlux')
        durasi : durasi penyimpanan ('short' | 'medium' | 'long')
    
    Returns:
        dict lengkap berisi semua tahap dan hasil akhir
    """

    # ── STEP 1: FUZZIFIKASI ──────────────────────────────────
    mu_suhu = {
        "dingin": FuzzySuhu.dingin(suhu),
        "normal": FuzzySuhu.normal(suhu),
        "panas":  FuzzySuhu.panas(suhu),
    }
    mu_humid = {
        "kering":  FuzzyHumid.kering(humid),
        "optimal": FuzzyHumid.optimal(humid),
        "lembap":  FuzzyHumid.lembap(humid),
    }

    # ── STEP 2 & 3: EVALUASI RULE + AGREGASI ────────────────
    fired_rules = evaluate_rules(mu_suhu, mu_humid)

    # ── STEP 4: DEFUZZIFIKASI ────────────────────────────────
    raw_score = defuzzify(fired_rules)

    # ── STEP 5: KOREKSI FAKTOR JENIS & DURASI ───────────────
    jenis_f  = JENIS_FACTOR.get(jenis, 1.0)
    durasi_p = DURASI_PENALTY.get(durasi, 0.0)
    final_score = max(0, min(100, round((raw_score * jenis_f) - durasi_p)))

    # ── STEP 6: KLASIFIKASI OUTPUT ───────────────────────────
    if final_score >= 75:
        kondisi = "Ideal"
        risiko  = "Sangat Rendah"
        warna   = "ideal"
        rekomendasi = [
            "Pertahankan kondisi penyimpanan yang ada saat ini.",
            "Gunakan watch winder jika jam automatic tidak dipakai > 48 jam.",
            "Servis mekanik berkala setiap 3–5 tahun di service center resmi.",
            "Dokumentasikan kondisi jam untuk keperluan asuransi.",
        ]
    elif final_score >= 40:
        kondisi = "Perlu Perhatian"
        risiko  = "Sedang"
        warna   = "warning"
        rekomendasi = [
            "Investasi dehumidifier / humidifier untuk stabilisasi kelembapan.",
            "Simpan dalam watch case berbahan cedar dengan seal kedap udara.",
            "Monitor kondisi dengan hygrometer digital secara rutin.",
            "Percepat jadwal servis mekanik jika paparan berlangsung lama.",
        ]
    else:
        kondisi = "Berbahaya"
        risiko  = "Tinggi"
        warna   = "danger"
        rekomendasi = [
            "SEGERA pindahkan ke lingkungan penyimpanan yang terkontrol.",
            "Bawa ke service center resmi untuk inspeksi seal dan lubrikasi.",
            "Pertimbangkan safe deposit box beriklim terkontrol.",
            "Konsultasikan dengan boutique resmi untuk penilaian kondisi.",
        ]

    return {
        # Input
        "input": {
            "suhu": suhu, "humid": humid,
            "jenis": jenis, "durasi": durasi,
        },
        # Fuzzifikasi
        "mu_suhu":  mu_suhu,
        "mu_humid": mu_humid,
        # Rules
        "fired_rules": {k: round(v, 4) for k, v in fired_rules.items()},
        # Output
        "raw_score":    raw_score,
        "final_score":  final_score,
        "kondisi":      kondisi,
        "risiko":       risiko,
        "warna":        warna,
        "rekomendasi":  rekomendasi,
    }
