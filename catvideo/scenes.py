"""Gambar kucing line-art + 12 adegan. Semua koordinat dalam ruang 720x1280."""
import math
import cairo

INK = (0.10, 0.10, 0.11)
BG = (0.957, 0.957, 0.945)
BLUE = (0.184, 0.42, 1.0)
GREY = (0.62, 0.62, 0.60)
W, H = 720, 1280
GROUND = 960


# ---------------------------------------------------------------- helpers
def _init(ctx, lw=4.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(lw)


def sf(ctx, lw=4.0, fill=BG, ink=INK):
    """fill + stroke path saat ini."""
    if fill is not None:
        ctx.set_source_rgb(*fill)
        ctx.fill_preserve()
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(lw)
    ctx.stroke()


def line(ctx, x1, y1, x2, y2, lw=4.0, ink=INK):
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(lw)
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.stroke()


def hollow_stroke(ctx, outer=16.0, inner=9.0):
    """Garis 'berongga' (tail/pipa): stroke tebal ink lalu stroke tipis BG."""
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(outer)
    ctx.stroke_preserve()
    ctx.set_source_rgb(*BG)
    ctx.set_line_width(inner)
    ctx.stroke()


def ellipse(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def blink(t, period=4.2, phase=0.0, dur=0.2):
    u = (t + phase) % period
    return math.sin(math.pi * u / dur) if u < dur else 0.0


def ground(ctx, g=GROUND):
    line(ctx, -600, g, W + 600, g, 3.5)


def heart(ctx, cx, cy, s, alpha=1.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.move_to(0, 6)
    ctx.curve_to(-14, -4, -10, -16, 0, -9)
    ctx.curve_to(10, -16, 14, -4, 0, 6)
    ctx.set_source_rgba(*BLUE, alpha)
    ctx.fill_preserve()
    ctx.restore()
    ctx.new_path()


def sparkle(ctx, cx, cy, r, lw=3.0, alpha=1.0, ink=INK):
    ctx.set_source_rgba(*ink, alpha)
    ctx.set_line_width(lw)
    ctx.move_to(cx - r, cy)
    ctx.line_to(cx + r, cy)
    ctx.move_to(cx, cy - r)
    ctx.line_to(cx, cy + r)
    ctx.stroke()


def bug(ctx, t, cx, cy, ax=90, ay=40, sc=1.0):
    """Serangga kecil terbang ala video contoh."""
    x = cx + ax * math.sin(t * 0.9) + 30 * math.sin(t * 2.3)
    y = cy + ay * math.sin(t * 1.3 + 1.0) + 12 * math.sin(t * 3.1)
    flap = abs(math.sin(t * 22))
    ctx.set_source_rgb(*INK)
    ellipse(ctx, x - 5 * sc, y - 3 * sc, 6 * sc, (1 + 5 * flap) * sc, -0.5)
    ctx.fill()
    ellipse(ctx, x + 5 * sc, y - 3 * sc, 6 * sc, (1 + 5 * flap) * sc, 0.5)
    ctx.fill()
    ellipse(ctx, x, y, 2.2 * sc, 5 * sc, 0)
    ctx.fill()


# ---------------------------------------------------------------- kucing duduk
def cat_sit(ctx, x, g, s=1.0, t=0.0, look=0.0, eyes="open", phase=0.0,
            hat=False, up=0.0, lookup=0.0, tail_amp=24.0):
    """Kucing duduk tampak depan. look: -1..1 arah pandang, lookup: -1..1 (atas)."""
    ctx.save()
    ctx.translate(x, g)
    ctx.scale(s, s)
    _init(ctx, 4.2)
    sway = math.sin(t * 1.6 + phase)
    br = 1 + 0.014 * math.sin(t * 2.0 + phase)

    # ekor (di belakang badan)
    ctx.move_to(54, -8)
    ctx.curve_to(135, -2, 160 + 6 * sway, -80, 120 + tail_amp * sway, -150)
    hollow_stroke(ctx, 17, 9)

    # badan
    ctx.save()
    ctx.scale(1, br)
    ctx.move_to(-34, -140)
    ctx.curve_to(-62, -122, -80, -62, -72, -14)
    ctx.curve_to(-70, -3, -62, 0, -50, 0)
    ctx.line_to(50, 0)
    ctx.curve_to(62, 0, 70, -3, 72, -14)
    ctx.curve_to(80, -62, 62, -122, 34, -140)
    ctx.close_path()
    sf(ctx, 4.2)
    ctx.restore()

    # kaki depan
    for sx in (-1, 1):
        ctx.move_to(sx * 17, -88)
        ctx.line_to(sx * 17, -12)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4.2)
        ctx.stroke()
        ellipse(ctx, sx * 22, -8 - up * (10 if sx > 0 else 0), 19, 10)
        sf(ctx, 4.2)

    # kepala
    ctx.save()
    ctx.translate(look * 8, -182 + 1.5 * math.sin(t * 2 + phase))
    ctx.rotate(0.035 * math.sin(t * 0.9 + phase) + look * 0.05)
    # telinga
    for sx in (-1, 1):
        ctx.move_to(sx * 58, -26)
        ctx.line_to(sx * 55, -86)
        ctx.line_to(sx * 15, -50)
        ctx.close_path()
        sf(ctx, 4.2)
        ctx.move_to(sx * 49, -42)
        ctx.line_to(sx * 48, -68)
        ctx.line_to(sx * 31, -52)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(2.6)
        ctx.stroke()
    ellipse(ctx, 0, 0, 67, 54)
    sf(ctx, 4.2)
    # mata
    bl = blink(t, 4.3, phase * 1.7)
    for sx in (-1, 1):
        ex, ey = sx * 26 + look * 7, -2 - lookup * 5
        ctx.set_source_rgb(*INK)
        if eyes == "happy":
            ctx.set_line_width(4)
            ctx.arc(ex, ey + 3, 9, math.pi * 1.08, math.pi * 1.92)
            ctx.stroke()
        elif eyes == "sleep" or bl > 0.85:
            ctx.set_line_width(4)
            ctx.arc(ex, ey - 4, 9, math.pi * 0.1, math.pi * 0.9)
            ctx.stroke()
        else:
            ellipse(ctx, ex, ey, 4.8, 5.6 * (1 - 0.7 * bl))
            ctx.fill()
    # hidung + mulut
    ctx.set_source_rgb(*INK)
    ctx.move_to(-5 + look * 6, 9)
    ctx.line_to(5 + look * 6, 9)
    ctx.line_to(look * 6, 15)
    ctx.close_path()
    ctx.fill()
    ctx.set_line_width(3)
    ctx.arc(-6 + look * 6, 18, 6, 0, math.pi)
    ctx.stroke()
    ctx.arc(6 + look * 6, 18, 6, 0, math.pi)
    ctx.stroke()
    # kumis
    for sy, dy in ((6, -4), (13, 6)):
        ctx.set_line_width(2.4)
        ctx.move_to(-46, sy)
        ctx.line_to(-92, sy + dy)
        ctx.move_to(46, sy)
        ctx.line_to(92, sy + dy)
        ctx.stroke()
    if hat:
        ctx.move_to(-38, -42)
        ctx.line_to(-34, -92)
        ctx.line_to(34, -92)
        ctx.line_to(38, -42)
        ctx.close_path()
        sf(ctx, 4)
        for cx_, cy_, r_ in ((-34, -108, 26), (0, -124, 32), (34, -108, 26)):
            ctx.arc(cx_, cy_, r_, 0, 2 * math.pi)
            sf(ctx, 4)
        ctx.move_to(-37, -62)
        ctx.line_to(37, -62)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.restore()
    ctx.restore()


# ---------------------------------------------------------------- kucing tidur (drape di tepi garis)
def cat_sleep(ctx, x0, g, t):
    ctx.save()
    ctx.translate(x0, g)
    _init(ctx, 4.2)
    br = 1 + 0.025 * math.sin(t * 1.8)
    sway = math.sin(t * 1.1) * 9
    # ekor menjuntai
    ctx.move_to(352, -22)
    ctx.curve_to(392, 6, 384 + sway, 90, 362 + sway * 1.5, 168)
    hollow_stroke(ctx, 19, 11)
    # badan
    ctx.move_to(56, -44)
    ctx.curve_to(120, -108 * br, 250, -104 * br, 326, -44)
    ctx.curve_to(356, -22, 366, -4, 346, 0)
    ctx.line_to(56, 0)
    ctx.close_path()
    sf(ctx, 4.2)
    # kaki belakang menjuntai
    ctx.move_to(296, -2)
    ctx.curve_to(290, 40, 300, 80, 318, 92)
    ctx.curve_to(332, 98, 340, 86, 330, 76)
    ctx.curve_to(326, 50, 330, 20, 336, -2)
    sf(ctx, 4.2)
    # kaki depan menjuntai
    ctx.move_to(118, -2)
    ctx.curve_to(112, 36, 116, 70, 128, 84)
    ctx.curve_to(142, 92, 152, 80, 144, 68)
    ctx.curve_to(142, 44, 146, 18, 150, -2)
    sf(ctx, 4.2)
    # kepala (bertumpu di tepi)
    ctx.save()
    ctx.translate(34, -28)
    ctx.rotate(0.05 * math.sin(t * 1.8))
    for sx, ang in ((-1, 0), (1, 0)):
        ctx.move_to(sx * 30 - 2, -14)
        ctx.line_to(sx * 26 + 6, -58)
        ctx.line_to(sx * 4 + 10, -26)
        ctx.close_path()
        sf(ctx, 4)
    ellipse(ctx, 6, 0, 44, 32)
    sf(ctx, 4.2)
    ctx.set_line_width(3.4)
    ctx.set_source_rgb(*INK)
    for ex in (-14, 22):
        ctx.arc(ex, -4, 8, math.pi * 0.1, math.pi * 0.9)
        ctx.stroke()
    ctx.move_to(0, 8)
    ctx.line_to(8, 8)
    ctx.line_to(4, 13)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    ctx.restore()


def zzz(ctx, x, y, t):
    for i in range(3):
        u = ((t * 0.35) + i / 3.0) % 1.0
        a = math.sin(math.pi * u)
        sz = 10 + 12 * u
        cx, cy = x + 40 * u + i * 6, y - 120 * u
        ctx.set_source_rgba(*INK, a)
        ctx.set_line_width(3.2)
        ctx.move_to(cx - sz, cy - sz)
        ctx.line_to(cx + sz, cy - sz)
        ctx.line_to(cx - sz, cy + sz)
        ctx.line_to(cx + sz, cy + sz)
        ctx.stroke()


# ---------------------------------------------------------------- adegan
def scene_tidur(ctx, t, T):
    g = 900
    ground(ctx, g)
    cat_sleep(ctx, 120, g, t)
    zzz(ctx, 180, g - 90, t)
    bug(ctx, t, 520, g - 280, 110, 50)


def scene_koin(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 250, g, 1.05, t, look=0.6, lookup=-0.2)
    # toples
    jx = 520
    n = int(t // 2.6)  # jumlah koin masuk
    ctx.move_to(jx - 62, g - 150)
    ctx.line_to(jx - 70, g - 20)
    ctx.curve_to(jx - 70, g - 2, jx - 60, g, jx - 50, g)
    ctx.line_to(jx + 50, g)
    ctx.curve_to(jx + 60, g, jx + 70, g - 2, jx + 70, g - 20)
    ctx.line_to(jx + 62, g - 150)
    sf(ctx, 4.2)
    for i in range(min(n, 9)):
        ellipse(ctx, jx - 28 + (i % 3) * 28, g - 14 - (i // 3) * 16, 17, 8)
        sf(ctx, 3.4, fill=BG)
    # tutup
    ctx.rectangle(jx - 72, g - 172, 144, 22)
    sf(ctx, 4.2)
    # koin jatuh
    u = (t % 2.6) / 2.6
    if u < 0.78:
        k = u / 0.78
        cy = 560 + (g - 200 - 560) * (k * k)
        ctx.arc(jx, cy, 22, 0, 2 * math.pi)
        sf(ctx, 4, fill=BG)
        ctx.arc(jx, cy, 12, 0, 2 * math.pi)
        ctx.set_line_width(2.4)
        ctx.set_source_rgb(*INK)
        ctx.stroke()
    else:
        k = (u - 0.78) / 0.22
        for a in range(4):
            ang = a * math.pi / 2 + 0.4
            sparkle(ctx, jx + 60 * math.cos(ang) * k, g - 200 + 60 * math.sin(ang) * k - 20,
                    6 * (1 - k), 3, 1 - k, BLUE)


def scene_baca(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 360, g, 1.0, t, look=0.0, lookup=-1.0)
    # buku terbuka di depan
    bx, by = 360, g - 6
    ctx.move_to(bx, by - 70)
    ctx.curve_to(bx - 40, by - 86, bx - 100, by - 84, bx - 140, by - 70)
    ctx.line_to(bx - 150, by)
    ctx.curve_to(bx - 100, by - 14, bx - 40, by - 14, bx, by)
    ctx.close_path()
    sf(ctx, 4)
    ctx.move_to(bx, by - 70)
    ctx.curve_to(bx + 40, by - 86, bx + 100, by - 84, bx + 140, by - 70)
    ctx.line_to(bx + 150, by)
    ctx.curve_to(bx + 100, by - 14, bx + 40, by - 14, bx, by)
    ctx.close_path()
    sf(ctx, 4)
    for r in range(3):
        for sx in (-1, 1):
            ctx.set_source_rgb(*GREY)
            ctx.set_line_width(2.4)
            ctx.move_to(bx + sx * 24, by - 56 + r * 14 + (0))
            ctx.line_to(bx + sx * 112, by - 58 + r * 14)
            ctx.stroke()
    # halaman membalik
    u = (t % 4.0) / 4.0
    if u < 0.2:
        k = u / 0.2
        w = math.cos(math.pi * k) * 120
        ctx.move_to(bx, by - 70)
        ctx.line_to(bx + w, by - 76 - 18 * math.sin(math.pi * k))
        ctx.line_to(bx + w * 1.05, by - 6)
        ctx.line_to(bx, by - 2)
        ctx.close_path()
        sf(ctx, 3.6)
    # huruf melayang
    for i in range(3):
        v = ((t * 0.3) + i / 3.0) % 1.0
        sparkle(ctx, 150 + i * 210, 760 - 140 * v, 7, 3, math.sin(math.pi * v), BLUE)


def scene_laptop(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 360, g, 1.0, t, look=0.0, lookup=-0.4)
    lx, ly = 360, g
    # layar (tampak belakang)
    ctx.move_to(lx - 135, ly - 4)
    ctx.line_to(lx - 125, ly - 106)
    ctx.curve_to(lx - 125, ly - 182, lx - 115, ly - 120, lx - 105, ly - 120)
    ctx.line_to(lx + 105, ly - 120)
    ctx.curve_to(lx + 115, ly - 120, lx + 125, ly - 182, lx + 125, ly - 106)
    ctx.line_to(lx + 135, ly - 4)
    ctx.close_path()
    sf(ctx, 4.2)
    ctx.arc(lx, ly - 60, 14, 0, 2 * math.pi)
    sf(ctx, 3.2, fill=BG)
    ctx.rectangle(lx - 160, ly - 6, 320, 10)
    sf(ctx, 4.2)
    # cakar mengetik (mengintip dari atas layar)
    for i, sx in enumerate((-1, 1)):
        d = max(0.0, math.sin(t * 7 + i * math.pi)) * 12
        ellipse(ctx, lx + sx * 44, ly - 128 - d, 20, 11)
        sf(ctx, 4)
    # titik kode melayang
    for i in range(4):
        v = ((t * 0.4) + i / 4.0) % 1.0
        sparkle(ctx, 160 + i * 130, 780 - 120 * v, 6, 3, math.sin(math.pi * v), BLUE)


def scene_cangkir(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 260, g, 1.05, t, look=0.5, eyes="happy")
    cx = 530
    ellipse(ctx, cx, g - 6, 78, 11)
    sf(ctx, 4)
    ctx.move_to(cx - 52, g - 88)
    ctx.line_to(cx - 40, g - 16)
    ctx.curve_to(cx - 36, g - 2, cx + 36, g - 2, cx + 40, g - 16)
    ctx.line_to(cx + 52, g - 88)
    ctx.close_path()
    sf(ctx, 4.2)
    ctx.arc(cx + 56, g - 56, 22, -math.pi * 0.5, math.pi * 0.55)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    ellipse(ctx, cx, g - 88, 52, 9)
    sf(ctx, 4.2)
    for i in range(3):
        ctx.set_source_rgba(*INK, 0.55)
        ctx.set_line_width(3.4)
        px = cx - 24 + i * 24
        for k in range(24):
            yy = g - 108 - k * 6
            xx = px + 7 * math.sin(k * 0.5 - t * 3 + i * 1.7)
            (ctx.move_to if k == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()


def scene_bulan(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    # bulan
    mx, my = 520, 560
    ctx.arc(mx, my, 90, 0, 2 * math.pi)
    sf(ctx, 4.2)
    for cx_, cy_, r_ in ((-26, -20, 15), (24, 18, 11), (-8, 38, 8)):
        ctx.arc(mx + cx_, my + cy_, r_, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(2.6)
        ctx.stroke()
    for i, (sx, sy) in enumerate(((110, 520), (230, 700), (640, 760), (330, 560), (80, 800))):
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2.2 + i * 1.9))
        sparkle(ctx, sx, sy, 9 * (0.6 + 0.4 * a), 3, a)
    cat_sit(ctx, 240, g, 1.05, t, look=0.8, lookup=1.0)
    # gelembung pikiran
    for i, (dx, dy, r) in enumerate(((120, -330, 7), (150, -362, 11), (190, -408, 17))):
        ctx.arc(240 + dx, g + dy - 6 * math.sin(t * 2 + i), r, 0, 2 * math.pi)
        sf(ctx, 3.4)


def scene_hujan(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    # awan
    ccx, ccy = 360, 440
    cl = ((-110, 14, 46), (-52, -14, 58), (22, -22, 64), (92, 6, 50), (-6, 30, 52))
    ctx.set_source_rgb(*INK)
    for dx, dy, r in cl:
        ctx.arc(ccx + dx, ccy + dy, r, 0, 2 * math.pi)
        ctx.set_line_width(4.2)
        ctx.stroke()
    ctx.set_source_rgb(*BG)
    for dx, dy, r in cl:
        ctx.arc(ccx + dx, ccy + dy, r - 2.2, 0, 2 * math.pi)
        ctx.fill()
    # hujan
    for i in range(14):
        x = 150 + i * 31 + (i % 3) * 7
        sp = 520 + (i % 4) * 90
        off = (i * 137) % 300
        y = 520 + ((t * sp + off) % 440)
        if x < 215 or x > 505 or y < 760 or True:
            if 470 < y < g - 4 or (y < 760):
                pass
        ctx.set_source_rgb(*BLUE)
        ctx.set_line_width(3.2)
        # lewati area payung
        if not (205 < x < 515 and y > 560):
            ctx.move_to(x, y)
            ctx.line_to(x - 5, y + 20)
            ctx.stroke()
    # kucing + payung
    cat_sit(ctx, 360, g, 1.0, t, look=0.0, lookup=0.6)
    ux, uy = 360, 640 + 5 * math.sin(t * 1.5)
    ctx.move_to(ux - 150, uy)
    ctx.curve_to(ux - 140, uy - 110, ux + 140, uy - 110, ux + 150, uy)
    for k in range(3):
        a = ux + 150 - k * 100
        ctx.curve_to(a - 16, uy + 22, a - 84, uy + 22, a - 100, uy)
    ctx.close_path()
    sf(ctx, 4.4)
    ctx.move_to(ux, uy - 70)
    ctx.line_to(ux, uy - 94)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    # riak genangan
    for i in range(2):
        u = ((t * 0.8) + i * 0.5) % 1.0
        ctx.set_source_rgba(*BLUE, 1 - u)
        ctx.set_line_width(3)
        ellipse(ctx, 560, g + 24, 12 + 50 * u, 4 + 12 * u)
        ctx.stroke()


def scene_tanaman(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    # matahari
    sx, sy = 130, 560
    ctx.arc(sx, sy, 44, 0, 2 * math.pi)
    sf(ctx, 4.2)
    for k in range(10):
        a = k * math.pi / 5 + t * 0.4
        line(ctx, sx + 62 * math.cos(a), sy + 62 * math.sin(a), sx + 82 * math.cos(a), sy + 82 * math.sin(a), 3.6)
    cat_sit(ctx, 250, g, 1.0, t, look=0.8, lookup=0.0)
    px = 540
    ctx.move_to(px - 56, g - 100)
    ctx.line_to(px - 42, g - 4)
    ctx.line_to(px + 42, g - 4)
    ctx.line_to(px + 56, g - 100)
    ctx.close_path()
    sf(ctx, 4.2)
    ctx.rectangle(px - 64, g - 122, 128, 24)
    sf(ctx, 4.2)
    prog = min(1.0, t / max(1.0, T * 0.75))
    top = 40 + 190 * prog
    sway = 6 * math.sin(t * 1.4)
    ctx.move_to(px, g - 122)
    ctx.curve_to(px + 4, g - 122 - top * 0.4, px + sway, g - 122 - top * 0.7, px + sway * 1.4, g - 122 - top)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    for frac, side in ((0.3, -1), (0.52, 1), (0.74, -1)):
        if prog > frac:
            k = min(1.0, (prog - frac) / 0.12)
            yy = g - 122 - top * frac
            xx = px + sway * frac
            ctx.save()
            ctx.translate(xx, yy)
            ctx.scale(side * k, k)
            ctx.move_to(0, 0)
            ctx.curve_to(26, -34, 64, -30, 76, -8)
            ctx.curve_to(52, 14, 16, 12, 0, 0)
            sf(ctx, 3.8)
            ctx.restore()
    if prog > 0.97:
        k = min(1.0, (t - T * 0.75) / 1.2)
        fx, fy = px + sway * 1.4, g - 122 - top
        for a in range(6):
            ang = a * math.pi / 3
            ctx.arc(fx + 26 * k * math.cos(ang), fy + 26 * k * math.sin(ang), 15 * k, 0, 2 * math.pi)
            sf(ctx, 3.6)
        ctx.arc(fx, fy, 12 * k, 0, 2 * math.pi)
        sf(ctx, 3.6, fill=(1.0, 0.86, 0.3))


def scene_masak(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 250, g, 1.05, t, look=0.6, hat=True, eyes="happy")
    px = 530
    # kompor
    ctx.rectangle(px - 110, g - 70, 220, 70)
    sf(ctx, 4.2)
    for k in range(3):
        u = (t * 3 + k) % 3
        ctx.move_to(px - 60 + k * 60, g - 70)
        ctx.curve_to(px - 66 + k * 60, g - 86 - 4 * u, px - 54 + k * 60, g - 96, px - 60 + k * 60, g - 108 + 6 * math.sin(t * 8 + k))
        ctx.set_source_rgb(*BLUE)
        ctx.set_line_width(3.4)
        ctx.stroke()
    # panci
    lid = 4 * abs(math.sin(t * 6))
    ctx.rectangle(px - 90, g - 190, 180, 110)
    sf(ctx, 4.2)
    for sx in (-1, 1):
        ctx.arc(px + sx * 100, g - 160, 12, -math.pi * 0.5 + (sx < 0) * math.pi, math.pi * 0.5 + (sx < 0) * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.rectangle(px - 98, g - 204 - lid, 196, 16)
    sf(ctx, 4.2)
    ctx.arc(px, g - 214 - lid, 8, 0, 2 * math.pi)
    sf(ctx, 3.6)
    for i in range(3):
        u = ((t * 0.5) + i / 3.0) % 1.0
        ctx.set_source_rgba(*INK, 0.5 * math.sin(math.pi * u))
        ctx.set_line_width(3.4)
        for k in range(16):
            yy = g - 236 - u * 120 - k * 5
            xx = px - 40 + i * 40 + 8 * math.sin(k * 0.55 - t * 3 + i)
            (ctx.move_to if k == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()


def scene_jam(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 250, g, 1.05, t, look=0.8, lookup=0.3)
    cx, cy, r = 520, 690, 110
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    sf(ctx, 5)
    for k in range(12):
        a = k * math.pi / 6
        line(ctx, cx + (r - 18) * math.cos(a), cy + (r - 18) * math.sin(a),
             cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a), 3.6)
    am = t * 1.5
    line(ctx, cx, cy, cx + 78 * math.sin(am), cy - 78 * math.cos(am), 6)
    ah = am / 12
    line(ctx, cx, cy, cx + 50 * math.sin(ah), cy - 50 * math.cos(ah), 7, BLUE)
    ctx.arc(cx, cy, 6, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.fill()
    line(ctx, cx - 40, cy + r - 4, cx - 56, g, 4.2)
    line(ctx, cx + 40, cy + r - 4, cx + 56, g, 4.2)
    for i in range(3):
        n = (t - 1.0 - i * 2.4)
        bx, by = 120, 700 + i * 52
        ctx.rectangle(bx, by, 30, 30)
        sf(ctx, 3.6)
        if n > 0:
            k = min(1.0, n / 0.5)
            ctx.move_to(bx + 6, by + 16)
            ctx.line_to(bx + 6 + 7 * k, by + 16 + 8 * k)
            if k > 0.5:
                ctx.line_to(bx + 14 + 14 * (k - 0.5) * 2, by + 24 - 20 * (k - 0.5) * 2)
            ctx.set_source_rgb(*BLUE)
            ctx.set_line_width(5)
            ctx.stroke()


def scene_keluarga(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    cat_sit(ctx, 250, g, 1.1, t, look=0.5, eyes="happy", phase=0.0)
    cat_sit(ctx, 500, g, 0.58, t, look=-0.6, phase=1.3, tail_amp=18)
    for i in range(3):
        u = ((t * 0.28) + i / 3.0) % 1.0
        heart(ctx, 375 + 12 * math.sin(t * 2 + i), g - 330 - 150 * u, 1.3, math.sin(math.pi * u))


def scene_keran(ctx, t, T):
    g = GROUND
    ground(ctx, g)
    px, py = 500, 620
    ctx.move_to(-20, py)
    ctx.line_to(px, py)
    ctx.curve_to(px + 40, py, px + 40, py + 24, px + 40, py + 56)
    hollow_stroke(ctx, 40, 30)
    ctx.rectangle(px + 22, py + 52, 36, 22)
    sf(ctx, 4)
    ctx.move_to(px - 70, py - 20)
    ctx.line_to(px - 70, py - 52)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.move_to(px - 100, py - 56)
    ctx.line_to(px - 40, py - 56)
    ctx.set_line_width(7)
    ctx.stroke()
    # tetesan
    for i in range(2):
        u = ((t * 0.9) + i * 0.5) % 1.0
        if u < 0.85:
            k = u / 0.85
            y = py + 90 + (g - py - 110) * k * k
            ctx.move_to(px + 40, y - 14)
            ctx.curve_to(px + 28, y + 2, px + 30, y + 14, px + 40, y + 14)
            ctx.curve_to(px + 50, y + 14, px + 52, y + 2, px + 40, y - 14)
            ctx.set_source_rgb(*BLUE)
            ctx.fill()
        else:
            k = (u - 0.85) / 0.15
            ctx.set_source_rgba(*BLUE, 1 - k)
            ctx.set_line_width(3)
            ellipse(ctx, px + 40, g + 14, 6 + 30 * k, 2 + 7 * k)
            ctx.stroke()
    cat_sit(ctx, 200, g, 1.05, t, look=0.8, lookup=0.4)
    # kunci inggris
    ang = 0.35 * math.sin(t * 2.4)
    ctx.save()
    ctx.translate(420, g - 12)
    ctx.rotate(0.45 + ang * 0.5)
    ctx.move_to(0, 0)
    ctx.line_to(0, -130)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(14)
    ctx.stroke()
    ctx.set_source_rgb(*BG)
    ctx.set_line_width(7)
    ctx.move_to(0, 0)
    ctx.line_to(0, -130)
    ctx.stroke()
    ctx.arc(0, -138, 24, math.pi * 1.25, math.pi * 1.75 + math.pi * 1.5)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.restore()


SCENES = {
    "tidur": scene_tidur, "koin": scene_koin, "baca": scene_baca, "laptop": scene_laptop,
    "cangkir": scene_cangkir, "bulan": scene_bulan, "hujan": scene_hujan,
    "tanaman": scene_tanaman, "masak": scene_masak, "jam": scene_jam,
    "keluarga": scene_keluarga, "keran": scene_keran,
}
