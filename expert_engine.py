from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# BAGIAN 1: KNOWLEDGE BASE — Basis Pengetahuan
# ──────────────────────────────────────────────────────────────

@dataclass
class Rule:
    """
    Satu aturan dalam Knowledge Base.
    Format: IF (conditions) THEN (action)
    """
    id: str                          # ID unik rule, e.g. "R01"
    name: str                        # Nama deskriptif rule
    conditions: dict                 # {atribut: nilai_yang_match}
    action: str                      # Output / kesimpulan rule ini
    score_delta: int                 # Poin yang ditambah/kurang ke skor
    confidence: float = 1.0          # Tingkat kepercayaan rule [0..1]
    explanation: str = ""            # Penjelasan mengapa rule ini penting


# ── Knowledge Base: semua rule sistem pakar ──────────────────
KNOWLEDGE_BASE: list[Rule] = [

    # ═══════════════════════════════════════════════════════
    # RULES UNTUK JAHITAN (bobot 25 poin)
    # ═══════════════════════════════════════════════════════
    Rule(
        id="R01", name="Jahitan Sempurna → Indikasi Asli",
        conditions={"jahitan": "sempurna"},
        action="jahitan_authentic",
        score_delta=25,
        confidence=0.92,
        explanation="Produk luxury asli memiliki jahitan tangan presisi "
                    "dengan jarak antar jahitan seragam (8-9 jahitan per cm pada Hermès)."
    ),
    Rule(
        id="R02", name="Jahitan Minor → Uncertain",
        conditions={"jahitan": "minor"},
        action="jahitan_uncertain",
        score_delta=12,
        confidence=0.65,
        explanation="Ketidakrataan kecil bisa terjadi pada produk asli vintaj "
                    "atau refurbished, namun perlu verifikasi lebih lanjut."
    ),
    Rule(
        id="R03", name="Jahitan Buruk → Indikasi Palsu",
        conditions={"jahitan": "buruk"},
        action="jahitan_fake",
        score_delta=0,
        confidence=0.95,
        explanation="Produk luxury asli tidak pernah memiliki jahitan yang "
                    "tidak konsisten — ini adalah red flag utama pemalsuan."
    ),

    # ═══════════════════════════════════════════════════════
    # RULES UNTUK HARDWARE (bobot 25 poin)
    # ═══════════════════════════════════════════════════════
    Rule(
        id="R04", name="Hardware Solid Berlogo → Indikasi Asli",
        conditions={"hw": "solid"},
        action="hw_authentic",
        score_delta=25,
        confidence=0.90,
        explanation="Hardware Hermès/Chanel/LV asli terbuat dari brass berlapis "
                    "gold atau palladium — terasa berat, tidak goyang, logo terukir dalam."
    ),
    Rule(
        id="R05", name="Hardware Medium → Uncertain",
        conditions={"hw": "medium"},
        action="hw_uncertain",
        score_delta=12,
        confidence=0.55,
        explanation="Hardware dengan berat sedang bisa jadi produk asli lama "
                    "yang hardware-nya sudah aus, atau produk super-fake berkualitas tinggi."
    ),
    Rule(
        id="R06", name="Hardware Ringan Tanpa Logo → Indikasi Palsu",
        conditions={"hw": "ringan"},
        action="hw_fake",
        score_delta=0,
        confidence=0.97,
        explanation="Hardware ringan tanpa branding jelas adalah tanda pemalsuan "
                    "yang paling mudah dideteksi. Tidak ada luxury brand yang menggunakan ini."
    ),

    # ═══════════════════════════════════════════════════════
    # RULES UNTUK DOKUMEN (bobot 25 poin)
    # ═══════════════════════════════════════════════════════
    Rule(
        id="R07", name="Dokumen Lengkap → Nilai Investasi Tinggi",
        conditions={"dok": "lengkap"},
        action="dok_complete",
        score_delta=25,
        confidence=0.88,
        explanation="Receipt asli, dustbag, dan box original meningkatkan "
                    "nilai resale 25–35%. Sertifikat keaslian Hermès sulit dipalsukan."
    ),
    Rule(
        id="R08", name="Dokumen Partial → Uncertain",
        conditions={"dok": "partial"},
        action="dok_partial",
        score_delta=10,
        confidence=0.60,
        explanation="Kehilangan sebagian dokumen umum terjadi pada tas secondhand "
                    "yang berpindah tangan berkali-kali. Tidak langsung menunjukkan pemalsuan."
    ),
    Rule(
        id="R09", name="Tanpa Dokumen → Risiko Tinggi",
        conditions={"dok": "tidak"},
        action="dok_missing",
        score_delta=0,
        confidence=0.72,
        explanation="Ketiadaan dokumen pada tas baru / hampir baru sangat mencurigakan. "
                    "Seller produk asli hampir selalu menyimpan dokumen pembelian."
    ),

    # ═══════════════════════════════════════════════════════
    # RULES UNTUK MATERIAL / AROMA (bobot 25 poin)
    # ═══════════════════════════════════════════════════════
    Rule(
        id="R10", name="Kulit Genuine Natural → Asli",
        conditions={"aroma": "genuine"},
        action="material_authentic",
        score_delta=25,
        confidence=0.93,
        explanation="Kulit asli (Togo, Epsom, Caviar) memiliki aroma earthy yang "
                    "khas dan tidak bisa direplikasi sempurna oleh material sintetis."
    ),
    Rule(
        id="R11", name="Aroma Kimia → Uncertain",
        conditions={"aroma": "chemical"},
        action="material_uncertain",
        score_delta=8,
        confidence=0.68,
        explanation="Aroma kimia bisa berasal dari proses penyamakan ulang atau "
                    "konditioner kulit yang digunakan pemilik sebelumnya."
    ),
    Rule(
        id="R12", name="Aroma Plastik/Lem → Palsu",
        conditions={"aroma": "plastik"},
        action="material_fake",
        score_delta=0,
        confidence=0.98,
        explanation="Aroma plastik atau lem adalah bukti penggunaan PU leather "
                    "atau bahan sintetis — tidak pernah digunakan oleh Hermès, Chanel, atau LV."
    ),

    # ═══════════════════════════════════════════════════════
    # RULES KOMBINASI — BONUS / PENALTY (Forward Chaining lanjutan)
    # ═══════════════════════════════════════════════════════
    Rule(
        id="R13", name="TRIPLE AUTHENTIC — Semua Asli",
        conditions={"jahitan": "sempurna", "hw": "solid", "aroma": "genuine"},
        action="triple_authentic_bonus",
        score_delta=5,   # Bonus +5
        confidence=0.99,
        explanation="Kombinasi ketiga atribut fisik utama yang sempurna "
                    "sangat sulit dipalsukan secara bersamaan."
    ),
    Rule(
        id="R14", name="DOUBLE FAKE — Hardware + Material Palsu",
        conditions={"hw": "ringan", "aroma": "plastik"},
        action="double_fake_penalty",
        score_delta=-10,  # Penalty -10
        confidence=0.99,
        explanation="Kombinasi hardware ringan tanpa logo DAN material sintetis "
                    "adalah pola klasik produk tiruan kelas bawah."
    ),
    Rule(
        id="R15", name="HERMÈS BONUS — Brand Prestige",
        conditions={"brand": "hermes", "jahitan": "sempurna", "dok": "lengkap"},
        action="hermes_investment_grade",
        score_delta=3,   # Bonus +3 untuk nilai investasi
        confidence=0.95,
        explanation="Hermès Birkin/Kelly dengan dokumen lengkap dan jahitan "
                    "sempurna adalah investment-grade asset yang paling dicari."
    ),
    Rule(
        id="R16", name="CHANEL BONUS — Classic Collection",
        conditions={"brand": "chanel", "hw": "solid", "dok": "lengkap"},
        action="chanel_investment_grade",
        score_delta=3,
        confidence=0.93,
        explanation="Chanel Classic Flap dengan hardware solid dan card asli "
                    "terapresiasi nilai >70% dalam 5 tahun terakhir."
    ),
]


# ──────────────────────────────────────────────────────────────
# BAGIAN 2: WORKING MEMORY
# ──────────────────────────────────────────────────────────────

@dataclass
class WorkingMemory:
    """
    Menyimpan fakta yang diketahui selama sesi inferensi.
    Diinisialisasi dengan fakta dari user, lalu diperkaya
    oleh hasil firing rule.
    """
    facts: dict = field(default_factory=dict)       # Fakta yang diketahui
    fired_rules: list = field(default_factory=list) # Rule yang sudah aktif
    conclusions: list = field(default_factory=list) # Kesimpulan yang didapat
    score: int = 0                                   # Akumulasi skor

    def add_fact(self, key: str, value):
        self.facts[key] = value

    def has_fact(self, key: str, value=None) -> bool:
        if value is None:
            return key in self.facts
        return self.facts.get(key) == value

    def add_conclusion(self, action: str, rule_id: str):
        if action not in self.conclusions:
            self.conclusions.append(action)
            self.fired_rules.append(rule_id)


# ──────────────────────────────────────────────────────────────
# BAGIAN 3: INFERENCE ENGINE — Forward Chaining
# ──────────────────────────────────────────────────────────────

class ForwardChainingEngine:
    """
    Mesin Inferensi Forward Chaining.
    
    Algoritma:
      1. Mulai dari fakta awal (input user)
      2. Cocokkan kondisi setiap rule dengan fakta di Working Memory
      3. Jika semua kondisi rule terpenuhi → FIRE rule tersebut
      4. Tambahkan kesimpulan rule ke Working Memory sebagai fakta baru
      5. Ulangi hingga tidak ada rule baru yang bisa di-fire (fixed point)
    
    Ini disebut "data-driven" / "bottom-up" reasoning.
    """

    def __init__(self, knowledge_base: list[Rule]):
        self.kb = knowledge_base
        self.wm = WorkingMemory()
        self.trace = []  # Jejak inferensi untuk transparansi

    def load_facts(self, facts: dict):
        """Muat fakta awal dari input user ke Working Memory."""
        for key, value in facts.items():
            self.wm.add_fact(key, value)
        self.trace.append(f"[INIT] Working Memory dimuat: {facts}")

    def _check_conditions(self, rule: Rule) -> bool:
        """
        Periksa apakah semua kondisi rule terpenuhi oleh Working Memory.
        Menggunakan AND logic — semua kondisi harus match.
        """
        for attr, expected_val in rule.conditions.items():
            actual_val = self.wm.facts.get(attr)
            if actual_val != expected_val:
                return False
        return True

    def run(self) -> WorkingMemory:
        """
        Jalankan forward chaining hingga fixed point (agenda kosong).
        
        Returns:
            WorkingMemory yang sudah diisi kesimpulan
        """
        agenda = list(self.kb)  # Semua rule yang belum di-fire
        changed = True

        cycle = 0
        while changed and agenda:
            changed = False
            cycle += 1
            remaining = []

            for rule in agenda:
                if self._check_conditions(rule):
                    # ── FIRE RULE ────────────────────────────
                    self.wm.add_conclusion(rule.action, rule.id)

                    # Hitung delta skor (bisa negatif untuk penalty)
                    self.wm.score += rule.score_delta
                    self.wm.score = max(0, min(100, self.wm.score))

                    # Tambah action sebagai fakta baru
                    self.wm.add_fact(rule.action, True)

                    self.trace.append(
                        f"[Cycle {cycle}] FIRE {rule.id}: '{rule.name}' "
                        f"→ +{rule.score_delta} pts | Confidence: {rule.confidence:.0%}"
                    )
                    changed = True
                else:
                    remaining.append(rule)

            agenda = remaining

        self.trace.append(f"[DONE] Fixed point tercapai setelah {cycle} siklus.")
        self.trace.append(f"[DONE] Skor akhir: {self.wm.score}/100")
        self.trace.append(f"[DONE] Rule aktif: {self.wm.fired_rules}")
        return self.wm


# ──────────────────────────────────────────────────────────────
# BAGIAN 4: KNOWLEDGE UNTUK INVESTASI PER BRAND
# ──────────────────────────────────────────────────────────────

BRAND_NAMES = {
    "hermes": "Hermès",
    "chanel": "Chanel",
    "lv":     "Louis Vuitton",
    "other":  "Luxury Brand",
}

INVESTMENT_KNOWLEDGE = {
    "hermes": {
        "authentic": [
            "Hermès Birkin & Kelly terapresiasi rata-rata 14% per tahun dalam dekade terakhir.",
            "Birkin 25 Togo Gold saat ini dihargai 2–3x lipat harga retail di pasar resale.",
            "Dokumen lengkap meningkatkan nilai resale 25–35%.",
            "Pertimbangkan konsinyasi di Sotheby's, Christie's, atau Vestiaire Collective.",
        ],
        "uncertain": [
            "Verifikasi ke boutique Hermès terdekat sebelum transaksi apapun.",
            "Gunakan layanan Bababebi atau Love That Bag untuk authentication Indonesia.",
            "Periksa blind stamp (tahun produksi) dan craftsman letter di bagian dalam.",
        ],
        "fake": [
            "Produk ini tidak memiliki nilai investasi sebagai luxury asset.",
            "Penjualan produk tiruan Hermès melanggar UU Merek No. 20 Tahun 2016.",
            "Gunakan Vestiaire Collective atau The Real Real untuk pembelian aman.",
        ],
    },
    "chanel": {
        "authentic": [
            "Chanel Classic Flap terapresiasi >70% dalam 5 tahun terakhir.",
            "Hologram sticker dan authenticity card adalah wajib pada tas Chanel asli.",
            "Chanel mini rectangle saat ini dijual >3x harga retail di lelang.",
            "Simpan dalam dustbag dan box asli — kondisi 'pristine' nilai tertinggi.",
        ],
        "uncertain": [
            "Scan hologram sticker dengan aplikasi Entrupy untuk verifikasi.",
            "Periksa CC logo alignment — pada produk asli selalu simetris sempurna.",
            "Konsultasi ke Chanel boutique untuk certificate of authenticity.",
        ],
        "fake": [
            "Tidak ada nilai investasi pada produk non-authentic.",
            "Melanggar hak kekayaan intelektual Chanel S.A.",
            "Belanja aman di Fashionphile atau bagian preloved Chanel boutique resmi.",
        ],
    },
    "lv": {
        "authentic": [
            "Louis Vuitton limited edition dan collaboration memiliki appreciation rate tinggi.",
            "LV Neverfull MM adalah salah satu tas paling liquid di pasar resale.",
            "Date code dan heat stamp harus konsisten dengan tahun produksi.",
            "Resale platform terpercaya: Rebag, Fashionphile, The Real Real.",
        ],
        "uncertain": [
            "Periksa date code format — LV menggunakan sistem kode 2 huruf + 4 angka.",
            "Canvas LV Monogram asli memiliki tekstur dan berat khas yang sulit dipalsukan.",
            "Gunakan layanan LV Client Services untuk verifikasi.",
        ],
        "fake": [
            "Tidak ada nilai investasi pada produk non-authentic.",
            "Penjualan replika LV merupakan pelanggaran hukum internasional.",
            "Hubungi Louis Vuitton customer service untuk edukasi keaslian produk.",
        ],
    },
    "other": {
        "authentic": [
            "Luxury bag lainnya (Bottega Veneta, Dior, Gucci) juga memiliki pasar resale aktif.",
            "Kelengkapan dokumen dan kondisi fisik adalah penentu nilai resale utama.",
            "Gunakan platform terpercaya untuk penjualan: Vestiaire Collective, Tradesy.",
        ],
        "uncertain": [
            "Cek authentication specialist sesuai brand spesifik tas Anda.",
            "Setiap brand memiliki tanda keaslian yang berbeda — pelajari brand guide-nya.",
        ],
        "fake": [
            "Tidak ada nilai investasi pada produk non-authentic.",
            "Jual hanya produk yang dapat diverifikasi keasliannya.",
        ],
    },
}


# ──────────────────────────────────────────────────────────────
# BAGIAN 5: FUNGSI UTAMA SISTEM PAKAR
# ──────────────────────────────────────────────────────────────

def run_expert_system(facts: dict) -> dict:
    """
    Jalankan seluruh pipeline Sistem Pakar Forward Chaining.
    
    Pipeline:
      Facts → Working Memory → Forward Chaining → 
      Skor Akhir → Verdict → Investment Advice → Output
    
    Args:
        facts: dict berisi {brand, jahitan, hw, dok, aroma}
    
    Returns:
        dict lengkap berisi semua hasil dan jejak inferensi
    """

    # ── STEP 1: Inisialisasi engine ──────────────────────────
    engine = ForwardChainingEngine(KNOWLEDGE_BASE)
    engine.load_facts(facts)

    # ── STEP 2: Jalankan Forward Chaining ───────────────────
    wm = engine.run()

    # ── STEP 3: Tentukan verdict berdasarkan skor ───────────
    score = wm.score
    brand = facts.get("brand", "other")
    brand_name = BRAND_NAMES.get(brand, "Luxury Brand")

    if score >= 80:
        verdict        = "Authentic"
        verdict_id     = "authentic"
        verdict_detail = (
            f"Seluruh atribut fisik konsisten dengan standar produk original {brand_name}. "
            f"Jahitan presisi, hardware berbobot dengan branding jelas, serta material kulit "
            f"genuine adalah tanda keaslian yang sangat sulit dipalsukan secara bersamaan."
        )
        badge_class    = "authentic"
        invest_key     = "authentic"

    elif score >= 40:
        verdict        = "Uncertain"
        verdict_id     = "uncertain"
        verdict_detail = (
            f"Beberapa atribut tidak sepenuhnya memenuhi standar {brand_name}. "
            f"Dibutuhkan verifikasi lebih lanjut oleh authentication expert atau "
            f"boutique resmi sebelum transaksi dilakukan."
        )
        badge_class    = "uncertain"
        invest_key     = "uncertain"

    else:
        verdict        = "Non-Authentic"
        verdict_id     = "fake"
        verdict_detail = (
            f"Mayoritas atribut tidak memenuhi standar produk original {brand_name}. "
            f"Hardware ringan tanpa branding, material sintetis, dan absennya dokumen "
            f"adalah indikator klasik produk tiruan."
        )
        badge_class    = "fake"
        invest_key     = "fake"

    # ── STEP 4: Ambil rekomendasi investasi dari knowledge ──
    invest_recs = INVESTMENT_KNOWLEDGE.get(brand, INVESTMENT_KNOWLEDGE["other"])
    invests     = invest_recs.get(invest_key, [])

    # ── STEP 5: Bangun breakdown atribut per dimensi ────────
    attr_breakdown = {
        "Kualitas Jahitan": _classify_attr("jahitan", facts.get("jahitan")),
        "Hardware":         _classify_attr("hw",      facts.get("hw")),
        "Dokumentasi":      _classify_attr("dok",     facts.get("dok")),
        "Material":         _classify_attr("aroma",   facts.get("aroma")),
    }

    return {
        # Input facts
        "facts":          facts,
        "brand_name":     brand_name,
        # Inference result
        "score":          score,
        "verdict":        verdict,
        "verdict_id":     verdict_id,
        "verdict_detail": verdict_detail,
        "badge_class":    badge_class,
        # Detail breakdown
        "attr_breakdown": attr_breakdown,
        "fired_rules":    wm.fired_rules,
        "conclusions":    wm.conclusions,
        # Investment
        "invests":        invests,
        # Trace (untuk debugging / transparansi)
        "trace":          engine.trace,
    }


def _classify_attr(attr: str, value: Optional[str]) -> dict:
    """Klasifikasikan nilai atribut ke label dan kelas CSS."""
    mapping = {
        "jahitan": {
            "sempurna": ("Excellent", "good"),
            "minor":    ("Acceptable", "warn"),
            "buruk":    ("Poor", "bad"),
        },
        "hw": {
            "solid":   ("Authentic Grade", "good"),
            "medium":  ("Uncertain", "warn"),
            "ringan":  ("Non-authentic", "bad"),
        },
        "dok": {
            "lengkap": ("Complete", "good"),
            "partial": ("Partial", "warn"),
            "tidak":   ("Missing", "bad"),
        },
        "aroma": {
            "genuine":   ("Genuine Leather", "good"),
            "chemical":  ("Uncertain", "warn"),
            "plastik":   ("Synthetic", "bad"),
        },
    }
    result = mapping.get(attr, {}).get(value, ("Unknown", "warn"))
    return {"label": result[0], "cls": result[1]}
