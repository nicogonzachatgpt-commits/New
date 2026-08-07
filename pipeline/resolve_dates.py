"""Resolve exact upload dates + view counts for candidate URLs without
downloading media. Reads pipeline/date_candidates.txt (one URL per line),
appends to pipeline_data/dates/dates.tsv. Already-resolved video IDs are
skipped, so reruns only retry failures.

YouTube URLs cascade through alternate player clients (tv, web_embedded,
android) to dodge datacenter bot-checks; a short sleep paces requests.
"""
import os
import re
import subprocess
import time

SRC = "pipeline/date_candidates.txt"
OUT_DIR = "pipeline_data/dates"
OUT = os.path.join(OUT_DIR, "dates.tsv")
FMT = "%(id)s\t%(upload_date)s\t%(timestamp)s\t%(view_count)s\t%(duration)s\t%(uploader)s\t%(extractor)s\t%(webpage_url)s\t%(title)s"
ID_RE = re.compile(r"(?:shorts/|watch\?v=|youtu\.be/)([\w-]{11})|/video/(\d+)|/shipin/(\d+)|bilibili\.com/video/(BV\w+)")

os.makedirs(OUT_DIR, exist_ok=True)

def url_id(u):
    m = ID_RE.search(u)
    return next((g for g in (m.groups() if m else []) if g), u)

urls = [l.strip() for l in open(SRC) if l.strip() and not l.startswith("#")]

done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        parts = line.rstrip("\n").split("\t")
        if len(parts) > 7 and parts[0] != "ERROR":
            done.add(parts[0])

YT_VARIANTS = [
    ["--extractor-args", "youtube:player_client=tv"],
    ["--extractor-args", "youtube:player_client=web_embedded"],
    ["--extractor-args", "youtube:player_client=android"],
]

def resolve(url):
    is_yt = "youtube.com" in url or "youtu.be" in url
    variants = YT_VARIANTS if is_yt else [[]]
    err = ""
    for extra in variants:
        try:
            r = subprocess.run(
                ["yt-dlp", "--skip-download", "--no-playlist", "--print", FMT,
                 *extra, url],
                capture_output=True, text=True, timeout=90)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip().replace("\n", " "), None
            err = (r.stderr or "")[-160:].replace("\n", " ").replace("\t", " ")
        except Exception as e:
            err = str(e)[:160]
    return None, err

pending = [u for u in urls if url_id(u) not in done]
print(f"pending {len(pending)} of {len(urls)}", flush=True)

yt_ok = None  # canary verdict: None until 5 YouTube URLs attempted
yt_tried = yt_hits = 0

with open(OUT, "a", encoding="utf-8") as fh:
    for i, url in enumerate(pending):
        is_yt = "youtube.com" in url or "youtu.be" in url
        if is_yt and yt_ok is False:
            fh.write(f"SKIPPED\tNA\tNA\tNA\tNA\tNA\tNA\t{url}\tyoutube canary failed, all clients bot-walled\n")
            continue
        line, err = resolve(url)
        if is_yt and yt_ok is None:
            yt_tried += 1
            yt_hits += 1 if line else 0
            if yt_tried >= 5:
                yt_ok = yt_hits > 0
                print(f"CANARY youtube: {yt_hits}/5 ok -> {'continuing' if yt_ok else 'skipping remaining youtube urls'}", flush=True)
        if line:
            fh.write(line + "\n")
        else:
            fh.write(f"ERROR\tNA\tNA\tNA\tNA\tNA\tNA\t{url}\t{err}\n")
        if (i + 1) % 25 == 0:
            fh.flush()
            print(f"{i+1}/{len(pending)}", flush=True)
        time.sleep(0.7)

print("DONE", len(pending))
