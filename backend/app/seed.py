"""
Idempotent seed of the four selection pages'
generic attribute templates using Prisma.
"""

from app.prisma_client import db


TEMPLATES: dict[int, list[tuple[str, list[str]]]] = {
    1: [
        ("Core Functionality", ["Tracking", "Reporting", "Automation", "Notifications"]),
        ("Integrations", ["REST API", "Webhooks", "Email", "Slack"]),
        ("Deployment", ["Cloud", "On-Premise", "Hybrid", "Edge"]),
        ("Scale", ["Small", "Medium", "Large", "Enterprise"]),
        ("Security", ["SSO", "2FA", "Audit Logs", "Encryption"]),
    ],
    2: [
        ("Interface", ["Web", "Mobile", "Desktop", "CLI"]),
        ("Language", ["English", "Spanish", "French", "German"]),
        ("Performance", ["Low Latency", "High Throughput", "Reliable", "Efficient"]),
        ("Data Handling", ["Batch", "Streaming", "Real-time", "Archival"]),
        ("Support", ["Self-service", "Chat", "Phone", "SLA"]),
    ],
    3: [
        ("Storage", ["PostgreSQL", "Redis", "S3", "Local Disk"]),
        ("Analytics", ["Dashboards", "Custom Queries", "Export", "Forecasts"]),
        ("Access Control", ["Roles", "Permissions", "Teams", "Whitelist"]),
        ("Notifications", ["Email", "Push", "SMS", "In-app"]),
        ("Compliance", ["GDPR", "SOC2", "ISO 27001", "HIPAA"]),
    ],
    4: [
        ("Hardware", ["Sensor", "Controller", "Gateway", "Chip"]),
        ("Protocol", ["MQTT", "Modbus", "HTTP", "BLE"]),
        ("Power", ["Battery", "Mains", "Solar", "PoE"]),
        ("Connectivity", ["Wi-Fi", "Ethernet", "Cellular", "Zigbee"]),
        ("Module", ["Input", "Display", "Actuator", "Communication"]),
    ],
}


async def ensure_attributes():

    for page, groups in TEMPLATES.items():

        for group_name, sub_names in groups:

            existing_group = await db.attribute_groups.find_first(
                where={
                    "page": page,
                    "name": group_name,
                }
            )

            if existing_group:
                continue

            group = await db.attribute_groups.create(
                data={
                    "page": page,
                    "name": group_name,
                }
            )

            for sub_name in sub_names:

                await db.attributes.create(
                    data={
                        "group_id": group.id,
                        "name": sub_name,
                    }
                )