from __future__ import annotations

import random
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.app.core.config import settings
from backend.app.schemas import (
    EmailOutreach,
    EvidenceItem,
    FitExplanation,
    TalkingPoint,
)
from backend.app.services.llm_client import LlmError, ollama_generate_json


def _currency_from_market(market: str) -> str:
    market_upper = market.upper()
    if market_upper == "FR":
        return "EUR"
    if market_upper == "UK":
        return "GBP"
    return "EUR"


def _compute_fit_score(sector: str, position: str, market: str) -> float:
    base = 0.55
    if sector in {"automotive", "luxury", "sportswear"}:
        base += 0.10
    if position in {"PG", "SG"}:
        base += 0.05
    if market.upper() in {"FR", "UK"}:
        base += 0.05
    return max(0.0, min(1.0, base + random.uniform(-0.10, 0.20)))


def _pick_evidence(engine: Engine, locale: str, limit: int = 4) -> list[EvidenceItem]:
    query = text(
        """
        SELECT id, title, text_content, doc_type
        FROM documents
        WHERE locale = :locale
        ORDER BY random()
        LIMIT 80
        """
    )

    with engine.begin() as conn:
        rows = conn.execute(query, {"locale": locale}).mappings().all()

    evidence: list[EvidenceItem] = []
    seen_types: set[str] = set()

    for row in rows:
        doc_type = str(row.get("doc_type") or "unknown")
        if doc_type in seen_types:
            continue

        seen_types.add(doc_type)
        snippet = str(row["text_content"])[:180].strip()
        evidence.append(
            EvidenceItem(
                id=str(row["id"]),
                title=str(row["title"]),
                snippet=snippet,
            )
        )

        if len(evidence) >= limit:
            break

    return evidence


def build_outreach_pack(
    *,
    engine: Engine,
    athlete_id: str,
    sponsor_id: str,
    locale: str,
    market: str,
    tone: str,
    channel: str,
) -> tuple[
    float,
    list[FitExplanation],
    list[TalkingPoint],
    EmailOutreach,
    str,
    list[EvidenceItem],
    list[tuple[str, list[str], str]],
    dict[str, Any],
    list[dict[str, str]],
]:
    athlete_query = text(
        """
        SELECT id, full_name, country, position, level
        FROM athletes
        WHERE id = :id
        """
    )
    sponsor_query = text(
        """
        SELECT id, name, sector, market, budget_range
        FROM sponsors
        WHERE id = :id
        """
    )

    with engine.begin() as conn:
        athlete = conn.execute(athlete_query, {"id": athlete_id}).mappings().first()
        sponsor = conn.execute(sponsor_query, {"id": sponsor_id}).mappings().first()

    if athlete is None:
        raise ValueError(f"Unknown athlete_id: {athlete_id}")
    if sponsor is None:
        raise ValueError(f"Unknown sponsor_id: {sponsor_id}")

    fit_score = _compute_fit_score(
        sector=str(sponsor["sector"]),
        position=str(athlete["position"]),
        market=market,
    )

    if locale.startswith("fr"):
        fit_explanations = [
            FitExplanation(
                feature="alignement_narratif",
                impact=0.18,
                note="Le mindset performance s’aligne avec le positionnement de la marque.",
            ),
            FitExplanation(
                feature="affinite_audience",
                impact=0.15,
                note="Affinité entre l’audience et la catégorie sponsor.",
            ),
            FitExplanation(
                feature="timing",
                impact=0.11,
                note="Le format pilote court colle à la fenêtre de momentum.",
            ),
        ]
    else:
        fit_explanations = [
            FitExplanation(
                feature="narrative_match",
                impact=0.18,
                note="Performance mindset aligns with brand positioning.",
            ),
            FitExplanation(
                feature="audience_affinity",
                impact=0.15,
                note="Audience interest overlaps with sponsor category.",
            ),
            FitExplanation(
                feature="timing",
                impact=0.11,
                note="Short pilot fits current momentum window.",
            ),
        ]

    # Sellable blocks
    currency = _currency_from_market(market)

    if currency == "EUR":
        offer_packages: list[tuple[str, list[str], str]] = [
            ("Starter", ["1 Reel (30–45s)", "3 clips (10–15s)", "4 stories CTA"], "15–25k EUR"),
            ("Standard", ["1 Reel (30–45s)", "5 clips (10–15s)", "6 stories CTA"], "25–45k EUR"),
            ("Premium", ["2 Reels", "8 clips", "10 stories CTA", "1 appearance"], "45–80k EUR"),
        ]
    else:
        offer_packages = [
            ("Starter", ["1 Reel (30–45s)", "3 clips (10–15s)", "4 CTA stories"], "12–20k GBP"),
            ("Standard", ["1 Reel (30–45s)", "5 clips (10–15s)", "6 CTA stories"], "20–40k GBP"),
            ("Premium", ["2 Reels", "8 clips", "10 CTA stories", "1 appearance"], "40–70k GBP"),
        ]

    measurement_plan: dict[str, Any] = {
        "primary_kpis": ["Reach", "Saves", "CTR", "Qualified actions (code/link)"],
        "tracking_method": "Unique tracking link + code, weekly snapshot export",
        "reporting": "Weekly report + end-of-pilot summary with learnings",
    }

    recommended_assets: list[dict[str, str]] = [
        {
            "asset_type": "reel_reference",
            "title": "Premium hero reel reference",
            "why": "Matches sector + premium tone.",
        },
        {
            "asset_type": "story_sequence",
            "title": "CTA story structure",
            "why": "Optimized for measurable actions.",
        },
        {
            "asset_type": "bts_pack",
            "title": "Behind-the-scenes content pack",
            "why": "Authenticity + engagement uplift.",
        },
    ]

    evidence = _pick_evidence(engine=engine, locale=locale, limit=4)
    evidence_ids = [e.id for e in evidence]

    # -------------------------------
    # 1) TEMPLATE FIRST (always defined)
    # -------------------------------
    if locale.startswith("fr"):
        subject = (
            f"Proposition de partenariat : {sponsor['name']} × "
            f"{athlete['full_name']} (pilote 2 semaines)"
        )
        body = (
            "Bonjour {Prénom},\n\n"
            f"Je vous contacte avec une proposition de partenariat simple à activer et "
            f"mesurable pour {sponsor['name']}.\n\n"
            f"{athlete['full_name']} traverse une période de dynamique intéressante, et "
            "l’angle « performance & précision » s’aligne avec votre positionnement.\n\n"
            "Pilote sur 2 semaines :\n"
            "1) Journée de contenu (formats courts + coulisses)\n"
            "2) 1 vidéo principale (30–45s)\n"
            "3) Stories avec CTA (lien/code unique)\n\n"
            "Je peux adapter la proposition selon votre objectif "
            "(notoriété vs drive-to-store).\n\n"
            "Seriez-vous disponible pour un échange de 15 minutes la semaine prochaine ?\n\n"
            "Bien cordialement,\n"
            "Daniel\n"
        )

        one_pager = (
            f"# Pilote Partenariat — {sponsor['name']} × {athlete['full_name']}\n\n"
            "## Objectif\n"
            "Lancer une activation premium locale sur 2 semaines, orientée résultats.\n\n"
            "## Pourquoi ce fit\n"
            "- Alignement narratif (discipline, performance)\n"
            "- Affinité audience\n"
            "- Structure pilote faible friction\n\n"
            "## Activation proposée (2 semaines)\n"
            "1. Journée de contenu + teaser\n"
            "2. Vidéo principale + séquence stories avec CTA\n\n"
            "## Livrables\n"
            "- 1 vidéo principale (30–45s)\n"
            "- 4 clips (10–15s)\n"
            "- 6 stories avec CTA\n\n"
            "## Mesure (KPIs)\n"
            "- Reach, Saves, CTR, actions qualifiées (code/lien)\n\n"
            "## Preuves (internes)\n"
            + "\n".join([f"- {e.title} (id: {e.id})" for e in evidence])
            + "\n"
        )

        talking_points = [
            TalkingPoint(
                claim="Activation premium locale, faible friction, mesurable.",
                evidence_ids=evidence_ids[:2],
            ),
            TalkingPoint(
                claim="Narratif performance & précision cohérent avec la marque.",
                evidence_ids=evidence_ids[2:],
            ),
        ]
    else:
        subject = (
            f"Partnership idea: {sponsor['name']} × {athlete['full_name']} "
            "(2-week measurable pilot)"
        )
        body = (
            "Hi {FirstName},\n\n"
            f"I’m reaching out with a focused partnership idea designed to be low-friction "
            f"and measurable for {sponsor['name']}.\n\n"
            f"{athlete['full_name']} is in a strong momentum window, and the narrative "
            "aligns with your positioning: precision, discipline, premium experience.\n\n"
            "2-week pilot:\n"
            "1) Content day (short-form + behind-the-scenes)\n"
            "2) 1 Hero Reel (30–45s)\n"
            "3) Story sequence + CTA (unique link/code)\n\n"
            "If you tell me whether your priority is awareness or drive-to-store, "
            "I’ll tailor the plan accordingly.\n\n"
            "Open to a quick 15-minute call next week?\n\n"
            "Best,\n"
            "Daniel\n"
        )

        one_pager = (
            f"# Partnership Pilot — {sponsor['name']} × {athlete['full_name']}\n\n"
            "## Objective\n"
            "Launch a premium, local activation over 2 weeks with measurable outcomes.\n\n"
            "## Why this fit\n"
            "- Narrative match (performance mindset)\n"
            "- Audience affinity\n"
            "- Low-friction pilot structure\n\n"
            "## Proposed Activation (2 weeks)\n"
            "1. Content day + teaser\n"
            "2. Hero Reel + CTA story sequence\n\n"
            "## Deliverables\n"
            "- 1 Hero Reel (30–45s)\n"
            "- 4 short clips (10–15s)\n"
            "- 6 CTA stories\n\n"
            "## Measurement (KPIs)\n"
            "- Reach, Saves, CTR, qualified actions (code/link)\n\n"
            "## Internal Evidence\n"
            + "\n".join([f"- {e.title} (id: {e.id})" for e in evidence])
            + "\n"
        )

        talking_points = [
            TalkingPoint(
                claim="Low-friction, measurable 2-week pilot tailored to sponsor objectives.",
                evidence_ids=evidence_ids[:2],
            ),
            TalkingPoint(
                claim="Premium storytelling aligned with athlete momentum and brand positioning.",
                evidence_ids=evidence_ids[2:],
            ),
        ]

    email = EmailOutreach(subject=subject, body=body)

    # -------------------------------
    # 2) OPTIONAL LLM OVERRIDE (no early return!)
    # -------------------------------
    if settings.generation_mode == "llm" and settings.llm_provider == "ollama":
        evidence_block = "\n".join(
            [f"- ({e.id}) {e.title}: {e.snippet}" for e in evidence]
        )
        system_style = (
            "French business tone. Short, confident, measurable. No exaggeration."
            if locale.startswith("fr")
            else "UK business tone. Clear, concise, premium. No exaggeration."
        )

        prompt = f"""\
You are Sponsorship Copilot. Write an outreach email + a one-page proposal.
Rules:
- Output MUST be valid JSON with keys: subject, body, one_pager_markdown.
- Use ONLY the provided facts and evidence. Do not invent results, followers, or numbers.
- Keep it professional and concise.
- Language must match locale={locale}.

Athlete:
- name: {athlete['full_name']}
- position: {athlete['position']}
- level: {athlete['level']}
- country: {athlete['country']}

Sponsor:
- name: {sponsor['name']}
- sector: {sponsor['sector']}
- market: {sponsor['market']}
- budget_range: {sponsor['budget_range']}

Evidence (internal):
{evidence_block}

Style:
{system_style}
""".strip()

        try:
            llm_json = ollama_generate_json(prompt=prompt)
            email = EmailOutreach(
                subject=str(llm_json["subject"]),
                body=str(llm_json["body"]),
            )
            one_pager = str(llm_json["one_pager_markdown"])
        except (KeyError, TypeError, LlmError):
            # fallback to template
            pass

    # -------------------------------
    # 3) SINGLE RETURN AT END
    # -------------------------------
    return (
        fit_score,
        fit_explanations,
        talking_points,
        email,
        one_pager,
        evidence,
        offer_packages,
        measurement_plan,
        recommended_assets,
    )