import logging
from datetime import datetime, timedelta

import typer
from pl_key_value_sqlite_db.load_bool import load_bool
from pl_key_value_sqlite_db.load_datetime import load_datetime
from pl_tiny_clients.current_datetime import current_datetime
from pl_tiny_clients.delay import delay
from pl_tiny_clients.display_power_events import display_power_events
from pl_tiny_clients.notify import notify
from pl_user_io.display import display

from pl_ergonomics.ergonomics_key_values import ErgonomicsBoolKey, ErgonomicsDatetimeKey


# Exported for testing since the main function is an infinite loop
def loop(
    last_short_break: datetime, last_long_break: datetime
) -> tuple[datetime, datetime]:
    def _check_afk() -> tuple[bool, timedelta]:
        currently_afk = False
        recent_afk_time = timedelta(seconds=0)

        _, computer_asleep_time = delay(timedelta(minutes=1))
        if computer_asleep_time is not None:
            recent_afk_time = max(recent_afk_time, computer_asleep_time)

        display_off_timestamp, display_on_timestamp = display_power_events()
        display_is_off = display_off_timestamp > display_on_timestamp
        if display_is_off:
            currently_afk = True
            recent_afk_time = max(
                recent_afk_time, current_datetime() - display_off_timestamp
            )

        if load_bool(ErgonomicsBoolKey.AFK):
            currently_afk = True
            afk_timestamp = load_datetime(ErgonomicsDatetimeKey.AFK_TIMESTAMP)
            recent_afk_time = max(recent_afk_time, current_datetime() - afk_timestamp)

        return currently_afk, recent_afk_time

    currently_afk, recent_afk_time = _check_afk()

    if recent_afk_time >= timedelta(minutes=5):
        # I was AFK for 5 minutes, equivalent to the long break.
        last_short_break = current_datetime()
        last_long_break = current_datetime()
    elif recent_afk_time >= timedelta(seconds=20):
        # I have been AFK for 20 seconds, equivalent to the 20 20 20 20 rule.
        last_short_break = current_datetime()

    if currently_afk:
        return last_short_break, last_long_break

    if last_long_break <= current_datetime() - timedelta(hours=1):
        notify("Take a 5-minute break.", title="Ergonomics")
        return current_datetime(), current_datetime()

    if last_short_break <= current_datetime() - timedelta(minutes=20):
        notify(
            "• Walk 20 feet away\n• Look 20 feet away for 20 seconds",
            title="Ergonomics",
        )
        return current_datetime(), last_long_break

    return last_short_break, last_long_break


MINUTES_SHORT_BREAK = 20
MINUTES_LONG_BREAK = 60


def ergonomics() -> None:
    last_short_break = current_datetime()
    last_long_break = current_datetime()

    display("The Ergonomics script is running.")
    try:
        while True:
            # Ergonomics is a long-running app and is therefore more difficult to debug than other apps. Therefore, I expect these observability logs to be valuable.
            logging.debug(
                f"Last short break: {last_short_break}; Last long break: {last_long_break}"
            )
            last_short_break, last_long_break = loop(last_short_break, last_long_break)
    except Exception:
        notify("Error in Ergonomics script.")
        raise


def main() -> None:
    typer.run(ergonomics)  # pragma: no cover
