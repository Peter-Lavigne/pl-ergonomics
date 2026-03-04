from datetime import datetime

from pl_tiny_clients.constants import SYSTEM_TIMEZONE

ARBITRARY_DATETIME = datetime.fromtimestamp(
    946684800, tz=SYSTEM_TIMEZONE
)  # January 1, 2000 at 00:00:00 in the system timezone
DEFAULT_DATETIME = ARBITRARY_DATETIME
