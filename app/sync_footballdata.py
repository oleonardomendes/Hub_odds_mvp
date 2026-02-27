from .db import get_db
from .providers.footballdata import competition as api_comp, competition_teams as api_teams, competition_matches as api_matches

def upsert_competition(code: str, name: str, country: str, season_year: int, provider_id: int):
    with get_db() as con:
        row = con.execute("SELECT id FROM competitions WHERE provider_code=?", (code,)).fetchone()
        if row:
            con.execute(
                "UPDATE competitions SET name=?, country=?, season_year=?, provider_id=? WHERE id=?",
                (name, country, season_year, provider_id, row["id"])
            )
            return row["id"]
        cur = con.execute(
            "INSERT INTO competitions(name,country,season_year,provider_code,provider_id) VALUES(?,?,?,?,?)",
            (name, country, season_year, code, provider_id)
        )
        return cur.lastrowid

def upsert_team(competition_id: int, provider_id: int, name: str):
    with get_db() as con:
        row = con.execute("SELECT id FROM teams WHERE provider_id=? AND competition_id=?", (provider_id, competition_id)).fetchone()
        if row:
            con.execute("UPDATE teams SET name=? WHERE id=?", (name, row["id"]))
            return row["id"]
        cur = con.execute(
            "INSERT INTO teams(competition_id,name,provider_id) VALUES(?,?,?)",
            (competition_id, name, provider_id)
        )
        return cur.lastrowid

def upsert_match(competition_id: int, provider_id: int, kickoff_utc: str, status: str,
                 home_team_id: int, away_team_id: int, home_score: int | None, away_score: int | None):
    with get_db() as con:
        row = con.execute("SELECT id FROM matches WHERE provider_id=?", (provider_id,)).fetchone()
        if row:
            con.execute(
                """UPDATE matches SET competition_id=?, kickoff_utc=?, status=?, home_team_id=?, away_team_id=?,
                   home_score=?, away_score=? WHERE id=?""",
                (competition_id, kickoff_utc, status, home_team_id, away_team_id, home_score, away_score, row["id"])
            )
            return row["id"]
        cur = con.execute(
            """INSERT INTO matches(competition_id,kickoff_utc,status,home_team_id,away_team_id,home_score,away_score,provider_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (competition_id, kickoff_utc, status, home_team_id, away_team_id, home_score, away_score, provider_id)
        )
        return cur.lastrowid

def sync_competition(code: str, season_year: int, date_from: str, date_to: str) -> dict:
    c = api_comp(code)
    comp_name = c["name"]
    country = (c.get("area") or {}).get("name", "Unknown")
    provider_competition_id = c["id"]

    competition_id = upsert_competition(code, comp_name, country, season_year, provider_competition_id)

    teams_json = api_teams(code, season_year)
    team_map = {}
    for t in teams_json.get("teams", []):
        local_id = upsert_team(competition_id, t["id"], t["name"])
        team_map[t["id"]] = local_id

    matches_json = api_matches(code, date_from, date_to, season_year)
    inserted = 0

    for m in matches_json.get("matches", []):
        mid = m["id"]
        kickoff = m["utcDate"]
        api_status = m["status"]

        status = "finished" if api_status in ("FINISHED", "AWARDED") else "scheduled"

        home_pid = m["homeTeam"]["id"]
        away_pid = m["awayTeam"]["id"]
        if home_pid not in team_map or away_pid not in team_map:
            continue

        score = m.get("score") or {}
        ft = (score.get("fullTime") or {})
        hs = ft.get("home")
        aas = ft.get("away")

        upsert_match(
            competition_id=competition_id,
            provider_id=mid,
            kickoff_utc=kickoff,
            status=status,
            home_team_id=team_map[home_pid],
            away_team_id=team_map[away_pid],
            home_score=hs if status == "finished" else None,
            away_score=aas if status == "finished" else None,
        )
        inserted += 1

    return {"ok": True, "code": code, "competition_id": competition_id, "teams": len(team_map), "matches": inserted}