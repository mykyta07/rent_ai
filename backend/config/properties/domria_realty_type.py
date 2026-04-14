"""
Визначення realty_type (apartment / house / commercial) для DOM.RIA.

Порядок сигналів (від надійніших):
1) slug у всіх посиланнях на оголошення (realty-…-kvartira-… / …-dom-…);
2) короткі бейджі з HTML: span.v-text у .label-wrap («Перевірена квартира», «Перевірений будинок»);
3) обережні ключові слова в заголовку/описі (без голого «будинок» — у квартирах часто «Будинок знаходиться…»).

Усе працює з локальним HTML / текстом у БД; зовнішні API тут не викликаються.
"""
import re
from typing import Iterable, List, Optional, Tuple

from bs4 import Tag

_COMMERCIAL_URL_FRAGMENTS = (
    "ofis",
    "magazin",
    "magazyn",
    "sklad",
    "pomesch",
    "prymischen",
    "kommerc",
    "komerts",
    "torgova",
    "torgovy",
    "gotovyj-biznes",
    "gotovyy-biznes",
    "salon-",
    "kafe-",
    "restoran-",
    "proizvodstv",
)
_HOUSE_URL_FRAGMENTS = (
    "-dom-",
    "/dom/",
    "budynok",
    "budinok",
    "dacha",
    "kottedzh",
    "kotedg",
    "taunhaus",
    "chast-doma",
    "chast-bud",
    "chastyn",
    "domik",
    "sadoviy-domik",
)
# Окремо «dom-» на початку сегмента (не домен dom.ria — там крапка після dom)
_APARTMENT_URL_FRAGMENTS = (
    "kvartira",
    "kvartyra",
    "novostroj",
    "novobudova",
    "novobudiv",
)

_COMMERCIAL_UA = (
    "комерцій",
    "офіс",
    "магазин",
    "склад",
    "приміщен",
    "торгов",
    "готовий бізнес",
    "кафе",
    "ресторан",
    "салон",
    "виробництв",
)
# Без «будинок» / «частина будин» — у описах квартир типові фрази про будинок як будівлю.
_HOUSE_UA = (
    "котедж",
    "дача",
    "таунхаус",
    "окремий будинок",
    "приватний будинок",
    "приватний будин",
    "садиб",
    "садовий будиночок",
)


def collect_domria_listing_urls(item: Tag) -> List[str]:
    """Усі посилання на сторінку оголошення в межах картки section.realty-item."""
    out: List[str] = []
    seen = set()
    for a in item.find_all("a", href=True):
        h = (a.get("href") or "").strip()
        if not h:
            continue
        low = h.lower()
        if "dom.ria" not in low:
            continue
        if "realtor-" in low:
            continue
        if "realty-" not in low and "/realty/" not in low:
            continue
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def extract_label_wrap_v_texts(item: Tag) -> List[str]:
    """Бейджі DOM.RIA: span.v-text у .label-wrap."""
    texts: List[str] = []
    for wrap in item.select(".label-wrap"):
        for span in wrap.select("span.v-text"):
            t = span.get_text(separator=" ", strip=True)
            if t:
                texts.append(t)
    return texts


def infer_realty_type_from_realty_item_section(item: Tag) -> Tuple[Optional[str], str]:
    """
    Повертає (realty_id або None, realty_type) для однієї картки зі збереженого HTML.
    Якщо немає realty-link / id у URL — (None, 'apartment').
    """
    link = item.find("a", class_="realty-link")
    if not link or not link.get("href"):
        return None, "apartment"
    url = str(link["href"]).strip()
    id_match = re.search(r"-(\d+)\.html", url)
    if not id_match:
        return None, "apartment"
    realty_id = id_match.group(1)
    extra_urls = [h for h in collect_domria_listing_urls(item) if h != url]
    badge_texts = extract_label_wrap_v_texts(item)
    title_el = item.find("a", class_="size22")
    title = title_el.get_text(strip=True) if title_el else ""
    desc_el = item.find("div", class_="desc-hidden")
    desc = desc_el.get_text(strip=True) if desc_el else ""
    rt = infer_realty_type(
        url=url,
        title=title,
        description=desc,
        card_text="",
        extra_urls=extra_urls,
        badge_texts=badge_texts,
    )
    return realty_id, rt


def domria_listing_id_from_description(description: Optional[str]) -> Optional[str]:
    """Витягнути id оголошення з рядка DOM.RIA ID у описі Property (без хибного збігу 12 у 123)."""
    if not description:
        return None
    m = re.search(r"DOM\.RIA ID:\s*(\d+)(?!\d)", description.strip())
    return m.group(1) if m else None


def extract_domria_url_from_text(text: Optional[str]) -> str:
    """Якщо в тексті є посилання на dom.ria — повернути його (для slug)."""
    if not text:
        return ""
    m = re.search(r"https?://[^\s\]\)\"']*dom\.ria[^\s\]\)\"']*", text, re.I)
    return m.group(0) if m else ""


def _slug_type_from_url_blob(blob: str) -> Optional[str]:
    u = (blob or "").lower()
    if not u.strip():
        return None
    for frag in _COMMERCIAL_URL_FRAGMENTS:
        if frag in u:
            return "commercial"
    for frag in _HOUSE_URL_FRAGMENTS:
        if frag in u:
            return "house"
    if re.search(r"(?:^|[/-])dom-", u):
        return "house"
    for frag in _APARTMENT_URL_FRAGMENTS:
        if frag in u:
            return "apartment"
    return None


def infer_realty_type_from_domria_badges(badge_texts: Optional[Iterable[str]]) -> Optional[str]:
    """
    Бейджі на картці пошуку DOM.RIA: .label-wrap span.v-text
    (напр. «Перевірена квартира · MAX», «Перевірений будинок»).
    """
    if not badge_texts:
        return None
    for raw in badge_texts:
        t = (raw or "").lower().replace("\xa0", " ").strip()
        if not t or len(t) > 120:
            continue
        if "ріелтор" in t or "рілтор" in t or "360" in t:
            continue
        if "комерц" in t or "офіс" in t or "приміщен" in t:
            return "commercial"
        if "квартир" in t:
            return "apartment"
        if "будинок" in t:
            return "house"
    return None


def infer_realty_type(
    *,
    url: str = "",
    title: str = "",
    description: str = "",
    card_text: str = "",
    extra_urls: Optional[List[str]] = None,
    badge_texts: Optional[List[str]] = None,
) -> str:
    """
    Повертає apartment | house | commercial.
    extra_urls — усі href на картці оголошення (tit, фото); badge_texts — v-text з .label-wrap.
    """
    parts = [url or "", extract_domria_url_from_text(description) or "", extract_domria_url_from_text(title) or ""]
    if extra_urls:
        parts.extend(extra_urls)
    url_blob = " ".join(parts)

    by_slug = _slug_type_from_url_blob(url_blob)
    if by_slug:
        return by_slug

    by_badge = infer_realty_type_from_domria_badges(badge_texts)
    if by_badge:
        return by_badge

    blob = " ".join([title or "", description or ""]).lower()
    for word in _COMMERCIAL_UA:
        if word in blob:
            return "commercial"
    for word in _HOUSE_UA:
        if word in blob:
            return "house"
    if "квартир" in blob:
        return "apartment"

    if card_text:
        ct = card_text.lower()
        for word in _COMMERCIAL_UA:
            if word in ct:
                return "commercial"
        for word in _HOUSE_UA:
            if word in ct:
                return "house"
        if "квартир" in ct:
            return "apartment"

    return "apartment"
