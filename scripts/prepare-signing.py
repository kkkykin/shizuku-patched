#!/usr/bin/env python3
"""Prepare signing.properties using Actions secrets or the bundled emacs-keystore."""

import base64
import os
from pathlib import Path
import sys


def escape_property(value):
    escapes = {"\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t",
               "\f": "\\f", " ": "\\ ", "=": "\\=", ":": "\\:"}
    units = value.encode("utf-16-be")
    result = []
    for offset in range(0, len(units), 2):
        unit = int.from_bytes(units[offset:offset + 2], "big")
        char = chr(unit)
        result.append(escapes.get(char, char) if unit < 128 else f"\\u{unit:04x}")
    return "".join(result)


if len(sys.argv) != 2:
    raise SystemExit("Usage: prepare-signing.py PATH_TO_SHIZUKU")

source_dir = Path(sys.argv[1]).resolve()
key_file = Path(os.environ["RUNNER_TEMP"]) / "shizuku-patched-signing.jks"
names = ("KEYSTORE", "KEYSTORE_PASSWORD", "KEYSTORE_ALIAS", "KEYSTORE_ALIAS_PASSWORD")
secrets = {name: os.environ.get(name, "") for name in names}
custom_signing = any(secrets.values())
if custom_signing and not all(secrets[name] for name in names[:3]):
    raise SystemExit("Configure KEYSTORE, KEYSTORE_PASSWORD, and KEYSTORE_ALIAS together.")

os.umask(0o077)
if custom_signing:
    try:
        key_file.write_bytes(base64.b64decode("".join(secrets["KEYSTORE"].split()), validate=True))
    except ValueError:
        raise SystemExit("KEYSTORE must contain a base64-encoded keystore.") from None
    secrets["KEYSTORE_ALIAS_PASSWORD"] = (
        secrets["KEYSTORE_ALIAS_PASSWORD"] or secrets["KEYSTORE_PASSWORD"]
    )
    mode = "custom"
else:
    bundled_key = Path(__file__).resolve().parent.parent / "emacs-keystore"
    if not bundled_key.is_file():
        raise SystemExit("Default signing keystore is missing: emacs-keystore")
    key_file.write_bytes(bundled_key.read_bytes())
    secrets.update(KEYSTORE_PASSWORD="emacs1", KEYSTORE_ALIAS="Emacs keystore",
                   KEYSTORE_ALIAS_PASSWORD="emacs1")
    mode = "emacs-keystore"

properties = {"KEYSTORE_FILE": str(key_file),
              **{name: secrets[name] for name in names if name != "KEYSTORE"}}
(source_dir / "signing.properties").write_text(
    "".join(f"{name}={escape_property(value)}\n" for name, value in properties.items()),
    encoding="ascii",
)
print(f"signing={mode}")
