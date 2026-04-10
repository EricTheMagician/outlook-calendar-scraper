import logging
from playwright.async_api import Page, expect

log = logging.getLogger("scraper.auth")


async def authenticate(
    page: Page, email: str = None, get_email=None, get_password=None, get_totp=None
):
    """
    Handles the Microsoft login flow.
    If get_password or get_totp are None, it expects the user to enter them manually in the browser.
    """
    log.info("Starting authentication flow")

    # Wait for the login form to appear
    try:
        await page.wait_for_selector('input[type="email"]', timeout=10000)
    except Exception:
        log.info(
            "No email login input found, maybe already logged in or unexpected page state."
        )
        return

    email_val = None
    if email:
        email_val = email
    elif get_email:
        log.info("Using provided email callback.")
        email_val = get_email()

    if email_val:
        log.info("Filling email.")
        await page.wait_for_timeout(1000)
        await page.locator('input[type="email"]').focus()
        await page.wait_for_timeout(500)
        await page.locator('input[type="email"]').press_sequentially(
            email_val, delay=10
        )
        await page.wait_for_timeout(500)
        await page.click('input[type="submit"]')
    else:
        log.info("No email provided. Waiting for user to enter email manually.")
        log.warning("Please enter your email in the browser window and continue.")
        await page.pause()

    # Check for password field or other prompts
    try:
        await page.wait_for_selector('input[type="password"]', timeout=5000)
        log.info("Password field found.")
        if get_password:
            log.info("Using provided password callback.")
            password = get_password()
            await page.wait_for_timeout(1000)
            await page.locator('input[type="password"]').focus()
            await page.wait_for_timeout(500)
            await page.locator('input[type="password"]').press_sequentially(
                password, delay=50
            )
            await page.wait_for_timeout(500)
            await page.click('input[type="submit"]')
            await page.wait_for_timeout(2000)
        else:
            log.info(
                "No password callback provided. Waiting for user to enter password manually."
            )
            # Use pause so the user can interact
            log.warning(
                "Please enter your password in the browser window and continue."
            )
            await page.pause()
    except Exception:
        log.info(
            "No explicit password field appeared (maybe cached, or went straight to TOTP/MFA)."
        )

    # Wait for potential intermediate step "Verify your identity" -> "Use a verification code"
    try:
        log.info("Checking for 'Verify your identity' intermediate step...")
        # Add a short delay to allow the DOM to render after password submission
        await page.wait_for_timeout(3000)

        verify_code_btn = page.locator('text="Use a verification code"')
        count = await verify_code_btn.count()
        log.info(f"Found {count} elements matching 'Use a verification code' text.")

        if count > 0:
            is_vis = await verify_code_btn.first.is_visible(timeout=2000)
            log.info(f"Is the first matching element visible? {is_vis}")
            if is_vis:
                log.info(
                    "Clicking 'Use a verification code' button (using force=True)."
                )
                await verify_code_btn.first.click(force=True)
                await page.wait_for_timeout(2000)
            else:
                log.info("The element was found but is hidden.")
        else:
            log.info(
                "No elements containing the text 'Use a verification code' were found in the DOM."
            )

    except Exception as e:
        log.warning(f"Failed to check or click verification button: {e}")
        pass

    # Wait for potential TOTP or approve sign in from authenticator app
    # After password, there could be a TOTP code input
    try:
        # Simplistic check: look for an input that takes a code
        # Many Microsoft forms use input[name="otc"] for one-time code
        otc_input = page.locator('input[name="otc"]')
        if await otc_input.count() > 0 and await otc_input.is_visible(timeout=3000):
            log.info("TOTP field found.")
            if get_totp:
                log.info("Using provided TOTP callback.")
                totp = get_totp()
                await page.wait_for_timeout(1000)
                await otc_input.focus()
                await page.wait_for_timeout(500)
                await otc_input.press_sequentially(totp, delay=50)
                await page.wait_for_timeout(500)
                await page.click('input[type="submit"]')
                await page.wait_for_timeout(2000)
            else:
                log.info(
                    "No TOTP callback provided. Waiting for user to enter manual TOTP."
                )
                log.warning(
                    "Please enter your TOTP code in the browser window and continue."
                )
                await page.pause()
    except Exception:
        pass

    # Handle 'Stay signed in?' prompt
    try:
        # Check explicitly for "Stay signed in?" to avoid clicking "Cancel" (also #idBtn_Back) on other forms
        stay_signed_text = page.locator('text="Stay signed in?"')
        if (
            await stay_signed_text.count() > 0
            and await stay_signed_text.first.is_visible(timeout=5000)
        ):
            btn_no = page.locator("#idBtn_Back")
            if await btn_no.count() > 0 and await btn_no.is_visible(timeout=2000):
                log.info("Handling 'Stay signed in' prompt - clicking No.")
                await btn_no.click()
    except Exception:
        pass

    log.info("Auth flow steps completed. Waiting for calendar to load...")
