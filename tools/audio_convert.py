"""Convert a WAV (any rate, 16/24/32-bit, mono/stereo) to GBA Direct Sound data:
signed 8-bit mono at 18157 Hz (exactly 304 samples per video frame).
Pure numpy so builds are deterministic and need no external tools."""
import wave
import numpy as np

RATE = 18157           # 16777216 / 924: timer reload 65536-924, 304 samples per frame


def load_wav(path):
    w = wave.open(path)
    ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    raw = w.readframes(n)
    if sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v).astype(np.float64) / (1 << 23)
    elif sw == 2:
        v = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768
    elif sw == 4:
        v = np.frombuffer(raw, dtype='<i4').astype(np.float64) / 2147483648
    else:
        v = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128) / 128
    v = v.reshape(-1, ch).mean(axis=1)
    return v, sr


def lowpass(x, sr, cutoff):
    taps = 127
    n = np.arange(taps) - (taps - 1) / 2
    h = np.sinc(2 * cutoff / sr * n) * np.blackman(taps)
    h /= h.sum()
    return np.convolve(x, h, mode='same')


def convert(path):
    x, sr = load_wav(path)
    x = lowpass(x, sr, RATE * 0.45)                 # anti-alias before resampling
    t = np.arange(0, len(x) / sr, 1.0 / RATE)
    y = np.interp(t * sr, np.arange(len(x)), x)
    peak = np.max(np.abs(y)) or 1.0
    y = y / peak * 0.97
    rnd = np.random.default_rng(1234)                # light TPDF dither, fixed seed = reproducible
    y = y * 127 + (rnd.random(len(y)) - rnd.random(len(y))) * 0.5
    q = np.clip(np.round(y), -128, 127).astype(np.int8)
    return q.tobytes(), len(q) / RATE
