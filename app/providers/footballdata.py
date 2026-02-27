import os, json, urllib.parse, urllib.request

BASE_URL = "https://api.football-data.org/v4"
TOKEN = os.getenv("FOOTBALLDATA_TOKEN", "")

class FootballDataError(RuntimeError):
    pass

def _get(path: str, params: dict | None = None) -> dict:
    if not TOKEN:
        raise FootballDataError("FOOTBALLDATA_TOKEN não configurado.")

    qs = ""
    if params:
        qs = "?" + urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}{qs}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("X-Auth-Token", TOKEN)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise FootballDataError(f"Erro football-data.org: {e}")

def competition(code: str) -> dict:
    return _get(f"/competitions/{code}")

def competition_teams(code: str, season: int | None = None) -> dict:
    params = {}
    if season:
        params["season"] = season
    return _get(f"/competitions/{code}/teams", params)

def competition_matches(code: str, date_from: str, date_to: str, season: int | None = None, status: str | None = None) -> dict:
    params = {"dateFrom": date_from, "dateTo": date_to}
    if season:
        params["season"] = season
    if status:
        params["status"] = status
    return _get(f"/competitions/{code}/matches", params)