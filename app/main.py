from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .models import EvaluateRequest, EvaluateResponse, Reason
from .repository import list_competitions, search_matches, get_match
from .features import estimate_lambdas
from .poisson import prob_over_25, prob_btts_yes
from .risk import compute_confidence

app = FastAPI(title="Odds MVP (manual)", version="0.1.0")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/competitions")
def api_competitions():
    return list_competitions()

@app.get("/api/matches")
def api_matches(q: str = "", competition_id: int | None = None, limit: int = 80):
    return search_matches(q=q, competition_id=competition_id, limit=limit)

@app.get("/api/matches/{match_id}")
def api_match(match_id: int):
    return get_match(match_id)

@app.post("/api/evaluate", response_model=EvaluateResponse)
def api_evaluate(req: EvaluateRequest):
    m = get_match(req.match_id)

    feats = estimate_lambdas(req.match_id, lookback=req.lookback)
    lam_home = feats["lambda_home"]
    lam_away = feats["lambda_away"]

    # model probability
    if req.market == "ou25":
        p_over = prob_over_25(lam_home, lam_away)
        p_model = p_over if req.selection == "over" else (1.0 - p_over)
    elif req.market == "btts":
        p_yes = prob_btts_yes(lam_home, lam_away)
        p_model = p_yes if req.selection == "yes" else (1.0 - p_yes)
    else:
        raise ValueError("unsupported market")

    p_odd = 1.0 / req.odd
    edge = p_model - p_odd
    ev = p_model * req.odd - 1.0

    confidence, risk = compute_confidence(edge=edge, home_n=feats["home_n"], away_n=feats["away_n"],
                                        lam_home=lam_home, lam_away=lam_away)

    reasons = [
        Reason(label="Jogo", value=f'{m["home_team_name"]} vs {m["away_team_name"]} — {m["competition_name"]}'),
        Reason(label="Dados recentes", value=f'home_n={feats["home_n"]} | away_n={feats["away_n"]} | lookback={req.lookback}'),
        Reason(label="Média liga (home/away)", value=f'{feats["league_avg_home"]:.2f} / {feats["league_avg_away"]:.2f}'),
    ]

    if feats.get("home_gf_home_avg") is not None:
        reasons.append(Reason(label="Home (gols marcados em casa, últimos N)", value=f'{feats["home_gf_home_avg"]:.2f}'))
    if feats.get("away_ga_away_avg") is not None:
        reasons.append(Reason(label="Away (gols sofridos fora, últimos N)", value=f'{feats["away_ga_away_avg"]:.2f}'))
    if feats.get("away_gf_away_avg") is not None:
        reasons.append(Reason(label="Away (gols marcados fora, últimos N)", value=f'{feats["away_gf_away_avg"]:.2f}'))
    if feats.get("home_ga_home_avg") is not None:
        reasons.append(Reason(label="Home (gols sofridos em casa, últimos N)", value=f'{feats["home_ga_home_avg"]:.2f}'))

    # risk-reduction guardrails (added as reasons)
    if edge < 0.03:
        reasons.append(Reason(label="Alerta (edge)", value="Edge < 3pp → sinal fraco para reduzir risco."))
    if feats["home_n"] < 5 or feats["away_n"] < 5:
        reasons.append(Reason(label="Alerta (amostra)", value="Poucos jogos recentes → risco aumenta."))

    return EvaluateResponse(
        match_id=req.match_id,
        market=req.market,
        selection=req.selection,
        odd=req.odd,
        p_model=float(p_model),
        p_odd=float(p_odd),
        edge=float(edge),
        ev=float(ev),
        confidence=int(confidence),
        risk=risk,
        reasons=reasons,
        lambda_home=float(lam_home),
        lambda_away=float(lam_away),
    )
