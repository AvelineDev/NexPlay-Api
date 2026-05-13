from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

BASE = "https://anichin.club"
MAL  = "https://myanimelist.net"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Referer": BASE,
}

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        log.error(f"fetch error {url}: {e}")
        return None

def fetch_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error(f"fetch_json error {url}: {e}")
        return None

def err(msg, code=500):
    return jsonify({"error": msg}), code

# ─── ANICHIN ENDPOINTS ──────────────────────────────────────────

@app.route("/api/anime/anichin/home")
def anichin_home():
    try:
        soup = fetch(BASE + "/")
        if not soup:
            return err("Gagal fetch home")

        # Featured slider
        slider = []
        for item in soup.select(".bixbox.bbnofrm .listupd article, .postbody .bixbox article")[:10]:
            a = item.select_one("a")
            img = item.select_one("img")
            title = item.select_one(".tt, h2, h3")
            genre = item.select_one(".typez, .type")
            if not a:
                continue
            slider.append({
                "slug": a.get("href", "").rstrip("/").split("/")[-1],
                "title": title.text.strip() if title else "",
                "thumbnail": img.get("src", img.get("data-src", "")) if img else "",
                "type": genre.text.strip() if genre else "donghua",
                "url": a.get("href", ""),
            })

        # Latest anime
        latest = []
        for item in soup.select(".listupd article, .utao article")[:20]:
            a = item.select_one("a")
            img = item.select_one("img")
            title = item.select_one(".tt, h2, h3, .lchx")
            ep = item.select_one(".ep, .epx")
            if not a:
                continue
            latest.append({
                "slug": a.get("href", "").rstrip("/").split("/")[-1],
                "title": title.text.strip() if title else "",
                "thumbnail": img.get("src", img.get("data-src", "")) if img else "",
                "episode": ep.text.strip() if ep else "",
                "url": a.get("href", ""),
            })

        return jsonify({
            "result": {
                "featuredSlider": slider or latest[:8],
                "latestAnime": latest,
            }
        })
    except Exception as e:
        log.error(f"home error: {e}")
        return err(str(e))


@app.route("/api/anime/anichin/schedule")
def anichin_schedule():
    try:
        soup = fetch(BASE + "/jadwal-rilis/")
        if not soup:
            return err("Gagal fetch jadwal")

        days = {}
        day_map = {
            "senin": "Monday", "selasa": "Tuesday", "rabu": "Wednesday",
            "kamis": "Thursday", "jumat": "Friday", "sabtu": "Saturday",
            "minggu": "Sunday"
        }

        for section in soup.select(".bixbox, .soralist"):
            heading = section.select_one("h3, h2, .releases h3")
            if not heading:
                continue
            day_id = heading.text.strip().lower()
            day_en = day_map.get(day_id, day_id.capitalize())
            items = []
            for li in section.select("li, article"):
                a = li.select_one("a")
                img = li.select_one("img")
                title = li.select_one(".tt, h2, span")
                ep = li.select_one(".ep, .epx")
                if not a:
                    continue
                items.append({
                    "slug": a.get("href", "").rstrip("/").split("/")[-1],
                    "title": title.text.strip() if title else a.text.strip(),
                    "thumbnail": img.get("src", img.get("data-src", "")) if img else "",
                    "episode": ep.text.strip() if ep else "",
                    "url": a.get("href", ""),
                })
            if items:
                days[day_en] = items

        return jsonify({"result": days})
    except Exception as e:
        log.error(f"schedule error: {e}")
        return err(str(e))


@app.route("/api/anime/anichin/search")
def anichin_search():
    q = request.args.get("q", "")
    if not q:
        return err("Query diperlukan", 400)
    try:
        soup = fetch(f"{BASE}/?s={requests.utils.quote(q)}")
        if not soup:
            return err("Gagal fetch search")

        results = []
        for item in soup.select(".listupd article, article.bs"):
            a = item.select_one("a")
            img = item.select_one("img")
            title = item.select_one(".tt, h2, h3")
            genre = item.select_one(".typez, .type, .bt span")
            score = item.select_one(".numscore, .rating")
            if not a:
                continue
            results.append({
                "slug": a.get("href", "").rstrip("/").split("/")[-1],
                "title": title.text.strip() if title else "",
                "thumbnail": img.get("src", img.get("data-src", "")) if img else "",
                "type": genre.text.strip() if genre else "",
                "score": score.text.strip() if score else "",
                "url": a.get("href", ""),
            })

        return jsonify({"result": results, "total": len(results)})
    except Exception as e:
        log.error(f"search error: {e}")
        return err(str(e))


@app.route("/api/anime/anichin/detail")
def anichin_detail():
    url_param = request.args.get("url", "")
    if not url_param:
        return err("URL diperlukan", 400)
    try:
        full_url = BASE + url_param if url_param.startswith("/") else url_param
        soup = fetch(full_url)
        if not soup:
            return err("Gagal fetch detail")

        title = soup.select_one(".entry-title, h1.entry-title")
        thumb = soup.select_one(".thumb img, .bigcontent img")
        synopsis = soup.select_one(".entry-content, .synp p, [itemprop='description']")
        score = soup.select_one(".num, .rating strong, [itemprop='ratingValue']")
        status = None
        genre_list = []
        episodes = []

        for info in soup.select(".spe span, .info-left span"):
            text = info.text.strip()
            if "Status" in text:
                s = info.select_one("a")
                status = s.text.strip() if s else text.replace("Status:", "").strip()
            if "Genre" in text or info.select_one("a[href*='genre']"):
                for g in info.select("a"):
                    genre_list.append(g.text.strip())

        for ep in soup.select("#episode_by_pagination li a, .eplister li a, .epsleft li a")[:50]:
            ep_title = ep.select_one(".epl-title, span")
            ep_num = ep.select_one(".epl-num")
            episodes.append({
                "title": ep_title.text.strip() if ep_title else ep.text.strip(),
                "episode": ep_num.text.strip() if ep_num else "",
                "url": ep.get("href", ""),
                "slug": ep.get("href", "").rstrip("/").split("/")[-1],
            })

        return jsonify({
            "result": {
                "title": title.text.strip() if title else "",
                "thumbnail": thumb.get("src", thumb.get("data-src", "")) if thumb else "",
                "synopsis": synopsis.text.strip() if synopsis else "",
                "score": score.text.strip() if score else "",
                "status": status or "",
                "genres": genre_list,
                "episodes": episodes,
                "url": full_url,
            }
        })
    except Exception as e:
        log.error(f"detail error: {e}")
        return err(str(e))


@app.route("/api/anime/anichin/stream")
def anichin_stream():
    url_param = request.args.get("url", "")
    if not url_param:
        return err("URL diperlukan", 400)
    try:
        full_url = BASE + "/" + url_param.lstrip("/") if not url_param.startswith("http") else url_param
        soup = fetch(full_url)
        if not soup:
            return err("Gagal fetch stream")

        sources = []

        # Iframe sources
        for iframe in soup.select("iframe[src], iframe[data-src]"):
            src = iframe.get("src") or iframe.get("data-src", "")
            if src and "javascript" not in src:
                sources.append({"type": "iframe", "url": src, "label": "Stream"})

        # Mirror links
        for a in soup.select(".mirrorlist a, .listserver a, .mirror a"):
            sources.append({
                "type": "mirror",
                "url": a.get("href", a.get("data-src", "")),
                "label": a.text.strip() or "Mirror",
            })

        # Script-based sources
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string:
                urls = re.findall(r'(?:file|src|source)\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', script.string)
                for u in urls:
                    sources.append({"type": "m3u8", "url": u, "label": "HLS"})

        ep_title = soup.select_one(".entry-title, h1")
        nav_prev = soup.select_one(".naveps .next a, [rel='prev'] a")
        nav_next = soup.select_one(".naveps .prev a, [rel='next'] a")

        return jsonify({
            "result": {
                "title": ep_title.text.strip() if ep_title else "",
                "sources": sources,
                "prev": nav_prev.get("href", "") if nav_prev else "",
                "next": nav_next.get("href", "") if nav_next else "",
            }
        })
    except Exception as e:
        log.error(f"stream error: {e}")
        return err(str(e))


# ─── MAL ENDPOINTS ──────────────────────────────────────────────

def parse_mal_card(item):
    title = item.select_one("h3.hb, .title strong, .title h3")
    img = item.select_one("img")
    score = item.select_one(".scormem span, .score")
    link = item.select_one("a.hoverinfo_trigger, a[href*='/anime/']")
    mal_id = None
    if link:
        m = re.search(r'/anime/(\d+)', link.get("href", ""))
        if m:
            mal_id = m.group(1)
    return {
        "malId": mal_id,
        "title": title.text.strip() if title else "",
        "thumbnail": img.get("data-src", img.get("src", "")) if img else "",
        "score": score.text.strip() if score else "",
        "url": link.get("href", "") if link else "",
    }


@app.route("/api/anime/mal/popular")
def mal_popular():
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * 50
    try:
        soup = fetch(f"{MAL}/topanime.php?limit={offset}")
        if not soup:
            return err("Gagal fetch MAL popular")
        items = []
        for row in soup.select("tr.ranking-list"):
            title = row.select_one(".title .di-ib h3, h3.hb")
            img = row.select_one("img")
            score = row.select_one(".score-label")
            link = row.select_one("a[href*='/anime/']")
            mal_id = None
            if link:
                m = re.search(r'/anime/(\d+)', link.get("href", ""))
                if m:
                    mal_id = m.group(1)
            if title:
                items.append({
                    "malId": mal_id,
                    "title": title.text.strip(),
                    "thumbnail": img.get("data-src", img.get("src", "")) if img else "",
                    "score": score.text.strip() if score else "",
                    "url": link.get("href", "") if link else "",
                })
        return jsonify({"data": items, "total": len(items)})
    except Exception as e:
        log.error(f"mal popular error: {e}")
        return err(str(e))


@app.route("/api/anime/mal/ongoing")
def mal_ongoing():
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * 50
    try:
        soup = fetch(f"{MAL}/anime/season?limit={offset}")
        if not soup:
            # Fallback to top airing
            soup = fetch(f"{MAL}/topanime.php?type=airing&limit={offset}")
        if not soup:
            return err("Gagal fetch MAL ongoing")
        items = []
        for row in soup.select("tr.ranking-list, .seasonal-anime"):
            title = row.select_one(".title .di-ib h3, h3.title, h2.h2_anime_title")
            img = row.select_one("img")
            score = row.select_one(".score-label, .score")
            link = row.select_one("a[href*='/anime/']")
            mal_id = None
            if link:
                m = re.search(r'/anime/(\d+)', link.get("href", ""))
                if m:
                    mal_id = m.group(1)
            if title:
                items.append({
                    "malId": mal_id,
                    "title": title.text.strip(),
                    "thumbnail": img.get("data-src", img.get("src", "")) if img else "",
                    "score": score.text.strip() if score else "",
                    "url": link.get("href", "") if link else "",
                })
        return jsonify({"data": items, "total": len(items)})
    except Exception as e:
        log.error(f"mal ongoing error: {e}")
        return err(str(e))


@app.route("/api/anime/mal/genre")
def mal_genre():
    genre_id = request.args.get("genreId", "1")
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * 50
    try:
        soup = fetch(f"{MAL}/anime/genre/{genre_id}?limit={offset}")
        if not soup:
            return err("Gagal fetch MAL genre")
        items = []
        for item in soup.select(".js-anime-category-producer, .seasonal-anime, tr.ranking-list"):
            title = item.select_one("h2.h2_anime_title a, h3.hb, .di-ib h3")
            img = item.select_one("img")
            score = item.select_one(".score, .score-label")
            link = item.select_one("a[href*='/anime/']")
            mal_id = None
            if link:
                m = re.search(r'/anime/(\d+)', link.get("href", ""))
                if m:
                    mal_id = m.group(1)
            if title:
                items.append({
                    "malId": mal_id,
                    "title": title.text.strip(),
                    "thumbnail": img.get("data-src", img.get("src", "")) if img else "",
                    "score": score.text.strip() if score else "",
                    "url": link.get("href", "") if link else "",
                })
        return jsonify({"data": items, "total": len(items)})
    except Exception as e:
        log.error(f"mal genre error: {e}")
        return err(str(e))


@app.route("/api/anime/mal/search")
def mal_search():
    q = request.args.get("q", "")
    if not q:
        return err("Query diperlukan", 400)
    try:
        data = fetch_json(f"https://api.jikan.moe/v4/anime?q={requests.utils.quote(q)}&limit=20")
        if data and "data" in data:
            items = [{
                "malId": str(a.get("mal_id", "")),
                "title": a.get("title", ""),
                "thumbnail": a.get("images", {}).get("jpg", {}).get("image_url", ""),
                "score": str(a.get("score", "")),
                "url": a.get("url", ""),
                "type": a.get("type", ""),
            } for a in data["data"]]
            return jsonify({"data": items, "total": len(items)})
        return err("Tidak ada hasil")
    except Exception as e:
        log.error(f"mal search error: {e}")
        return err(str(e))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "NexPlay API"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
