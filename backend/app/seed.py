"""Idempotent seed of the four selection pages' generic attribute templates."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attribute, AttributeGroup

# Each page holds 5 main attributes; each holds a few sub-attributes.
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


async def ensure_attributes(session: AsyncSession) -> None:
    """Seed groups + attributes, skipping any that already exist by name."""
    for page, groups in TEMPLATES.items():
        for group_name, sub_names in groups:
            existing_group = await session.scalar(
                select(AttributeGroup).where(
                    AttributeGroup.page == page,
                    AttributeGroup.name == group_name,
                )
            )
            if existing_group:
                continue

            group = AttributeGroup(page=page, name=group_name)
            session.add(group)
            await session.flush()
            for sub_name in sub_names:
                session.add(Attribute(group_id=group.id, name=sub_name))

    await session.commit()