from pl_key_value_sqlite_db.key_types import BoolKey, DatetimeKey


class ErgonomicsBoolKey(BoolKey):
    AFK = "afk"


class ErgonomicsDatetimeKey(DatetimeKey):
    AFK_TIMESTAMP = "afk_timestamp"
