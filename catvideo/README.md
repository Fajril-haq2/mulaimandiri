# catvideo — video kucing quote @mulaimandiri_

Folder ini berdiri sendiri dan tidak menyentuh file alur harian (render.py, music.py, fonts/ di root repo).

- content.json  : 30 konten (teks, caption, hashtag, adegan, musik)
- build_video.py: perakit video. Contoh dari root repo:
    python catvideo/build_video.py --dry
    python catvideo/build_video.py --day 5 --out catvideo/out
- scenes.py / music.py / fonts/ : khusus video kucing (musik orisinal hasil sintesis kode)
- RENCANA_30_HARI.md : ringkasan 30 hari

Workflow: .github/workflows/cat-quote-video.yml (variabel repo: CAT_START_DATE, CAT_WEEKDAYS).
