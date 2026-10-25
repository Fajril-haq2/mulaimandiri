"""Musik latar ORISINAL (disintesis dengan numpy) -> bebas klaim hak cipta.
4 suasana: tenang, harapan, ceria, malam. Deterministik per (mood, seed)."""
import wave
import numpy as np

SR = 44100

MOODS = {
    # root = nada MIDI akar, prog = (offset semiton, kualitas M/m)
    "tenang":  dict(bpm=72, root=48, prog=[(0, "M"), (9, "m"), (5, "M"), (7, "M")],
                    scale=[0, 2, 4, 7, 9], arp=1.0, mel=0.55, perc=False, wet=0.30, vol=1.0),
    "harapan": dict(bpm=84, root=50, prog=[(0, "M"), (7, "M"), (9, "m"), (5, "M")],
                    scale=[0, 2, 4, 7, 9], arp=1.0, mel=0.7, perc=False, wet=0.28, vol=1.0),
    "ceria":   dict(bpm=98, root=55, prog=[(0, "M"), (5, "M"), (7, "M"), (5, "M")],
                    scale=[0, 2, 4, 7, 9], arp=1.0, mel=0.8, perc=True, wet=0.22, vol=1.0),
    "malam":   dict(bpm=64, root=57, prog=[(0, "m"), (8, "M"), (3, "M"), (10, "M")],
                    scale=[0, 3, 5, 7, 10], arp=0.7, mel=0.4, perc=False, wet=0.40, vol=0.95),
}
CHORD = {"M": [0, 4, 7], "m": [0, 3, 7]}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _add(buf, start, sig):
    i = int(start * SR)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def _t(d):
    return np.arange(int(d * SR)) / SR


def pad(f, d):
    t = _t(d)
    s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.004 * t)
         + 0.25 * np.sin(2 * np.pi * f * 2 * t))
    a, r = min(0.9, d * 0.4), min(1.1, d * 0.4)
    env = np.minimum(1, t / a) * np.minimum(1, (d - t) / r)
    return s * env * 0.11


def pluck(f, d, vel=1.0):
    t = _t(d)
    s = np.zeros_like(t)
    for k, (amp, dec) in enumerate(((1.0, 3.2), (0.42, 5.5), (0.2, 8.0), (0.1, 11.0)), start=1):
        s += amp * np.sin(2 * np.pi * f * k * t) * np.exp(-dec * t)
    s *= np.minimum(1, t / 0.006)
    return s * 0.2 * vel


def bass(f, d):
    t = _t(d)
    env = np.minimum(1, t / 0.03) * np.exp(-1.4 * t)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)) * env * 0.26


def kick(d=0.22):
    t = _t(d)
    f = 110 * np.exp(-t * 14) + 45
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 16) * 0.28


def shaker(rng, d=0.07):
    t = _t(d)
    n = rng.standard_normal(len(t))
    n = n - np.concatenate([[0], n[:-1]])  # high-pass kasar
    return n * np.exp(-t * 55) * 0.05


def _ir(rng, secs=1.8):
    n = int(secs * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n) * np.exp(-3.2 * t)
    k = np.ones(40) / 40
    x = np.convolve(x, k, mode="same")  # redam sisi tajam
    return x / np.sqrt((x ** 2).sum())


def _reverb(x, ir):
    n = len(x) + len(ir)
    N = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return y


def make_music(mood, duration, seed=0):
    p = MOODS[mood]
    rng = np.random.default_rng(seed * 7919 + len(mood))
    dur = duration + 2.5
    beat = 60.0 / p["bpm"]
    bar = beat * 4
    n = int(dur * SR)
    dry = np.zeros(n)
    nbars = int(dur / bar) + 2
    mel_idx = int(rng.integers(0, 5))
    for b in range(nbars):
        off, q = p["prog"][b % 4]
        base = p["root"] + off
        ch = [base + x for x in CHORD[q]]
        t0 = b * bar
        for m in ch:
            _add(dry, t0, pad(hz(m + 12), bar + 0.6))
        _add(dry, t0, bass(hz(base - 12), bar * 0.9))
        _add(dry, t0 + beat * 2, bass(hz(base - 12 + (7 if q == "M" else 0)), bar * 0.45) * 0.7)
        # arpeggio 8th
        pat = [0, 1, 2, 1, 2, 1, 0, 1]
        for i, k in enumerate(pat):
            if p["arp"] < 1 and rng.random() > p["arp"]:
                continue
            note = ch[k] + 12
            _add(dry, t0 + i * beat / 2, pluck(hz(note), 1.4, 0.55 + 0.25 * (i % 2 == 0)))
        # melodi pentatonik
        steps = [0, 1.5, 2, 3, 3.5]
        for st in steps:
            if rng.random() < p["mel"] * 0.6:
                mel_idx = int(np.clip(mel_idx + rng.integers(-2, 3), 0, 9))
                deg = p["scale"][mel_idx % 5] + 12 * (mel_idx // 5)
                _add(dry, t0 + st * beat, pluck(hz(p["root"] + 24 + deg), 1.8, 0.85))
        if p["perc"]:
            for i in range(4):
                if i % 2 == 0:
                    _add(dry, t0 + i * beat, kick())
                _add(dry, t0 + i * beat + beat / 2, shaker(rng))
    # reverb stereo
    irl, irr = _ir(rng), _ir(rng)
    wl, wr = _reverb(dry, irl), _reverb(dry, irr)
    w = p["wet"]
    dl = int(0.011 * SR)
    left = dry * (1 - w) + wl * w * 2.4
    right = np.concatenate([np.zeros(dl), dry[:-dl]]) * (1 - w) + wr * w * 2.4
    out = np.stack([left, right], axis=1)[: int(duration * SR)]
    # fade
    nn = len(out)
    fi, fo = int(0.5 * SR), int(2.2 * SR)
    env = np.ones(nn)
    env[:fi] = np.linspace(0, 1, fi)
    env[-fo:] = np.linspace(1, 0, fo) ** 1.5
    out *= env[:, None]
    out = out / (np.abs(out).max() + 1e-9) * 0.8 * p["vol"]
    return out.astype(np.float32)


def write_wav(path, data):
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    import sys
    m = sys.argv[1] if len(sys.argv) > 1 else "tenang"
    write_wav(f"/tmp/{m}.wav", make_music(m, 20, 3))
    print("ok", m)
