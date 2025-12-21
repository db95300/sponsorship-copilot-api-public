from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from faker import Faker
from sqlalchemy import text
from sqlalchemy.engine import Engine

fake = Faker()


@dataclass(frozen=True)
class SeedConfig:
    num_athletes: int = 5
    num_sponsors: int = 20
    num_documents: int = 80
    num_interactions: int = 200
    seed: int = 42


def _fit_score(sector: str, athlete_position: str, market: str) -> float:
    base = 0.45
    if sector in {"automotive", "luxury", "sportswear"}:
        base += 0.10
    if athlete_position in {"PG", "SG"}:
        base += 0.05
    if market in {"FR", "UK"}:
        base += 0.05
    return max(0.0, min(1.0, base + random.uniform(-0.15, 0.25)))


def seed_fake_data(engine: Engine, config: SeedConfig) -> dict[str, int]:
    random.seed(config.seed)
    Faker.seed(config.seed)

    athletes: list[dict[str, Any]] = []
    sponsors: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    interactions: list[dict[str, Any]] = []

    positions = ["PG", "SG", "SF", "PF", "C"]
    levels = ["pro", "elite", "rising"]
    sectors = ["automotive", "sportswear", "fintech", "luxury", "nutrition", "tech"]
    markets = ["FR", "UK"]

    # Athletes
    for i in range(config.num_athletes):
        athletes.append(
            {
                "id": f"ath_{i+1:03d}",
                "full_name": fake.name(),
                "country": random.choice(["France", "UK", "Spain", "Germany", "USA"]),
                "position": random.choice(positions),
                "level": random.choice(levels),
            }
        )

    # Sponsors
    for i in range(config.num_sponsors):
        sponsors.append(
            {
                "id": f"sp_{i+1:03d}",
                "name": fake.company(),
                "sector": random.choice(sectors),
                "market": random.choice(markets),
                "budget_range": random.choice(["5-15k", "15-50k", "50-150k", "150k+"]),
            }
        )

    # Documents (EN/FR) with types to diversify evidence
    locales = ["en-GB", "fr-FR"]
    doc_types = [
        "outreach_guideline",
        "activation_template",
        "brand_safety_checklist",
        "bilingual_guideline",
        "negotiation_notes",
    ]

    for i in range(config.num_documents):
        owner_type = random.choice(["agency", "athlete"])
        owner_id = (
            random.choice(athletes)["id"] if owner_type == "athlete" else "agency_001"
        )
        locale = random.choice(locales)
        doc_type = random.choice(doc_types)

        if locale == "en-GB":
            title_map = {
                "outreach_guideline": "Premium outreach guidelines",
                "activation_template": "Drive-to-store activation template",
                "brand_safety_checklist": "Brand safety checklist (content approvals)",
                "bilingual_guideline": "Bilingual messaging guideline (EN/FR)",
                "negotiation_notes": "Negotiation notes: rights, whitelisting, usage",
            }
            text_map = {
                "outreach_guideline": (
                    "Keep claims measurable. Start with a 2-week pilot. "
                    "Anchor every statement in stats or past creative proof."
                ),
                "activation_template": (
                    "Structure: content day + hero reel + CTA stories. "
                    "Add tracking link/code. Report weekly: views, saves, CTR."
                ),
                "brand_safety_checklist": (
                    "Pre-approval: key messages, wardrobe, location, partner mentions. "
                    "No controversial topics. Ensure brand-safe captions and tags."
                ),
                "bilingual_guideline": (
                    "Provide EN and FR versions. Adapt tone to market; avoid literal translation. "
                    "Keep the CTA simple and direct."
                ),
                "negotiation_notes": (
                    "Clarify usage rights (organic vs paid), duration, territory, whitelisting, "
                    "exclusivity, and approval workflow before production."
                ),
            }
        else:
            title_map = {
                "outreach_guideline": "Guide d’outreach premium",
                "activation_template": "Template d’activation drive-to-store",
                "brand_safety_checklist": "Checklist brand safety (validations contenu)",
                "bilingual_guideline": "Guide de communication bilingue (EN/FR)",
                "negotiation_notes": "Notes de négo : droits, whitelisting, usages",
            }
            text_map = {
                "outreach_guideline": (
                    "Rester factuel. Commencer par un pilote court. "
                    "Ancrer chaque affirmation dans des chiffres ou des preuves créatives."
                ),
                "activation_template": (
                    "Structure : journée de contenu + vidéo principale + stories avec CTA. "
                    "Ajouter lien/code de tracking. Reporting hebdo : vues, saves, CTR."
                ),
                "brand_safety_checklist": (
                    "Validation : messages clés, tenue, lieu, mentions partenaires. "
                    "Éviter les sujets sensibles. Légendes et tags brand-safe."
                ),
                "bilingual_guideline": (
                    "Fournir une version EN et FR. Adapter le ton au marché ; éviter la traduction littérale. "
                    "CTA simple et direct."
                ),
                "negotiation_notes": (
                    "Clarifier droits d’usage (organique vs paid), durée, territoire, whitelisting, "
                    "exclusivité et workflow de validation avant production."
                ),
            }

        title = title_map[doc_type]
        text_content = text_map[doc_type]

        documents.append(
            {
                "id": f"doc_{i+1:03d}",
                "owner_type": owner_type,
                "owner_id": owner_id,
                "locale": locale,
                "doc_type": doc_type,
                "title": title,
                "text_content": text_content,
            }
        )

    # Interactions correlated to fit score
    for i in range(config.num_interactions):
        athlete = random.choice(athletes)
        sponsor = random.choice(sponsors)
        score = _fit_score(sponsor["sector"], athlete["position"], sponsor["market"])

        if score > 0.78:
            outcome = random.choices(["interested", "replied"], weights=[70, 30])[0]
        elif score > 0.60:
            outcome = random.choices(["replied", "no_reply"], weights=[55, 45])[0]
        else:
            outcome = random.choices(["no_reply", "replied"], weights=[85, 15])[0]

        interactions.append(
            {
                "id": f"int_{i+1:04d}",
                "athlete_id": athlete["id"],
                "sponsor_id": sponsor["id"],
                "channel": random.choice(["email", "call"]),
                "outcome": outcome,
            }
        )

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM interactions"))
        conn.execute(text("DELETE FROM documents"))
        conn.execute(text("DELETE FROM sponsors"))
        conn.execute(text("DELETE FROM athletes"))

        conn.execute(
            text(
                "INSERT INTO athletes (id, full_name, country, position, level) "
                "VALUES (:id, :full_name, :country, :position, :level)"
            ),
            athletes,
        )
        conn.execute(
            text(
                "INSERT INTO sponsors (id, name, sector, market, budget_range) "
                "VALUES (:id, :name, :sector, :market, :budget_range)"
            ),
            sponsors,
        )
        conn.execute(
            text(
                "INSERT INTO documents (id, owner_type, owner_id, locale, doc_type, title, text_content) "
                "VALUES (:id, :owner_type, :owner_id, :locale, :doc_type, :title, :text_content)"
            ),
            documents,
        )
        conn.execute(
            text(
                "INSERT INTO interactions (id, athlete_id, sponsor_id, channel, outcome) "
                "VALUES (:id, :athlete_id, :sponsor_id, :channel, :outcome)"
            ),
            interactions,
        )

    return {
        "athletes": len(athletes),
        "sponsors": len(sponsors),
        "documents": len(documents),
        "interactions": len(interactions),
    }
