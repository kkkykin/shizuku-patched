#!/usr/bin/env python3
"""Prepare signing.properties using Actions secrets or a fresh debug key."""

import base64
import os
from pathlib import Path
import subprocess
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
if any(secrets.values()) and not all(secrets.values()):
    raise SystemExit("Configure all four signing secrets: " + ", ".join(names))

os.umask(0o077)
if secrets["KEYSTORE"]:
    try:
        key_file.write_bytes(base64.b64decode("".join(secrets["KEYSTORE"].split()), validate=True))
    except ValueError:
        raise SystemExit("KEYSTORE must contain a base64-encoded keystore.") from None
    mode = "custom"
else:
    subprocess.run([
        "keytool", "-genkeypair", "-keystore", str(key_file),
        "-storepass", "android", "-keypass", "android",
        "-alias", "androiddebugkey", "-dname", "CN=Android Debug,O=Android,C=US",
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
    ], check=True, stdout=subprocess.DEVNULL)
    secrets.update(KEYSTORE_PASSWORD="android", KEYSTORE_ALIAS="androiddebugkey",
                   KEYSTORE_ALIAS_PASSWORD="android")
    mode = "debug"

properties = {"KEYSTORE_FILE": str(key_file),
              **{name: secrets[name] for name in names if name != "KEYSTORE"}}
(source_dir / "signing.properties").write_text(
    "".join(f"{name}={escape_property(value)}\n" for name, value in properties.items()),
    encoding="ascii",
)
print(f"signing={mode}")
