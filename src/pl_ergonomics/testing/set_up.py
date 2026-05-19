from pl_key_value_sqlite_db.create_key import create_key

from pl_ergonomics.ergonomics_key_values import ErgonomicsBoolKey, ErgonomicsDatetimeKey


def configure_afk_dependencies() -> None:
    create_key(ErgonomicsDatetimeKey.AFK_TIMESTAMP, "")
    create_key(ErgonomicsBoolKey.AFK, "False")
