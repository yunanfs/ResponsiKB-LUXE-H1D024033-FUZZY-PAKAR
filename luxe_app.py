import os
import sys
import json
from datetime import datetime

try:
    from fuzzy_engine import run_fuzzy
    from expert_engine import run_expert_system
except ImportError as e:
    print(f"[ERROR] Gagal import engine: {e}")
    sys.exit(1)

try:
    import webview
except ModuleNotFoundError:
    print("[ERROR] Module 'webview' tidak ditemukan.")
    print("Jalankan: python -m pip install pywebview")
    sys.exit(1)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "luxury-systems.html")


class LuxeAPI:
    def calculate_fuzzy(self, suhu, humid, jenis, durasi):
        print(f"[FUZZY] suhu={suhu}, humid={humid}, jenis={jenis}, durasi={durasi}")
        result = run_fuzzy(float(suhu), float(humid), str(jenis), str(durasi))
        print(f"[FUZZY] Score: {result['final_score']} | {result['kondisi']}")
        print(f"[FUZZY] Rules: {result['fired_rules']}")
        return result

    def run_diagnosis(self, brand, jahitan, hw, dok, aroma):
        facts = {"brand": brand, "jahitan": jahitan, "hw": hw, "dok": dok, "aroma": aroma}
        print(f"\n[PAKAR] Facts: {facts}")
        result = run_expert_system(facts)
        for line in result["trace"]:
            print(f"        {line}")
        print(f"[PAKAR] Score={result['score']} | Verdict={result['verdict']}\n")
        return result

    def save_diagnosis_result(self, result):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fn = os.path.join(BASE_DIR, f"hasil_diagnosa_{ts}.txt")
            with open(fn, "w", encoding="utf-8") as f:
                f.write("=" * 55 + "\n")
                f.write("    LUXE — Hasil Diagnosa Keaslian Tas Mewah\n")
                f.write("=" * 55 + "\n\n")
                f.write(f"Tanggal : {datetime.now().strftime('%d %B %Y, %H:%M')}\n")
                f.write(f"Merek   : {result.get('brand_name','-')}\n")
                f.write(f"Skor    : {result.get('score',0)}/100\n")
                f.write(f"Verdict : {result.get('verdict','-')}\n\n")
                f.write("── Atribut Fisik ──\n")
                for attr, info in result.get("attr_breakdown", {}).items():
                    f.write(f"  {attr:<22}: {info['label']}\n")
                f.write("\n── Rule Aktif ──\n")
                for r in result.get("fired_rules", []):
                    f.write(f"  [{r}]\n")
                f.write("\n── Rekomendasi ──\n")
                for i, rec in enumerate(result.get("invests", []), 1):
                    f.write(f"  {i}. {rec}\n")
                f.write("\n" + "=" * 55 + "\n")
            print(f"[LUXE] Saved: {fn}")
            return {"success": True, "filename": os.path.basename(fn)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_app_info(self):
        return {"name": "LUXE", "version": "2.0.0",
                "engine": "Python Mamdani Fuzzy + Forward Chaining"}

    def log(self, message):
        print(f"[JS] {message}")


BRIDGE_JS = """
<script>
// Python Bridge — override JS functions to call Python engine
const _origFuzzy = window.updateFuzzy;
window.updateFuzzy = async function() {
    const s = +document.getElementById('suhu-range').value;
    const h = +document.getElementById('humid-range').value;
    const jenis  = document.getElementById('jenis-jam').value;
    const durasi = document.getElementById('durasi').value;
    document.getElementById('suhu-display').textContent = s + '°C';
    document.getElementById('humid-display').textContent = h + '%';
    document.getElementById('suhu-fill').style.width = (s/50*100)+'%';
    document.getElementById('humid-fill').style.width = h+'%';
    try {
        const r = await window.pywebview.api.calculate_fuzzy(s, h, jenis, durasi);
        document.getElementById('mu-suhu').style.width = (r.mu_suhu.normal*100)+'%';
        document.getElementById('mu-suhu-txt').textContent = r.mu_suhu.normal.toFixed(2);
        document.getElementById('mu-humid').style.width = (r.mu_humid.optimal*100)+'%';
        document.getElementById('mu-humid-txt').textContent = r.mu_humid.optimal.toFixed(2);
        document.getElementById('result-score').textContent = r.final_score;
        const panel = document.getElementById('result-panel');
        const st = document.getElementById('result-status');
        panel.className = 'result-panel'; st.className = 'result-status';
        const map = {
            'Ideal':           ['ideal','status-ideal','Kondisi Ideal','Penyimpanan Optimal'],
            'Perlu Perhatian': ['warning','status-ok','Perlu Perhatian','Kondisi Suboptimal'],
            'Berbahaya':       ['danger','status-bad','Kondisi Berbahaya','Risiko Kerusakan Tinggi'],
        };
        const m = map[r.kondisi] || map['Berbahaya'];
        panel.classList.add(m[0]); st.classList.add(m[1]);
        st.textContent = m[2];
        document.getElementById('result-title').textContent = m[3];
        document.getElementById('result-recs').innerHTML =
            r.rekomendasi.map(x => `<li><div class="rec-bullet"></div>${x}</li>`).join('');
    } catch(e) { if(_origFuzzy) _origFuzzy(); }
};

const _origDiag = window.runDiagnosis;
window.runDiagnosis = async function() {
    const qs = ['brand','jahitan','hw','dok','aroma'];
    for(const q of qs) {
        if(!expertAnswers[q]) {
            document.querySelectorAll(`[data-q="${q}"]`).forEach(o => {
                o.style.borderColor='rgba(226,75,74,0.5)';
                setTimeout(()=>o.style.borderColor='',1500);
            });
            return;
        }
    }
    try {
        const r = await window.pywebview.api.run_diagnosis(
            expertAnswers.brand, expertAnswers.jahitan,
            expertAnswers.hw, expertAnswers.dok, expertAnswers.aroma
        );
        document.getElementById('modal-score').textContent = r.score;
        const badge = document.getElementById('modal-badge');
        badge.textContent = r.verdict; badge.className = 'modal-badge badge-'+r.badge_class;
        document.getElementById('modal-verdict-grid').innerHTML =
            Object.entries(r.attr_breakdown).map(([k,v])=>
                `<div class="modal-verdict-row"><span class="modal-vkey">${k}</span><span class="modal-vval ${v.cls}">${v.label}</span></div>`
            ).join('');
        document.getElementById('modal-vtitle').textContent = r.verdict;
        document.getElementById('modal-vdetail').textContent = r.verdict_detail;
        document.getElementById('modal-invest').innerHTML =
            r.invests.map(i=>`<div class="modal-invest-item"><div class="modal-invest-dot"></div><p class="modal-invest-txt">${i}</p></div>`).join('');
        const overlay = document.getElementById('result-modal');
        const bar = document.getElementById('modal-bar');
        bar.style.width='0'; overlay.classList.add('open');
        document.body.style.overflow='hidden';
        setTimeout(()=>{ bar.style.width=r.score+'%'; },300);
        window.pywebview.api.save_diagnosis_result(r);
    } catch(e) { if(_origDiag) _origDiag(); }
};

window.addEventListener('pywebviewready', function() {
    console.log('[LUXE] Python bridge ready!');
    window.updateFuzzy();
});
</script>
"""


def main():
    if not os.path.exists(HTML_FILE):
        print(f"[ERROR] File tidak ditemukan: {HTML_FILE}")
        sys.exit(1)

    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    patched = html.replace("</body>", BRIDGE_JS + "\n</body>")
    tmp = os.path.join(BASE_DIR, "_luxe_runtime.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(patched)

    print("=" * 55)
    print("   LUXE — Intelligent Luxury Systems v2.0")
    print("=" * 55)

    tf = run_fuzzy(22, 47, "mechanical", "short")
    print(f"[TEST] Fuzzy OK → {tf['final_score']} ({tf['kondisi']})")

    tp = run_expert_system({"brand":"hermes","jahitan":"sempurna","hw":"solid","dok":"lengkap","aroma":"genuine"})
    print(f"[TEST] Expert OK → {tp['score']} ({tp['verdict']}) | Rules: {tp['fired_rules']}")
    print(f"\n[LUXE] Membuka: {HTML_FILE}\n")

    api = LuxeAPI()
    window = webview.create_window(
        title            = "LUXE — Intelligent Luxury Systems",
        url              = f"file:///{tmp.replace(os.sep, '/')}",
        js_api           = api,
        width            = 1280,
        height           = 820,
        min_size         = (900, 600),
        background_color = "#080808",
        text_select      = False,
    )

    def on_loaded():
        print("[LUXE] UI loaded. Python engine aktif.")

    window.events.loaded += on_loaded
    webview.start(debug=False)

    if os.path.exists(tmp):
        os.remove(tmp)


if __name__ == "__main__":
    main()
