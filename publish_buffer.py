"""Kirim SATU video harian dari content.csv ke antrean Buffer (TikTok) lewat Buffer GraphQL API.
Env wajib : BUFFER_API_KEY, MEDIA_BASE_URL (URL publik folder berisi ID.mp4, tanpa garis miring akhir)
Env opsi  : BUFFER_CHANNEL_ID (kalau kosong, dicari otomatis channel TikTok pertama)
Opsi      : --next (cetak ID post berikutnya)  --dry-run  --only P001 (tes, status tak diubah)
            --force (abaikan penjaga 'sudah kirim hari ini')  --list (tampilkan channel)
"""
import os, sys, csv, json, time, datetime, urllib.request, urllib.error
from zoneinfo import ZoneInfo

API = "https://api.buffer.com"
KEY = os.environ.get("BUFFER_API_KEY")
BASE = os.environ.get("MEDIA_BASE_URL", "").rstrip("/")
HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "content.csv")

def gql(query):
    req = urllib.request.Request(API, json.dumps({"query": query}, ensure_ascii=False).encode(),
        {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} dari Buffer: {e.read().decode()[:400]}")
    if data.get("errors"): sys.exit(f"GraphQL error: {json.dumps(data['errors'], ensure_ascii=False)[:600]}")
    return data["data"]

def channels():
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    out = []
    for o in orgs:
        for c in gql('query { channels(input: {organizationId: %s}) { id name displayName service isQueuePaused } }' % json.dumps(o["id"]))["channels"]:
            c["org"] = o["name"]; out.append(c)
    return out

def url_ok(url, tries=12, wait=30):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Range": "bytes=0-1023", "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status in (200, 206): return True
        except Exception: pass
        print(f"  menunggu URL aktif ({i+1}/{tries}) {url}"); time.sleep(wait)
    return False

def create(channel_id, text, video_url):
    q = '''mutation { createPost(input: {
      text: %s
      channelId: %s
      schedulingType: automatic
      mode: addToQueue
      assets: [{ video: { url: %s metadata: { thumbnailOffset: 500 } } }]
    }) {
      ... on PostActionSuccess { post { id } }
      ... on MutationError { message }
    } }''' % (json.dumps(text, ensure_ascii=False), json.dumps(channel_id), json.dumps(video_url))
    return gql(q)["createPost"]

def load():
    with open(CSV, encoding="utf-8-sig") as f:
        r = csv.DictReader(f); return list(r), r.fieldnames

def save(rows, fields):
    with open(CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    rows, fields = load()
    today = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()
    only = sys.argv[sys.argv.index("--only")+1] if "--only" in sys.argv else None
    dry, force = "--dry-run" in sys.argv, "--force" in sys.argv
    pick = next((r for r in rows if (r["id"] == only if only else r.get("status", "pending") == "pending")), None)
    if "--next" in sys.argv:
        print(pick["id"] if pick else ""); sys.exit(0 if pick else 1)
    if not KEY and not dry: sys.exit("BUFFER_API_KEY belum diset")
    if "--list" in sys.argv:
        for c in channels(): print(c)
        sys.exit()
    if not pick: sys.exit("Tidak ada post pending. Jalankan generate_content.py --force")
    if not only and not force and any(r.get("queued_date") == today for r in rows):
        print("Sudah ada post dikirim hari ini, dilewati."); sys.exit(0)
    if not BASE: sys.exit("MEDIA_BASE_URL belum diset")
    vurl = f'{BASE}/{pick["id"]}.mp4'; text = pick["caption_lengkap"]
    if dry: print("DRY", pick["id"], vurl, "|", text[:60].replace("\n", " ")); sys.exit(0)
    cid = os.environ.get("BUFFER_CHANNEL_ID")
    if not cid:
        tt = [c for c in channels() if "tiktok" in str(c["service"]).lower()]
        if not tt: sys.exit("Channel TikTok tidak ditemukan di Buffer. Hubungkan dulu di buffer.com")
        cid = tt[0]["id"]; print("Channel TikTok:", tt[0]["displayName"] or tt[0]["name"])
    if not url_ok(vurl): sys.exit(f"GAGAL: video tidak bisa dibuka publik: {vurl}")
    res = create(cid, text, vurl)
    if "message" in res: sys.exit(f'GAGAL {pick["id"]}: {res["message"]}')
    print("OK antrean", pick["id"], res["post"]["id"])
    if not only:
        pick["status"], pick["queued_date"] = "queued", today
        save(rows, fields)
