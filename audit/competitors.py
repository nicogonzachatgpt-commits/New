"""Fetch TikTok accounts in the ecommerce / media-buying niche, find their
best-performing videos, and keep only lightweight artifacts (frames, subs,
metadata) so the repo stays small."""
import json, os, subprocess, glob

# Handles surfaced by web research. Unknown/dead ones just error out and are skipped.
HANDLES = [
    # Spanish-language, same niche as gonzaher2
    "nicodonovan.ads",
    "_ecommerceenaccion",
    "marketingparadise",
    "magdielmarketing",
    "rubenmanez",
    "vilmanunez",
    "juanmerodio",
    "ecommerciante",
    # English-language, same offer (ads / email / CRO for ecommerce)
    "theecomcoach",
    "chase_chappell",
    "samdespo",
    "alexfedotoff",
    "sellanythingonline",
    "foreplay_co",
]

TOP_N = 2          # top videos per account to download
FRAMES = 5         # frames extracted per video
OUT = "competitor_data"
os.makedirs(OUT, exist_ok=True)


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


summary = {}

for handle in HANDLES:
    print(f"=== {handle} ===", flush=True)
    entry = {"handle": handle, "videos": [], "error": None}
    r = run(f'yt-dlp --flat-playlist -J --playlist-end 40 "https://www.tiktok.com/@{handle}"')
    if r.returncode != 0 or not r.stdout.strip() or r.stdout.strip() == "null":
        entry["error"] = (r.stderr or "no output")[-400:]
        summary[handle] = entry
        print("  FAILED:", entry["error"][:200], flush=True)
        continue

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        entry["error"] = f"json: {e}"
        summary[handle] = entry
        continue

    vids = data.get("entries") or []
    entry["channel"] = data.get("title") or data.get("channel")
    entry["video_count_sampled"] = len(vids)
    for v in vids:
        entry["videos"].append({
            "id": v.get("id"),
            "duration": v.get("duration"),
            "view_count": v.get("view_count"),
            "like_count": v.get("like_count"),
            "comment_count": v.get("comment_count"),
            "save_count": v.get("save_count"),
            "repost_count": v.get("repost_count"),
            "timestamp": v.get("timestamp"),
            "title": v.get("title"),
            "description": v.get("description"),
            "url": v.get("url"),
        })

    # Top performers by views
    ranked = sorted(
        [v for v in entry["videos"] if v.get("view_count")],
        key=lambda v: v["view_count"], reverse=True,
    )[:TOP_N]
    entry["top_ids"] = [v["id"] for v in ranked]

    d = f"{OUT}/{handle}"
    os.makedirs(d, exist_ok=True)
    for v in ranked:
        vid, url = v["id"], v["url"]
        print(f"  downloading {vid} ({v['view_count']} views)", flush=True)
        run(
            f'yt-dlp -f "best[filesize<40M]/best" --write-info-json '
            f'--write-subs --write-auto-subs --sub-langs "es.*,en.*" '
            f'-o "{d}/{vid}.%(ext)s" "{url}"'
        )
        mp4 = f"{d}/{vid}.mp4"
        if os.path.exists(mp4):
            dur = v.get("duration") or 30
            for i in range(FRAMES):
                # sample across the clip, biased to the opening (hook lives there)
                t = round(dur * (i / (FRAMES + 1)) ** 1.3, 2) if i else 0.4
                run(
                    f'ffmpeg -loglevel error -ss {t} -i "{mp4}" -vframes 1 '
                    f'-vf "scale=440:-1" -q:v 6 "{d}/{vid}_f{i}_{t}s.jpg" -y'
                )
            os.remove(mp4)  # keep the repo light — frames are enough to read the hook

    summary[handle] = entry

with open(f"{OUT}/summary.json", "w") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)

ok = [h for h, e in summary.items() if not e["error"]]
print(f"\nDONE. {len(ok)}/{len(HANDLES)} accounts fetched: {ok}")
print("frames:", len(glob.glob(f"{OUT}/*/*.jpg")))
