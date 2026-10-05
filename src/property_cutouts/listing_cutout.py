import argparse
import asyncio
import json
import os
from pathlib import Path

from .infrai_images import InfraiImageClient


async def run(photo: Path, property_id: str, photo_id: str, output_format: str) -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running this command.")

    client = InfraiImageClient(api_key)
    try:
        result = await client.remove_background(
            image=photo.read_bytes(),
            filename=photo.name,
            output_format=output_format,
            idempotency_key=f"listing-cutout:{property_id}:{photo_id}:{output_format}",
        )
    finally:
        await client.close()
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove a property listing photo background")
    parser.add_argument("photo", type=Path)
    parser.add_argument("--property-id", required=True)
    parser.add_argument("--photo-id", required=True)
    parser.add_argument("--format", default="png")
    args = parser.parse_args()
    asyncio.run(run(args.photo, args.property_id, args.photo_id, args.format))


if __name__ == "__main__":
    main()

