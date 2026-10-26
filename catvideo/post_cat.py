#!/usr/bin/env python3
"""Jadwalkan 1 video kucing ke Buffer (TikTok) pada JAM TETAP (default 17:00 WIB) di hari yang sama.

Memakai mode Buffer 'customScheduled' + dueAt, jadi TIDAK memakai slot antrean 19:00 milik alur harian
dan tidak mengubah publish_buffer.py. Hanya fungsi gql/channels/url_ok dari publish_buffer.py yang dipakai.

Env wajib : BUFFER_API_KEY, MEDIA_BASE_URL (sama seperti alur lama)
Env opsi  : BUFFER_CHANNEL_ID (kosong = cari channel TikTok pertama)
            CAT_POST_TIME     (jam tayang WIB, default 17:00)
Contoh    : python catvideo/post_cat.py --name cat_day05 --caption-file catvideo/out/day05.txt
Opsi      : --dry-run (tidak mengirim)  --force (abaikan penjaga ganda video kucing)
Penjaga   : tidak mengirim dua kali dalam sehari (catvideo/posted_log.txt).
"""
import argparse, datetime, json, os, sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import publish_buffer as pb  # alur lama, dipakai apa adanya

LOG = os.path.join(HERE, "posted_log.txt")
WIB = ZoneInfo("Asia/Jakarta")


def due_utc(hhmm):
    """Jam hhmm WIB hari ini -> ISO UTC. Kalau sudah lewat (workflow telat), geser ke sekarang+20 menit."""
    now = datetime.datetime.now(WIB)
    h, m = (int(x) for x in hhmm.split(":"))
    due = now.replace(hour=h, minute=m, second=0, microsecond=0)
    late = due - now < datetime.timedelta(minutes=10)
    if late:
        due = now + datetime.timedelta(minutes=20)
    iso = due.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return iso, late


def create_scheduled(channel_id, text, video_url, due_iso):
    q = '''mutation { createPost(input: {
      text: %s
      channelId: %s
      schedulingType: automatic
      mode: customScheduled
      dueAt: %s
      assets: [{ video: { url: %s metadata: { thumbnailOffset: 500 } } }]
    }) {
      ... on PostActionSuccess { post { id dueAt } }
      ... on MutationError { message }
    } }''' % (json.dumps(text, ensure_ascii=False), json.dumps(channel_id),
              json.dumps(due_iso), json.dumps(video_url))
    return pb.gql(q)["createPost"]


def sudah_kirim_hari_ini(t):
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            return any(line.startswith(t) for line in f)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="nama file mp4 tanpa .mp4 di folder media publik")
    ap.add_argument("--caption-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    t = datetime.datetime.now(WIB).date().isoformat()
    if not a.force and sudah_kirim_hari_ini(t):
        print("Video kucing hari ini sudah dijadwalkan (posted_log.txt). Dilewati.")
        return 0
    if not pb.BASE:
        sys.exit("MEDIA_BASE_URL belum diset")
    vurl = f"{pb.BASE}/{a.name}.mp4"
    text = open(a.caption_file, encoding="utf-8").read().strip()
    due, late = due_utc(os.environ.get("CAT_POST_TIME", "17:00"))
    if a.dry_run:
        print("DRY", a.name, vurl, "| tayang (UTC):", due, "| telat:", late, "|", text[:50].replace("\n", " "))
        return 0
    if not pb.KEY:
        sys.exit("BUFFER_API_KEY belum diset")
    if late:
        print("PERINGATAN: jam tayang hari ini sudah lewat/terlalu dekat, dijadwalkan ulang ke", due)
    cid = os.environ.get("BUFFER_CHANNEL_ID")
    if not cid:
        tt = [c for c in pb.channels() if "tiktok" in str(c["service"]).lower()]
        if not tt:
            sys.exit("Channel TikTok tidak ditemukan di Buffer. Hubungkan dulu di buffer.com")
        cid = tt[0]["id"]
        print("Channel TikTok:", tt[0]["displayName"] or tt[0]["name"])
    if not pb.url_ok(vurl):
        sys.exit(f"GAGAL: video tidak bisa dibuka publik: {vurl}")
    res = create_scheduled(cid, text, vurl, due)
    if "message" in res:
        sys.exit(f'GAGAL {a.name}: {res["message"]}')
    print("OK terjadwal", a.name, res["post"]["id"], "dueAt", res["post"].get("dueAt"))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{t} {a.name} {res['post']['id']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
