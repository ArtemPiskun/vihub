# VI HUB — фанатский портал о GTA 6

Двуязычный: русская версия в корне, английская в `/en/` (связаны через hreflang).

Статический сайт, который сам обновляется каждые 15 минут: новости из RSS и YouTube, тренды и рейтинг блогеров из мониторинга, гайды из Markdown. Никаких серверов и баз: Python (только стандартная библиотека) + GitHub Actions + GitHub Pages. Хостинг бесплатный.

## Разделы
- **Главная**: отсчёт до релиза, главное сейчас, время разблокировки, топ блогеров за 24 часа, видео, которые «стреляют», гайды, кнопка Telegram.
- **Новости** (`/news/`): лента с фильтром по категориям (новости, обновления, гайды, видео, слухи).
- **Гайды** (`/guides/`): статьи из `content/guides/*.md`.
- **Видео** (`/videos/`): тренды YouTube по скорости просмотров в час.
- **Рейтинг** (`/creators/`): рейтинг каналов.
- **Об игре** (`/game/`): факты, хронология, регионы, персонажи.
- **API для бота**: `/news.json` и `/rss.xml`.

## Откуда берутся данные
| Файл | Кто пишет |
|---|---|
| `content/news.json` | Telegram-бот / мониторинг (полностью перегенерирует) |
| `content/news.ingest.json` | `scripts/ingest.py` (RSS, YouTube RSS, внешний JSON) |
| `content/news.manual.json` | вы вручную (эксклюзивы, закреп) |
| `content/trending.json`, `content/channels.json` | бот мониторинга; если его нет, `ingest.py` при наличии `YOUTUBE_API_KEY` |
| `content/game.json` | факты об игре, правится руками |
| `content/guides/*.md` | гайды (front matter: title, summary, category, updated) |

Все `content/news*.json` объединяются, дубликаты отсеиваются по `id`/`url`.

Формат новости:
```json
{"id":"sha1(url)","title":"...","summary":"...","url":"https://...","source":"IGN",
 "source_type":"official|youtube|media|leak|community","category":"news|update|guide|video|leak",
 "published":"2026-11-19T05:00:00Z","image":"","tags":[],"score":0-100,"verified":true}
```
`score >= 80` получает метку «Горячее», `verified: false` метку «Не подтверждено».

## Запуск локально
```bash
python3 scripts/ingest.py      # собрать новости (нужен интернет)
python3 scripts/build.py       # собрать сайт в dist/
python3 -m http.server -d dist 8000
```

## Деплой на GitHub Pages (5 минут)
1. Создайте репозиторий и залейте эту папку в ветку `main`.
2. Settings → Pages → Source: **GitHub Actions**.
3. Settings → Secrets and variables → Actions:
   - Secrets (необязательно): `YOUTUBE_API_KEY` (статистика просмотров), `ANTHROPIC_API_KEY` (автоперевод англоязычных заголовков на русский).
   - Secret `INDEXNOW_KEY`: любая строка из 32 hex-символов, нужна для мгновенной индексации в Яндексе и Bing.
   - Variables: `YOUTUBE_URL` (ссылка на ваш канал), `SITE_URL` (например `https://vihub.ru`), `TELEGRAM_URL` (ссылка на канал), `EXTERNAL_NEWS_URL` (JSON-лента бота, если она опубликована по URL).
4. Workflow `.github/workflows/update.yml` запускается каждые 15 минут, коммитит новый контент и деплоит сайт.
5. Свой домен: Settings → Pages → Custom domain.

## Как добавить источник
`config/sources.json`: `feeds` (любая RSS/Atom-лента, `filter: true` оставляет только записи с ключевыми словами про GTA 6), `youtube_channels` (channel_id).

## Как добавить гайд
Положите `content/guides/<slug>.md`:
```
---
title: Заголовок
summary: Одна строка для карточки
category: Старт | Прохождение | Мир
updated: 2026-11-19
---
## Раздел
Текст, **жирный**, [ссылка](https://...), списки через "- ".
```

## SEO, что уже встроено
- Уникальные title/description под поисковые запросы, один H1 на страницу, ответ на вопрос в первом абзаце (блок-ответ).
- hreflang ru/en + x-default, canonical, sitemap.xml с альтернативами и lastmod, robots.txt.
- schema.org: WebSite, Organization, VideoGame, Article, FAQPage, BreadcrumbList.
- OG/Twitter-картинки 1200x630 для каждой страницы (`node scripts/og.js` после добавления гайда).
- Теги (`/tags/`), хлебные крошки, «Другие гайды» по общим тегам, оглавление в длинных гайдах.
- Лёгкая вставка YouTube (iframe грузится по клику), без тяжёлых скриптов.
- IndexNow-пинг Яндекса и Bing после каждого push.
- Telegram-конверсия: кнопка в шапке, блок в каждом гайде, плашка на мобильных после прокрутки.

## Новый гайд с FAQ-разметкой
Вопрос-ответ в тексте гайда пишется так, и он попадает в FAQPage schema:
```
? Вопрос
! Ответ
```
Пара RU/EN связывается полем `key:` в front matter (одинаковое значение в обоих файлах). Английские гайды лежат в `content/guides/en/`.
