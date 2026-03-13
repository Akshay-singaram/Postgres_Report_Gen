from datetime import datetime, timezone

DEBOUNCE_SECONDS = 30

# Placeholder commissioned date — same for all equipment
# Update last_maintenance to actual date when maintenance is performed
PLACEHOLDER_COMMISSIONED = datetime(2023, 1, 1, tzinfo=timezone.utc)

EQUIPMENT = [
    {
        "id": "FN-0504",
        "label": "Fan FN-0504",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "FN-0501B",
        "label": "Fan FN-0501B",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "FN-0501A",
        "label": "Fan FN-0501A",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "FN-0801A.3",
        "label": "Fan FN-0801A.3",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "FN-0801A.4",
        "label": "Fan FN-0801A.4",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "P-0801A.1",
        "label": "Pump P-0801A.1",
        "type": "pump",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "P-0801A.2",
        "label": "Pump P-0801A.2",
        "type": "pump",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "P-0802A",
        "label": "Pump P-0802A",
        "type": "pump",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "P-0802B",
        "label": "Pump P-0802B",
        "type": "pump",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "FN-1702",
        "label": "Fan FN-1702",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "P-1701",
        "label": "Pump P-1701",
        "type": "pump",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "FN-2002",
        "label": "Fan FN-2002",
        "type": "fan",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
    {
        "id": "P-2001",
        "label": "Pump P-2001",
        "type": "pump",
        "commissioned": PLACEHOLDER_COMMISSIONED,
        "last_maintenance": PLACEHOLDER_COMMISSIONED,
        "maintenance_interval_hours": 8760,  # TODO: set real interval
        "notes": "",
    },
]
