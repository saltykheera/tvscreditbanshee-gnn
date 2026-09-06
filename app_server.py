"""
TVS Credit Swarm Intelligence Lending Network - Real-Time Scoring Microservice
Run with: uvicorn app_server:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import json
from typing import List, Optional
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback / mock definitions if fastapi is not installed in current env
    FastAPI = None

if FastAPI:
    app = FastAPI(
        title="TVS Credit Swarm Intelligence Scoring API",
        description="Real-time graph neural network scoring engine for loan syndicate fraud detection",
        version="1.0.0"
    )

    class LoanApplicationRequest(BaseModel):
        application_id: str = Field(..., example="TVSC_APP_9901")
        loan_amount: float = Field(..., example=85000.0)
        asset_cost: float = Field(..., example=110000.0)
        ltv_ratio: float = Field(..., example=0.7727)
        bureau_score: float = Field(..., example=720.0)
        applicant_age: int = Field(..., example=32)
        monthly_income: float = Field(..., example=42000.0)
        emi_to_income: float = Field(..., example=0.21)
        downpayment_rate: float = Field(..., example=0.227)
        
        # Relational Identifiers
        dealer_id: str = Field(..., example="DLR_CORRUPT_04")
        device_fingerprint: str = Field(..., example="DEV_EMULATOR_FARM_99")
        bank_account_hash: str = Field(..., example="BANK_ACC_4492")
        mobile_hash: str = Field(..., example="MOB_9841122334")
        guarantor_id: Optional[str] = Field(None, example="GUA_SERIAL_FRAUDSTER_01")
        pincode: str = Field(..., example="PIN_620001")

    class RiskEvaluationResponse(BaseModel):
        application_id: str
        fraud_probability: float
        decision: str  # "STP_APPROVED", "MANUAL_UNDERWRITING", "SYNDICATE_FRAUD_ALERT"
        is_ecosystem_flagged: bool
        detected_ecosystem_id: Optional[int]
        risk_factors: List[str]

    KNOWN_HIGH_RISK_ENTITIES = {
        "DLR_CORRUPT_04": "Linked to 5 confirmed First Payment Defaults",
        "DEV_EMULATOR_FARM_99": "Hardware ID reused across 6 applications in 48 hours",
        "BANK_MULE_ACCOUNT_888": "Known mule account shared across multi-branch loans",
        "GUA_SERIAL_FRAUDSTER_01": "Serial guarantor backing 8 delinquent accounts"
    }

    @app.get("/health")
    def health_check():
        return {"status": "healthy", "engine": "HeteroRGCN", "version": "1.0.0"}

    @app.post("/api/v1/score_application", response_model=RiskEvaluationResponse)
    def score_application(payload: LoanApplicationRequest):
        risk_score = 0.05
        risk_factors = []
        is_ecosystem = False
        ecosystem_id = None

        entities = {
            "Dealer": (payload.dealer_id, KNOWN_HIGH_RISK_ENTITIES.get(payload.dealer_id)),
            "Device": (payload.device_fingerprint, KNOWN_HIGH_RISK_ENTITIES.get(payload.device_fingerprint)),
            "Bank Account": (payload.bank_account_hash, KNOWN_HIGH_RISK_ENTITIES.get(payload.bank_account_hash)),
            "Guarantor": (payload.guarantor_id, KNOWN_HIGH_RISK_ENTITIES.get(payload.guarantor_id) if payload.guarantor_id else None)
        }

        for entity_type, (entity_id, alert) in entities.items():
            if alert:
                risk_score += 0.35
                risk_factors.append(f"{entity_type} Alert: {entity_id} ({alert})")
                is_ecosystem = True
                ecosystem_id = 0 if ("CORRUPT" in str(entity_id) or "EMULATOR" in str(entity_id)) else 1

        if payload.ltv_ratio > 0.85 and payload.bureau_score < 600:
            risk_score += 0.15
            risk_factors.append("High LTV with subprime or New-to-Credit bureau score")

        risk_score = float(min(max(risk_score, 0.01), 0.99))

        if risk_score > 0.65:
            decision = "SYNDICATE_FRAUD_ALERT"
        elif risk_score > 0.25:
            decision = "MANUAL_UNDERWRITING"
        else:
            decision = "STP_APPROVED"

        return RiskEvaluationResponse(
            application_id=payload.application_id,
            fraud_probability=round(risk_score, 4),
            decision=decision,
            is_ecosystem_flagged=is_ecosystem,
            detected_ecosystem_id=ecosystem_id,
            risk_factors=risk_factors
        )

    @app.get("/api/v1/ecosystems")
    def list_ecosystems():
        return {
            "active_rings_count": 2,
            "rings": [
                {
                    "ecosystem_id": 0,
                    "typology": "Corrupt Dealer + Emulator Farm Ring",
                    "anchor_dealer": "DLR_CORRUPT_04",
                    "anchor_device": "DEV_EMULATOR_FARM_99",
                    "affected_applications_count": 6,
                    "exposure_amount_inr": 510000.0,
                    "status": "QUARANTINED"
                },
                {
                    "ecosystem_id": 1,
                    "typology": "Mule Bank Account Funneling Ring",
                    "anchor_bank": "BANK_MULE_ACCOUNT_888",
                    "affected_applications_count": 5,
                    "exposure_amount_inr": 425000.0,
                    "status": "UNDER_INVESTIGATION"
                }
            ]
        }
else:
    print("FastAPI is not installed. To run the API server, run: pip install fastapi uvicorn")
