#!/usr/bin/env python3
"""Download every procedure image from a running Vet Anesthesia site to this computer.

The "Download Backup" button only saves the database (.db), not the photos. This script
fetches the photos through the site's own API, so it works even when the hosting
file browser cannot download large files.

    python3 scripts/backup_images.py https://ansanes.up.railway.app
    python3 scripts/backup_images.py https://ansanes.up.railway.app --out ~/Desktop/ansanes_images

It asks for an admin username and password (typed here, never saved or printed), and
writes   <out>/procedure_images/<record_id>/<filename>   — the same layout the server uses.
Re-running skips files that were already downloaded, so an interrupted run can be resumed.
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


def request(url, *, data=None, headers=None, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    return urllib.request.urlopen(req, timeout=timeout)


def login(base, username, password):
    body = urllib.parse.urlencode({"username": username, "password": password}).encode()
    try:
        with request(f"{base}/api/auth/token", data=body,
                     headers={"Content-Type": "application/x-www-form-urlencoded"}) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"Login failed (HTTP {e.code}). Check the username and password.")


def get_json(base, path, token):
    with request(f"{base}{path}", headers={"Authorization": f"Bearer {token}"}) as r:
        return json.load(r)


def download(base, token, record_id, filename, dest, tries=3):
    url = f"{base}/api/images/{record_id}/{urllib.parse.quote(filename)}?token={urllib.parse.quote(token)}"
    tmp = dest + ".part"
    for attempt in range(1, tries + 1):
        try:
            with request(url, timeout=180) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(tmp, dest)
            return os.path.getsize(dest)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None            # the file is not on the server any more
            err = f"HTTP {e.code}"
        except Exception as e:         # network hiccup: retry
            err = str(e)
        time.sleep(2 * attempt)
    raise RuntimeError(err)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base_url", help="e.g. https://ansanes.up.railway.app")
    ap.add_argument("--out", default="./images_backup", help="folder to write into (default ./images_backup)")
    ap.add_argument("--user", default=None, help="admin username (asked if omitted)")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    username = args.user or os.environ.get("VET_USER") or input("Admin username: ").strip()
    password = os.environ.get("VET_PASSWORD") or getpass.getpass("Password (hidden): ")
    token = login(base, username, password)
    print("Logged in. Listing images…")

    records = get_json(base, "/api/records", token)
    images = []
    for rec in records:
        for img in get_json(base, f"/api/records/{rec['id']}/images", token):
            images.append((rec["id"], img["filename"]))
    print(f"{len(images)} image entries in {len({r for r, _ in images})} records.")

    root = os.path.join(os.path.expanduser(args.out), "procedure_images")
    done = skipped = 0
    missing, failed, total_bytes = [], [], 0
    for n, (rid, name) in enumerate(images, 1):
        folder = os.path.join(root, str(rid))
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, name)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skipped += 1
            total_bytes += os.path.getsize(dest)
            continue
        try:
            size = download(base, token, rid, name, dest)
        except Exception as e:
            failed.append((rid, name, str(e)))
            print(f"  [{n}/{len(images)}] FAILED {rid}/{name}: {e}")
            continue
        if size is None:
            missing.append((rid, name))
            continue
        done += 1
        total_bytes += size
        print(f"  [{n}/{len(images)}] {rid}/{name}  {size / 1_048_576:.1f} MB")

    print("\n──────── Summary ────────")
    print(f"Downloaded now : {done}")
    print(f"Already had    : {skipped}")
    print(f"Not on server  : {len(missing)}   (database row exists but the photo file is already gone)")
    print(f"Failed         : {len(failed)}")
    print(f"Total on disk  : {total_bytes / 1_048_576:.1f} MB in {root}")
    if failed:
        print("Some downloads failed — run the same command again to retry them.")
        sys.exit(1)


if __name__ == "__main__":
    main()
