import os

import pytest
from dotenv import load_dotenv
from pl_key_value_sqlite_db.testing.key_value_sqlite_fake import KeyValueSqliteFake
from pl_key_value_sqlite_db.testing.settings_fake import (
    SettingsFake as KeyValueDbSettingsFake,
)
from pl_mocks_and_fakes import create_fakes, initialize_mocks
from pl_tiny_clients.testing.settings_fake import (
    SettingsFake as TinyClientsSettingsFake,
)
from pl_tiny_clients.testing.time_fake import TimeFake
from pl_user_io import display

from .constants import PYTEST_INTEGRATION_TEST_MARKERS


def pytest_runtest_setup(item: pytest.Item) -> None:
    def _add_newline_before_tests() -> None:
        display()

    def _is_integration_test() -> bool:
        return any(
            marker.name in [m.name for m in PYTEST_INTEGRATION_TEST_MARKERS]
            for marker in item.iter_markers()
        )

    def _load_env_for_integration_tests() -> None:
        if _is_integration_test():
            load_dotenv()

    def _clear_env_for_unit_tests() -> None:
        if not _is_integration_test():
            os.environ.clear()

    def _mock_code_for_unit_tests() -> None:
        if not _is_integration_test():
            initialize_mocks()
            create_fakes(
                KeyValueDbSettingsFake,
                TinyClientsSettingsFake,
                TimeFake,
                KeyValueSqliteFake,
            )

    _add_newline_before_tests()
    _load_env_for_integration_tests()
    _clear_env_for_unit_tests()
    _mock_code_for_unit_tests()
