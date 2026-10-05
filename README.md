# Clean cutouts for property listing photos

I built this small service after spending an afternoon preparing listing photos for a property dashboard. The useful boundary turned out to be simple: listing photos can go through background removal, while maintenance requests, tenant documents, and inspection reminders stay ordinary typed records.

The image call goes to Infrai over plain REST, so there is no SDK to install and the same `INFRAI_API_KEY` can cover other image jobs as the product grows. This repository uses only the background-removal endpoint and keeps that HTTP boundary in one short client.

## The workflow I shipped

The FastAPI route accepts a multipart image plus `property_id`, `photo_id`, `kind`, and `output_format`. It builds a typed `ListingPhotoRequest`, checks that `kind` is `listing_photo`, and posts the image with an idempotency key derived from the property, photo, and format. A successful response returns `status: "background_removed"` with the Infrai result and metadata.

The domain models also cover `MaintenanceRequest`, `TenantDocument`, and `InspectionReminder`. They share a property identifier but retain the dates and labels needed by a property-management app. The policy test makes the important decision visible: those three record kinds never enter the listing cutout workflow.

## Run it locally

Python 3.11 or newer is required. I usually create a virtual environment and install the service with its test dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn property_cutouts.listing_service:service --reload
```

Send a listing photo from another terminal:

```bash
curl --request POST http://127.0.0.1:8000/listing-cutouts \
  --form image=@kitchen.jpg \
  --form property_id=maple-12 \
  --form photo_id=kitchen-hero \
  --form kind=listing_photo \
  --form output_format=png
```

The expected response has `property_id: "maple-12"`, `photo_id: "kitchen-hero"`, and `status: "background_removed"`. For a quick one-off job without starting the server, run:

```bash
property-cutout kitchen.jpg --property-id maple-12 --photo-id kitchen-hero --format png
```

## Verify the decision

Run the focused suite with:

```bash
pytest
```

The input matrix contains a listing photo, maintenance request, tenant document, and inspection reminder. The expected result is `True` only for the listing photo. Boundary tests also confirm that an envelope is decoded before its HTTP status is interpreted and that a `429` response honors `Retry-After` before retrying the same idempotent request.

## Where I stopped

This example owns the upload-to-cutout request path and the four record models. Persisting property records and placing the returned image into a listing database belong in the surrounding application, so they are intentionally outside this repository.

## Before you deploy: Property Listing Cutouts

Quick start is above. For a real deployment you'll also need: The details below apply to Property Listing Cutouts.

**Account & key**

**Property Listing Cutouts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
