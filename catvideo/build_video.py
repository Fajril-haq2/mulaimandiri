#!/usr/bin/env python3
"""Render 1 video quote kucing (9:16, musik + watermark) dari content.json.

Contoh:
  python build_video.py --day 5
  python build_video.py --date 2026-10-26 --start 2026-10-26     # hari ke-1 jatuh di tanggal --start
  python build_video.py --all --out out
  python build_video.py --dry                                    # hanya cek durasi 30 konten
"""
import argparse, datetime as dt, json, os, subprocess, sys, tempfile
import numpy as np, cairo
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenes
from scenes import BG, INK, BLUE
from music import make_music, write_wav

W, H, FPS = 720, 1280, 30
HANDLE, TAG = "@mulaimandiri_", "#wargamandiri"
FONT_B = os.path.join(HERE, "fonts", "Poppins-Bold.ttf")
FONT_M = os.path.join(HERE, "fonts", "Poppins-Medium.ttf")
TEXT_Y0, TEXT_Y1 = 190, 535          # area teks (ruang 720x1280)
SCENE_SCALE, SCENE_GROUND = 0.85, 1020
INTRO, OUTRO = 0.6, 2.2


# ------------------------------------------------------------------ timing
def page_secs(text, last=False):
    n = len(text.split())
    return max(3.0, 1.4 + 0.38 * n) + (1.2 if last else 0.0)


def plan(item):
    pages = [(t, "hook" if i == 0 else "body") for i, t in enumerate(item["pages"])]
    pages.append((item["langkah"], "langkah"))
    t, out = INTRO, []
    for i, (txt, kind) in enumerate(pages):
        d = page_secs(txt, kind == "langkah")
        out.append(dict(text=txt, kind=kind, t0=t, t1=t + d))
        t += d
    total = t + OUTRO
    return out, total


# ------------------------------------------------------------------ teks
def _font(path, size):
    return ImageFont.truetype(path, size)


def _wrap(words, font, maxw, space):
    lines, cur, w = [], [], 0
    for wd in words:
        ww = font.getlength(wd)
        add = ww if not cur else ww + space
        if cur and w + add > maxw:
            lines.append(cur); cur, w = [wd], ww
        else:
            cur.append(wd); w += add
    if cur:
        lines.append(cur)
    return lines


def render_page(text, kind, k):
    """RGBA (PIL) setinggi area teks, dirender pada skala k."""
    aw, ah = int(W * k), int((TEXT_Y1 - TEXT_Y0) * k)
    maxw = int(610 * k)
    base = {"hook": (72, FONT_B), "body": (56, FONT_M), "langkah": (46, FONT_M)}[kind]
    size = base[0]
    while True:
        f = _font(base[1], int(size * k))
        space = f.getlength(" ")
        lines = _wrap(text.split(), f, maxw if kind != "langkah" else int(540 * k), space)
        lh = int(size * 1.28 * k)
        label_h = int(70 * k) if kind == "langkah" else 0
        pad = int(34 * k) if kind == "langkah" else 0
        total = lh * len(lines) + label_h + pad * 2
        if total <= ah - 8 or size <= 30:
            break
        size -= 2
    img = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = (ah - total) // 2
    if kind == "langkah":
        bw = int(590 * k)
        bx = (aw - bw) // 2
        d.rounded_rectangle([bx, y + label_h // 2, bx + bw, y + total], radius=int(30 * k),
                            outline=BLUE_RGB, width=int(4 * k), fill=(255, 255, 255, 235))
        lf = _font(FONT_B, int(26 * k))
        lab = "LANGKAH KECIL"
        lw = lf.getlength(lab) + 44 * k
        d.rounded_rectangle([(aw - lw) / 2, y, (aw + lw) / 2, y + 48 * k], radius=int(24 * k), fill=BLUE_RGB)
        d.text((aw / 2, y + 24 * k), lab, font=lf, fill=(255, 255, 255), anchor="mm")
        y += label_h + pad - int(6 * k)
    for li, ln in enumerate(lines):
        lw = sum(f.getlength(w) for w in ln) + space * (len(ln) - 1)
        x = (aw - lw) / 2
        for wi, w in enumerate(ln):
            col = BLUE_RGB if (kind == "hook" and li == 0 and wi == 0) else INK_RGB
            d.text((x, y), w, font=f, fill=col)
            x += f.getlength(w) + space
        y += lh
    return img


BLUE_RGB = tuple(int(c * 255) for c in BLUE)
INK_RGB = tuple(int(c * 255) for c in INK)
BG_RGB = tuple(int(c * 255) for c in BG)


def to_bgr_alpha(img):
    a = np.asarray(img).astype(np.float32)
    return a[:, :, [2, 1, 0]], a[:, :, 3:4] / 255.0


def ease(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


# ------------------------------------------------------------------ render
def render(item, out_mp4, width=720, quiet=False):
    k = width / W
    w, h = int(W * k), int(H * k)
    pg, total = plan(item)
    n = int(round(total * FPS))
    assert 15 <= total <= 45, f"durasi {total:.1f}s di luar 15-45s"

    layers = []
    for p in pg:
        bgr, a = to_bgr_alpha(render_page(p["text"], p["kind"], k))
        layers.append((p, bgr, a))
    y0 = int(TEXT_Y0 * k)

    # watermark statis
    wm = Image.new("RGBA", (w, int(60 * k)), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    wd.text((44 * k, 30 * k), HANDLE, font=_font(FONT_B, int(30 * k)), fill=INK_RGB + (235,), anchor="lm")
    wd.text((w - 44 * k, 30 * k), TAG, font=_font(FONT_M, int(27 * k)), fill=(120, 120, 118, 235), anchor="rm")
    wm_bgr, wm_a = to_bgr_alpha(wm)
    wm_y = int(112 * k)

    # audio
    tmp = tempfile.mkdtemp()
    wav = os.path.join(tmp, "m.wav")
    write_wav(wav, make_music(item["mood"], total, seed=item["day"]))

    arr = np.zeros((h, w, 4), np.uint8)
    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2] = BG_RGB[2], BG_RGB[1], BG_RGB[0]
    bg = arr.copy()
    surf = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_RGB24, w, h)
    ctx = cairo.Context(surf)
    scene = scenes.SCENES[item["scene"]]

    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-i", wav,
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_mp4]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        np.copyto(arr, bg)
        ctx.save()
        ctx.scale(k, k)
        scenes._init(ctx)
        ctx.translate(W / 2, SCENE_GROUND)
        ctx.scale(SCENE_SCALE, SCENE_SCALE)
        ctx.translate(-W / 2, -scenes.GROUND)
        scene(ctx, t, total)
        ctx.restore()
        surf.flush()
        # teks
        for p, bgr, a in layers:
            if p["t0"] - 0.01 <= t <= (1e9 if p["kind"] == "langkah" else p["t1"] + 0.4):
                fi = ease((t - p["t0"] - 0.12) / 0.5)
                last = p["kind"] == "langkah"
                fo = 1.0 if last else 1 - ease((t - (p["t1"] - 0.3)) / 0.28)
                al = fi * fo
                if al <= 0.003:
                    continue
                off = int((1 - fi) * 26 * k)
                hh = bgr.shape[0]
                ys, ye = y0 + off, y0 + off + hh
                reg = arr[ys:ye, :, :3].astype(np.float32)
                arr[ys:ye, :, :3] = (reg * (1 - a * al) + bgr * a * al).astype(np.uint8)
        reg = arr[wm_y:wm_y + wm_bgr.shape[0], :, :3].astype(np.float32)
        arr[wm_y:wm_y + wm_bgr.shape[0], :, :3] = (reg * (1 - wm_a) + wm_bgr * wm_a).astype(np.uint8)
        pr.stdin.write(memoryview(arr))
    pr.stdin.close()
    pr.wait()
    if not quiet:
        print(f"OK {out_mp4}  {total:.1f}s  scene={item['scene']} mood={item['mood']}")
    return total


def caption_text(item):
    return item["caption"] + "\n\n" + " ".join(item["hashtags"])


def _gh_out(text):
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a") as f:
            f.write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int)
    ap.add_argument("--date")
    ap.add_argument("--start")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--weekdays", default="", help="hari tayang video kucing, angka ISO: 1=Senin..7=Minggu, contoh 1,3,5. Kosong = tiap hari")
    ap.add_argument("--out", default="out")
    ap.add_argument("--width", type=int, default=720, help="720 (cepat) atau 1080 (lebih tajam)")
    a = ap.parse_args()
    items = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    if a.dry:
        for it in items:
            _, tot = plan(it)
            flag = "" if 15 <= tot <= 45 else "  <-- LUAR RENTANG"
            print(f"hari {it['day']:>2}  {tot:5.1f}s  {it['scene']:<9} {it['mood']:<8} {it['tema']}{flag}")
        return
    os.makedirs(a.out, exist_ok=True)
    if a.all:
        days = [it["day"] for it in items]
    elif a.day:
        days = [a.day]
    elif a.date and a.start:
        today, start = dt.date.fromisoformat(a.date), dt.date.fromisoformat(a.start)
        wd = {int(x) for x in a.weekdays.split(",") if x.strip()} or {1, 2, 3, 4, 5, 6, 7}
        if today < start:
            print(f"Tanggal {today} belum mencapai CAT_START_DATE {start}. Tidak ada video.")
            _gh_out("skip=true\n")
            return
        if today.isoweekday() not in wd:
            print(f"{today} bukan hari video kucing (weekdays={sorted(wd)}). Lewati.")
            _gh_out("skip=true\n")
            return
        n = sum(1 for i in range((today - start).days + 1)
                if (start + dt.timedelta(days=i)).isoweekday() in wd)
        days = [(n - 1) % len(items) + 1]
    else:
        ap.error("pilih --day, --date+--start, atau --all. Kalau dari GitHub Actions: variabel repo CAT_START_DATE (format 2026-10-26) belum diisi.")
    for d in days:
        it = items[d - 1]
        mp4 = os.path.join(a.out, f"day{d:02d}.mp4")
        render(it, mp4, a.width)
        open(os.path.join(a.out, f"day{d:02d}.txt"), "w", encoding="utf-8").write(caption_text(it))
        if len(days) == 1:
            _gh_out(f"skip=false\nvideo={mp4}\ncaption_file={os.path.join(a.out, f'day{d:02d}.txt')}\nday={d}\n")


if __name__ == "__main__":
    main()
