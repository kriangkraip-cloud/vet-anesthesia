#!/usr/bin/env python3
"""Upload photos saved by backup_images.py back to a running Vet Anesthesia site.

Use this after the database has been restored (the database rows point at the files).

    python3 scripts/restore_images.py https://ansanes.up.railway.app --src ~/Desktop/ansanes_images

Asks for an admin username and password (typed here, never saved or printed).
Safe to run again: it just overwrites each file with the same content.
Only the Python standard library is needed.
"""
import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"}


def login(base, username, password):
    body = urllib.parse.urlencode({"username": username, "password": password}).encode()
    req = urllib.request.Request(f"{base}/api/auth/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Login failed (HTTP {e.code}). Check the username and password.")


def upload(base, token, rid, name, path, tries=3):
    url = f"{base}/api/backup/images/{rid}/{urllib.parse.quote(name)}"
    with open(path, "rb") as f:
        data = f.read()
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(url, data=data, method="PUT", headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["bytes"]
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code in (400, 403, 404, 405):
                raise RuntimeError(err + " — is this the new version of the site (with the restore endpoint)?")
        except Exception as e:
            err = str(e)
        time.sleep(2 * attempt)
    raise RuntimeError(err)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_url")
    ap.add_argument("--src", required=True, help="folder that contains procedure_images/ (the --out of backup_images.py)")
    ap.add_argument("--user", default=None)
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    src = os.path.expanduser(args.src)
    root = os.path.join(src, "procedure_images")
    if not os.path.isdir(root):
        root = src if os.path.basename(src.rstrip("/")) == "procedure_images" else root
    if not os.path.isdir(root):
        sys.exit(f"Folder not found: {root}")

    files = []
    for rid in sorted(os.listdir(root)):
        folder = os.path.join(root, rid)
        if rid.isdigit() and os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if os.path.splitext(name)[1].lower() in EXTS:
                    files.append((int(rid), name, os.path.join(folder, name)))
    print(f"{len(files)} files to upload from {root}")
    if not files:
        return

    username = args.user or os.environ.get("VET_USER") or input("Admin username: ").strip()
    password = os.environ.get("VET_PASSWORD") or getpass.getpass("Password (hidden): ")
    token = login(base, username, password)

    ok, failed, total = 0, [], 0
    for n, (rid, name, path) in enumerate(files, 1):
        try:
            total += upload(base, token, rid, name, path)
            ok += 1
            print(f"  [{n}/{len(files)}] {rid}/{name}")
        except Exception as e:
            failed.append((rid, name, str(e)))
            print(f"  [{n}/{len(files)}] FAILED {rid}/{name}: {e}")
    print(f"\nUploaded {ok}/{len(files)} files ({total / 1_048_576:.1f} MB). Failed: {len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
