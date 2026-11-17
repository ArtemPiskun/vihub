#!/usr/bin/env python3
"""Статический генератор сайта VI HUB (GTA 6). Только stdlib. Двуязычный: RU в корне, EN в /en/.

Читает content/*.json и content/guides/**/*.md, пишет готовый сайт в dist/.
Запуск: python3 scripts/build.py [--base-url https://example.com]
"""
import argparse
import datetime as dt
import glob
import hashlib
import html
import json
import os
import re
import shutil
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
DIST = os.path.join(ROOT, "dist")

SITE_NAME = "VI HUB"
TELEGRAM_URL = os.environ.get("TELEGRAM_URL") or "https://t.me/PIR_LIFE"
YOUTUBE_URL = os.environ.get("YOUTUBE_URL", "")
LANGS = ["ru", "en", "uk"]
PREFIX = {"ru": "", "en": "en/", "uk": "uk/"}
LOCALE = {"ru": "ru_RU", "en": "en_US", "uk": "uk_UA"}
LANG_LABEL = {"ru": "RU", "en": "EN", "uk": "UA"}

T = {
    "ru": {
        "home": "Главная", "news": "Новости", "guides": "Гайды", "videos": "Видео", "creators": "Рейтинг",
        "game": "Об игре", "tags": "Теги", "all_news": "Все новости →", "all_guides": "Все гайды →",
        "all_videos": "Все видео →", "rating": "Рейтинг →", "about": "Всё об игре →",
        "home_title": "GTA 6: дата выхода, новости, гайды и время релиза",
        "home_desc": "GTA 6 выходит 19 ноября 2026. Точное время разблокировки по регионам, цена, размер, гайды, прохождение и свежие новости Grand Theft Auto VI каждые 15 минут.",
        "hero_eyebrow": "Grand Theft Auto VI · 19 ноября 2026",
        "hero_h1": "GTA 6: всё о <span class=\"grad\">Леониде</span> в одном месте",
        "hero_lead": "GTA 6 выходит 19 ноября 2026 на PS5 и Xbox Series X|S. Здесь время разблокировки, цены, гайды, прохождение и самые горячие видео, обновление каждые 15 минут.",
        "cta_main": "Чек-лист к релизу", "cta_tg": "Наш Telegram",
        "now": "Главное сейчас", "unlock": "Когда откроется игра", "top_creators": "Топ блогеров за 24ч",
        "hot_videos": "Что стреляет на YouTube", "guides_start": "Гайды и старт", "more_news": "Ещё новости",
        "faq": "Частые вопросы", "regions": "Регионы Леониды", "characters": "Персонажи", "timeline": "Хронология",
        "unlock_times": "Время разблокировки", "map_guide": "Гайд по карте →", "more": "Подробнее →",
        "cd_label": "До релиза на PS5 и Xbox Series X|S", "cd_done": "GTA 6 уже вышла. Время играть.",
        "cd_units": ["дней", "часов", "минут", "секунд"],
        "tg_h": "Новости GTA 6 в Telegram", "tg_p": "Утечки, патчи, гайды и лучшие видео раньше всех. Без спама.",
        "subscribe": "Подписаться", "hot": "🔥 Горячее", "unverified": "Не подтверждено",
        "news_h1": "Новости GTA 6", "news_title": "Новости GTA 6 сегодня: патчи, утечки, официальные анонсы",
        "news_desc": "Свежие новости GTA 6 из официальных источников, СМИ, YouTube и сообщества. Лента обновляется автоматически каждые 15 минут, слухи помечены.",
        "news_lead": "Лента собирается автоматически из официальных источников, СМИ, YouTube и сообщества и обновляется каждые 15 минут. Слухи помечены меткой «Не подтверждено».",
        "all": "Все",
        "guides_h1": "Гайды и прохождение GTA 6", "guides_title": "Гайды GTA 6: прохождение, советы, карта и персонажи",
        "guides_desc": "Гайды по GTA 6: как подготовиться к релизу, какое издание купить, карта Леониды, персонажи, советы новичкам и прохождение миссий.",
        "guides_lead": "От подготовки к релизу до полного прохождения. Каждый гайд отвечает на вопрос в первых строках, а после 19 ноября раздел пополняется ежедневно.",
        "videos_h1": "Лучшие видео о GTA 6", "videos_title": "Видео GTA 6: трейлеры, разборы и тренды YouTube",
        "videos_desc": "Самые быстрорастущие видео о GTA 6 на YouTube прямо сейчас: трейлеры, разборы, геймплей. Сортировка по просмотрам в час.",
        "videos_lead": "Видео о GTA 6, которые набирают просмотры быстрее всего прямо сейчас. Мы сортируем ролики по скорости набора просмотров в час, а не по общему числу, поэтому новые разборы попадают наверх в первые часы.",
        "creators_h1": "Рейтинг блогеров GTA 6", "creators_title": "Рейтинг YouTube-блогеров по GTA 6 за 24 часа",
        "creators_desc": "Кто сейчас задаёт тон в теме GTA 6 на YouTube: число роликов за сутки, просмотры в час и итоговый score.",
        "creators_lead": "Рейтинг пересчитывается каждые 15 минут. Score учитывает суммарные просмотры в час по свежим роликам канала и небольшой бонус за регулярность: до четырёх роликов в сутки.",
        "game_h1": "Grand Theft Auto VI: что известно об игре",
        "game_title": "GTA 6: дата выхода, цена, платформы, карта и персонажи",
        "game_desc": "Всё официально известное о GTA 6: дата выхода 19 ноября 2026, цена $79.99, размер до 212 ГБ, карта Леониды, Лусия и Джейсон, хронология анонсов.",
        "game_lead": "GTA 6 выходит 19 ноября 2026 на PS5 и Xbox Series X|S, версия для ПК не анонсирована. Ниже собраны только официально подтверждённые факты.",
        "empty_videos": "Тренды появятся после первого прогона мониторинга YouTube.",
        "empty_creators": "Рейтинг заполнится автоматически после первого прогона мониторинга YouTube.",
        "th": ["#", "Канал", "Видео 24ч", "Просм./ч", "Score", "Лучшее"], "watch": "смотреть",
        "views": "просм.", "per_h": "/ч", "updated": "Обновлено", "other_guides": "Другие гайды",
        "tags_h1": "Теги", "tag_title": "{t}: новости и гайды GTA 6", "tag_desc": "Всё по теме «{t}» в GTA 6: новости, гайды и разборы.",
        "footer": "фанатский портал о Grand Theft Auto VI. Не связан с Rockstar Games и Take-Two.",
        "skip": "К содержанию", "toc": "Содержание", "play_video": "Смотреть видео",
        "ago": ["мин назад", "ч назад", "дн назад"],
        "cats": {"news": "Новости", "update": "Обновления", "guide": "Гайды", "video": "Видео", "leak": "Слухи"},
        "src": {"official": "Официально", "media": "СМИ", "youtube": "YouTube", "community": "Сообщество", "leak": "Слухи"},
        "months": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
        "cat_order": ["Старт", "Прохождение", "Мир"],
    },
    "en": {
        "home": "Home", "news": "News", "guides": "Guides", "videos": "Videos", "creators": "Creators",
        "game": "The game", "tags": "Tags", "all_news": "All news →", "all_guides": "All guides →",
        "all_videos": "All videos →", "rating": "Full ranking →", "about": "Everything about the game →",
        "home_title": "GTA 6 Release Time, News, Guides and Countdown",
        "home_desc": "GTA 6 launches November 19, 2026. Exact unlock times by region, price, file size, guides, walkthroughs and Grand Theft Auto VI news updated every 15 minutes.",
        "hero_eyebrow": "Grand Theft Auto VI · November 19, 2026",
        "hero_h1": "GTA 6: everything about <span class=\"grad\">Leonida</span> in one place",
        "hero_lead": "GTA 6 launches November 19, 2026 on PS5 and Xbox Series X|S. Unlock times, prices, guides, walkthroughs and the hottest videos, refreshed every 15 minutes.",
        "cta_main": "Launch checklist", "cta_tg": "Telegram",
        "now": "Top stories", "unlock": "When GTA 6 unlocks", "top_creators": "Top creators, last 24h",
        "hot_videos": "Trending on YouTube", "guides_start": "Guides", "more_news": "More news",
        "faq": "FAQ", "regions": "Regions of Leonida", "characters": "Characters", "timeline": "Timeline",
        "unlock_times": "Unlock times", "map_guide": "Map guide →", "more": "More →",
        "cd_label": "Until launch on PS5 and Xbox Series X|S", "cd_done": "GTA 6 is out. Go play.",
        "cd_units": ["days", "hours", "minutes", "seconds"],
        "tg_h": "GTA 6 news on Telegram", "tg_p": "Leaks, patches, guides and the best videos first. No spam.",
        "subscribe": "Subscribe", "hot": "🔥 Hot", "unverified": "Unconfirmed",
        "news_h1": "GTA 6 News", "news_title": "GTA 6 News Today: Patches, Leaks and Official Updates",
        "news_desc": "Latest GTA 6 news from Rockstar, the press, YouTube and the community. The feed updates every 15 minutes and labels rumors.",
        "news_lead": "The feed pulls from Rockstar, the gaming press, YouTube and the community and updates every 15 minutes. Rumors carry an \"Unconfirmed\" label.",
        "all": "All",
        "guides_h1": "GTA 6 Guides and Walkthrough", "guides_title": "GTA 6 Guides: Walkthrough, Tips, Map and Characters",
        "guides_desc": "GTA 6 guides: launch checklist, which edition to buy, Leonida map, characters, beginner tips and mission walkthroughs.",
        "guides_lead": "From launch prep to a full walkthrough. Every guide answers the question in its first lines, and after November 19 the section grows daily.",
        "videos_h1": "Best GTA 6 Videos Right Now", "videos_title": "GTA 6 Videos: Trailers, Breakdowns and YouTube Trends",
        "videos_desc": "The fastest-growing GTA 6 videos on YouTube right now: trailers, breakdowns and gameplay, ranked by views per hour.",
        "videos_lead": "GTA 6 videos gaining views fastest right now. We rank by views per hour rather than total views, so fresh breakdowns reach the top within hours.",
        "creators_h1": "Top GTA 6 YouTubers", "creators_title": "Top GTA 6 YouTube Creators in the Last 24 Hours",
        "creators_desc": "Who leads GTA 6 on YouTube right now: uploads in 24 hours, views per hour and an overall score.",
        "creators_lead": "The ranking refreshes every 15 minutes. Score combines views per hour across a channel's recent uploads with a small consistency bonus for up to four uploads a day.",
        "game_h1": "Grand Theft Auto VI: what we know",
        "game_title": "GTA 6 Release Date, Price, Platforms, Map and Characters",
        "game_desc": "Everything confirmed about GTA 6: November 19, 2026 release, $79.99 price, up to 212 GB, the Leonida map, Lucia and Jason, and the full announcement timeline.",
        "game_lead": "GTA 6 launches November 19, 2026 on PS5 and Xbox Series X|S, with no PC version announced. Everything below is officially confirmed.",
        "empty_videos": "Trending videos appear after the first YouTube monitoring run.",
        "empty_creators": "The ranking fills in automatically after the first YouTube monitoring run.",
        "th": ["#", "Channel", "Videos 24h", "Views/h", "Score", "Best"], "watch": "watch",
        "views": "views", "per_h": "/h", "updated": "Updated", "other_guides": "More guides",
        "tags_h1": "Tags", "tag_title": "{t}: GTA 6 News and Guides", "tag_desc": "Everything about {t} in GTA 6: news, guides and breakdowns.",
        "footer": "fan site about Grand Theft Auto VI. Not affiliated with Rockstar Games or Take-Two.",
        "skip": "Skip to content", "toc": "Contents", "play_video": "Play video",
        "ago": ["min ago", "h ago", "d ago"],
        "cats": {"news": "News", "update": "Updates", "guide": "Guides", "video": "Video", "leak": "Rumors"},
        "src": {"official": "Official", "media": "Press", "youtube": "YouTube", "community": "Community", "leak": "Rumor"},
        "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        "cat_order": ["Start", "Walkthrough", "World"],
    },
    "uk": {
        "home": "Головна", "news": "Новини", "guides": "Гайди", "videos": "Відео", "creators": "Рейтинг",
        "game": "Про гру", "tags": "Теги", "all_news": "Усі новини →", "all_guides": "Усі гайди →",
        "all_videos": "Усі відео →", "rating": "Рейтинг →", "about": "Усе про гру →",
        "home_title": "GTA 6: дата виходу, новини, гайди та час релізу",
        "home_desc": "GTA 6 виходить 19 листопада 2026. Точний час розблокування за регіонами, ціна, розмір, гайди, проходження і свіжі новини Grand Theft Auto VI кожні 15 хвилин.",
        "hero_eyebrow": "Grand Theft Auto VI · 19 листопада 2026",
        "hero_h1": "GTA 6: усе про <span class=\"grad\">Леоніду</span> в одному місці",
        "hero_lead": "GTA 6 виходить 19 листопада 2026 на PS5 та Xbox Series X|S. Тут час розблокування, ціни, гайди, проходження і найгарячіші відео, оновлення кожні 15 хвилин.",
        "cta_main": "Чек-лист до релізу", "cta_tg": "Наш Telegram",
        "now": "Головне зараз", "unlock": "Коли відкриється гра", "top_creators": "Топ блогерів за 24 год",
        "hot_videos": "Що стріляє на YouTube", "guides_start": "Гайди та старт", "more_news": "Ще новини",
        "faq": "Часті питання", "regions": "Регіони Леоніди", "characters": "Персонажі", "timeline": "Хронологія",
        "unlock_times": "Час розблокування", "map_guide": "Гайд по карті →", "more": "Детальніше →",
        "cd_label": "До релізу на PS5 та Xbox Series X|S", "cd_done": "GTA 6 вже вийшла. Час грати.",
        "cd_units": ["днів", "годин", "хвилин", "секунд"],
        "tg_h": "Новини GTA 6 у Telegram", "tg_p": "Злиття, патчі, гайди й найкращі відео раніше за всіх. Без спаму.",
        "subscribe": "Підписатися", "hot": "🔥 Гаряче", "unverified": "Не підтверджено",
        "news_h1": "Новини GTA 6", "news_title": "Новини GTA 6 сьогодні: патчі, злиття, офіційні анонси",
        "news_desc": "Свіжі новини GTA 6 з офіційних джерел, медіа, YouTube і спільноти. Стрічка оновлюється автоматично кожні 15 хвилин, чутки позначені.",
        "news_lead": "Стрічка збирається автоматично з офіційних джерел, медіа, YouTube і спільноти та оновлюється кожні 15 хвилин. Чутки мають позначку «Не підтверджено».",
        "all": "Усі",
        "guides_h1": "Гайди та проходження GTA 6", "guides_title": "Гайди GTA 6: проходження, поради, карта і персонажі",
        "guides_desc": "Гайди з GTA 6: як підготуватися до релізу, яке видання купити, карта Леоніди, персонажі, поради новачкам і проходження місій.",
        "guides_lead": "Від підготовки до релізу до повного проходження. Кожен гайд відповідає на питання в перших рядках, а після 19 листопада розділ поповнюється щодня.",
        "videos_h1": "Найкращі відео про GTA 6", "videos_title": "Відео GTA 6: трейлери, розбори та тренди YouTube",
        "videos_desc": "Відео про GTA 6, що найшвидше набирають перегляди на YouTube просто зараз: трейлери, розбори, геймплей. Сортування за переглядами на годину.",
        "videos_lead": "Відео про GTA 6, які найшвидше набирають перегляди просто зараз. Ми сортуємо ролики за швидкістю переглядів на годину, а не за загальною кількістю, тож нові розбори потрапляють нагору вже за кілька годин.",
        "creators_h1": "Рейтинг блогерів GTA 6", "creators_title": "Рейтинг YouTube-блогерів з GTA 6 за 24 години",
        "creators_desc": "Хто зараз задає тон у темі GTA 6 на YouTube: кількість роликів за добу, перегляди на годину і підсумковий score.",
        "creators_lead": "Рейтинг перераховується кожні 15 хвилин. Score враховує сумарні перегляди на годину по свіжих роликах каналу й невеликий бонус за регулярність: до чотирьох роликів на добу.",
        "game_h1": "Grand Theft Auto VI: що відомо про гру",
        "game_title": "GTA 6: дата виходу, ціна, платформи, карта і персонажі",
        "game_desc": "Усе офіційно відоме про GTA 6: дата виходу 19 листопада 2026, ціна $79.99, розмір до 212 ГБ, карта Леоніди, Лусія і Джейсон, хронологія анонсів.",
        "game_lead": "GTA 6 виходить 19 листопада 2026 на PS5 та Xbox Series X|S, версію для ПК не анонсовано. Нижче зібрано лише офіційно підтверджені факти.",
        "empty_videos": "Тренди з'являться після першого запуску моніторингу YouTube.",
        "empty_creators": "Рейтинг заповниться автоматично після першого запуску моніторингу YouTube.",
        "th": ["#", "Канал", "Відео 24 год", "Перегл./год", "Score", "Найкраще"], "watch": "дивитися",
        "views": "перегл.", "per_h": "/год", "updated": "Оновлено", "other_guides": "Інші гайди",
        "tags_h1": "Теги", "tag_title": "{t}: новини та гайди GTA 6", "tag_desc": "Усе на тему «{t}» у GTA 6: новини, гайди й розбори.",
        "footer": "фанатський портал про Grand Theft Auto VI. Не пов'язаний з Rockstar Games і Take-Two.",
        "skip": "До змісту", "toc": "Зміст", "play_video": "Дивитися відео",
        "ago": ["хв тому", "год тому", "дн тому"],
        "cats": {"news": "Новини", "update": "Оновлення", "guide": "Гайди", "video": "Відео", "leak": "Чутки"},
        "src": {"official": "Офіційно", "media": "Медіа", "youtube": "YouTube", "community": "Спільнота", "leak": "Чутки"},
        "months": ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"],
        "cat_order": ["Старт", "Проходження", "Світ"],
    },
}

e = html.escape
CYR = re.compile("[а-яА-ЯёЁ]")
TR = {"і": "i", "ї": "yi", "є": "ye", "ґ": "g", "'": ""}
TR.update(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
              ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))
CYR = re.compile("[а-яА-ЯёЁіїєґІЇЄҐ]")


def slugify(s):
    s = "".join(TR.get(c, c) for c in s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "tag"


# ---------- data ----------

def load_json(name, default):
    p = os.path.join(CONTENT, name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as ex:
        print(f"! skip {name}: {ex}")
        return default


def parse_dt(s):
    if not s:
        return dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def load_news():
    """news.json (бот) + news.*.json (автоимпорт, ручные) -> дедуп по id/url."""
    items, seen = [], set()
    for p in sorted(glob.glob(os.path.join(CONTENT, "news*.json"))):
        data = load_json(os.path.basename(p), [])
        if isinstance(data, dict):
            data = data.get("items", [])
        for it in data:
            if not isinstance(it, dict) or not it.get("title"):
                continue
            key = (it.get("id") or it.get("url") or it["title"]).strip().lower()
            if key in seen:
                continue
            seen.add(key)
            it["_dt"] = parse_dt(it.get("published"))
            it.setdefault("lang", "ru" if CYR.search(it["title"]) else "en")
            items.append(it)
    items.sort(key=lambda x: x["_dt"], reverse=True)
    return items


def news_for(lang, news):
    """RU-версия показывает всё (переведённое и русское), EN — англоязычное и оригиналы переводов."""
    if lang == "ru":
        return news
    out = []
    for n in news:
        if lang == "uk" and n.get("title_uk"):
            out.append(dict(n, title=n["title_uk"], summary=n.get("summary_uk", "")))
        elif n.get("lang") == "en":
            out.append(n)
        elif n.get("title_en"):
            out.append(dict(n, title=n["title_en"], summary=n.get("summary_en", "")))
        elif n.get("title_orig"):
            m = dict(n, title=n["title_orig"], summary=n.get("summary_orig", ""))
            out.append(m)
    return out


def date_h(d, lang):
    m = T[lang]["months"][d.month - 1]
    return f"{m} {d.day}, {d.year}" if lang == "en" else f"{d.day} {m} {d.year}"


def ago(d, now, lang):
    s = (now - d).total_seconds()
    a = T[lang]["ago"]
    if s < 0 or s >= 86400 * 7:
        return date_h(d, lang)
    if s < 3600:
        return f"{max(1, int(s // 60))} {a[0]}"
    if s < 86400:
        return f"{int(s // 3600)} {a[1]}"
    return f"{int(s // 86400)} {a[2]}"


def fmt_num(n, lang):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    k, m = {"ru": ("тыс", "млн"), "uk": ("тис", "млн")}.get(lang, ("K", "M"))
    sep = "" if lang == "en" else " "
    if n >= 1e6:
        return f"{n / 1e6:.1f}".rstrip("0").rstrip(".") + sep + m
    if n >= 1e3:
        return f"{n / 1e3:.1f}".rstrip("0").rstrip(".") + sep + k
    return str(int(n))


# ---------- markdown (минимальный) ----------

def inline_md(t):
    t = e(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\[(.+?)\]\((?!https?://)([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


def md_to_html(src):
    out, para, lst = [], [], None

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + inline_md(" ".join(para)) + "</p>")
            para = []
        if lst:
            out.append(f"<{lst[0]}>" + "".join(f"<li>{inline_md(x)}</li>" for x in lst[1]) + f"</{lst[0]}>")
            lst = None

    for raw in src.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush()
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(f'<h{lvl} id="{slugify(m.group(2))[:60]}">{inline_md(m.group(2))}</h{lvl}>')
            continue
        m = re.match(r"^\s*[-*]\s+(.*)", line)
        m2 = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if m or m2:
            kind = "ul" if m else "ol"
            if para:
                out.append("<p>" + inline_md(" ".join(para)) + "</p>")
                para = []
            if not lst or lst[0] != kind:
                flush()
                lst = (kind, [])
            lst[1].append((m or m2).group(1))
            continue
        if line.startswith(">"):
            flush()
            out.append(f'<div class="note">{inline_md(line.lstrip("> "))}</div>')
            continue
        if lst:
            flush()
        para.append(line.strip())
    flush()
    return "\n".join(out)


def load_guides(lang):
    folder = os.path.join(CONTENT, "guides") if lang == "ru" else os.path.join(CONTENT, "guides", lang)
    guides = []
    for p in sorted(glob.glob(os.path.join(folder, "*.md"))):
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        meta, body = {}, txt
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
        if m:
            for ln in m.group(1).splitlines():
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = m.group(2)
        slug = os.path.splitext(os.path.basename(p))[0]
        faq = []
        for q, a in re.findall(r"^\?\s*(.+)\n!\s*(.+)$", body, re.M):
            faq.append({"q": q.strip(), "a": a.strip()})
        body = re.sub(r"^\?\s*(.+)\n!\s*(.+)$", lambda mm: f"### {mm.group(1)}\n{mm.group(2)}", body, flags=re.M)
        guides.append({
            "slug": slug, "lang": lang,
            "key": meta.get("key", slug),
            "title": meta.get("title", slug),
            "seo_title": meta.get("seo_title", meta.get("title", slug)),
            "summary": meta.get("summary", ""),
            "category": meta.get("category", ""),
            "updated": meta.get("updated", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "video": meta.get("video", ""),
            "faq": faq,
            "html": md_to_html(body),
            "words": len(re.sub(r"[#*>\-\[\]()]", " ", body).split()),
        })
    order = {c: i for i, c in enumerate(T[lang]["cat_order"])}
    guides.sort(key=lambda g: (order.get(g["category"], 9), int(g.get("key") != "checklist"), g["title"]))
    return guides


# ---------- page shell ----------

class Ctx:
    def __init__(self, lang, base_url, now):
        self.lang, self.base_url, self.now = lang, base_url, now
        self.t = T[lang]
        self.sitemap = []  # (out_path, alternates{lang: out_path}, lastmod)


def depth_rel(out_path):
    d = out_path.count("/")
    return "../" * d if d else "./"


def url_of(out_path):
    p = out_path[:-len("index.html")] if out_path.endswith("index.html") else out_path
    return p


def page(ctx, out_path, title, body, desc, alternates=None, og_type="website", ld=None, crumbs=None, og_image=None):
    t, lang, rel = ctx.t, ctx.lang, depth_rel(out_path)
    L = rel + PREFIX[lang]
    section = out_path[len(PREFIX[lang]):].split("/")[0] if "/" in out_path[len(PREFIX[lang]):] else ""
    nav_items = [("", t["home"]), ("news", t["news"]), ("guides", t["guides"]), ("videos", t["videos"]),
                 ("creators", t["creators"]), ("game", t["game"])]
    nav = "".join(
        f'<a href="{L}{s + "/" if s else ""}"{" aria-current=\"page\"" if s == section else ""}>{n}</a>'
        for s, n in nav_items)
    alternates = alternates or {lang: out_path}
    switch = '<span class="langs">' + "".join(
        (f'<span class="lang cur" aria-current="true">{LANG_LABEL[lg]}</span>' if lg == lang else
         f'<a class="lang" href="{rel}{url_of(alternates.get(lg) or PREFIX[lg] + "index.html")}" hreflang="{lg}" lang="{lg}">{LANG_LABEL[lg]}</a>')
        for lg in LANGS) + '</span>'
    bu = ctx.base_url
    head_links = ""
    if bu:
        head_links += f'<link rel="canonical" href="{bu}/{url_of(out_path)}">\n'
        for lg, op in alternates.items():
            head_links += f'<link rel="alternate" hreflang="{lg}" href="{bu}/{url_of(op)}">\n'
        xd = alternates.get("en") or alternates.get("ru")
        if xd and len(alternates) > 1:
            head_links += f'<link rel="alternate" hreflang="x-default" href="{bu}/{url_of(xd)}">\n'
    img = og_image or "assets/og/default.jpg"
    img_abs = f"{bu}/{img}" if bu else rel + img
    ld_all = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": f"{bu}/{url_of(u)}"} if bu else {})}
        for i, (n, u) in enumerate(crumbs)]}] if crumbs else []
    ld_all += ld or []
    ld_html = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>\n" for x in ld_all)
    crumbs_html = ""
    if crumbs and len(crumbs) > 1:
        parts = [f'<a href="{rel}{url_of(u)}">{e(n)}</a>' for n, u in crumbs[:-1]] + [f"<span>{e(crumbs[-1][0])}</span>"]
        crumbs_html = f'<nav class="crumbs wrap" aria-label="breadcrumbs">{" / ".join(parts)}</nav>'
    ctx.sitemap.append((out_path, alternates))
    full_title = title if SITE_NAME in title else f"{title} | {SITE_NAME}"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
{head_links}<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(img_abs)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(img_abs)}">
<meta name="theme-color" content="#0b0a12">
<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{L}rss.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Unbounded:wght@600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/style.css">
{ld_html}</head>
<body>
<a class="skip" href="#main">{t["skip"]}</a>
<header class="top">
  <div class="wrap top-in">
    <a class="logo" href="{L}" aria-label="{SITE_NAME}"><span class="logo-vi">VI</span><span class="logo-hub">HUB</span></a>
    <button class="burger" aria-label="Menu" aria-expanded="false">☰</button>
    <nav class="nav">{nav}{switch}<a class="tg" href="{TELEGRAM_URL}" target="_blank" rel="noopener">Telegram</a></nav>
  </div>
</header>
{crumbs_html}
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <div><strong>{SITE_NAME}</strong> · {t["footer"]}</div>
    <div class="foot-links"><a href="{L}tags/">{t["tags"]}</a><a href="{L}rss.xml">RSS</a><a href="{L}news.json">JSON</a><a href="{TELEGRAM_URL}" target="_blank" rel="noopener">Telegram</a>{f'<a href="{YOUTUBE_URL}" target="_blank" rel="noopener">YouTube</a>' if YOUTUBE_URL else ''}</div>
  </div>
</footer>
<div class="tg-bar" hidden><span>{t["tg_h"]}</span><a href="{TELEGRAM_URL}" target="_blank" rel="noopener">{t["subscribe"]}</a><button class="tg-x" aria-label="Close">×</button></div>
<script src="{rel}assets/app.js" defer></script>
</body>
</html>"""


# ---------- components ----------

def news_card(ctx, it, big=False):
    t = ctx.t
    cat, st, img = it.get("category", "news"), it.get("source_type", "media"), it.get("image") or ""
    pal = int(hashlib.md5((it.get("id") or it.get("url") or it["title"]).encode()).hexdigest(), 16) % 4
    src_name = (it.get("source") or "").strip()[:28]
    cover = (f'<div class="cv-sun" aria-hidden="true"></div><span class="cv-logo">VI<em>HUB</em></span>'
             f'<span class="cv-cat">{e(t["cats"].get(cat, cat))}</span><b class="cv-src">{e(src_name or "GTA 6")}</b>')
    photo = (f'<img src="{e(img)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">' if img else "")
    thumb = f'<div class="thumb cover cv-{pal}">{cover}{photo}</div>'
    badges = f'<span class="badge b-{e(st)}">{e(t["src"].get(st, st))}</span>'
    if (it.get("score") or 0) >= 80:
        badges += f'<span class="badge b-hot">{t["hot"]}</span>'
    if it.get("verified") is False:
        badges += f'<span class="badge b-leak">{t["unverified"]}</span>'
    tag = "h2" if big else "h3"
    summ = (it.get("summary") or "").strip()
    norm = lambda x: re.sub(r"\W+", "", x.lower())
    if summ and (norm(summ).startswith(norm(it["title"])[:40]) or len(summ) < 25):
        summ = ""
    it = dict(it, summary=summ)
    return f"""<article class="card news{' big' if big else ''}" data-cat="{e(cat)}">
  <a class="card-link" href="{e(it.get('url', '#'))}" target="_blank" rel="noopener nofollow">
  {thumb}
  <div class="card-body">
    <div class="badges">{badges}</div>
    <{tag}>{e(it['title'])}</{tag}>
    {f'<p>{e(it.get("summary", ""))}</p>' if it.get('summary') else ''}
    <div class="meta"><span>{e(it.get('source', ''))}</span><time datetime="{it['_dt'].strftime('%Y-%m-%dT%H:%M:%SZ')}">{ago(it['_dt'], ctx.now, ctx.lang)}</time></div>
  </div></a>
</article>"""


def video_card(ctx, v):
    t = ctx.t
    vid = v.get("video_id") or ""
    thumb = v.get("thumbnail") or (f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else "")
    vph = v.get("vph")
    return f"""<article class="card video"><a class="card-link" href="{e(v.get('url') or 'https://youtu.be/' + vid)}" target="_blank" rel="noopener nofollow">
  <div class="thumb vthumb" style="background-image:url('{e(thumb)}')"><span class="play" aria-hidden="true">▶</span></div>
  <div class="card-body">
    <h3>{e(v.get('title', ''))}</h3>
    <div class="meta"><span>{e(v.get('channel_title', ''))}</span><span>{fmt_num(v.get('views'), ctx.lang)} {t['views']}{f' · {fmt_num(vph, ctx.lang)}{t["per_h"]}' if vph else ''}</span></div>
  </div></a>
</article>"""


def guide_card(ctx, g, rel):
    return f"""<article class="card guide"><a class="card-link" href="{rel}{PREFIX[ctx.lang]}guides/{g['slug']}.html">
  <div class="card-body">
    <div class="badges"><span class="badge b-guide">{e(g['category'])}</span></div>
    <h3>{e(g['title'])}</h3>
    <p>{e(g['summary'])}</p>
  </div></a>
</article>"""


def creators_table(ctx, chs, limit=None):
    t = ctx.t
    if not chs:
        return f'<div class="empty">{t["empty_creators"]}</div>'
    rows = []
    for i, c in enumerate(chs[:limit] if limit else chs, 1):
        url = f"https://www.youtube.com/channel/{c.get('channel_id', '')}"
        best = c.get("best_video_url")
        rows.append(f"""<tr><td class="rank">{i}</td>
  <td><a href="{e(url)}" target="_blank" rel="noopener nofollow">{e(c.get('title', ''))}</a></td>
  <td class="num">{e(str(c.get('videos_24h', '—')))}</td><td class="num">{fmt_num(c.get('total_vph'), ctx.lang)}</td>
  <td class="num score">{e(str(round(c.get('score', 0))))}</td>
  <td>{f'<a href="{e(best)}" target="_blank" rel="noopener nofollow">{t["watch"]}</a>' if best else ''}</td></tr>""")
    th = "".join(f'<th{" class=\"num\"" if 2 <= i <= 4 else ""}>{h}</th>' for i, h in enumerate(t["th"]))
    return f'<div class="table-wrap"><table class="rating"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def countdown(ctx, game):
    t = ctx.t
    u = t["cd_units"]
    return f"""<div class="countdown" data-release="{e(game.get('release_iso', ''))}" data-lang="{ctx.lang}">
  <div class="cd-label">{t['cd_label']}</div>
  <div class="cd-grid">
    <div><b data-u="d">--</b><span>{u[0]}</span></div><div><b data-u="h">--</b><span>{u[1]}</span></div>
    <div><b data-u="m">--</b><span>{u[2]}</span></div><div><b data-u="s">--</b><span>{u[3]}</span></div>
  </div>
  <div class="cd-done" hidden>{t['cd_done']}</div>
</div>"""


def faq_block(items):
    return "".join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in items)


def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in items]}


def tag_links(ctx, tags, rel):
    if not tags:
        return ""
    return '<div class="tags">' + "".join(
        f'<a class="tag" href="{rel}{PREFIX[ctx.lang]}tags/{slugify(tg)}/">#{e(tg)}</a>' for tg in tags) + "</div>"


def lite_video(vid, label):
    return (f'<div class="yt" data-id="{e(vid)}" style="background-image:url(\'https://i.ytimg.com/vi/{e(vid)}/hqdefault.jpg\')">'
            f'<button class="yt-play" aria-label="{e(label)}">▶</button></div>')


# ---------- build ----------

def build_lang(ctx, game, news_all, trending, channels, guides, guide_alts, write):
    t, lang, now, P = ctx.t, ctx.lang, ctx.now, PREFIX[ctx.lang]
    news = news_for(lang, news_all)

    def alts(path_wo_prefix):
        return {lg: PREFIX[lg] + path_wo_prefix for lg in LANGS}

    home_crumb = (t["home"], P + "index.html")

    # ---- главная
    out = P + "index.html"
    rel = depth_rel(out)
    L = rel + P
    hot = sorted([n for n in news if (now - n["_dt"]).days < 7], key=lambda n: n.get("score", 0), reverse=True)
    lead = hot[0] if hot else (news[0] if news else None)
    rest = [n for n in news if n is not lead][:9]
    facts = "".join(f'<div class="fact"><span>{e(f["k"])}</span><b>{e(f["v"])}</b></div>' for f in game.get("facts", [])[:6])
    unlock = "".join(f'<li><b>{e(u["where"])}</b><span>{e(u["when"])}</span></li>' for u in game.get("unlock_times", []))
    checklist = next((g for g in guides if g["key"] == "checklist"), guides[0] if guides else None)
    body = f"""
<section class="hero">
  <div class="sun" aria-hidden="true"></div>
  <div class="wrap hero-in">
    <div class="hero-text">
      <div class="eyebrow">{t['hero_eyebrow']}</div>
      <h1>{t['hero_h1']}</h1>
      <p class="lead">{t['hero_lead']}</p>
      <div class="cta">{f'<a class="btn" href="{L}guides/{checklist["slug"]}.html">{t["cta_main"]}</a>' if checklist else ''}<a class="btn ghost" href="{TELEGRAM_URL}" target="_blank" rel="noopener">{t['cta_tg']}</a></div>
    </div>
    {countdown(ctx, game)}
  </div>
</section>
<section class="wrap block">
  <div class="block-head"><h2>{t['now']}</h2><a href="{L}news/">{t['all_news']}</a></div>
  <div class="grid news-grid">{news_card(ctx, lead, big=True) if lead else ''}{''.join(news_card(ctx, n) for n in rest[:5])}</div>
</section>
<section class="wrap block split">
  <div><div class="block-head"><h2>{t['unlock']}</h2><a href="{L}game/">{t['about']}</a></div><ul class="unlock">{unlock}</ul><div class="facts">{facts}</div></div>
  <div><div class="block-head"><h2>{t['top_creators']}</h2><a href="{L}creators/">{t['rating']}</a></div>{creators_table(ctx, channels, 5)}</div>
</section>
<section class="wrap block">
  <div class="block-head"><h2>{t['hot_videos']}</h2><a href="{L}videos/">{t['all_videos']}</a></div>
  {'<div class="grid video-grid">' + ''.join(video_card(ctx, v) for v in trending[:8]) + '</div>' if trending else f'<div class="empty">{t["empty_videos"]}</div>'}
</section>
<section class="wrap block">
  <div class="block-head"><h2>{t['guides_start']}</h2><a href="{L}guides/">{t['all_guides']}</a></div>
  <div class="grid guide-grid">{''.join(guide_card(ctx, g, rel) for g in guides[:6])}</div>
</section>
<section class="wrap block"><h2 class="mt0">{t['faq']}</h2><div class="faq">{faq_block(game.get('faq', []))}</div></section>
{f'<section class="wrap block"><div class="block-head"><h2>{t["more_news"]}</h2></div><div class="grid news-grid small">' + ''.join(news_card(ctx, n) for n in rest[5:11]) + '</div></section>' if len(rest) > 5 else ''}
<section class="wrap block tg-cta"><div><h2>{t['tg_h']}</h2><p>{t['tg_p']}</p></div><a class="btn" href="{TELEGRAM_URL}" target="_blank" rel="noopener">{t['subscribe']}</a></section>
"""
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "inLanguage": lang,
               **({"url": f"{ctx.base_url}/{P}"} if ctx.base_url else {})}
    org_ld = {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME,
              "sameAs": [u for u in [TELEGRAM_URL if len(TELEGRAM_URL) > 14 else "", YOUTUBE_URL] if u],
              **({"url": f"{ctx.base_url}/", "logo": f"{ctx.base_url}/assets/og/default.jpg"} if ctx.base_url else {})}
    game_ld = {"@context": "https://schema.org", "@type": "VideoGame", "name": "Grand Theft Auto VI",
               "alternateName": ["GTA 6", "GTA VI"], "datePublished": "2026-11-19",
               "gamePlatform": game.get("platforms", []), "publisher": {"@type": "Organization", "name": "Rockstar Games"}}
    write(out, page(ctx, out, t["home_title"], body, t["home_desc"], alts("index.html"),
                    ld=[site_ld, org_ld, game_ld, faq_ld(game.get("faq", []))] if game.get("faq") else [site_ld, org_ld, game_ld],
                    og_image=f"assets/og/{lang}-home.jpg"))

    # ---- новости
    out = P + "news/index.html"
    rel = depth_rel(out)
    filt = f'<button class="chip active" data-f="all">{t["all"]}</button>' + "".join(
        f'<button class="chip" data-f="{k}">{v}</button>' for k, v in t["cats"].items())
    body = f"""<section class="wrap page-head"><h1>{t['news_h1']}</h1><p class="lead">{t['news_lead']}</p>
<div class="chips" data-target="#news-list">{filt}</div></section>
<section class="wrap block"><div class="grid news-grid small" id="news-list">{''.join(news_card(ctx, n) for n in news[:120])}</div></section>"""
    write(out, page(ctx, out, t["news_title"], body, t["news_desc"], alts("news/index.html"),
                    crumbs=[home_crumb, (t["news"], out)], og_image=f"assets/og/{lang}-news.jpg"))

    # ---- гайды
    out = P + "guides/index.html"
    rel = depth_rel(out)
    body = f"""<section class="wrap page-head"><h1>{t['guides_h1']}</h1><p class="lead">{t['guides_lead']}</p></section>
<section class="wrap block"><div class="grid guide-grid">{''.join(guide_card(ctx, g, rel) for g in guides)}</div></section>"""
    write(out, page(ctx, out, t["guides_title"], body, t["guides_desc"], alts("guides/index.html"),
                    crumbs=[home_crumb, (t["guides"], out)], og_image=f"assets/og/{lang}-guides.jpg"))
    for g in guides:
        out = f"{P}guides/{g['slug']}.html"
        rel = depth_rel(out)
        related = [g2 for g2 in guides if g2 is not g]
        related.sort(key=lambda g2: (-len(set(g2["tags"]) & set(g["tags"])), g2["category"] != g["category"]))
        others = "".join(f'<li><a href="{g2["slug"]}.html">{e(g2["title"])}</a></li>' for g2 in related[:6])
        alt = {lg: f"{PREFIX[lg]}guides/{s}.html" for lg, s in guide_alts.get(g["key"], {}).items()}
        alt[lang] = out
        heads = re.findall(r'<h3 id="([^"]+)">(.*?)</h3>', g["html"])
        toc = ('<nav class="toc"><b>' + t["toc"] + '</b><ol>' +
               "".join(f'<li><a href="#{i}">{h}</a></li>' for i, h in heads) + '</ol></nav>') if len(heads) >= 3 else ""
        video = f'<div class="video-embed">{lite_video(g["video"], t["play_video"])}</div>' if g["video"] else ""
        upd = g["updated"]
        body = f"""<article class="wrap article">
  <div class="badges"><span class="badge b-guide">{e(g['category'])}</span>{f'<span class="badge"><time datetime="{e(upd)}">{t["updated"]} {date_h(parse_dt(upd + "T00:00:00Z"), lang)}</time></span>' if upd else ''}</div>
  <h1>{e(g['title'])}</h1>
  <p class="lead answer">{e(g['summary'])}</p>
  {toc}
  {video}
  <div class="prose">{g['html']}</div>
  {tag_links(ctx, g['tags'], rel)}
  <aside class="tg-inline"><div><b>{t['tg_h']}</b><span>{t['tg_p']}</span></div><a class="btn small" href="{TELEGRAM_URL}" target="_blank" rel="noopener">{t['subscribe']}</a></aside>
  <aside class="more"><h2>{t['other_guides']}</h2><ul>{others}</ul></aside>
</article>"""
        art = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"][:110], "description": g["summary"],
               "inLanguage": lang, "dateModified": upd or None, "datePublished": upd or None,
               "author": {"@type": "Organization", "name": SITE_NAME}, "publisher": {"@type": "Organization", "name": SITE_NAME},
               "about": {"@type": "VideoGame", "name": "Grand Theft Auto VI"},
               **({"image": f"{ctx.base_url}/assets/og/{lang}-g-{g['slug']}.jpg", "mainEntityOfPage": f"{ctx.base_url}/{out}"} if ctx.base_url else {})}
        art = {k: v for k, v in art.items() if v is not None}
        ld = [art] + ([faq_ld(g["faq"])] if g["faq"] else [])
        write(out, page(ctx, out, g["seo_title"], body, g["summary"], alt, og_type="article", ld=ld,
                        crumbs=[home_crumb, (t["guides"], P + "guides/index.html"), (g["title"], out)],
                        og_image=f"assets/og/{lang}-g-{g['slug']}.jpg"))

    # ---- видео
    out = P + "videos/index.html"
    body = f"""<section class="wrap page-head"><h1>{t['videos_h1']}</h1><p class="lead">{t['videos_lead']}</p></section>
<section class="wrap block">{'<div class="grid video-grid">' + ''.join(video_card(ctx, v) for v in trending[:60]) + '</div>' if trending else f'<div class="empty">{t["empty_videos"]}</div>'}</section>"""
    write(out, page(ctx, out, t["videos_title"], body, t["videos_desc"], alts("videos/index.html"),
                    crumbs=[home_crumb, (t["videos"], out)], og_image=f"assets/og/{lang}-videos.jpg"))

    # ---- рейтинг
    out = P + "creators/index.html"
    body = f"""<section class="wrap page-head"><h1>{t['creators_h1']}</h1><p class="lead">{t['creators_lead']}</p></section>
<section class="wrap block">{creators_table(ctx, channels)}</section>"""
    write(out, page(ctx, out, t["creators_title"], body, t["creators_desc"], alts("creators/index.html"),
                    crumbs=[home_crumb, (t["creators"], out)], og_image=f"assets/og/{lang}-creators.jpg"))

    # ---- об игре
    out = P + "game/index.html"
    rel = depth_rel(out)
    L = rel + P
    tl = "".join(
        f'<li class="{"future" if parse_dt(x["date"] + "T00:00:00Z") > now else ""}"><time datetime="{x["date"]}">{date_h(parse_dt(x["date"] + "T00:00:00Z"), lang)}</time><span>{e(x["text"])}</span></li>'
        for x in game.get("timeline", []))
    regions = "".join(f'<div class="card region"><div class="card-body"><h3>{e(r["name"])}</h3><p>{e(r["desc"])}</p></div></div>' for r in game.get("regions", []))
    chars = "".join(f'<div class="card char"><div class="card-body"><h3>{e(c["name"])}</h3><p>{e(c["desc"])}</p></div></div>' for c in game.get("characters", []))
    allfacts = "".join(f'<div class="fact"><span>{e(f["k"])}</span><b>{e(f["v"])}</b></div>' for f in game.get("facts", []))
    gmap = next((g for g in guides if g["key"] == "map"), None)
    gchar = next((g for g in guides if g["key"] == "characters"), None)
    body = f"""<section class="wrap page-head"><h1>{t['game_h1']}</h1><p class="lead">{t['game_lead']}</p></section>
<section class="wrap block split">
  <div><div class="facts">{allfacts}</div><h2 class="mt">{t['unlock_times']}</h2><ul class="unlock">{unlock}</ul></div>
  <div>{countdown(ctx, game)}<h2 class="mt">{t['timeline']}</h2><ol class="timeline">{tl}</ol></div>
</section>
<section class="wrap block"><h2 class="mt0">{t['faq']}</h2><div class="faq">{faq_block(game.get('faq', []))}</div></section>
<section class="wrap block"><div class="block-head"><h2>{t['regions']}</h2>{f'<a href="{L}guides/{gmap["slug"]}.html">{t["map_guide"]}</a>' if gmap else ''}</div><div class="grid guide-grid">{regions}</div></section>
<section class="wrap block"><div class="block-head"><h2>{t['characters']}</h2>{f'<a href="{L}guides/{gchar["slug"]}.html">{t["more"]}</a>' if gchar else ''}</div><div class="grid guide-grid">{chars}</div></section>"""
    write(out, page(ctx, out, t["game_title"], body, t["game_desc"], alts("game/index.html"),
                    ld=[game_ld] + ([faq_ld(game["faq"])] if game.get("faq") else []),
                    crumbs=[home_crumb, (t["game"], out)], og_image=f"assets/og/{lang}-game.jpg"))

    # ---- теги
    tagmap = {}
    for g in guides:
        for tg in g["tags"]:
            tagmap.setdefault(slugify(tg), {"name": tg, "guides": [], "news": []})["guides"].append(g)
    for n in news[:300]:
        for tg in n.get("tags") or []:
            if isinstance(tg, str) and tg.strip() and not (lang != "ru" and CYR.search(tg)):
                tagmap.setdefault(slugify(tg), {"name": tg.strip(), "guides": [], "news": []})["news"].append(n)
    tagmap = {k: v for k, v in tagmap.items() if len(v["guides"]) + len(v["news"]) >= 1}
    for slug, tg in tagmap.items():
        out = f"{P}tags/{slug}/index.html"
        rel = depth_rel(out)
        gl = "".join(guide_card(ctx, g, rel) for g in tg["guides"])
        nl = "".join(news_card(ctx, n) for n in tg["news"][:40])
        body = f"""<section class="wrap page-head"><h1>#{e(tg['name'])}</h1><p class="lead">{e(t['tag_desc'].format(t=tg['name']))}</p></section>
{f'<section class="wrap block"><div class="block-head"><h2>{t["guides"]}</h2></div><div class="grid guide-grid">{gl}</div></section>' if gl else ''}
{f'<section class="wrap block"><div class="block-head"><h2>{t["news"]}</h2></div><div class="grid news-grid small">{nl}</div></section>' if nl else ''}"""
        thin = len(tg["guides"]) + len(tg["news"]) < 2
        html_out = page(ctx, out, t["tag_title"].format(t=tg["name"]), body, t["tag_desc"].format(t=tg["name"]), {lang: out},
                        crumbs=[home_crumb, (t["tags"], P + "tags/index.html"), ("#" + tg["name"], out)])
        if thin:  # не индексируем страницы-пустышки
            html_out = html_out.replace("index,follow,max-image-preview:large,max-snippet:-1", "noindex,follow")
            ctx.sitemap.pop()
        write(out, html_out)
    out = P + "tags/index.html"
    rel = depth_rel(out)
    cloud = "".join(f'<a class="tag" href="{slug}/">#{e(v["name"])} <small>{len(v["guides"]) + len(v["news"])}</small></a>'
                    for slug, v in sorted(tagmap.items(), key=lambda kv: -(len(kv[1]["guides"]) + len(kv[1]["news"]))))
    body = f'<section class="wrap page-head"><h1>{t["tags_h1"]}</h1></section><section class="wrap block"><div class="tags big">{cloud}</div></section>'
    write(out, page(ctx, out, f'{t["tags_h1"]} GTA 6', body, t["guides_desc"], {lang: out},
                    crumbs=[home_crumb, (t["tags"], out)]))

    # ---- API, RSS
    public = [{k: v for k, v in n.items() if not k.startswith("_")} for n in news[:200]]
    write(P + "news.json", json.dumps(public, ensure_ascii=False, indent=1))
    rss_items = "".join(
        f"<item><title>{e(n['title'])}</title><link>{e(n.get('url', ''))}</link>"
        f"<guid isPermaLink=\"false\">{e(n.get('id') or n.get('url', ''))}</guid>"
        f"<pubDate>{format_datetime(n['_dt'])}</pubDate><description>{e(n.get('summary', ''))}</description></item>"
        for n in news[:50])
    write(P + "rss.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{SITE_NAME}</title>'
                         f'<link>{e((ctx.base_url or "") + "/" + P)}</link><description>{e(t["home_desc"])}</description>'
                         f'<language>{lang}</language>{rss_items}</channel></rss>')


def build(base_url=""):
    now = dt.datetime.now(dt.timezone.utc)
    news = load_news()
    trending = load_json("trending.json", [])
    channels = load_json("channels.json", [])
    trending = sorted(trending.get("items", []) if isinstance(trending, dict) else trending, key=lambda v: v.get("score", 0), reverse=True)
    channels = sorted(channels.get("items", []) if isinstance(channels, dict) else channels, key=lambda c: c.get("score", 0), reverse=True)

    guides = {lg: load_guides(lg) for lg in LANGS}
    guide_alts = {}
    for lg in LANGS:
        for g in guides[lg]:
            guide_alts.setdefault(g["key"], {})[lg] = g["slug"]

    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(DIST, "assets"))

    def write(rel_path, text):
        full = os.path.join(DIST, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    all_urls = []
    for lg in LANGS:
        game = load_json("game.json" if lg == "ru" else f"game.{lg}.json", {})
        ctx = Ctx(lg, base_url, now)
        build_lang(ctx, game, news, trending, channels, guides[lg], guide_alts, write)
        all_urls += ctx.sitemap

    # sitemap с hreflang + robots + IndexNow
    if base_url:
        today = now.strftime("%Y-%m-%d")
        rows = []
        for out, alts in all_urls:
            links = "".join(f'<xhtml:link rel="alternate" hreflang="{lg}" href="{base_url}/{url_of(p)}"/>' for lg, p in alts.items()) if len(alts) > 1 else ""
            pr = "1.0" if out in ("index.html", "en/index.html") else "0.8" if "guides/" in out or "game/" in out else "0.6"
            rows.append(f"<url><loc>{base_url}/{url_of(out)}</loc><lastmod>{today}</lastmod><priority>{pr}</priority>{links}</url>")
        write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                             'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(rows) + "</urlset>")
        host = base_url.split("/")[2]
        if not host.endswith("github.io"):
            write("CNAME", host + "\n")
        write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")
        write("urls.txt", "\n".join(f"{base_url}/{url_of(o)}" for o, _ in all_urls))
    key = os.environ.get("INDEXNOW_KEY", "")
    if key:
        write(f"{key}.txt", key)
    if base_url:  # 404 открывается по любому пути, поэтому ссылки делаем абсолютными
        h404 = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()
        h404 = h404.replace('href="./', f'href="{base_url}/').replace('src="./', f'src="{base_url}/')
        write("404.html", h404.replace("index,follow,max-image-preview:large,max-snippet:-1", "noindex"))
    print(f"built: {len(news)} news, {sum(len(v) for v in guides.values())} guides, {len(trending)} videos, "
          f"{len(channels)} channels, {len(all_urls)} indexable pages -> {DIST}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.environ.get("SITE_URL", "").rstrip("/"))
    build(ap.parse_args().base_url)
