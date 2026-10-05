from datetime import date, datetime, timezone

import pytest

from property_cutouts.property_records import (
    InspectionReminder,
    ListingPhotoRequest,
    MaintenanceRequest,
    RecordKind,
    TenantDocument,
    accepts_background_removal,
)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (RecordKind.LISTING_PHOTO, True),
        (RecordKind.MAINTENANCE_REQUEST, False),
        (RecordKind.TENANT_DOCUMENT, False),
        (RecordKind.INSPECTION_REMINDER, False),
    ],
)
def test_only_listing_photos_enter_the_cutout_workflow(
    kind: RecordKind, expected: bool
) -> None:
    request = ListingPhotoRequest(
        property_id="maple-12",
        photo_id="kitchen-hero",
        kind=kind,
    )
    assert accepts_background_removal(request) is expected


def test_property_records_keep_their_operational_dates() -> None:
    maintenance = MaintenanceRequest(
        request_id="mr-41",
        property_id="maple-12",
        summary="Replace the hallway light",
        reported_at=datetime(2026, 9, 5, 9, 30, tzinfo=timezone.utc),
    )
    document = TenantDocument(
        document_id="doc-8",
        property_id="maple-12",
        document_type="move_in_checklist",
        received_on=date(2026, 9, 5),
    )
    reminder = InspectionReminder(
        reminder_id="inspect-3",
        property_id="maple-12",
        due_on=date(2026, 9, 12),
        area="smoke detectors",
    )
    assert maintenance.property_id == document.property_id == reminder.property_id
    assert reminder.due_on > document.received_on

