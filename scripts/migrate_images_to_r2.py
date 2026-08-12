"""One-time migration: upload local procedure_images/ files to Cloudflare R2.

Requires the R2_* env vars (see app/storage.py) plus SOURCE_IMAGES_DIR
pointing at the local DATA_DIR (the folder that directly contains
procedure_images/).

Usage:
    SOURCE_IMAGES_DIR=/app/data \\
    R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... R2_BUCKET_NAME=... \\
    python3 scripts/migrate_images_to_r2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import storage  # noqa: E402

SOURCE_IMAGES_DIR = os.environ.get(
    "SOURCE_IMAGES_DIR",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)


def main():
    if not storage.USE_R2:
        print("R2 env vars not set (R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY / R2_BUCKET_NAME). Aborting.")
        sys.exit(1)

    root = os.path.join(SOURCE_IMAGES_DIR, "procedure_images")
    if not os.path.isdir(root):
        print(f"No local procedure_images directory found at {root} — nothing to migrate.")
        return

    count = 0
    for record_id in os.listdir(root):
        record_dir = os.path.join(root, record_id)
        if not os.path.isdir(record_dir):
            continue
        for filename in os.listdir(record_dir):
            file_path = os.path.join(record_dir, filename)
            if not os.path.isfile(file_path):
                continue
            with open(file_path, "rb") as f:
                content = f.read()
            key = storage.image_key(int(record_id), filename)
            storage.save_file(key, content)
            count += 1
            print(f"  uploaded {key} ({len(content)} bytes)")

    print(f"Migration complete: {count} images uploaded to R2 bucket.")


if __name__ == "__main__":
    main()
