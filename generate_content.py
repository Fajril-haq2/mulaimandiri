"""Jaga stok konten: kalau post berstatus pending < MIN_PENDING (default 3), buat 7 post baru via Gemini (gratis) dan TAMBAHKAN ke content.csv
Butuh env: GEMINI_API_KEY   (opsional: GEMINI_MODEL)
"""
import os, re, csv, json, glob, sys, time, datetime, urllib.request, urllib.error

KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
BASE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["id","hari","jam","tema","kicker","judul","s2_judul","s2_isi","s3_judul","s3_isi",
          "s4_judul","s4_isi","cta_judul","cta_isi","caption","hashtag","caption_lengkap","status","queued_date"]
TEMA = ["Keuangan","Humor","Tips Harian","Mindset","Lifestyle","Rumah Tangga","Parenting"]

def old_titles():
    t = set()
    for p in glob.glob(os.path.join(BASE, "archive", "*.csv")) + [os.path.join(BASE, "content.csv")]:
        if os.path.exists(p):
            with open(p, encoding="utf-8-sig") as f:
                t.update(r["judul"] for r in csv.DictReader(f))
    return sorted(t)

PROMPT = """Kamu penulis konten TikTok carousel untuk akun @mulaimandiri_.
Positioning: "Belajar berdikari tanpa bikin drama sosial. Edukasi harian buat Gen Z & Milenial (termasuk bapak muda)."
Tone: santai, receh, hangat, jujur, sedikit nyinyir ke diri sendiri (BUKAN ke orang lain). Pakai kata "warga", "kita", "masih belajar", "pelan-pelan", "tanpa drama". Selalu pakai "kamu", jangan "lu"/"gue".
Prinsip: edukasi dulu, hiburan menyusul. Tidak memancing drama. Selalu ada solusi/langkah kecil. Sudut pandang "kita masih belajar bareng".
Jangan beri janji hasil keuangan/medis, jangan sebut angka statistik yang tidak pasti, jangan ada saran medis spesifik.

Buat TEPAT 7 post untuk 7 hari: tiap hari 1 post, jam selalu "19:00". Selang-seling: edukasi/tips, humor, mindset, relasi.
Pakai tema berbeda tiap hari dari 6 tema: humor keresahan Gen Z/Milenial, mindset (overthinking, banding-bandingkan), rumah tangga & parenting bapak muda, lifestyle praktis, keuangan sederhana, tips harian. Variasikan, jangan semua anak kos.
JANGAN ulangi judul berikut: {old}

Format: JSON array berisi 7 objek dengan kunci persis:
hari (1-7), jam ("19:00"), tema, kicker (maks 35 karakter), judul (maks 80 karakter, jadi judul cover),
s2_judul, s3_judul, s4_judul (maks 38 karakter, huruf kapital boleh),
s2_isi, s3_isi, s4_isi (maks 190 karakter, 1-2 kalimat, konkret),
cta_judul (maks 45 karakter, berupa pertanyaan), cta_isi (maks 150 karakter, ajak komentar + save),
caption (maks 200 karakter), hashtag (4 hashtag, selalu mulai dengan #wargamandiri #mulaimandiri).
Keluarkan HANYA JSON."""

LIMITS = {"kicker":35,"judul":80,"s2_judul":38,"s3_judul":38,"s4_judul":38,"s2_isi":190,"s3_isi":190,
          "s4_isi":190,"cta_judul":45,"cta_isi":150,"caption":200}

def call():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    body = {"contents":[{"parts":[{"text": PROMPT.format(old="; ".join(old_titles()) or "-")}]}],
            "generationConfig":{"responseMimeType":"application/json","temperature":0.9}}
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    return data["candidates"][0]["content"]["parts"][0]["text"]

def validate(items):
    if not isinstance(items, list) or len(items) != 7: raise ValueError(f"harus 7 post, dapat {len(items) if isinstance(items,list) else '?'}")
    for i, it in enumerate(items, 1):
        for k, mx in LIMITS.items():
            if k not in it or not str(it[k]).strip(): raise ValueError(f"post {i}: kolom {k} kosong")
            if len(str(it[k])) > mx + 15: raise ValueError(f"post {i}: {k} terlalu panjang ({len(it[k])}>{mx})")
        if re.search(r"\b(lu|gue|gw)\b", " ".join(str(v).lower() for v in it.values())): raise ValueError(f"post {i}: ada kata lu/gue")

def load():
    cur = os.path.join(BASE, "content.csv")
    if not os.path.exists(cur): return []
    with open(cur, encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def write(items):
    existing = load()
    nums = [int(r["id"][1:]) for r in existing if r["id"][1:].isdigit()]
    n = max(nums, default=0)
    rows = existing[:]
    for it in items:
        n += 1
        r = {k: str(it.get(k, "")).strip() for k in FIELDS}
        r["id"] = f"P{n:03d}"; r["status"] = "pending"; r["queued_date"] = ""
        if not r["hashtag"].startswith("#"): r["hashtag"] = "#wargamandiri #mulaimandiri"
        r["caption_lengkap"] = f'{r["caption"]}\n\n{r["hashtag"]}'
        rows.append(r)
    with open(os.path.join(BASE, "content.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    pending = [r for r in load() if r.get("status", "pending") == "pending"]
    need = int(os.environ.get("MIN_PENDING", "3"))
    if len(pending) >= need and "--force" not in sys.argv:
        print(f"Stok cukup ({len(pending)} pending), tidak membuat konten baru"); sys.exit(0)
    if not KEY: sys.exit("GEMINI_API_KEY belum diset")
    last = None
    for attempt in range(1, 4):
        try:
            items = json.loads(call()); validate(items); write(items); print("OK 7 post dibuat"); break
        except (ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError) as e:
            last = e; print(f"percobaan {attempt} gagal: {e}"); time.sleep(5)
    else:
        sys.exit(f"Gagal setelah 3 percobaan: {last}")
