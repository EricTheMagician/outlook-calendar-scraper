import logging
import re
from playwright.async_api import Page

log = logging.getLogger("scraper.outlook")

# The extraction script — identical to what you'd run manually in DevTools.
# Tries the top-level document first, falls back to the first iframe's contentDocument.
_EXTRACT_JS = """
() => {
    return [...document.querySelectorAll('[data-calitemid]')].map(el => {
        const btn = el.querySelector('[role="button"][aria-label]');
        if (!btn) return null;

        const label = btn.getAttribute('aria-label');
        const parts = label.split(', ');

        const title = parts[0];
        const time  = parts[1];
        const date  = parts[2];

        const isRecurring = label.includes('Recurring event');
        const isTentative = label.includes('Tentative');
        const organizer   = (label.match(/By (.+?)(?:,|$)/) || [])[1] || null;
        const location    = parts.find(p =>
            p.includes('Teams') || p.includes('Meeting') || p.includes('Room')
        ) || null;

        return {
            title, date, time, location,
            organizer, isRecurring, isTentative,
            calitemid: el.getAttribute('data-calitemid')
        };
    }).filter(Boolean);
}
"""


async def extract_visible_events(page: Page) -> list[dict]:
    """Inject the extraction script and return the parsed event list."""
    log.info(f"Extracting events from {page.url}")
    events = await page.evaluate(_EXTRACT_JS)
    log.info(f"Extracted {len(events)} events")
    return events


async def navigate_calendar(page: Page, direction: str = "forward"):
    """Click the calendar's next/previous navigation button and wait for re-render."""
    if direction == "forward":
        # Matches labels like "Go to next month 2026 May" or "Go to next week"
        btn = page.get_by_role("button", name=re.compile(r"Go to next", re.IGNORECASE))
    else:
        btn = page.get_by_role(
            "button", name=re.compile(r"Go to previous", re.IGNORECASE)
        )

    await btn.first.click()
    # Wait for at least one event tile to re-render before extracting
    await page.wait_for_selector("[data-calitemid]", timeout=10_000)
    log.info(f"Navigated calendar {direction}")


async def set_calendar_view(page: Page, view: str = "month"):
    """Switch calendar to Week, Work week, or Month view for broader event coverage."""
    view_map = {
        "month": "Month",
        "week": "Week",
        "workweek": "Work week",
    }

    name = view_map.get(view.lower())
    if not name:
        raise ValueError(f"Unknown view '{view}'. Choose: month, week, workweek")

    await page.get_by_role("button", name=name, exact=True).click()
    await page.wait_for_selector("[data-calitemid]", timeout=10_000)
    log.info(f"Switched to {view} view")
