# Outlook Calendar Scraper

This project is a tool to automate scraping calendar events from Outlook and export them to an `.ics` file. Since it works via the browser automation (Playwright), it can bypass or automate parts of the login flow.

**Note from the author:** This project was entirely vibe coded.

## Usage

By default, when you run the script, it will prompt you in the terminal to manually input your email, password, and TOTP/MFA code.

If you want fully automated runs (without being prompted), you **must update the 3 `get` methods** in `main.py` so that they return the correct values for your environment.

Specifically, update the following methods:
1. `get_email_callback()` - Should return your email address.
2. `get_password_callback()` - Should return your password.
3. `get_totp_callback()` - Should return your TOTP / MFA code (or handle retrieving it automatically).

Once configured (or if you prefer to use the default interactive prompts), run the script:

```bash
python main.py
```

### Command Line Arguments

The script supports the following CLI arguments:

- `--headless`: Runs the browser in headless mode (without a visible GUI window). It is **not recommended** to use this flag for the very first run, so you can visually verify that the login and extraction flow works smoothly.
