"""Weekly "NJ Fire Jobs" carousel: paid (career) and per diem firefighter openings in New Jersey.

The list lives in content/jobs/jobs.json and is checked/updated by hand or by a weekly research run.
Only openings verified in the last MAX_AGE days and not past their deadline go out.

  python jobs.py render  -> write the slides to content/jobs/out/ (for previewing)
  python jobs.py post    -> render, host and post the carousel (skips if already posted this week)
"""
import datetime as dt
import json
import os
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "jobs" / "jobs.json"
OUT = ROOT / "content" / "jobs" / "out"
STATE = ROOT / "state" / "jobs.json"
BRAND = ROOT / "brand"
HEAVY = str(BRAND / "fonts" / "barlow-condensed-latin-800-normal.woff")
SEMI = str(BRAND / "fonts" / "barlow-condensed-latin-600-normal.woff")
W, H = 1080, 1350
BG, RED, WHITE, GREY, DIM = (12, 12, 14), (198, 40, 40), (255, 255, 255), (170, 170, 176), (40, 40, 46)
MAX_AGE = 8          # days since an opening was last confirmed
MIN_JOBS = 2         # don't post a "list" of one
MAX_JOBS = 8         # cover + jobs + exam + closing slide must stay <= 10
TAGS = "#njfirefighter #firefighterjobs #perdiem #njfire #firejobs #newjersey #firefighter #stationhq"


def today():
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date()


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, f, max_w):
    words, lines, cur = str(text).split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def fit(d, text, path, size, max_w, max_lines, min_size=40):
    while True:
        f = font(path, size)
        lines = wrap(d, text, f, max_w)
        if len(lines) <= max_lines or size <= min_size:
            return f, lines[:max_lines]
        size -= 4


def lh(f, k=0.95):
    a, b = f.getmetrics()
    return int((a + b) * k)


def base(page, total):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=RED)
    small = font(SEMI, 30)
    logo = Image.open(BRAND / "logo_badge.png").convert("RGBA").resize((52, 53))
    img.paste(logo, (75, H - 100), logo)
    d.text((140, H - 92), "STATIONHQ", font=small, fill=WHITE)
    if total > 1:
        t = f"{page}/{total}"
        d.text((W - 75 - d.textlength(t, font=small), H - 92), t, font=small, fill=GREY)
    return img, d


def pill(d, x, y, text, fill=RED, color=WHITE, size=34):
    f = font(HEAVY, size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 44, y + size + 22], radius=(size + 22) // 2, fill=fill)
    d.text((x + 22, y + 8), text, font=f, fill=color)
    return x + w + 44


def nice_date(s):
    d = dt.date.fromisoformat(s)
    return d.strftime("%b ") + str(d.day)


def deadline_text(j):
    return "Rolling / until filled" if j["deadline"] == "rolling" else "Apply by " + nice_date(j["deadline"])


def cover(jobs, week, total):
    img, d = base(1, total)
    x = 75
    pill(d, x, 120, "WEEK OF " + (week.strftime("%b ") + str(week.day)).upper())
    big = font(HEAVY, 210)
    d.text((x, 210), "NJ FIRE", font=big, fill=WHITE)
    d.text((x, 210 + lh(big, 0.82)), "JOBS", font=big, fill=RED)
    f = font(SEMI, 52)
    y = 210 + lh(big, 0.82) * 2 + 30
    for line in wrap(d, "Paid & per diem firefighter openings in New Jersey", f, W - 150):
        d.text((x, y), line, font=f, fill=WHITE)
        y += lh(f)
    y += 40
    n_pd = sum(j["type"] == "per diem" for j in jobs)
    n_c = len(jobs) - n_pd
    stats = []
    if n_c:
        stats.append(f"{n_c} CAREER")
    if n_pd:
        stats.append(f"{n_pd} PER DIEM")
    for s in stats:
        x = pill(d, x, y, s, fill=DIM) + 16
    y += 110
    tf = font(SEMI, 46)
    for j in jobs[:6]:
        d.rectangle([75, y + 20, 91, y + 36], fill=RED)
        d.text((115, y), wrap(d, j["dept"], tf, W - 200)[0], font=tf, fill=WHITE)
        y += lh(tf) + 6
    sf = font(HEAVY, 40)
    d.text((75, H - 190), "SWIPE FOR DETAILS  >>", font=sf, fill=GREY)
    return img


def job_slide(j, page, total, new):
    img, d = base(page, total)
    x, y = 75, 110
    nx = pill(d, x, y, j["type"].upper())
    if new:
        pill(d, nx + 16, y, "NEW", fill=WHITE, color=BG)
    y += 110
    f, lines = fit(d, j["dept"], HEAVY, 120, W - 150, 3, 70)
    for l in lines:
        d.text((x, y), l, font=f, fill=WHITE)
        y += lh(f, 0.88)
    sf = font(SEMI, 44)
    d.text((x, y + 6), f"{j['town']}  ·  {j['county']} County", font=sf, fill=GREY)
    y += lh(sf) + 50
    d.rectangle([x, y, x + 90, y + 8], fill=RED)
    y += 40
    label, val = font(HEAVY, 32), font(SEMI, 42)
    rows = [("POSITION", j["title"]), ("PAY", j.get("pay") or "See posting"),
            ("DEADLINE", deadline_text(j)), ("HOW TO APPLY", j["apply"])]
    if j.get("needs"):
        rows.append(("GOOD TO KNOW", " · ".join(j["needs"])))
    for k, v in rows:
        vl = wrap(d, v, val, W - 150)[:3]
        if y + lh(label) + lh(val, 0.92) * len(vl) > H - 190:
            break
        d.text((x, y), k, font=label, fill=RED)
        y += lh(label) + 2
        for l in vl:
            d.text((x, y), l, font=val, fill=WHITE)
            y += lh(val, 0.92)
        y += 26
    nf = font(SEMI, 28)
    d.text((x, H - 160), f"Checked {nice_date(j['verified'])}. Confirm details with the department.", font=nf, fill=GREY)
    return img


def exam_slide(e, page, total):
    img, d = base(page, total)
    x, y = 75, 110
    pill(d, x, y, "EXAM WATCH")
    y += 120
    f, lines = fit(d, e["title"], HEAVY, 110, W - 150, 3, 70)
    for l in lines:
        d.text((x, y), l, font=f, fill=WHITE)
        y += lh(f, 0.88)
    y += 50
    vf = font(SEMI, 50)
    for line in e["lines"]:
        d.rectangle([x, y + 22, x + 16, y + 38], fill=RED)
        for i, l in enumerate(wrap(d, line, vf, W - 190)):
            d.text((x + 40, y), l, font=vf, fill=WHITE)
            y += lh(vf, 0.92)
        y += 24
    nf = font(SEMI, 28)
    d.text((x, H - 160), f"Source: {e['source']}. Checked {nice_date(e['verified'])}.", font=nf, fill=GREY)
    return img


def closing_slide(page, total):
    img, d = base(page, total)
    x = 75
    big = font(HEAVY, 140)
    y = 300
    for l in ["NEW LIST", "EVERY"]:
        d.text((x, y), l, font=big, fill=WHITE)
        y += lh(big, 0.85)
    d.text((x, y), "SATURDAY", font=big, fill=RED)
    y += lh(big, 0.85) + 50
    f = font(SEMI, 50)
    for line in ["Follow so you don't miss an opening.",
                 "Know a department that's hiring? DM us and we'll add it."]:
        for l in wrap(d, line, f, W - 150):
            d.text((x, y), l, font=f, fill=WHITE)
            y += lh(f)
        y += 24
    return img


def load():
    data = json.loads(DATA.read_text())
    t = today()
    jobs = []
    for j in data["jobs"]:
        age = (t - dt.date.fromisoformat(j["verified"])).days
        if age > MAX_AGE:
            print(f"skip {j['id']}: last checked {j['verified']} ({age} days ago)")
            continue
        if j["deadline"] != "rolling" and dt.date.fromisoformat(j["deadline"]) < t + dt.timedelta(days=2):
            print(f"skip {j['id']}: deadline {j['deadline']}")
            continue
        jobs.append(j)
    # soonest deadline first, rolling ones after
    jobs.sort(key=lambda j: (j["deadline"] == "rolling", j["deadline"], j["dept"]))
    exam = data.get("exam")
    if exam and (t - dt.date.fromisoformat(exam["verified"])).days > MAX_AGE:
        exam = None
    return jobs[:MAX_JOBS], exam


def build(state):
    jobs, exam = load()
    total = 1 + len(jobs) + (1 if exam else 0) + 1
    seen = state.get("seen", {})
    slides = [cover(jobs, today(), total)]
    for i, j in enumerate(jobs):
        slides.append(job_slide(j, i + 2, total, new=j["id"] not in seen))
    if exam:
        slides.append(exam_slide(exam, total - 1, total))
    slides.append(closing_slide(total, total))
    return jobs, exam, slides


def caption(jobs, exam):
    lines = [f"NJ FIRE JOBS: week of {nice_date(today().isoformat())} \U0001F692",
             "Paid & per diem firefighter openings in New Jersey. Swipe for details. ➡️", ""]
    for j in jobs:
        lines.append(f"\U0001F4CD {j['dept']} ({j['county']} Co.): {j['title']}, {deadline_text(j).lower()}")
        lines.append(f"   Apply: {j['apply']}")
    if exam:
        lines += ["", f"\U0001F4DD {exam['title']}: " + "; ".join(exam["lines"])]
    lines += ["",
              "Openings are pulled from official department and town postings and checked the week they go out. "
              "Always confirm details with the department before applying. StationHQ isn't hiring for or "
              "affiliated with these departments.",
              "", "Know a department that's hiring? DM us. New list every Saturday, follow so you don't miss one.",
              "", TAGS]
    return "\n".join(lines)


def render():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    jobs, exam, slides = build(state)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.jpg"):
        f.unlink()
    for i, s in enumerate(slides, 1):
        s.save(OUT / f"slide_{i:02d}.jpg", "JPEG", quality=92)
    (OUT / "caption.txt").write_text(caption(jobs, exam))
    print(f"Rendered {len(slides)} slides ({len(jobs)} openings) to {OUT}")
    return jobs


def post():
    import ig
    import media_host
    import tempfile
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    t = today()
    if state.get("last") and (t - dt.date.fromisoformat(state["last"])).days < 6 and not os.environ.get("FORCE"):
        print(f"Jobs list already went out this week ({state['last']})")
        return
    jobs, exam, slides = build(state)
    if len(jobs) < MIN_JOBS:
        print(f"Only {len(jobs)} verified opening(s); need {MIN_JOBS}. Not posting this week.")
        return
    work = pathlib.Path(tempfile.mkdtemp())
    stamp = t.strftime("%Y%m%d")
    files = []
    for i, s in enumerate(slides, 1):
        p = work / f"jobs_{stamp}_{i:02d}.jpg"
        s.save(p, "JPEG", quality=92)
        files.append(p)
    urls = media_host.host_files(files, work)
    cap = caption(jobs, exam)
    if os.environ.get("DRY_RUN"):
        print("[dry run] would post carousel:\n  " + "\n  ".join(urls) + "\n\n" + cap)
        return
    ig.publish_carousel(urls, cap, first_comment="Which department would you want to work for? \U0001F447")
    seen = state.get("seen", {})
    for j in jobs:
        seen.setdefault(j["id"], t.isoformat())
    state.update(last=t.isoformat(), seen=seen)
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Posted NJ Fire Jobs carousel ({len(jobs)} openings)")


if __name__ == "__main__":
    {"render": render, "post": post}[sys.argv[1]]()
