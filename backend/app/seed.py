"""
Idempotent seed helpers for:

1. The four embedded-system selection pages
2. Development ADMIN and USER accounts

The seed functions are safe to run repeatedly.
Existing user passwords are never overwritten automatically.
"""

from app.auth import hash_password
from app.config import settings
from app.prisma_client import db


TEMPLATES: dict[
    int,
    list[
        tuple[
            str,
            list[str],
        ]
    ],
] = {
    1: [
        (
            "Core Functionality",
            [
                "Tracking",
                "Reporting",
                "Automation",
                "Notifications",
            ],
        ),
        (
            "Integrations",
            [
                "REST API",
                "Webhooks",
                "Email",
                "Slack",
            ],
        ),
        (
            "Deployment",
            [
                "Cloud",
                "On-Premise",
                "Hybrid",
                "Edge",
            ],
        ),
        (
            "Scale",
            [
                "Small",
                "Medium",
                "Large",
                "Enterprise",
            ],
        ),
        (
            "Security",
            [
                "SSO",
                "2FA",
                "Audit Logs",
                "Encryption",
            ],
        ),
    ],
    2: [
        (
            "Interface",
            [
                "Web",
                "Mobile",
                "Desktop",
                "CLI",
            ],
        ),
        (
            "Language",
            [
                "English",
                "Spanish",
                "French",
                "German",
            ],
        ),
        (
            "Performance",
            [
                "Low Latency",
                "High Throughput",
                "Reliable",
                "Efficient",
            ],
        ),
        (
            "Data Handling",
            [
                "Batch",
                "Streaming",
                "Real-time",
                "Archival",
            ],
        ),
        (
            "Support",
            [
                "Self-service",
                "Chat",
                "Phone",
                "SLA",
            ],
        ),
    ],
    3: [
        (
            "Storage",
            [
                "PostgreSQL",
                "Redis",
                "S3",
                "Local Disk",
            ],
        ),
        (
            "Analytics",
            [
                "Dashboards",
                "Custom Queries",
                "Export",
                "Forecasts",
            ],
        ),
        (
            "Access Control",
            [
                "Roles",
                "Permissions",
                "Teams",
                "Whitelist",
            ],
        ),
        (
            "Notifications",
            [
                "Email",
                "Push",
                "SMS",
                "In-app",
            ],
        ),
        (
            "Compliance",
            [
                "GDPR",
                "SOC2",
                "ISO 27001",
                "HIPAA",
            ],
        ),
    ],
    4: [
        (
            "Hardware",
            [
                "Sensor",
                "Controller",
                "Gateway",
                "Chip",
            ],
        ),
        (
            "Protocol",
            [
                "MQTT",
                "Modbus",
                "HTTP",
                "BLE",
            ],
        ),
        (
            "Power",
            [
                "Battery",
                "Mains",
                "Solar",
                "PoE",
            ],
        ),
        (
            "Connectivity",
            [
                "Wi-Fi",
                "Ethernet",
                "Cellular",
                "Zigbee",
            ],
        ),
        (
            "Module",
            [
                "Input",
                "Display",
                "Actuator",
                "Communication",
            ],
        ),
    ],
}


async def ensure_attributes() -> None:
    """
    Create missing attribute groups and attributes.

    Existing groups and attributes are preserved. If a group exists
    but one of its expected attributes is missing, only the missing
    attribute is created.
    """

    for page, groups in TEMPLATES.items():
        for group_name, attribute_names in groups:
            group = (
                await db.attribute_groups.find_first(
                    where={
                        "page": page,
                        "name": group_name,
                    }
                )
            )

            if group is None:
                group = (
                    await db.attribute_groups.create(
                        data={
                            "page": page,
                            "name": group_name,
                        }
                    )
                )

            existing_attributes = (
                await db.attributes.find_many(
                    where={
                        "group_id": group.id,
                    }
                )
            )

            existing_attribute_names = {
                attribute.name
                for attribute
                in existing_attributes
            }

            for attribute_name in (
                attribute_names
            ):
                if (
                    attribute_name
                    in existing_attribute_names
                ):
                    continue

                await db.attributes.create(
                    data={
                        "group_id": group.id,
                        "name": attribute_name,
                    }
                )


async def ensure_users() -> None:
    """
    Create initial development ADMIN and USER accounts.

    User creation is skipped completely when SEED_DEFAULT_USERS=false.

    Existing users are not recreated and their password hashes are not
    overwritten. This prevents every backend restart from resetting a
    user's password.
    """

    if not settings.seed_default_users:
        return

    default_users = [
        {
            "username": (
                settings
                .initial_admin_username
            ),
            "password": (
                settings
                .initial_admin_password
            ),
            "role": "ADMIN",
        },
        {
            "username": (
                settings
                .initial_user_username
            ),
            "password": (
                settings
                .initial_user_password
            ),
            "role": "USER",
        },
    ]

    for user_data in default_users:
        username = (
            user_data["username"]
            .strip()
        )

        existing_user = (
            await db.users.find_unique(
                where={
                    "username": username,
                }
            )
        )

        if existing_user is not None:
            continue

        await db.users.create(
            data={
                "username": username,
                "password": hash_password(
                    user_data["password"]
                ),
                "role": user_data["role"],
            }
        )