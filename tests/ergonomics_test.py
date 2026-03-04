from datetime import datetime, timedelta

import pytest
from pl_key_value_sqlite_db.create_key import create_key
from pl_key_value_sqlite_db.save_bool import save_bool
from pl_key_value_sqlite_db.save_datetime import save_datetime
from pl_mocks_and_fakes import mock_for, stub
from pl_tiny_clients.delay import DelayResponse, delay
from pl_tiny_clients.display_power_events import DisplayPowerEventsResponse
from pl_tiny_clients.testing.assertions import assert_notified
from pl_tiny_clients.testing.mocks import (
    display_power_events_mock,
    notify_mock,
)
from pl_tiny_clients.testing.stubs import (
    stub_current_datetime,
    stub_display_power_events,
)

from pl_ergonomics.ergonomics import ergonomics, loop
from pl_ergonomics.ergonomics_key_values import ErgonomicsBoolKey, ErgonomicsDatetimeKey

from .constants import ARBITRARY_DATETIME, DEFAULT_DATETIME


def set_up(current_dt: datetime = ARBITRARY_DATETIME) -> None:
    create_key(ErgonomicsBoolKey.AFK, "")
    save_bool(ErgonomicsBoolKey.AFK, False)
    create_key(ErgonomicsDatetimeKey.AFK_TIMESTAMP, "")
    save_datetime(ErgonomicsDatetimeKey.AFK_TIMESTAMP, DEFAULT_DATETIME)
    stub_computer_awake()
    stub_display(ARBITRARY_DATETIME, ARBITRARY_DATETIME)
    stub_current_datetime(current_dt)


def stub_computer_asleep(t: timedelta) -> None:
    stub(delay)(DelayResponse(timedelta(minutes=0), t))


def stub_computer_awake() -> None:
    stub(delay)(DelayResponse(timedelta(minutes=0), None))


def stub_display(off: datetime, on: datetime) -> None:
    stub_display_power_events(DisplayPowerEventsResponse(off, on))


def _call_exists(message: str, title: str | None = None) -> bool:
    for call in notify_mock().call_args_list:
        if call[0][0] == message and (title is None or call[0][1] == title):
            return True
    return False


def assert_notified_once(message: str, title: str | None = None) -> None:
    if not _call_exists(message, title):
        pytest.fail(
            f"Expected to be notified once with message '{message}' and title '{title}'."
        )


def assert_not_notified(message: str, title: str | None = None) -> None:
    if _call_exists(message, title):
        pytest.fail(
            f"Expected to not be notified with message '{message}' and title '{title}', but was notified."
        )


def assert_short_break() -> None:
    assert_notified_once(
        "• Walk 20 feet away\n• Look 20 feet away for 20 seconds",
        title="Ergonomics",
    )


def assert_no_short_break() -> None:
    assert_not_notified(
        "• Walk 20 feet away\n• Look 20 feet away for 20 seconds",
        title="Ergonomics",
    )


def assert_long_break() -> None:
    assert_notified_once("Take a 5-minute break.", title="Ergonomics")


def assert_no_long_break() -> None:
    assert_not_notified("Take a 5-minute break.", title="Ergonomics")


def test_main_loop_notifies_about_exception() -> None:
    set_up()
    display_power_events_mock().side_effect = Exception("Test exception")

    with pytest.raises(Exception):
        ergonomics()

    assert_notified("Error in Ergonomics script.")


def test_waits_one_minute_every_loop() -> None:
    set_up()
    loop(ARBITRARY_DATETIME, ARBITRARY_DATETIME)

    mock_for(delay).assert_called_once_with(timedelta(minutes=1))


def test_take_a_short_break_after_20_minutes() -> None:
    set_up(current_dt=ARBITRARY_DATETIME + timedelta(minutes=20))
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME

    last_short_break, last_long_break = loop(last_short_break, last_long_break)

    assert_short_break()
    assert last_short_break == ARBITRARY_DATETIME + timedelta(minutes=20)


def test_dont_take_a_short_break_after_19_minutes() -> None:
    set_up(current_dt=ARBITRARY_DATETIME + timedelta(minutes=19))
    initial_last_short_break = ARBITRARY_DATETIME
    last_short_break = initial_last_short_break
    last_long_break = ARBITRARY_DATETIME

    last_short_break, last_long_break = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == initial_last_short_break


def test_take_an_long_break_after_60_minutes() -> None:
    set_up(current_dt=ARBITRARY_DATETIME + timedelta(minutes=60))
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME

    last_short_break, last_long_break = loop(last_short_break, last_long_break)

    assert_long_break()
    assert last_long_break == ARBITRARY_DATETIME + timedelta(minutes=60)


def test_dont_take_an_long_break_after_59_minutes() -> None:
    set_up(current_dt=ARBITRARY_DATETIME + timedelta(minutes=59))
    initial_last_long_break = ARBITRARY_DATETIME
    last_short_break = ARBITRARY_DATETIME
    last_long_break = initial_last_long_break

    last_short_break, last_long_break = loop(last_short_break, last_long_break)

    assert_no_long_break()
    assert last_long_break == initial_last_long_break


def test_skip_short_break_if_afk_for_break_time__computer_asleep() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_computer_asleep(timedelta(seconds=20))

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_dont_skip_short_break_if_afk_for_less_than_break_time__computer_asleep() -> (
    None
):
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_computer_asleep(timedelta(seconds=19))

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_dont_skip_short_break_if_not_afk__computer_asleep() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_computer_awake()

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_skip_long_break_if_afk_for_break_time__computer_asleep() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    stub_computer_asleep(timedelta(minutes=5))

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_no_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_dont_skip_long_break_if_afk_for_less_than_break_time__computer_asleep() -> (
    None
):
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    stub_computer_asleep(timedelta(minutes=4, seconds=59))

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_dont_skip_long_break_if_not_afk__computer_asleep() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    stub_computer_awake()

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_defer_short_break_if_afk_less_than_break_time__display() -> None:
    set_up()
    # The display can be off while the computer is still awake.

    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=19),
        ARBITRARY_DATETIME - timedelta(seconds=20),
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME - timedelta(minutes=20)


def test_skip_short_break_if_afk_for_break_time__display() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=20),
        ARBITRARY_DATETIME - timedelta(seconds=21),
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_dont_skip_short_break_if_not_afk__display() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=1),
        ARBITRARY_DATETIME - timedelta(seconds=0),
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_defer_long_break_if_afk_less_than_break_time__display() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    stub_display(
        ARBITRARY_DATETIME - timedelta(minutes=4, seconds=59),
        ARBITRARY_DATETIME - timedelta(minutes=5),
    )

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_no_long_break()
    assert last_long_break == ARBITRARY_DATETIME - timedelta(minutes=60)


def test_skip_long_break_if_afk_for_break_time__display() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    stub_display(
        ARBITRARY_DATETIME - timedelta(minutes=5),
        ARBITRARY_DATETIME - timedelta(minutes=5, seconds=1),
    )

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_no_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_dont_skip_long_break_if_not_afk__display() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=1),
        ARBITRARY_DATETIME - timedelta(seconds=0),
    )

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_defer_short_break_if_afk_less_than_break_time__using_explicit_afk() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP, ARBITRARY_DATETIME - timedelta(seconds=19)
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME - timedelta(minutes=20)


def test_skip_short_break_if_afk_for_break_time__using_explicit_afk() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP, ARBITRARY_DATETIME - timedelta(seconds=20)
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_dont_skip_short_break_if_not_afk__using_explicit_afk() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    save_bool(ErgonomicsBoolKey.AFK, False)

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_defer_long_break_if_afk_less_than_break_time__using_explicit_afk() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP,
        ARBITRARY_DATETIME - timedelta(minutes=4, seconds=59),
    )

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_no_long_break()
    assert last_long_break == ARBITRARY_DATETIME - timedelta(minutes=60)


def test_skip_long_break_if_afk_for_break_time__using_explicit_afk() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP, ARBITRARY_DATETIME - timedelta(minutes=5)
    )

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_no_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_dont_skip_long_break_if_not_afk__using_explicit_afk() -> None:
    set_up()
    last_short_break = ARBITRARY_DATETIME
    last_long_break = ARBITRARY_DATETIME - timedelta(minutes=60)
    save_bool(ErgonomicsBoolKey.AFK, False)

    _, last_long_break = loop(last_short_break, last_long_break)

    assert_long_break()
    assert last_long_break == ARBITRARY_DATETIME


def test_use_longest_afk_method_to_determine_afk_time__computer_asleep() -> None:
    set_up()
    # This test combines the three "skip short break" tests

    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_computer_asleep(timedelta(seconds=20))
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=19),
        ARBITRARY_DATETIME - timedelta(seconds=20),
    )
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP, ARBITRARY_DATETIME - timedelta(seconds=19)
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_use_longest_afk_method_to_determine_afk_time__display() -> None:
    set_up()
    # This test combines the three "skip short break" tests

    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_computer_asleep(timedelta(seconds=19))
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=20),
        ARBITRARY_DATETIME - timedelta(seconds=21),
    )
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP, ARBITRARY_DATETIME - timedelta(seconds=19)
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME


def test_use_longest_afk_method_to_determine_afk_time__using_explicit_afk() -> None:
    set_up()
    # This test combines the three "skip short break" tests

    last_short_break = ARBITRARY_DATETIME - timedelta(minutes=20)
    last_long_break = ARBITRARY_DATETIME
    stub_computer_asleep(timedelta(seconds=19))
    stub_display(
        ARBITRARY_DATETIME - timedelta(seconds=19),
        ARBITRARY_DATETIME - timedelta(seconds=20),
    )
    save_bool(ErgonomicsBoolKey.AFK, True)
    save_datetime(
        ErgonomicsDatetimeKey.AFK_TIMESTAMP, ARBITRARY_DATETIME - timedelta(seconds=20)
    )

    last_short_break, _ = loop(last_short_break, last_long_break)

    assert_no_short_break()
    assert last_short_break == ARBITRARY_DATETIME
