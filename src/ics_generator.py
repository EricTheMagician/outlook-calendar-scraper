import logging
from datetime import datetime, timedelta
from dateutil import parser
from ics import Calendar, Event

log = logging.getLogger("scraper.ics")


def parse_date_time(date_str: str, time_str: str):
    """
    Tries to parse the date and time strings from the frontend into a python datetime object.
    Outlook formats can be tricky (e.g., 'Today', 'Tomorrow', 'Oct 15', '10:00 AM to 11:00 AM').
    """
    now = datetime.now()

    # Clean up Date
    d_str = date_str.lower().strip()
    if d_str == "today":
        base_date = now.date()
    elif d_str == "tomorrow":
        base_date = (now + timedelta(days=1)).date()
    elif d_str == "yesterday":
        base_date = (now - timedelta(days=1)).date()
    else:
        try:
            # e.g. "Mon, Oct 15"
            base_date = parser.parse(d_str).date()

            # Since outlook UI might not include the year, if the parsed date is in the past by more than a month
            # when we are querying forward, we might need to adjust the year. Let's assume dateutil handles most.
            # E.g. if we are in Dec exploring Jan.
            if base_date.month < now.month and now.month - base_date.month > 6:
                base_date = base_date.replace(year=now.year + 1)
        except Exception as e:
            log.warning(f"Could not parse date string '{date_str}': {e}")
            base_date = now.date()

    # Clean up Time
    # Expected format like "10:00 AM to 11:00 AM" or "All day"
    t_str = time_str.lower().strip()
    start_dt = None
    end_dt = None
    all_day = False

    if "all day" in t_str:
        all_day = True
        start_dt = datetime.combine(base_date, datetime.min.time())
        end_dt = datetime.combine(base_date, datetime.max.time())
    else:
        parts = t_str.split(" to ")
        try:
            st = parser.parse(parts[0]).time()
            start_dt = datetime.combine(base_date, st)

            if len(parts) > 1:
                et = parser.parse(parts[1]).time()
                end_dt = datetime.combine(base_date, et)
            else:
                end_dt = start_dt + timedelta(hours=1)  # default duration
        except Exception as e:
            log.warning(f"Could not parse time string '{time_str}': {e}")
            all_day = True
            start_dt = datetime.combine(base_date, datetime.min.time())
            end_dt = datetime.combine(base_date, datetime.max.time())

    return start_dt, end_dt, all_day


def generate_ics(events_data: list[dict], output_path: str = "calendar.ics"):
    """
    Generates an ICS file from the extracted events list.
    """
    c = Calendar()

    for ev in events_data:
        try:
            e = Event()
            e.name = ev.get("title", "Untitled Event")
            e.location = ev.get("location")
            if ev.get("organizer"):
                e.description = f"Organizer: {ev.get('organizer')}"

            start_dt, end_dt, all_day = parse_date_time(
                ev.get("date", ""), ev.get("time", "")
            )

            e.begin = start_dt
            e.end = end_dt

            if all_day:
                e.make_all_day()

            c.events.add(e)
        except Exception as err:
            log.warning(f"Failed to process event {ev}: {err}")

    with open(output_path, "w") as f:
        f.writelines(c.serialize_iter())

    log.info(f"Generated ICS file at {output_path} with {len(c.events)} events.")
    return output_path
