from __future__ import annotations

from pydantic import BaseModel, Field


class OfferPackage(BaseModel):
    name: str
    deliverables: list[str]
    price_range: str


class Offer(BaseModel):
    currency: str
    packages: list[OfferPackage]


class MeasurementPlan(BaseModel):
    primary_kpis: list[str]
    tracking_method: str
    reporting: str


class RecommendedAsset(BaseModel):
    asset_type: str
    title: str
    why: str


class OutreachPackRequest(BaseModel):
    athlete_id: str = Field(..., examples=["ath_001"])
    sponsor_id: str = Field(..., examples=["sp_001"])
    locale: str = Field(default="en-GB", examples=["en-GB", "fr-FR"])
    market: str = Field(default="UK", examples=["UK", "FR"])
    tone: str = Field(default="premium_warm", examples=["premium_warm"])
    channel: str = Field(default="email", examples=["email"])


class FitExplanation(BaseModel):
    feature: str
    impact: float
    note: str


class TalkingPoint(BaseModel):
    claim: str
    evidence_ids: list[str]


class EmailOutreach(BaseModel):
    subject: str
    body: str


class EvidenceItem(BaseModel):
    id: str
    title: str
    snippet: str


class OutreachPackResponse(BaseModel):
    fit_score: float
    fit_explanations: list[FitExplanation]
    talking_points: list[TalkingPoint]
    email_outreach: EmailOutreach
    one_pager_markdown: str
    evidence: list[EvidenceItem]
    offer: Offer
    measurement_plan: MeasurementPlan
    recommended_assets: list[RecommendedAsset]
    locale: str
    market: str
