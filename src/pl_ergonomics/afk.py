from collections.abc import Iterator
from contextlib import contextmanager

from pl_key_value_sqlite_db.save_bool import save_bool
from pl_key_value_sqlite_db.save_datetime import save_datetime
from pl_tiny_clients.current_datetime import current_datetime

from pl_ergonomics.ergonomics_key_values import ErgonomicsBoolKey, ErgonomicsDatetimeKey


@contextmanager
def afk() -> Iterator[None]:
    # Uses of this function are untested. I'm unsure how to test calls without either (1) creating assertion hooks that check the database mid-run or (2) mocking this, neither of which seem ideal.

    save_datetime(ErgonomicsDatetimeKey.AFK_TIMESTAMP, current_datetime())
    save_bool(ErgonomicsBoolKey.AFK, True)
    try:
        yield
    finally:
        save_bool(ErgonomicsBoolKey.AFK, False)
