MULAIMANDIRI_ - Otomatisasi harian ke Buffer (1 post/hari)
content.csv         : bank konten (kolom status: pending / queued)
generate_content.py : tambah 7 post via Gemini kalau stok pending < 3
render.py           : CSV -> slide PNG + MP4 (python render.py P001)
publish_buffer.py   : kirim 1 video pending ke antrean Buffer, lalu tandai queued
.github/workflows/daily.yml : jalan tiap hari 08.00 WIB
Tes: python publish_buffer.py --list | --next | --dry-run | --only P001
