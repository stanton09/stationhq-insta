"""Find the stretch of a video with the most visible, flickering fire."""
import subprocess

W, H, FPS = 96, 54, 4


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def flame_scores(path):
    """Per frame: fraction of pixels that are flame-colored and flickering (up-then-down brightness)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS},scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    size = W * H * 3
    frames = [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]
    out = [0.0] * min(2, len(frames))
    for k in range(2, len(frames)):
        a, p, q, hits = frames[k], frames[k - 1], frames[k - 2], 0
        for j in range(0, size, 3):
            r, g, b = a[j], a[j + 1], a[j + 2]
            if r > 190 and g > 70 and r - g > 35 and g - b > 35 and b < 150:
                d1, d2 = g - p[j + 1], p[j + 1] - q[j + 1]
                if (d1 > 20 and d2 < -20) or (d1 < -20 and d2 > 20):
                    hits += 1
        out.append(hits / (W * H))
    return out


def best_window(path, length):
    """Start (seconds) of the `length`-second stretch with the most fire. 0 if the video is short."""
    total = duration(path)
    if total <= length + 1:
        return 0.0
    sc = flame_scores(path)
    win = int(length * FPS)
    if len(sc) <= win:
        return 0.0
    pre = [0.0]
    for v in sc:
        pre.append(pre[-1] + v)
    if pre[-1] == 0:
        return 0.0  # no fire found: keep the start, where the poster put the action
    return max(range(0, len(sc) - win + 1), key=lambda i: pre[i + win] - pre[i]) / FPS
