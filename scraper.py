import asyncio
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from config import CRM_LOGIN_URL, CRM_PASSWORD, CRM_URL, CRM_USERNAME

NAV_TIMEOUT_MS = 90_000
GOTO_WAIT = "domcontentloaded"
TCP_CONNECT_TIMEOUT_S = 8
BASE_URL = "https://crm.avroraro.lan"

ROW_SELECTOR = (
    "tr.main-grid-row.main-grid-row-body[data-type='task'], "
    "tr.main-grid-row.main-grid-row-body[data-id]"
)
TITLE_LINK_SELECTOR = "td:nth-of-type(3) a.task-title, a.task-title, a[href*='/tasks/task/view/']"


async def assert_crm_reachable(url: str) -> None:
    host = urlparse(url).hostname
    if not host:
        raise RuntimeError(f"CRM_LOGIN_URL invalid: {url}")
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, 443),
            timeout=TCP_CONNECT_TIMEOUT_S,
        )
        writer.close()
        await writer.wait_closed()
    except Exception as exc:
        raise RuntimeError(
            f"CRM inaccesibil la nivel TCP: {host}:443. Detaliu: {exc}"
        ) from exc


def _clean_title(text: str) -> str:
    if not text:
        return "N/A"
    t = " ".join(text.split())
    t = re.sub(r"\b\d+\s*/\s*\d+\b", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t or "N/A"


def _extract_task_id_from_href(href: str) -> str:
    m = re.search(r"/tasks/task/view/(\d+)/?", href or "")
    return m.group(1) if m else ""


def _normalize_link(href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(BASE_URL, href)


def parse_date_strict(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = " ".join(value.split()).strip()
    for fmt in (
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_active_date(date_text: str | None) -> datetime | None:
    if not date_text:
        return None
    raw = " ".join(date_text.split()).strip()
    now = datetime.now()

    try:
        return datetime.strptime(raw, "%B %d, %H:%M").replace(year=now.year)
    except ValueError:
        pass

    m = re.match(r"today,\s*(\d{1,2}):(\d{2})", raw, re.IGNORECASE)
    if m:
        return now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)

    m = re.match(r"yesterday,\s*(\d{1,2}):(\d{2})", raw, re.IGNORECASE)
    if m:
        dt = now - timedelta(days=1)
        return dt.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)

    return parse_date_strict(raw)


def _norm_name(value: str) -> str:
    return " ".join((value or "").lower().split()).strip()


def _extract_datetimes_from_text(value: str) -> list[datetime]:
    text = " ".join((value or "").split())
    if not text:
        return []
    out: list[datetime] = []
    patterns = (
        r"\b\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\b",
    )
    for p in patterns:
        for m in re.finditer(p, text):
            dt = parse_date_strict(m.group(0))
            if dt is not None:
                out.append(dt)
    return out


def _extract_first_assignment_from_history(html: str, assignee: str) -> datetime | None:
    """
    Returns earliest timestamp where current assignee appears in assignment-related history text.
    """
    if not html or not assignee:
        return None
    soup = BeautifulSoup(html, "html.parser")
    target = _norm_name(assignee)
    if not target:
        return None

    selectors = (
        "#task-detail-history .feed-post-text",
        "#task-detail-history .feed-post-contentview",
        "#task-detail-history [data-role='task-history-item']",
        ".feed-post-text",
        ".feed-post-contentview",
        ".task-log-item",
        ".tasks-log-item",
    )
    assignment_words = ("responsible", "assignee", "assigned", "reassigned", "responsabil")
    found: list[datetime] = []
    for selector in selectors:
        for el in soup.select(selector):
            text = el.get_text(" ", strip=True)
            low = _norm_name(text)
            if target not in low:
                continue
            if not any(w in low for w in assignment_words):
                continue
            found.extend(_extract_datetimes_from_text(text))
    if not found:
        return None
    return min(found)


async def enrich_first_assignment(page, ticket: dict) -> dict:
    if not ticket.get("link") or not ticket.get("assignee"):
        return ticket
    try:
        await page.goto(ticket["link"], wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        html = await page.content()
        first_dt = _extract_first_assignment_from_history(html, ticket.get("assignee", ""))
        if first_dt is not None:
            ticket["assigned_at"] = first_dt
    except Exception:
        return ticket
    return ticket


def parse_tickets(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tickets: list[dict] = []

    for row in soup.select(ROW_SELECTOR):
        task_id = (row.get("data-id") or "").strip()
        if not task_id or task_id.startswith("template_"):
            continue

        title_el = row.select_one(TITLE_LINK_SELECTOR)
        title = _clean_title(title_el.get_text(" ", strip=True) if title_el else "N/A")
        href = title_el.get("href", "").strip() if title_el else ""
        link = _normalize_link(href)

        assignee_el = row.select_one("td:nth-of-type(7) .tasks-grid-username-inner")
        assignee = assignee_el.get_text(strip=True) if assignee_el else "N/A"

        active_el = row.select_one("td:nth-of-type(4) #changedDate")
        active_txt = active_el.get_text(" ", strip=True) if active_el else None

        tickets.append(
            {
                "id": task_id or _extract_task_id_from_href(href),
                "title": title,
                "assignee": assignee,
                "assigned_at": parse_active_date(active_txt),
                "active_raw": active_txt or "",
                "link": link,
            }
        )

    seen: set[str] = set()
    out: list[dict] = []
    for t in tickets:
        tid = str(t.get("id", "")).strip()
        if not tid or tid in seen:
            continue
        seen.add(tid)
        out.append(t)
    return out


async def get_tickets(target_url: str | None = None) -> list[dict]:
    url = target_url or CRM_URL
    await assert_crm_reachable(CRM_LOGIN_URL)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        page.set_default_navigation_timeout(NAV_TIMEOUT_MS)

        await page.goto(CRM_LOGIN_URL, wait_until=GOTO_WAIT, timeout=NAV_TIMEOUT_MS)
        await page.fill('input[name="USER_LOGIN"]', CRM_USERNAME)
        await page.fill('input[name="USER_PASSWORD"]', CRM_PASSWORD)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT_MS)

        await page.goto(url, wait_until=GOTO_WAIT, timeout=NAV_TIMEOUT_MS)
        await page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT_MS)
        await page.wait_for_selector("table.main-grid-table, body", timeout=20_000)

        html = await page.content()
        tickets = parse_tickets(html)
        for i, t in enumerate(tickets):
            tickets[i] = await enrich_first_assignment(page, t)
        await browser.close()
        return tickets