# catvideo — video kucing quote @mulaimandiri_

Folder ini berdiri sendiri dan tidak menyentuh file alur harian (render.py, music.py, fonts/ di root repo).

- content.json  : 30 konten (teks, caption, hashtag, adegan, musik)
- build_video.py: perakit video. Contoh dari root repo:
    python catvideo/build_video.py --dry
    python catvideo/build_video.py --day 5 --out catvideo/out
- scenes.py / music.py / fonts/ : khusus video kucing (musik orisinal hasil sintesis kode)
- RENCANA_30_HARI.md : ringkasan 30 hari

Workflow: .github/workflows/cat-quote-video.yml (variabel repo: CAT_START_DATE, CAT_WEEKDAYS).

Sambungan Buffer: post_cat.py memakai fungsi dari publish_buffer.py di root repo (tanpa mengubahnya) dan
menjadwalkan video kucing ke jam tetap (default 17:00 WIB, variabel repo CAT_POST_TIME) dengan mode Buffer
customScheduled. Slot antrean 19:00 milik alur harian tidak dipakai/diubah.
Penjaga: satu video kucing per hari (catvideo/posted_log.txt).
