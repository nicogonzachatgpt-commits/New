"""Fetch reference videos listed in pipeline/urls.txt, extract metadata,
transcripts (subtitles or Whisper) and evenly-spaced frames.

urls.txt format: one entry per line, either "<row_id>\t<url>" or just "<url>".
Results land in pipeline_data/<row_id>/ (meta.json + frame_N.jpg) plus a
global pipeline_data/index.json. Video files themselves are NOT committed.
"""
import glob
import json
import os
import shutil
import subprocess

URLS = "pipeline/urls.txt"
OUT = "pipeline_data"
N_FRAMES = 6

os.makedirs(OUT, exist_ok=True)

rows = []
with open(URLS) as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
        else:
            rows.append((f"{len(rows)+1:03d}", parts[0]))

def run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

_model = None
def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model

def srt_to_text(path):
    lines = []
    for l in open(path, encoding="utf-8", errors="replace"):
        l = l.strip()
        if not l or l.isdigit() or "-->" in l:
            continue
        if not lines or lines[-1] != l:
            lines.append(l)
    return " ".join(lines)

META_KEYS = ["id", "title", "description", "uploader", "uploader_id", "channel",
             "channel_follower_count", "view_count", "like_count", "comment_count",
             "repost_count", "duration", "upload_date", "webpage_url", "extractor",
             "language"]

index = []
for rid, url in rows:
    d = os.path.join(OUT, rid)
    tmp = os.path.join("tmp_dl", rid)
    os.makedirs(d, exist_ok=True)
    os.makedirs(tmp, exist_ok=True)
    info = {"row": rid, "url": url, "status": "failed"}
    try:
        r = run(["yt-dlp", "--no-playlist",
                 "-f", "b[filesize<120M]/bv*[height<=720]+ba/b",
                 "--write-info-json", "--write-subs", "--write-auto-subs",
                 "--sub-langs", "en.*,hi.*,zh.*,ru.*,es.*,pt.*",
                 "--convert-subs", "srt",
                 "-o", os.path.join(tmp, "video.%(ext)s"), url], timeout=900)
        if r.returncode != 0:
            info["yt_dlp_error"] = (r.stderr or "")[-400:]
        ij = glob.glob(os.path.join(tmp, "*.info.json"))
        meta = json.load(open(ij[0])) if ij else {}
        for k in META_KEYS:
            if meta.get(k) is not None:
                info[k] = meta[k]
        vids = [f for f in glob.glob(os.path.join(tmp, "video.*"))
                if not f.endswith((".json", ".srt", ".vtt"))]
        transcript, src = None, "none"
        srts = sorted(glob.glob(os.path.join(tmp, "*.srt")))
        if srts:
            lang = (meta.get("language") or "")[:2]
            pick = next((s for s in srts if lang and f".{lang}" in s), srts[0])
            transcript = srt_to_text(pick)
            src = "subtitles:" + os.path.basename(pick)
        if vids:
            v = vids[0]
            dur = float(meta.get("duration") or 30)
            for i in range(N_FRAMES):
                t = dur * (i + 0.5) / N_FRAMES
                run(["ffmpeg", "-y", "-ss", str(t), "-i", v, "-frames:v", "1",
                     "-vf", "scale=360:-2", "-q:v", "5",
                     os.path.join(d, f"frame_{i+1}.jpg")], timeout=120)
            if not transcript or len(transcript) < 40:
                wav = os.path.join(tmp, "a.wav")
                run(["ffmpeg", "-y", "-i", v, "-vn", "-ac", "1", "-ar", "16000",
                     wav], timeout=300)
                if os.path.exists(wav):
                    segs, winfo = get_model().transcribe(wav, vad_filter=True)
                    transcript = " ".join(s.text.strip() for s in segs).strip()
                    src = f"whisper-small:{winfo.language}"
                    info["whisper_language"] = winfo.language
        info["transcript"] = transcript
        info["transcript_source"] = src
        info["n_frames"] = len(glob.glob(os.path.join(d, "frame_*.jpg")))
        info["status"] = "ok" if (transcript or vids) else "no_media"
    except Exception as e:  # keep going on per-URL failures
        info["error"] = str(e)[:300]
    json.dump(info, open(os.path.join(d, "meta.json"), "w"),
              ensure_ascii=False, indent=1)
    index.append({k: info.get(k) for k in
                  ["row", "url", "status", "extractor", "view_count",
                   "title", "transcript_source", "n_frames"]})
    shutil.rmtree(tmp, ignore_errors=True)
    print(rid, info["status"], info.get("view_count"), flush=True)

json.dump(index, open(os.path.join(OUT, "index.json"), "w"),
          ensure_ascii=False, indent=1)
print("DONE", len(index))
