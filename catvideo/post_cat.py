#!/usr/bin/env python3
"""Kirim 1 video kucing ke antrean Buffer (TikTok) dengan MEMAKAI fungsi dari publish_buffer.py
(tanpa mengubah file itu). Penjaga: tidak mengirim kalau hari ini (WIB) sudah ada post
dari alur lama (content.csv: queued_date) atau dari video kucing (catvideo/posted_log.txt).

Env wajib : BUFFER_API_KEY, MEDIA_BASE_URL (sama seperti alur lama)
Env opsi  : BUFFER_CHANNEL_ID (kosong = cari channel TikTok pertama)
Contoh    : python catvideo/post_cat.py --name cat_day05 --caption-file catvideo/out/day05.txt
Opsi      : --dry-run (tidak mengirim)  --force (abaikan penjaga harian)
"""
import argparse, datetime, os, sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import publish_buffer as pb  # alur lama, dipakai apa adanya

LOG = os.path.join(HERE, "posted_log.txt")


def today():
    return datetime.datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()


def sudah_kirim_hari_ini(t):
    try:
        rows, _ = pb.load()
        if any(r.get("queued_date") == t for r in rows):
            return "alur harian lama (content.csv)"
    except FileNotFoundError:
        pass
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            if any(line.startswith(t) for line in f):
                return "video kucing (posted_log.txt)"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="nama file mp4 tanpa .mp4 di folder media publik")
    ap.add_argument("--caption-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    t = today()
    why = None if a.force else sudah_kirim_hari_ini(t)
    if why:
        print(f"Sudah ada post hari ini dari {why}. Dilewati.")
        return 0
    if not pb.BASE:
        sys.exit("MEDIA_BASE_URL belum diset")
    vurl = f"{pb.BASE}/{a.name}.mp4"
    text = open(a.caption_file, encoding="utf-8").read().strip()
    if a.dry_run:
        print("DRY", a.name, vurl, "|", text[:60].replace("\n", " "))
        return 0
    if not pb.KEY:
        sys.exit("BUFFER_API_KEY belum diset")
    cid = os.environ.get("BUFFER_CHANNEL_ID")
    if not cid:
        tt = [c for c in pb.channels() if "tiktok" in str(c["service"]).lower()]
        if not tt:
            sys.exit("Channel TikTok tidak ditemukan di Buffer. Hubungkan dulu di buffer.com")
        cid = tt[0]["id"]
        print("Channel TikTok:", tt[0]["displayName"] or tt[0]["name"])
    if not pb.url_ok(vurl):
        sys.exit(f"GAGAL: video tidak bisa dibuka publik: {vurl}")
    res = pb.create(cid, text, vurl)
    if "message" in res:
        sys.exit(f'GAGAL {a.name}: {res["message"]}')
    print("OK antrean", a.name, res["post"]["id"])
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{t} {a.name} {res['post']['id']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
