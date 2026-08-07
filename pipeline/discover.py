"""List all short-form videos (with view counts) for each channel/profile/search
in pipeline/channels.txt, using yt-dlp flat playlists on the CI runner.

channels.txt format: "<label>\t<url>" per line ("#" comments allowed).
Output: pipeline_data/discovery/<label>.json with trimmed entries.
"""
import json
import os
import subprocess

SRC = "pipeline/channels.txt"
OUT = "pipeline_data/discovery"
KEEP = ("id", "url", "webpage_url", "title", "view_count", "duration",
        "timestamp", "upload_date", "uploader", "channel", "channel_id")

os.makedirs(OUT, exist_ok=True)
summary = []

for line in open(SRC):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    label, url = line.split("\t", 1)
    entries, err = [], None
    try:
        r = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J",
             "--extractor-args", "youtubetab:approximate_date", url],
            capture_output=True, text=True, timeout=900)
        data = json.loads(r.stdout) if r.stdout.strip() else {}
        for e in data.get("entries") or []:
            if isinstance(e, dict):
                entries.append({k: e.get(k) for k in KEEP
                                if e.get(k) is not None})
        if not entries:
            err = (r.stderr or "empty result")[-300:]
    except Exception as exc:
        err = str(exc)[:300]
    json.dump({"label": label, "source_url": url, "count": len(entries),
               "error": err, "entries": entries},
              open(os.path.join(OUT, f"{label}.json"), "w"),
              ensure_ascii=False, indent=1)
    summary.append(f"{label}\t{len(entries)}\t{'' if not err else 'ERR'}")
    print(label, len(entries), err or "ok", flush=True)

with open(os.path.join(OUT, "_summary.txt"), "w") as fh:
    fh.write("\n".join(summary) + "\n")
print("DONE", len(summary))
