from datetime import datetime

from pl_key_value_sqlite_db.load_bool import load_bool
from pl_key_value_sqlite_db.load_datetime import load_datetime
from pl_tiny_clients.testing.stubs import stub_current_datetime

from pl_ergonomics.afk import afk
from pl_ergonomics.ergonomics_key_values import ErgonomicsBoolKey, ErgonomicsDatetimeKey
from pl_ergonomics.testing.set_up import configure_afk_dependencies

from .constants import SYSTEM_TIMEZONE


def _set_up() -> None:
    configure_afk_dependencies()


def test_sets_afk_timestamp() -> None:
    _set_up()
    stub_current_datetime(datetime(2024, 1, 1, 12, 0, 0))

    with afk():
        pass

    assert load_datetime(ErgonomicsDatetimeKey.AFK_TIMESTAMP) == datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=SYSTEM_TIMEZONE
    )


def test_sets_afk_true_and_false() -> None:
    _set_up()

    with afk():
        assert load_bool(ErgonomicsBoolKey.AFK) is True

    assert load_bool(ErgonomicsBoolKey.AFK) is False
