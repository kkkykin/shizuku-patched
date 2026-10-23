#!/usr/bin/env python3
"""Install the SDK required by upstream, including integer API path compatibility."""

import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

if len(sys.argv) != 2:
    raise SystemExit("Usage: install-android-sdk.py PATH_TO_SHIZUKU")

build_gradle = (Path(sys.argv[1]) / "build.gradle").read_text()


def setting(name, pattern):
    match = re.search(r"\b" + name + r"\s*=\s*" + pattern, build_gradle)
    if not match:
        raise SystemExit(f"Cannot read {name} from upstream build.gradle")
    return match.group(1)


api = setting("compileSdk", r"(\d+)\b")
build_tools = setting("buildToolsVersion", r'["\x27]([^"\x27]+)["\x27]')
ndk = setting("ndkVersion", r'["\x27]([^"\x27]+)["\x27]')
sdk_dir = Path(os.environ["ANDROID_HOME"])

subprocess.run([
    "sdkmanager", "--install", f"build-tools;{build_tools}",
    f"ndk;{ndk}", "cmake;3.31.6",
], check=True)

platform_dir = sdk_dir / "platforms" / f"android-{api}"
if not (platform_dir / "android.jar").is_file():
    base_url = "https://dl.google.com/android/repository/"
    with urllib.request.urlopen(base_url + "repository2-3.xml", timeout=60) as response:
        packages = {item.attrib["path"]: item
                    for item in ET.fromstring(response.read()).findall("remotePackage")}
    package = packages.get(f"platforms;android-{api}")
    if package is None:
        package = packages.get(f"platforms;android-{api}.0")
    if package is None:
        raise SystemExit(f"Android SDK Platform {api} is not published.")
    archive = package.find("archives/archive/complete")
    checksum = archive.find("checksum")
    digest = hashlib.new(checksum.attrib["type"])
    with tempfile.TemporaryDirectory(prefix="shizuku-sdk-", dir=os.environ["RUNNER_TEMP"]) as temporary:
        downloaded = Path(temporary) / "platform.zip"
        with urllib.request.urlopen(base_url + archive.findtext("url"), timeout=60) as response:
            with downloaded.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
        if digest.hexdigest() != checksum.text.strip():
            raise SystemExit("Android platform archive checksum mismatch.")
        with zipfile.ZipFile(downloaded) as platform_zip:
            platform_zip.extractall(Path(temporary) / "extracted")
        properties = list((Path(temporary) / "extracted").glob("*/source.properties"))
        if len(properties) != 1:
            raise SystemExit("Unexpected Android platform archive layout.")
        unpacked = properties[0].parent
        # AGP 8.11 expects android-37 and an integer AndroidVersion.ApiLevel.
        # Google's SDK 37.0 archive contains the same API 37 android.jar.
        text = properties[0].read_text()
        text, count = re.subn(
            rf"(?m)^AndroidVersion\.ApiLevel={re.escape(api)}(?:\.0)?$",
            f"AndroidVersion.ApiLevel={api}", text,
        )
        if count != 1:
            raise SystemExit("Unexpected Android platform API level.")
        properties[0].write_text(text)
        platform_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(unpacked), platform_dir)

with open(os.environ["GITHUB_ENV"], "a") as output:
    output.write(f"ANDROID_BUILD_TOOLS={build_tools}\n")
print(f"Installed Android API {api}, Build Tools {build_tools}, NDK {ndk}, CMake 3.31.6.")
