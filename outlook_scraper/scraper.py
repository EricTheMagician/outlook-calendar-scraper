import logging
from playwright.async_api import async_playwright
from .auth import authenticate
from .outlook_scraper import (
    extract_visible_events,
    navigate_calendar,
    set_calendar_view,
)

log = logging.getLogger("scraper.main")


async def run_outlook_scraper(
    email: str = None,
    headless: bool = False,
    get_email=None,
    get_password=None,
    get_totp=None,
) -> list[dict]:
    """
    Main entry point to scrape calendar events for the current month and the following 2 months.
    """
    all_events = {}

    async with async_playwright() as p:
        # Launch browser. We might want to use stealth if Microsoft blocks us
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to outlook calendar
        log.info("Navigating to Outlook Calendar...")
        await page.goto("https://outlook.office.com/calendar")

        # Authenticate
        await authenticate(
            page,
            email=email,
            get_email=get_email,
            get_password=get_password,
            get_totp=get_totp,
        )

        # Wait for calendar content to be ready
        log.info("Waiting for calendar grid...")
        try:
            await page.wait_for_selector("[data-calitemid]", timeout=30_000)
        except Exception as e:
            log.error(
                "Calendar did not load in time. You may need to complete auth manually."
            )
            if not headless:
                log.warning("Pausing for manual intervention...")
                await page.pause()
                await page.wait_for_selector("[data-calitemid]", timeout=30_000)
            else:
                raise e

        log.info("Calendar loaded. Switching to month view.")
        try:
            await set_calendar_view(page, "month")
        except Exception as e:
            log.warning(
                f"Could not explicitly set month view: {e}. Attempting extraction anyway."
            )

        # Loop 3 times to get current month + next 2
        for i in range(3):
            month_label = "current" if i == 0 else f"+{i}"
            log.info(f"Extracting events for month {month_label}...")

            # small delay to ensure rendering matches view switch or navigation
            await page.wait_for_timeout(2000)

            events = await extract_visible_events(page)
            for ev in events:
                cid = ev.get("calitemid")
                if cid and cid not in all_events:
                    all_events[cid] = ev

            if i < 2:
                log.info("Navigating to next month...")
                await navigate_calendar(page, "forward")

        log.info(f"Scrape complete. Extracted {len(all_events)} unique events.")
        await browser.close()

    return list(all_events.values())
