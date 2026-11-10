"""Build vertical NIST fire-science clips for TikTok (no posting).

Reuses download/best_window/build from nist.py, adds a credited Kevin MacLeod track,
and writes the results to content/tiktok/nist/<id>.mp4.
"""
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "scripts/nist.py").read_text()
src = src.split("\nTODAY =")[0].replace("import ig\n", "").replace("import media_host\n", "")
ns = {"__file__": str(ROOT / "scripts/nist.py")}
exec(compile(src, "nist_lib", "exec"), ns)

IDS = {
    "0_g93o3c3a": "music_investigations.mp3",
    "1_fajvo1tp": "music_ready_aim_fire.mp3",
    "1_unqumzj0": "music_guts_and_bourbon.mp3",
    "0_3ktuvtxj": "music_hustle.mp3",
    "0_nm11i0l0": "music_investigations.mp3",
}
OUT = ROOT / "content/tiktok/nist"
OUT.mkdir(parents=True, exist_ok=True)
for vid, track in IDS.items():
    v = next(x for x in ns["VIDEOS"] if x["id"] == vid)
    clip, work = ns["build"](v)
    dur = ns["duration"](clip)
    final = OUT / f"{vid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip),
                    "-i", str(ROOT / "brand/brisket/music" / track),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", f"volume=0.8,afade=t=in:d=0.5,afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{dur:.2f}", "-movflags", "+faststart", str(final)],
                   check=True)
    shutil.rmtree(work, ignore_errors=True)
    print("built", final, f"{dur:.1f}s")
