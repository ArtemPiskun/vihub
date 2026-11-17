#!/usr/bin/env python3
"""Автоимпорт новостей и YouTube-трендов о GTA 6. Только stdlib.

Пишет:
  content/news.ingest.json   — новости из RSS и YouTube RSS (дописывает, дедуп по url)
  content/trending.json      — топ видео (только если задан YOUTUBE_API_KEY
                               и бот мониторинга не положил свой файл свежее 2 часов)
  content/channels.json      — рейтинг блогеров (то же условие)

Переменные окружения (все необязательные):
  YOUTUBE_API_KEY     — статистика просмотров для трендов и рейтинга
  ANTHROPIC_API_KEY   — перевод/пересказ заголовков на русский
  EXTERNAL_NEWS_URL   — JSON-лента бота в формате news.json
"""
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
CFG = json.load(open(os.path.join(ROOT, "config", "sources.json"), encoding="utf-8"))
NOW = dt.datetime.now(dt.timezone.utc)
UA = {"User-Agent": "Mozilla/5.0 (compatible; news-aggregator/1.0)"}
KEYWORDS = [k.lower() for k in CFG.get("keywords", [])]
LEAK_WORDS = ["leak", "rumor", "rumour", "insider", "утечк", "слух", "инсайд"]
UPDATE_WORDS = ["patch", "update", "hotfix", "патч", "обновлен"]
GUIDE_WORDS = ["guide", "how to", "walkthrough", "tips", "гайд", "как ", "прохожд", "советы"]


def log(*a):
    print(*a, file=sys.stderr)


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", unescape(s)).strip()


def parse_date(s):
    if not s:
        return NOW
    from email.utils import parsedate_to_datetime
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return NOW
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def relevant(text):
    t = text.lower()
    return any(k in t for k in KEYWORDS)


def classify(text, default="news"):
    t = text.lower()
    if any(w in t for w in LEAK_WORDS):
        return "leak"
    if any(w in t for w in UPDATE_WORDS):
        return "update"
    if any(w in t for w in GUIDE_WORDS):
        return "guide"
    return default


def score(weight, published, bonus=0):
    age_h = max(0.0, (NOW - published).total_seconds() / 3600)
    fresh = max(0.0, 1 - age_h / 72)  # линейно гаснет за 3 суток
    return round(min(100, 100 * (0.55 * weight + 0.45 * fresh) + bonus))


def make_item(title, url, summary, source, stype, published, weight, image="", cat=None):
    if re.sub(r"\W+", "", summary.lower()).startswith(re.sub(r"\W+", "", title.lower())[:40]):
        summary = ""
    text = f"{title} {summary}"
    c = cat or classify(text)
    return {
        "id": hashlib.sha1(url.encode()).hexdigest(),
        "title": title.strip()[:200],
        "summary": summary.strip()[:300],
        "url": url,
        "source": source,
        "source_type": "leak" if c == "leak" and stype != "official" else stype,
        "category": c,
        "published": published.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image": image,
        "tags": [],
        "score": score(weight, published, 10 if stype == "official" else 0),
        "verified": stype == "official" or c != "leak",
    }


def parse_feed(raw):
    """RSS 2.0 и Atom -> список dict(title, link, summary, date, image)."""
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/",
          "yt": "http://www.youtube.com/xml/schemas/2015"}
    out = []
    for it in root.iter("item"):
        img = ""
        enc = it.find("enclosure")
        if enc is not None and "image" in (enc.get("type") or ""):
            img = enc.get("url", "")
        mt = it.find("media:content", ns)
        if mt is None:
            mt = it.find("media:thumbnail", ns)
        if not img and mt is not None:
            img = mt.get("url", "")
        out.append({"title": strip_html(it.findtext("title")), "link": (it.findtext("link") or "").strip(),
                    "summary": strip_html(it.findtext("description")), "date": it.findtext("pubDate"), "image": img})
    for en in root.findall("a:entry", ns):
        link = en.find("a:link", ns)
        vid = en.findtext("yt:videoId", default="", namespaces=ns)
        th = en.find(".//media:thumbnail", ns)
        desc = en.findtext(".//media:description", default="", namespaces=ns) or en.findtext("a:summary", default="", namespaces=ns)
        out.append({"title": strip_html(en.findtext("a:title", default="", namespaces=ns)),
                    "link": link.get("href") if link is not None else "",
                    "summary": strip_html(desc)[:300], "date": en.findtext("a:published", default="", namespaces=ns),
                    "image": th.get("url") if th is not None else "", "video_id": vid})
    return out


def ingest_feeds():
    items = []
    for f in CFG.get("feeds", []):
        try:
            entries = parse_feed(fetch(f["url"]))
        except Exception as ex:  # noqa: BLE001 — одна упавшая лента не должна ронять прогон
            log(f"! feed {f['name']}: {ex}")
            continue
        n = 0
        for x in entries:
            if not x["title"] or not x["link"]:
                continue
            if f.get("filter") and not relevant(x["title"] + " " + x["summary"]):
                continue
            pub = parse_date(x["date"])
            if (NOW - pub).days > 14:
                continue
            src = f["name"]
            title = x["title"]
            m = re.match(r"^(.*) - ([^-]{2,40})$", title)  # Google News: "Заголовок - Издание"
            if "news.google" in f["url"] and m:
                title, src = m.group(1), m.group(2)
            items.append(make_item(title, x["link"], x["summary"], src, f.get("type", "media"), pub,
                                   f.get("weight", 0.5), x.get("image", "")))
            n += 1
        log(f"  {f['name']}: {n}")
    return items


def ingest_youtube_rss():
    items, videos = [], []
    for ch in CFG.get("youtube_channels", []):
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['channel_id']}"
        try:
            entries = parse_feed(fetch(url))
        except Exception as ex:  # noqa: BLE001
            log(f"! yt {ch['name']}: {ex}")
            continue
        for x in entries:
            pub = parse_date(x["date"])
            if (NOW - pub).days > 7 or not relevant(x["title"] + " " + x["summary"]):
                continue
            stype = "official" if ch.get("official") else "youtube"
            items.append(make_item(x["title"], x["link"], x["summary"][:200], ch["name"], stype, pub,
                                   ch.get("weight", 0.6), x.get("image", ""), cat="video"))
            videos.append({"video_id": x.get("video_id"), "title": x["title"], "channel_id": ch["channel_id"],
                           "channel_title": ch["name"], "url": x["link"], "thumbnail": x.get("image", ""),
                           "published": pub.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return items, videos


def youtube_stats(videos):
    """Добавляет views/vph/score через YouTube Data API и возвращает (trending, channels)."""
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key or not videos:
        return None, None
    ids = [v["video_id"] for v in videos if v.get("video_id")]
    stats = {}
    for i in range(0, len(ids), 50):
        q = urllib.parse.urlencode({"part": "statistics", "id": ",".join(ids[i:i + 50]), "key": key})
        try:
            data = json.loads(fetch(f"https://www.googleapis.com/youtube/v3/videos?{q}"))
        except Exception as ex:  # noqa: BLE001
            log(f"! yt api: {ex}")
            return None, None
        for it in data.get("items", []):
            stats[it["id"]] = int(it["statistics"].get("viewCount", 0))
    for v in videos:
        views = stats.get(v.get("video_id"), 0)
        age_h = max(1.0, (NOW - dt.datetime.fromisoformat(v["published"].replace("Z", "+00:00"))).total_seconds() / 3600)
        v["views"], v["vph"] = views, round(views / age_h)
    top = max([v["vph"] for v in videos] + [1])
    for v in videos:
        v["score"] = round(100 * v["vph"] / top)
    trending = sorted(videos, key=lambda v: v["vph"], reverse=True)[:60]
    chans = {}
    for v in videos:
        age_h = (NOW - dt.datetime.fromisoformat(v["published"].replace("Z", "+00:00"))).total_seconds() / 3600
        c = chans.setdefault(v["channel_id"], {"channel_id": v["channel_id"], "title": v["channel_title"],
                                               "videos_24h": 0, "total_vph": 0, "best_video_url": "", "_best": -1})
        if age_h <= 24:
            c["videos_24h"] += 1
        c["total_vph"] += v["vph"]
        if v["vph"] > c["_best"]:
            c["_best"], c["best_video_url"] = v["vph"], v["url"]
    top_c = max([c["total_vph"] for c in chans.values()] + [1])
    out = []
    for c in chans.values():
        c.pop("_best")
        c["score"] = round(100 * c["total_vph"] / top_c * (1 + 0.05 * min(c["videos_24h"], 4)) / 1.2)
        out.append(c)
    return trending, sorted(out, key=lambda c: c["score"], reverse=True)


def ingest_external():
    url = os.environ.get("EXTERNAL_NEWS_URL") or next((x.get("url") for x in CFG.get("external_json", []) if x.get("url")), "")
    if not url:
        return []
    try:
        data = json.loads(fetch(url))
        return [d for d in data if isinstance(d, dict) and d.get("title") and d.get("url")]
    except Exception as ex:  # noqa: BLE001
        log(f"! external: {ex}")
        return []


def claude_json(prompt, tag):
    """Запрос к Claude API, возвращает JSON-массив из ответа или None (с понятной ошибкой в логе)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    body = json.dumps({"model": os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5"), "max_tokens": 6000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    text = ""
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            raise ValueError(f"нет JSON-массива, stop={resp.get('stop_reason')}, ответ: {text[:200]!r}")
        return json.loads(m.group(0))
    except urllib.error.HTTPError as ex:
        log(f"! {tag}: HTTP {ex.code} {ex.read()[:300]!r}")
    except Exception as ex:  # noqa: BLE001
        log(f"! {tag}: {ex}")
    return None


def _batches(todo, size=10):
    for n in range(0, len(todo), size):
        yield todo[n:n + size]


def translate(items, limit=40):
    """Переводит не-русские заголовки на русский через Claude API (если задан ключ)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return
    todo = [i for i in items if not re.search("[а-яА-ЯёЁ]", i["title"]) and not i.get("_tr")][:limit]
    done = 0
    for batch in _batches(todo):
        payload = [{"i": n, "title": i["title"], "summary": i["summary"][:300]} for n, i in enumerate(batch)]
        prompt = ("Переведи на русский заголовки и краткие описания новостей о GTA 6 для игрового портала. "
                  "Заголовок до 110 символов, живой, без кликбейта и без выдуманных фактов; описание 1-2 предложения. "
                  "Названия оставь как принято у русскоязычных игроков (Леонида, Вайс-Сити, Лусия, Джейсон). "
                  "Ответь только JSON-массивом [{\"i\":..,\"title\":..,\"summary\":..}] без пояснений.\n\n"
                  + json.dumps(payload, ensure_ascii=False))
        arr = claude_json(prompt, "translate")
        if arr is None:
            break
        for t in arr:
            try:
                it = batch[int(t["i"])]
            except (KeyError, ValueError, IndexError, TypeError):
                continue
            it["title_orig"], it["summary_orig"] = it["title"], it["summary"]
            it["title"], it["summary"], it["_tr"] = t.get("title") or it["title"], t.get("summary") or it["summary"], True
            done += 1
    log(f"  translate ru: {done}/{len(todo)}")


def translate_uk(items, limit=40):
    """Украинские заголовки для /uk/ (title_uk, summary_uk) через Claude API, если задан ключ."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return
    todo = [i for i in items if not i.get("title_uk")][:limit]
    done = 0
    for batch in _batches(todo):
        payload = [{"i": n, "title": i.get("title_orig") or i["title"],
                    "summary": (i.get("summary_orig") or i["summary"])[:300]} for n, i in enumerate(batch)]
        prompt = ("Переклади українською заголовки й короткі описи новин про GTA 6 для ігрового порталу. "
                  "Заголовок до 110 символів, без клікбейту й вигаданих фактів; опис 1-2 речення. "
                  "Назви: Леоніда, Вайс-Сіті, Лусія, Джейсон. Відповідай лише JSON-масивом "
                  "[{\"i\":..,\"title\":..,\"summary\":..}] без пояснень.\n\n"
                  + json.dumps(payload, ensure_ascii=False))
        arr = claude_json(prompt, "translate_uk")
        if arr is None:
            break
        for t in arr:
            try:
                it = batch[int(t["i"])]
            except (KeyError, ValueError, IndexError, TypeError):
                continue
            it["title_uk"], it["summary_uk"] = t.get("title") or "", t.get("summary") or ""
            done += 1
    log(f"  translate uk: {done}/{len(todo)}")


OG_RE = re.compile(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\'][^>]*content=["\']([^"\']+)', re.I)
OG_RE2 = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\'](?:og:image|twitter:image)["\']', re.I)


BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "text/html"}


def enrich_images(items, limit=40):
    """Берёт og:image со страницы статьи для новостей без картинки."""
    n = 0
    for it in items:
        if n >= limit:
            break
        if it.get("image") or it.get("_noimg") or "news.google.com" in it.get("url", ""):
            continue
        n += 1
        try:
            req = urllib.request.Request(it["url"], headers=BROWSER_UA)
            with urllib.request.urlopen(req, timeout=8) as r:
                page = r.read(300_000).decode("utf-8", "ignore")
            m = OG_RE.search(page) or OG_RE2.search(page)
            if m and m.group(1).startswith("http"):
                it["image"] = unescape(m.group(1))
            else:
                it["_noimg"] = True
        except Exception:  # noqa: BLE001
            it["_noimg"] = True


def file_age_h(name):
    p = os.path.join(CONTENT, name)
    if not os.path.exists(p):
        return 1e9
    return (NOW.timestamp() - os.path.getmtime(p)) / 3600


def main():
    path = os.path.join(CONTENT, "news.ingest.json")
    old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    log("feeds:")
    new = ingest_feeds()
    yt_items, videos = ingest_youtube_rss()
    new += yt_items + ingest_external()

    by_url = {i["url"]: i for i in old}
    for it in new:
        prev = by_url.get(it["url"])
        if prev:  # сохраняем перевод и обновляем только score
            prev["score"] = it.get("score", prev.get("score"))
        else:
            by_url[it["url"]] = it
    merged = [i for i in by_url.values() if (NOW - parse_date(i.get("published"))).days <= 30]
    # одна и та же статья из Google News и из RSS издания: оставляем прямую ссылку (с картинкой)
    key = lambda i: re.sub(r"\W+", "", re.sub(r"\s+[-–|]\s+[^-–|]+$", "", i.get("title_orig") or i["title"]).lower())[:60]
    direct = {key(i) for i in merged if "news.google.com" not in i["url"]}
    merged = [i for i in merged if "news.google.com" not in i["url"] or key(i) not in direct]
    enrich_images(merged)
    translate(merged)
    translate_uk(merged)
    merged.sort(key=lambda i: i.get("published", ""), reverse=True)
    merged = merged[:300]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
    log(f"news.ingest.json: {len(merged)} (+{len(new)} fetched)")

    # тренды/рейтинг: не перетираем свежие файлы бота мониторинга
    if file_age_h("trending.json") > 2 or os.environ.get("FORCE_YT"):
        trending, channels = youtube_stats(videos)
        if trending is not None:
            json.dump(trending, open(os.path.join(CONTENT, "trending.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            json.dump(channels, open(os.path.join(CONTENT, "channels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            log(f"trending: {len(trending)}, channels: {len(channels)}")


if __name__ == "__main__":
    main()
