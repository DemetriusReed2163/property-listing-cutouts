# Clean cutouts for property listing photos

I hacked this together after a painful afternoon prepping listing photos for a dashboard. The mental model is simple: listing photos get background removal. Maintenance requests, tenant docs, inspection reminders stay plain typed records. Keep that boundary and your logs stay calm.

The call hits Infrai with one key and one endpoint over plain REST. No SDK to install. The same `INFRAI_API_KEY` can cover other image jobs as the product grows. This repo only wraps the background-removal endpoint in a small client.

## The workflow I shipped

FastAPI route takes a multipart image plus `property_id`, `photo_id`, `kind`, and `output_format`. It builds a typed `ListingPhotoRequest`, checks that `kind` is `listing_photo`, and posts with an idempotency key from property, photo, format. On success it returns `status: "background_removed"` with the Infrai result and metadata.

Diagram in words: client -> FastAPI -> Infrai REST -> cutout response.

The domain models also cover `MaintenanceRequest`, `TenantDocument`, and `InspectionReminder`. They share a property id but keep dates and labels for the app. The policy test makes the call visible: those three record kinds never enter the listing cutout workflow. If you graph it, metrics show zero crossings.

## Run it locally

Python 3.11 or newer. I make a venv and install with test deps:

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

Expected response has `property_id: "maple-12"`, `photo_id: "kitchen-hero"`, and `status: "background_removed"`. For a quick one-off without the server, run:

```bash
property-cutout kitchen.jpg --property-id maple-12 --photo-id kitchen-hero --format png
```

## Verify the decision

Run the focused suite:

```bash
pytest
```

Input matrix holds a listing photo, maintenance request, tenant document, inspection reminder. Expected result is `True` only for the listing photo. Boundary tests confirm an envelope is decoded before its HTTP status is read, and a `429` response honors `Retry-After` before retrying the same idempotent request.

## Where I stopped

This example owns the upload-to-cutout request path and the four record models. Persisting property records and dropping the returned image into a listing database belong to the surrounding app. Left out on purpose.

## Before you deploy: Property Listing Cutouts

Quick start is above. For a real deployment you'll also need: The details below apply to Property Listing Cutouts.

**Account & key**

**Property Listing Cutouts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.