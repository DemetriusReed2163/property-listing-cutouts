import os
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .infrai_images import InfraiError, InfraiImageClient, InfraiTransportError
from .property_records import (
    CutoutResult,
    ListingPhotoRequest,
    RecordKind,
    accepts_background_removal,
)


service = FastAPI(title="Property listing cutouts")


@service.post("/listing-cutouts", response_model=CutoutResult)
async def create_listing_cutout(
    image: Annotated[UploadFile, File()],
    property_id: Annotated[str, Form()],
    photo_id: Annotated[str, Form()],
    kind: Annotated[RecordKind, Form()] = RecordKind.LISTING_PHOTO,
    output_format: Annotated[str, Form()] = "png",
) -> CutoutResult:
    request = ListingPhotoRequest(
        property_id=property_id,
        photo_id=photo_id,
        kind=kind,
        output_format=output_format,
    )
    if not accepts_background_removal(request):
        raise HTTPException(
            status_code=422,
            detail="Background removal is reserved for listing photos.",
        )

    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is not configured.")

    client = InfraiImageClient(api_key)
    try:
        result = await client.remove_background(
            image=await image.read(),
            filename=image.filename or f"{photo_id}.jpg",
            output_format=request.output_format,
            idempotency_key=f"listing-cutout:{property_id}:{photo_id}:{output_format}",
        )
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await client.close()

    return CutoutResult(
        property_id=property_id,
        photo_id=photo_id,
        status="background_removed",
        image=result["data"],
        metadata=result["metadata"] if isinstance(result["metadata"], dict) else None,
    )

