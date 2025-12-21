from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.db.session import engine
from backend.app.schemas import (
    MeasurementPlan,
    Offer,
    OfferPackage,
    OutreachPackRequest,
    OutreachPackResponse,
    RecommendedAsset,
)
from backend.app.services.outreach_pack import build_outreach_pack

router = APIRouter(prefix="/outreach-pack", tags=["outreach"])


@router.post("", response_model=OutreachPackResponse)
def outreach_pack(payload: OutreachPackRequest) -> OutreachPackResponse:
    try:
        (
            fit_score,
            fit_explanations,
            talking_points,
            email_outreach,
            one_pager_markdown,
            evidence,
            offer_packages,
            measurement_plan,
            recommended_assets,
        ) = build_outreach_pack(
            engine=engine,
            athlete_id=payload.athlete_id,
            sponsor_id=payload.sponsor_id,
            locale=payload.locale,
            market=payload.market,
            tone=payload.tone,
            channel=payload.channel,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # ✅ PUT YOUR BLOCK HERE (right after build_outreach_pack)
    currency = (
        "EUR"
        if payload.market.upper() == "FR"
        else "GBP" if payload.market.upper() == "UK" else "EUR"
    )

    offer = Offer(
        currency=currency,
        packages=[
            OfferPackage(name=p[0], deliverables=p[1], price_range=p[2])
            for p in offer_packages
        ],
    )

    measurement = MeasurementPlan(
        primary_kpis=measurement_plan["primary_kpis"],
        tracking_method=measurement_plan["tracking_method"],
        reporting=measurement_plan["reporting"],
    )

    assets = [
        RecommendedAsset(asset_type=a["asset_type"], title=a["title"], why=a["why"])
        for a in recommended_assets
    ]

    # ✅ then return the full response
    return OutreachPackResponse(
        fit_score=fit_score,
        fit_explanations=fit_explanations,
        talking_points=talking_points,
        email_outreach=email_outreach,
        one_pager_markdown=one_pager_markdown,
        evidence=evidence,
        offer=offer,
        measurement_plan=measurement,
        recommended_assets=assets,
        locale=payload.locale,
        market=payload.market,
    )
