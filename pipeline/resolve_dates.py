"""Resolve exact upload dates + view counts for candidate URLs without
downloading media. Reads pipeline/date_candidates.txt (one URL per line),
writes pipeline_data/dates/dates.tsv with:
id, upload_date, timestamp, view_count, duration, uploader, extractor, url, title
"""
import os
import subprocess

SRC = "pipeline/date_candidates.txt"
OUT_DIR = "pipeline_data/dates"
OUT = os.path.join(OUT_DIR, "dates.tsv")
FMT = "%(id)s\t%(upload_date)s\t%(timestamp)s\t%(view_count)s\t%(duration)s\t%(uploader)s\t%(extractor)s\t%(webpage_url)s\t%(title)s"

os.makedirs(OUT_DIR, exist_ok=True)

urls = []
for line in open(SRC):
    line = line.strip()
    if line and not line.startswith("#"):
        urls.append(line)

done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        parts = line.split("\t")
        if len(parts) > 7:
            done.add(parts[7])

with open(OUT, "a", encoding="utf-8") as fh:
    for i, url in enumerate(urls):
        if url in done:
            continue
        try:
            r = subprocess.run(
                ["yt-dlp", "--skip-download", "--no-playlist", "--print", FMT, url],
                capture_output=True, text=True, timeout=90)
            if r.returncode == 0 and r.stdout.strip():
                fh.write(r.stdout.strip().replace("\n", " ") + "\n")
            else:
                fh.write(f"ERROR\tNA\tNA\tNA\tNA\tNA\tNA\t{url}\t{(r.stderr or '')[-120:].strip()}\n")
        except Exception as e:
            fh.write(f"ERROR\tNA\tNA\tNA\tNA\tNA\tNA\t{url}\t{str(e)[:120]}\n")
        if (i + 1) % 25 == 0:
            fh.flush()
            print(f"{i+1}/{len(urls)}", flush=True)

print("DONE", len(urls))
