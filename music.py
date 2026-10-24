"""Musik latar orisinal (dibuat dengan kode, bebas hak cipta). 3 mood: lofi, ceria, tenang."""
import zlib, wave
import numpy as np

SR = 44100
CHORD = {"maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "7": [0, 4, 7, 10], "maj": [0, 4, 7], "m": [0, 3, 7]}
PROGS = {
    "lofi":   [[(0,"maj7"),(9,"m7"),(5,"maj7"),(7,"7")], [(2,"m7"),(7,"7"),(0,"maj7"),(9,"m7")], [(5,"maj7"),(4,"m7"),(2,"m7"),(7,"7")]],
    "ceria":  [[(0,"maj"),(7,"maj"),(9,"m"),(5,"maj")], [(0,"maj"),(5,"maj"),(9,"m"),(7,"maj")]],
    "tenang": [[(0,"maj7"),(5,"maj7"),(9,"m7"),(7,"7")], [(9,"m7"),(5,"maj7"),(0,"maj7"),(4,"m7")]],
}
BPM = {"lofi": 80, "ceria": 100, "tenang": 66}
MOOD_BY_TEMA = {"Humor": "ceria", "Mindset": "tenang", "Parenting": "tenang"}

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(buf, start, sig):
    s = int(start * SR)
    if s >= len(buf): return
    e = min(len(buf), s + len(sig)); buf[s:e] += sig[: e - s]

def tone(midi, length, kind):
    t = np.arange(int(length * SR)) / SR
    f = hz(midi); out = np.zeros_like(t)
    for k, a in enumerate([1, 0.45, 0.2, 0.1], 1):
        decay = (2.2 if kind == "keys" else 0.5) + k * (1.2 if kind == "keys" else 0.1)
        out += a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * decay)
        out += 0.5 * a * np.sin(2 * np.pi * (f * 1.003) * k * t) * np.exp(-t * decay)  # detune tipis
    att = 0.006 if kind == "keys" else 0.5
    out *= np.minimum(1, t / att)
    if kind == "keys": out *= 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    if kind == "pad": out *= np.minimum(1, (length - t) / 0.6)
    return out

def make_track(seed_text, duration, mood="lofi"):
    rng = np.random.default_rng(zlib.crc32(seed_text.encode()))
    n = int(duration * SR); buf = np.zeros(n)
    prog = PROGS[mood][rng.integers(len(PROGS[mood]))]
    key = int(rng.integers(-3, 4))
    beat = 60.0 / BPM[mood]; bar = beat * 4
    nbars = int(duration / bar) + 2
    for b in range(nbars):
        root, typ = prog[b % len(prog)]; t0 = b * bar
        notes = [60 + key + root + iv for iv in CHORD[typ]]
        notes = [m - 12 if m > 72 else m for m in notes]
        if mood == "tenang":
            for i, m in enumerate(notes): add(buf, t0 + i * 0.03, 0.22 * tone(m, bar + 0.8, "pad"))
            add(buf, t0, 0.35 * tone(36 + key + root, bar, "bass"))
            continue
        hits = [0, 2] if mood == "lofi" else [0, 1.5, 2, 3.5]
        for h in hits:
            for i, m in enumerate(notes): add(buf, t0 + h * beat + i * 0.015, 0.20 * tone(m, 1.8, "keys"))
        for h in ([0, 2.5] if mood == "lofi" else [0, 2]):
            add(buf, t0 + h * beat, 0.55 * tone(36 + key + root, beat * 1.8, "bass"))
        # drum
        tk = np.arange(int(0.28 * SR)) / SR
        kick = np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-tk * 28)) / SR) * np.exp(-tk * 13)
        for h in ([0, 2.5] if mood == "lofi" else [0, 1, 2, 3]): add(buf, t0 + h * beat, 0.8 * kick)
        ts = np.arange(int(0.18 * SR)) / SR
        nz = rng.standard_normal(len(ts)); nz = nz - 0.6 * np.roll(nz, 1)
        snare = nz * np.exp(-ts * 24)
        for h in [1, 3]: add(buf, t0 + h * beat, 0.22 * snare)
        th = np.arange(int(0.05 * SR)) / SR
        for i in range(8):
            hz_ = rng.standard_normal(len(th)); hz_ = hz_ - np.roll(hz_, 1)
            sw = 0.07 * beat if i % 2 else 0
            add(buf, t0 + i * beat / 2 + sw, (0.07 if i % 2 else 0.1) * hz_ * np.exp(-th * 90))
    # reverb sederhana
    wet = buf.copy()
    for d, g in [(0.23, 0.30), (0.37, 0.20), (0.53, 0.12)]:
        s = int(d * SR); wet[s:] += g * buf[:-s]
    buf = wet + 0.004 * rng.standard_normal(n)  # noise vinyl tipis
    buf /= max(1e-9, np.abs(buf).max()); return (0.9 * buf).astype(np.float32)

def save_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())

def mood_for(tema): return MOOD_BY_TEMA.get(tema, "lofi")
