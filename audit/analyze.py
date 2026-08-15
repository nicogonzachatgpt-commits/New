"""Compare competitor TikTok performance against gonzaher2's own numbers."""
import json, statistics as st

comp = json.load(open("competitor_data/summary.json"))
mine = json.load(open("tiktok_data/profile.json"))["entries"]


def rate(v, key):
    vc = v.get("view_count") or 0
    return (v.get(key) or 0) / vc * 100 if vc else 0


def band(d):
    if d is None:
        return "?"
    for hi, name in [(15, "0-15s"), (30, "16-30s"), (45, "31-45s"), (60, "46-60s")]:
        if d <= hi:
            return name
    return "60s+"


print("=" * 78)
print(f"{'CUENTA':<26}{'VIDS':>5}{'MEDIANA':>10}{'MEDIA':>10}{'MAX':>10}{'P90/MED':>9}")
print("=" * 78)

rows = []
allvids = []
for h, e in comp.items():
    if e.get("error"):
        print(f"{h:<26} -- {e['error'][:40]}")
        continue
    vids = [v for v in e["videos"] if v.get("view_count")]
    if not vids:
        continue
    views = sorted(v["view_count"] for v in vids)
    med, mx = st.median(views), max(views)
    p90 = views[int(len(views) * 0.9) - 1] if len(views) > 3 else mx
    rows.append((h, len(vids), med, st.mean(views), mx, p90 / med if med else 0))
    for v in vids:
        v["_handle"] = h
    allvids += vids

myv = [v for v in mine if v.get("view_count")]
mviews = sorted(v["view_count"] for v in myv)
rows.append(("gonzaher2 (VOS)", len(myv), st.median(mviews), st.mean(mviews),
             max(mviews), (mviews[int(len(mviews) * .9) - 1]) / st.median(mviews)))

for h, n, med, mean, mx, ratio in sorted(rows, key=lambda r: -r[2]):
    print(f"{h:<26}{n:>5}{med:>10,.0f}{mean:>10,.0f}{mx:>10,.0f}{ratio:>9.1f}x")

print("\n" + "=" * 78)
print("DURACIÓN vs VIEWS (todas las cuentas del nicho, normalizado por cuenta)")
print("=" * 78)
# normalize each video against its own account's median so big accounts don't dominate
medians = {h: st.median([v["view_count"] for v in allvids if v["_handle"] == h])
           for h in {v["_handle"] for v in allvids}}
buckets = {}
for v in allvids:
    m = medians[v["_handle"]] or 1
    buckets.setdefault(band(v.get("duration")), []).append(v["view_count"] / m)
for b in ["0-15s", "16-30s", "31-45s", "46-60s", "60s+", "?"]:
    if b in buckets:
        vals = buckets[b]
        print(f"  {b:<8} n={len(vals):<4} índice mediano vs su cuenta: {st.median(vals):.2f}x")

print("\n" + "=" * 78)
print("TOP 15 VIDEOS DEL NICHO (múltiplo sobre la mediana de su propia cuenta)")
print("=" * 78)
for v in sorted(allvids, key=lambda v: -(v["view_count"] / (medians[v["_handle"]] or 1)))[:15]:
    mult = v["view_count"] / (medians[v["_handle"]] or 1)
    desc = (v.get("description") or v.get("title") or "").replace("\n", " ")[:88]
    print(f"{mult:>6.1f}x {v['view_count']:>9,} views {str(v.get('duration'))+'s':>5} "
          f"@{v['_handle']:<20} {desc}")

print("\n" + "=" * 78)
print("ENGAGEMENT: qué señal acompaña a los videos que explotan")
print("=" * 78)
outliers = [v for v in allvids if v["view_count"] / (medians[v["_handle"]] or 1) >= 3]
normal = [v for v in allvids if v["view_count"] / (medians[v["_handle"]] or 1) < 3]
for label, group in [("OUTLIERS (>=3x)", outliers), ("NORMALES", normal)]:
    if not group:
        continue
    print(f"  {label:<18} n={len(group):<4} "
          f"likes {st.median([rate(v,'like_count') for v in group]):.2f}%  "
          f"coment {st.median([rate(v,'comment_count') for v in group]):.3f}%  "
          f"guardados {st.median([rate(v,'save_count') for v in group]):.3f}%  "
          f"dur.mediana {st.median([v.get('duration') or 0 for v in group]):.0f}s")
print(f"  {'VOS (gonzaher2)':<18} n={len(myv):<4} "
      f"likes {st.median([rate(v,'like_count') for v in myv]):.2f}%  "
      f"coment {st.median([rate(v,'comment_count') for v in myv]):.3f}%  "
      f"guardados {st.median([rate(v,'save_count') for v in myv]):.3f}%  "
      f"dur.mediana {st.median([v.get('duration') or 0 for v in myv]):.0f}s")

print("\n" + "=" * 78)
print("CAPTIONS: ¿los que rinden escriben descripción?")
print("=" * 78)
for label, group in [("OUTLIERS", outliers), ("NORMALES", normal), ("VOS", myv)]:
    if not group:
        continue
    withdesc = [v for v in group if (v.get("description") or "").strip()]
    lens = [len(v.get("description") or "") for v in withdesc]
    print(f"  {label:<10} con caption: {len(withdesc)}/{len(group)} "
          f"({len(withdesc)/len(group)*100:.0f}%)  largo mediano: "
          f"{st.median(lens) if lens else 0:.0f} chars")
