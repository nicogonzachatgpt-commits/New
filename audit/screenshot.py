import json, os, re, time
from urllib.parse import unquote, urlparse, parse_qs
from playwright.sync_api import sync_playwright

# Active ads from Meta Ad Library (lawyers, MX) — snapshot pages are public
SNAPSHOTS = [
    ("Justicia Legal", "951677597942307"),
    ("MH Hernandez y Marquez", "1365672848989032"),
    ("Carmona y Asociados", "2252244138871351"),
    ("Sesionlegal", "887514730709583"),
    ("GPO Abogados", "1578829283835086"),
    ("VV Abogados", "1905051170175029"),
    ("MG Consultoria Legal", "986585681064377"),
    ("Silerio Abogados", "1362783258680724"),
    ("Soluciones Juridicas YA", "2597861210648308"),
    ("Garza y Asociados", "2174647866731058"),
    ("Virtus Legal", "966522453125941"),
    ("R&B Soluciones Juridicas", "2123232178602563"),
    ("Abogados Saltillo", "4466541720224087"),
    ("Rosales-Abogados", "1028719923252734"),
    ("Tejada Rodrigo y Asociados", "945232231917427"),
    ("Abogados en Puebla de Confianza", "1362049826124718"),
]

OUT = "audit_data/ads"
os.makedirs(OUT, exist_ok=True)
results = []

def external_urls(page):
    urls = set()
    for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)"):
        if "l.facebook.com/l.php" in href:
            q = parse_qs(urlparse(href).query)
            if "u" in q:
                urls.add(unquote(q["u"][0]))
        elif href.startswith("http") and not re.search(r"facebook\.com|fb\.com|instagram\.com|whatsapp\.com|wa\.me|fb\.me", href):
            urls.add(href)
    return sorted(urls)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="es-ES")
    # Phase A: open each ad snapshot, screenshot it, extract landing URL
    for i, (name, ad_id) in enumerate(SNAPSHOTS, 1):
        page = ctx.new_page()
        entry = {"n": i, "advertiser": name, "ad_id": ad_id}
        try:
            page.goto(f"https://www.facebook.com/ads/library/?id={ad_id}", timeout=45000)
            page.wait_for_timeout(4000)
            for label in ["Decline optional cookies", "Rechazar cookies opcionales", "Allow all cookies", "Permitir todas las cookies"]:
                try:
                    page.get_by_role("button", name=label).first.click(timeout=1500)
                    page.wait_for_timeout(1500)
                    break
                except Exception:
                    pass
            page.wait_for_timeout(3000)
            page.screenshot(path=f"{OUT}/ad_{i:02d}_{ad_id}.jpg", quality=55, type="jpeg", full_page=True)
            entry["landing_urls"] = external_urls(page)
        except Exception as e:
            entry["error"] = str(e)[:200]
        results.append(entry)
        print(json.dumps(entry, ensure_ascii=False))
        page.close()

    # Phase B: screenshot each unique landing domain (mobile + desktop)
    seen = set()
    for entry in results:
        for url in entry.get("landing_urls", []):
            dom = urlparse(url).netloc.replace("www.", "")
            if not dom or dom in seen:
                continue
            seen.add(dom)
            landing = {"advertiser": entry["advertiser"], "url": url, "slug": dom}
            for device, vw, vh in [("mobile", 390, 844), ("desktop", 1366, 768)]:
                pg = browser.new_page(viewport={"width": vw, "height": vh})
                try:
                    t0 = time.time()
                    pg.goto(url, timeout=45000, wait_until="load")
                    landing[f"{device}_load_s"] = round(time.time() - t0, 2)
                    pg.wait_for_timeout(3000)
                    pg.screenshot(path=f"{OUT}/landing_{dom}_{device}.jpg", full_page=True, quality=55, type="jpeg")
                    if device == "mobile":
                        landing["title"] = pg.title()
                        landing["whatsapp_links"] = pg.locator('a[href*="wa.me"], a[href*="whatsapp"]').count()
                        landing["tel_links"] = pg.locator('a[href^="tel:"]').count()
                        landing["form_inputs"] = pg.locator("form input:visible, form textarea:visible").count()
                        landing["h1"] = " | ".join(pg.locator("h1").all_inner_texts())[:200]
                except Exception as e:
                    landing[f"{device}_error"] = str(e)[:200]
                pg.close()
            results.append({"landing": landing})
            print(json.dumps(landing, ensure_ascii=False))

with open(f"{OUT}/report.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
