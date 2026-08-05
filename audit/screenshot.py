import json, os, time
from playwright.sync_api import sync_playwright

SITES = [
    "https://bufetebysa.com/",
    "https://bufeteabogadoslima.com/",
    "https://grupobriffault.com/",
    "https://bufetedeabogadosej.com.mx/",
    "https://nexolegalmx.com.mx/",
    "https://despacho-de-abogados-cdmx.com/",
    "https://bufeteabogadoscdmx.com/",
    "https://saucedoabogados.com.mx/",
]

os.makedirs("audit_data", exist_ok=True)
report = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    for i, url in enumerate(SITES, 1):
        slug = url.split("//")[1].split("/")[0].replace("www.", "")
        entry = {"n": i, "url": url, "slug": slug}
        for device, vw, vh in [("mobile", 390, 844), ("desktop", 1366, 768)]:
            page = browser.new_page(viewport={"width": vw, "height": vh})
            try:
                t0 = time.time()
                resp = page.goto(url, timeout=45000, wait_until="load")
                entry[f"{device}_load_s"] = round(time.time() - t0, 2)
                entry[f"{device}_status"] = resp.status if resp else None
                page.wait_for_timeout(3000)
                page.screenshot(
                    path=f"audit_data/{i:02d}_{slug}_{device}.jpg",
                    full_page=True, quality=55, type="jpeg",
                )
                if device == "mobile":
                    entry["title"] = page.title()
                    entry["has_viewport_meta"] = page.locator('meta[name="viewport"]').count() > 0
                    entry["whatsapp_links"] = page.locator('a[href*="wa.me"], a[href*="whatsapp"]').count()
                    entry["tel_links"] = page.locator('a[href^="tel:"]').count()
                    entry["form_inputs"] = page.locator("form input:visible, form textarea:visible").count()
                    entry["h1"] = " | ".join(page.locator("h1").all_inner_texts())[:200]
                    entry["page_weight_kb"] = round(len(page.content()) / 1024)
            except Exception as e:
                entry[f"{device}_error"] = str(e)[:200]
            page.close()
        report.append(entry)
        print(json.dumps(entry, ensure_ascii=False))

with open("audit_data/report.json", "w") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
