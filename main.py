import json
import asyncio
import logging
import argparse
import subprocess
from outlook_scraper import run_outlook_scraper, generate_ics

logging.basicConfig(level=logging.INFO)

import getpass


def get_email_callback():
    return input("Enter your email: ")


def get_password_callback():
    return getpass.getpass("Enter your password: ")


def get_totp_callback():
    return input("Enter your TOTP / OTP code (if any): ")


async def main():
    parser = argparse.ArgumentParser(description="Outlook Calendar Scraper Demo")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browsers headlessly (not recommended for first run!)",
    )

    args = parser.parse_args()

    print("Starting scraper. You will be prompted for credentials as needed.")

    events = await run_outlook_scraper(
        headless=args.headless,
        get_email=get_email_callback,
        get_password=get_password_callback,
        get_totp=get_totp_callback,
    )

    if events:
        generate_ics(events, "calendar.ics")
        print("\nSUCCESS! Saved to calendar.ics.")
    else:
        print("\nNo events found or extraction failed.")


if __name__ == "__main__":
    asyncio.run(main())
