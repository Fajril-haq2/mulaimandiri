"""Render carousel @mulaimandiri_ dari content.csv -> PNG (1080x1920) + MP4 slideshow.
Pakai:  python render.py            (semua post)
        python render.py P01        (satu post)
        python render.py --no-video (PNG saja)
"""
import csv, os, sys, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BG, INK, MUTED, TEAL, SKY, LINE = "#F7F8FA", "#202127", "#4A4F57", "#2A9DB5", "#5BBFDD", "#B5B8B2"
HANDLE, TAG = "@mulaimandiri_", "#wargamandiri"
SECONDS_PER_SLIDE = 3.5
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

def poppins(size): return ImageFont.truetype(f"{FD}/Poppins-Bold.ttf", size)
def poppins_it(size): return ImageFont.truetype(f"{FD}/Poppins-Italic.ttf", size)
def poppins_reg(size): return ImageFont.truetype(f"{FD}/Poppins-Regular.ttf", size)
def inter(size):
    f = ImageFont.truetype(f"{FD}/Inter.ttf", size)
    try: f.set_variation_by_axes([14, 450])
    except Exception: pass
    return f

def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def fit_wrap(d, text, maker, start, minimum, maxw, maxlines):
    size = start
    while size >= minimum:
        f = maker(size); ls = wrap(d, text, f, maxw)
        if len(ls) <= maxlines: return f, ls, size
        size -= 4
    f = maker(minimum); return f, wrap(d, text, f, maxw), minimum

def frame():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((90, 130), HANDLE, font=poppins_reg(34), fill=TEAL)
    tw = d.textlength(TAG, font=poppins_reg(34))
    d.text((W - 90 - tw - 120, 130), TAG, font=poppins_reg(34), fill=TEAL)  # geser kiri dari zona tombol TikTok
    return im, d

LEFT, MAXW = 90, 780   # sisakan margin kanan untuk tombol like/komen TikTok

def cover(r):
    im, d = frame()
    y = 620
    d.text((LEFT, y), r["kicker"], font=poppins_reg(40), fill=MUTED); y += 90
    f, lines, size = fit_wrap(d, r["judul"], poppins, 84, 56, MAXW, 7)
    lh = int(size * 1.28)
    first = lines[0].split(" ")[0]
    fw = d.textlength(first, font=f)
    d.rounded_rectangle((LEFT - 14, y + 6, LEFT + fw + 18, y + lh - 2), radius=14, fill=SKY)
    for ln in lines:
        d.text((LEFT, y), ln, font=f, fill=INK); y += lh
    d.text((LEFT, y + 70), "Coba geser, warga mandiri...", font=poppins_it(38), fill=INK)
    return im

def content(r, n):
    im, d = frame()
    head, body = r[f"s{n}_judul"], r[f"s{n}_isi"]
    hf, hl, hs = fit_wrap(d, head.upper(), poppins, 76, 52, MAXW, 4)
    bf, bl, bs = fit_wrap(d, body, inter, 46, 36, MAXW, 9)
    hlh, blh = int(hs * 1.22), int(bs * 1.55)
    total = len(hl) * hlh + 70 + len(bl) * blh
    y = max(380, (H - total) // 2 - 80)
    for ln in hl: d.text((LEFT, y), ln, font=hf, fill=INK); y += hlh
    y += 30; d.line((LEFT, y, LEFT + MAXW, y), fill=LINE, width=4); y += 40
    for ln in bl: d.text((LEFT, y), ln, font=bf, fill=MUTED); y += blh
    return im

def cta(r):
    im, d = frame()
    hf, hl, hs = fit_wrap(d, r["cta_judul"].upper(), poppins, 76, 52, MAXW, 5)
    bf, bl, bs = fit_wrap(d, r["cta_isi"], inter, 46, 36, MAXW, 7)
    hlh, blh = int(hs * 1.22), int(bs * 1.55)
    total = len(hl) * hlh + 70 + len(bl) * blh
    y = max(380, (H - total) // 2 - 80)
    for ln in hl: d.text((LEFT, y), ln, font=hf, fill=TEAL); y += hlh
    y += 30; d.line((LEFT, y, LEFT + MAXW, y), fill=LINE, width=4); y += 40
    for ln in bl: d.text((LEFT, y), ln, font=bf, fill=MUTED); y += blh
    return im

def render_post(r, out, video=True):
    folder = os.path.join(out, r["id"]); os.makedirs(folder, exist_ok=True)
    imgs = [cover(r), content(r, 2), content(r, 3), content(r, 4), cta(r)]
    paths = []
    for i, im in enumerate(imgs, 1):
        p = os.path.join(folder, f"{r['id']}_slide{i}.png"); im.save(p, optimize=True); paths.append(p)
    with open(os.path.join(folder, f"{r['id']}_caption.txt"), "w", encoding="utf-8") as f:
        f.write(r["caption_lengkap"])
    if video and shutil.which("ffmpeg"):
        mp4 = os.path.join(out, f"{r['id']}.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", f"1/{SECONDS_PER_SLIDE}",
               "-i", os.path.join(folder, f"{r['id']}_slide%d.png"),
               "-vf", f"fps=30,format=yuv420p", "-c:v", "libx264", "-movflags", "+faststart", mp4]
        subprocess.run(cmd, check=True)
    print("OK", r["id"])

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    video = "--no-video" not in sys.argv
    base = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base, "output"); os.makedirs(out, exist_ok=True)
    with open(os.path.join(base, "content.csv"), encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if not args or r["id"] in args: render_post(r, out, video)
