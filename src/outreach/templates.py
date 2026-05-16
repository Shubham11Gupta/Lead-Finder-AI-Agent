"""Template library and rendering helpers for first-touch outreach."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PERSONA_FOUNDER = "founder_cofounder"
PERSONA_GROWTH = "head_of_growth"
PERSONA_BRAND = "ecommerce_or_brand_manager"

CHANNEL_EMAIL = "email"
CHANNEL_INSTAGRAM_DM = "instagram_dm"
CHANNEL_WHATSAPP = "whatsapp"

SIGNAL_NEW_LAUNCH = "new_launch"
SIGNAL_PAID_ADS = "paid_ads"
SIGNAL_LOW_UGC = "low_ugc"
SIGNAL_REVIEW_REQUEST = "review_request"
SIGNAL_SAMPLING = "sampling"
SIGNAL_GENERIC = "generic"


@dataclass(slots=True)
class TemplateDefinition:
    template_id: str
    persona: str
    channel: str
    signals: set[str]
    subject: str | None
    opening_line: str
    value_line: str
    cta_line: str
    fallback_line: str


TEMPLATE_LIBRARY: list[TemplateDefinition] = [
    TemplateDefinition(
        template_id="T1",
        persona=PERSONA_FOUNDER,
        channel=CHANNEL_EMAIL,
        signals={SIGNAL_NEW_LAUNCH, SIGNAL_GENERIC},
        subject="Launch to Repeat Purchase Loop",
        opening_line="Hi {contact_name}, noticed {brand_name} recently launched {sku_or_product}.",
        value_line=(
            "We help early D2C brands run a closed loop: Trio Box samples -> verified feedback -> "
            "Trio Coins -> full-size conversion, while generating zero-party insights."
        ),
        cta_line="Open to a 15-minute pilot discussion for one SKU?",
        fallback_line="If I reached the wrong person, could you point me to whoever owns growth or launch performance?",
    ),
    TemplateDefinition(
        template_id="T2",
        persona=PERSONA_FOUNDER,
        channel=CHANNEL_INSTAGRAM_DM,
        signals={SIGNAL_PAID_ADS, SIGNAL_GENERIC},
        subject=None,
        opening_line="Hey {brand_name} team, saw you actively promoting your products and loved the momentum.",
        value_line=(
            "We support D2C founders with a Trio Box trial model that improves first-purchase trust and "
            "converts verified trial users into full-size buyers."
        ),
        cta_line="Would you be open to a quick 15-minute pilot chat?",
        fallback_line="Happy to share a one-SKU pilot outline here if easier.",
    ),
    TemplateDefinition(
        template_id="T3",
        persona=PERSONA_GROWTH,
        channel=CHANNEL_EMAIL,
        signals={SIGNAL_LOW_UGC, SIGNAL_REVIEW_REQUEST, SIGNAL_GENERIC},
        subject="Improve UGC Quality for {brand_name}",
        opening_line=(
            "Hi {contact_name}, I noticed a strong product push at {brand_name} and an opportunity to deepen "
            "verified review volume."
        ),
        value_line=(
            "Our flow captures structured, verified trial feedback and links it to conversion behavior, giving "
            "your growth team actionable zero-party signals."
        ),
        cta_line="Would a one-SKU pilot brief be useful this week?",
        fallback_line="If helpful, I can send a short example of how we map feedback signals to campaign decisions.",
    ),
    TemplateDefinition(
        template_id="T4",
        persona=PERSONA_GROWTH,
        channel=CHANNEL_INSTAGRAM_DM,
        signals={SIGNAL_PAID_ADS, SIGNAL_GENERIC},
        subject=None,
        opening_line="Hi, noticed {brand_name} is running active campaigns and scaling awareness.",
        value_line=(
            "We run a sample-led conversion loop so paid traffic can be supported by verified trial feedback and "
            "stronger first-order confidence."
        ),
        cta_line="Open to a quick chat on a one-SKU test?",
        fallback_line="Can share a concise pilot flow directly in DM if preferred.",
    ),
    TemplateDefinition(
        template_id="T5",
        persona=PERSONA_BRAND,
        channel=CHANNEL_EMAIL,
        signals={SIGNAL_LOW_UGC, SIGNAL_REVIEW_REQUEST, SIGNAL_GENERIC},
        subject="Stronger Product Feedback Loop for {brand_name}",
        opening_line=(
            "Hi {contact_name}, saw {brand_name} in {category} and noticed strong potential to improve "
            "product-level review depth."
        ),
        value_line=(
            "Trio Box trials bring in verified product feedback and create a rewards-led path to full-size purchase."
        ),
        cta_line="Would you like a one-page pilot plan for your top SKU?",
        fallback_line="If relevant, I can tailor the plan to your current launch calendar.",
    ),
    TemplateDefinition(
        template_id="T6",
        persona=PERSONA_BRAND,
        channel=CHANNEL_WHATSAPP,
        signals={SIGNAL_SAMPLING, SIGNAL_GENERIC},
        subject=None,
        opening_line="Hi {contact_name}, this is {sender_name} from {sender_company}. We help D2C brands run sample-led discovery.",
        value_line=(
            "For brands like {brand_name}, Trio Box trials + verified feedback + Trio Coins can improve "
            "full-size conversion while generating zero-party insights."
        ),
        cta_line="Can we schedule a 15-minute call to discuss a one-SKU pilot?",
        fallback_line="If easier, I can send a short pilot summary on WhatsApp first.",
    ),
]


def render_template(
    template: TemplateDefinition,
    *,
    lead: dict[str, Any],
    sender_name: str,
    sender_company: str,
) -> tuple[str | None, str]:
    values = _placeholder_values(lead, sender_name=sender_name, sender_company=sender_company)

    subject = _render_line(template.subject, values) if template.subject else None
    opening = _render_line(template.opening_line, values)
    value_line = _render_line(template.value_line, values)
    cta = _render_line(template.cta_line, values)
    fallback = _render_line(template.fallback_line, values)

    lines = [opening, "", value_line, "", cta, "", fallback]
    if template.channel == CHANNEL_EMAIL:
        lines.extend(
            [
                "",
                f"Best,",
                f"{values['sender_name']}",
                f"{values['sender_company']}",
                "If this is not relevant, reply 'no' and we will not message again automatically.",
            ]
        )

    body = "\n".join(lines)
    return subject, body


def _placeholder_values(
    lead: dict[str, Any],
    *,
    sender_name: str,
    sender_company: str,
) -> dict[str, str]:
    brand_name = _safe_text(lead.get("brand_name"), default="your brand")
    category = _safe_text(lead.get("category"), default="your category")
    contact_name = _safe_text(lead.get("contact_name"), default="there")
    sku_or_product = _safe_text(lead.get("sku_or_product"), default=f"{category} product")

    signal_observed = _safe_text(lead.get("signal_observed"), default="recent market activity")
    booking_link = _safe_text(lead.get("booking_link"), default="")
    whatsapp_number = _safe_text(lead.get("whatsapp_business_link_or_number"), default="")

    return {
        "brand_name": brand_name,
        "contact_name": contact_name,
        "category": category,
        "signal_observed": signal_observed,
        "sku_or_product": sku_or_product,
        "sender_name": sender_name,
        "sender_company": sender_company,
        "booking_link": booking_link,
        "whatsapp_number": whatsapp_number,
    }


def _render_line(template: str | None, values: dict[str, str]) -> str:
    if not template:
        return ""
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered


def _safe_text(value: Any, *, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default

