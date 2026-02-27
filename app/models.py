from pydantic import BaseModel, Field
from typing import Literal, Optional, List

Market = Literal["ou25", "btts"]
Selection = Literal["over", "under", "yes", "no"]

class EvaluateRequest(BaseModel):
    match_id: int
    market: Market
    selection: Selection
    odd: float = Field(gt=1.0, description="Odd decimal (ex.: 1.95)")
    lookback: int = Field(default=10, ge=3, le=30, description="Quantidade de jogos recentes para cálculo")

class Reason(BaseModel):
    label: str
    value: str

class EvaluateResponse(BaseModel):
    match_id: int
    market: Market
    selection: Selection
    odd: float
    p_model: float
    p_odd: float
    edge: float
    ev: float
    confidence: int
    risk: Literal["BAIXO", "MEDIO", "ALTO"]
    reasons: List[Reason]
    lambda_home: float
    lambda_away: float
