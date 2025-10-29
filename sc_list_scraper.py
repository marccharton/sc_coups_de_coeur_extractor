from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import re
import pandas as pd
from urllib.parse import urljoin
from pathlib import Path
import argparse
import sys
import time
from datetime import datetime

LIST_YEAR_RE = re.compile(r"(19|20)\d{2}(?:\s*[–-]\s*(19|20)\d{2})?")

def log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

def extract_year_from_list_title(title: str) -> str:
    if not title:
        return ""
    m = LIST_YEAR_RE.search(title)
    return m.group(0).replace("–", "-").replace(" ", "") if m else ""

def clean_text(s: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", s or "").strip()

def is_album_href(href: str) -> bool:
    # Pages d’albums : /album/<slug>/<id>
    return href and href.startswith("/album/")

def safe_screenshot(page, folder: Path, label: str):
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{int(time.time())}_{label}.png"
        page.screenshot(path=str(path), full_page=True)
        log(f"📸 Capture d’écran: {path}")
    except Exception as e:
        log(f"⚠️ Impossible de faire une capture d’écran: {e}")

def parse_album_page(page, album_url: str, screenshot_dir):
    import re
    # --- helpers locaux ---
    def clean(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "")).strip()

    def extract_artists_from_page(page) -> list:
        import re
        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "")).strip()

        artists = []

        # 1) Source principale : le bloc des créateurs
        #    <p data-testid="creators"> <span data-testid="creators-category">Mixtape Street</span> de <a href="/contact/...">Artiste</a> … </p>
        try:
            creators = page.locator("[data-testid='creators']").first
            if creators.count() > 0:
                # On récupère *uniquement* les liens artistes à l'intérieur de ce bloc
                links = creators.locator("a[href^='/contact/'], a[href^='/artiste/']")
                for i in range(links.count()):
                    name = clean(links.nth(i).text_content())
                    if name and name not in artists:
                        artists.append(name)
        except Exception:
            pass

        # 2) Fallback : si le bloc creators n'est pas présent, on tente le conteneur qui porte juste la catégorie
        if not artists:
            try:
                cat = page.locator("[data-testid='creators-category']").first
                if cat.count() > 0:
                    # On remonte au parent le plus proche contenant aussi les liens
                    parent = cat.locator("xpath=ancestor::*[self::p or self::div][1]")
                    links = parent.locator("a[href^='/contact/'], a[href^='/artiste/']")
                    for i in range(links.count()):
                        name = clean(links.nth(i).text_content())
                        if name and name not in artists:
                            artists.append(name)
            except Exception:
                pass

        # 3) Fallback texte : ancienne heuristique “Album de …”
        if not artists:
            try:
                node = page.locator("xpath=//*[contains(normalize-space(.), 'Album de')]").first
                if node.count() > 0:
                    links = node.locator("a[href^='/contact/'], a[href^='/artiste/']")
                    for i in range(links.count()):
                        name = clean(links.nth(i).text_content())
                        if name and name not in artists:
                            artists.append(name)
            except Exception:
                pass

        # 4) Fallback ultime : regex sur tout le body
        if not artists:
            try:
                body_txt = page.locator("body").inner_text()
                m = re.search(r"Album de\s+([^\n]+)", body_txt, flags=re.IGNORECASE)
                if m:
                    raw = clean(m.group(1))
                    parts = re.split(r"\s*(?:,|&| et |/|•|\|)\s*", raw, flags=re.IGNORECASE)
                    for name in parts:
                        name = clean(name.strip(" .•|"))
                        if name and name.lower() not in ("various artists",):
                            if name not in artists:
                                artists.append(name)
            except Exception:
                pass

        return artists

    def extract_labels_from_page(page) -> list:
        import re
        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "")).strip()

        labels = []

        # 1) Les labels sont listés dans le bloc qui contient "Labels"
        try:
            # On cible précisément la ligne/zone "Labels :" pour éviter toute confusion
            node = page.locator("xpath=//*[contains(normalize-space(.), 'Labels')]").first
            if node.count() > 0:
                # Les labels sont aussi en /contact/ sur SensCritique
                links = node.locator("a[href^='/contact/']")
                for i in range(links.count()):
                    name = clean(links.nth(i).text_content())
                    if name and name not in labels:
                        labels.append(name)

                # Fallback si pas de liens cliquables : parse le texte après "Labels"
                if not labels:
                    txt = clean(node.inner_text())
                    # Ex: "Labels : Capitol Records, Top Dawg Entertainment"
                    m = re.search(r"Labels?\s*[:：]\s*(.+)$", txt, flags=re.IGNORECASE)
                    if m:
                        raw = m.group(1)
                        parts = re.split(r"\s*,\s*", raw)
                        for name in parts:
                            name = clean(name.strip(" .•|"))
                            if name and name not in labels:
                                labels.append(name)
        except Exception:
            pass

        return labels
    

    # --- navigation ---
    try:
        page.goto(album_url, wait_until="domcontentloaded")
    except Exception as e:
        try:
            log(f"❌ Erreur navigation {album_url}: {e}")
        except NameError:
            print(f"[parse_album_page] Erreur navigation {album_url}: {e}")
        try:
            safe_screenshot(page, screenshot_dir, "nav_error")
        except Exception:
            pass
        return {"album_title": "", "artist": ""}

    # --- titre album ---
    title = ""
    try:
        # Essai accessible (ARIA) puis h1 générique
        try:
            title = clean(page.get_by_role("heading", level=1).first.text_content())
        except Exception:
            title = clean(page.locator("h1").first.text_content())
    except Exception:
        title = ""

    # Fallback og:title (souvent "Titre - Artiste")
    if not title:
        try:
            og_title = page.locator('meta[property="og:title"]').get_attribute("content") or ""
            og_title = clean(og_title)
            for sep in (" - ", " – "):
                if sep in og_title:
                    title = og_title.split(sep, 1)[0].strip()
                    break
            if not title:
                title = og_title
        except Exception:
            pass

    # --- artistes ---
    artists_list = extract_artists_from_page(page)
    artist = ", ".join(artists_list)
    # --- labels ---
    labels_list = extract_labels_from_page(page)
    labels = ", ".join(labels_list)

    # debug si incomplet
    if (not title) or (not artist):
        try:
            log(f"⚠️ Infos incomplètes (title='{title}', artist='{artist}') pour {album_url}")
        except NameError:
            print(f"[parse_album_page] Infos incomplètes (title='{title}', artist='{artist}') pour {album_url}")
        try:
            safe_screenshot(page, screenshot_dir, "missing_fields")
        except Exception:
            pass

    return {"album_title": title, "artist": artist, "labels": labels}

def scrape_list(list_url: str, headless: bool, max_scrolls: int, scroll_wait_ms: int,
                nav_timeout_ms: int, screenshot_dir: Path) -> pd.DataFrame:
    with sync_playwright() as p:
        log(f"▶ Démarrage Playwright (headless={headless})")
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # Timeouts par défaut
        page.set_default_timeout(nav_timeout_ms)

        log("▶ Ouverture de la page de liste…")
        try:
            page.goto(list_url, wait_until="domcontentloaded")
        except PWTimeout:
            log("⏱️ Timeout sur la page de liste.")
            safe_screenshot(page, screenshot_dir, "timeout_list")
        except Exception as e:
            log(f"❌ Erreur d’ouverture de la liste: {e}")
            safe_screenshot(page, screenshot_dir, "open_list_error")
            browser.close()
            return pd.DataFrame()

        # Titre de la liste
        list_title = ""
        try:
            list_title = clean_text(page.locator("h1").first.text_content())
            log(f"✔ Titre de la liste détecté : \"{list_title}\"")
        except Exception:
            log("⚠️ Impossible de lire le titre de la liste (h1).")
        year_label = extract_year_from_list_title(list_title)
        if year_label:
            log(f"✔ Année extraite du titre : {year_label}")
        else:
            log("⚠️ Impossible d’extraire l’année depuis le titre — je laisse vide.")

        # Scroll pour charger tous les items
        log(f"▶ Scroll pour charger la liste (max {max_scrolls} passes)…")
        prev_height = 0
        passes = 0
        for _ in range(max_scrolls):
            passes += 1
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(scroll_wait_ms)
                curr_height = page.evaluate("document.body.scrollHeight")
            except Exception as e:
                log(f"⚠️ Erreur pendant le scroll: {e}")
                break
            if curr_height == prev_height:
                break
            prev_height = curr_height
        log(f"✔ Scroll terminé ({passes} passes)")

        log("▶ Détection des liens /album/…")
        anchors = page.locator("a[href^='/album/']")
        count = anchors.count()
        seen = set()
        album_urls = []
        for i in range(count):
            href = anchors.nth(i).get_attribute("href")
            if not is_album_href(href):
                continue
            href = href.split("#")[0]
            if href in seen:
                continue
            seen.add(href)
            album_urls.append(urljoin(list_url, href))
        log(f"✔ {len(album_urls)} liens d’albums uniques trouvés")

        items = []
        for idx, album_url in enumerate(album_urls, start=1):
            log(f"▶ Parsing album {idx}/{len(album_urls)} : {album_url}")
            details = parse_album_page(page, album_url, screenshot_dir)
            log(f"   → Titre=\"{details.get('album_title','')}\" | Artiste=\"{details.get('artist','')}\" | Labels=\"{details.get('labels','')}\"")
            items.append({
                "year_label": year_label,
                "album_title": details.get("album_title", ""),
                "artist": details.get("artist", ""),
                # "labels": details.get("labels", ""),
                "sc_album_url": album_url,
                "position": "",
                "sc_list_url": list_url,
            })

        browser.close()

    df = pd.DataFrame(items, columns=[
        "year_label", "album_title", "artist", "sc_album_url", "position", "sc_list_url"
    ])
    return df

def main():
    parser = argparse.ArgumentParser(description="Scrape une ou plusieurs listes SensCritique (albums).")
    parser.add_argument("input", help="URL d'une liste SensCritique OU chemin d'un fichier contenant plusieurs URLs")
    parser.add_argument("--outdir", default="exports", help="Dossier où enregistrer les CSV")
    parser.add_argument("--headful", action="store_true", help="Ouvrir le navigateur visible (debug)")
    parser.add_argument("--max-scrolls", type=int, default=30, help="Nombre max de passes de scroll")
    parser.add_argument("--scroll-wait", type=int, default=400, help="Attente (ms) entre scrolls")
    parser.add_argument("--nav-timeout", type=int, default=15000, help="Timeout navigation (ms)")
    parser.add_argument("--screenshots", default="screenshots", help="Dossier pour les captures d’écran")
    args = parser.parse_args()

    screenshot_dir = Path(args.screenshots)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- lecture du fichier ou URL unique ---
    if Path(args.input).exists():
        with open(args.input, "r", encoding="utf-8") as f:
            list_urls = [l.strip() for l in f.readlines() if l.strip()]
        log(f"✔ {len(list_urls)} liens lus depuis {args.input}")
    else:
        list_urls = [args.input]

    for list_url in list_urls:
        log(f"▶ Traitement de la liste : {list_url}")
        try:
            df = scrape_list(
                list_url=list_url,
                headless=not args.headful,
                max_scrolls=args.max_scrolls,
                scroll_wait_ms=args.scroll_wait,
                nav_timeout_ms=args.nav_timeout,
                screenshot_dir=screenshot_dir,
            )

            if df.empty:
                log(f"⚠️ Aucun album trouvé pour {list_url}")
                continue

            # --- nom de fichier auto ---
            list_title = clean_text(df['sc_list_url'].iloc[0].split('/')[-2]) if 'sc_list_url' in df else 'liste'
            year_label = df['year_label'].iloc[0] if 'year_label' in df else ''
            base_name = f"albums_{year_label or list_title}.csv".replace("/", "-").replace("–", "-")
            out_path = out_dir / base_name

            df.to_csv(out_path, index=False, encoding="utf-8")
            log(f"✔ Export CSV : {out_path} ({len(df)} lignes)")

        except KeyboardInterrupt:
            log("⛔ Interrompu par l’utilisateur.")
            sys.exit(1)
        except Exception as e:
            log(f"❌ Erreur inattendue sur {list_url}: {e}")

    log("🎉 Toutes les listes ont été traitées.")

if __name__ == "__main__":
    main()
