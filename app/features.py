from typing import Dict, List, Tuple
from datetime import datetime
from .db import get_db

def _fetch_recent_team_matches(con, team_id: int, before_kickoff_utc: str, lookback: int) -> List[dict]:
    # Get last N finished matches for the team before the given kickoff
    q = '''
    SELECT m.id as match_id, m.kickoff_utc, m.home_team_id, m.away_team_id,
           m.home_score, m.away_score, m.status
    FROM matches m
    WHERE m.status = 'finished'
      AND m.kickoff_utc < ?
      AND (m.home_team_id = ? OR m.away_team_id = ?)
    ORDER BY m.kickoff_utc DESC
    LIMIT ?
    '''
    rows = con.execute(q, (before_kickoff_utc, team_id, team_id, lookback)).fetchall()
    return [dict(r) for r in rows]

def _as_team_view(match: dict, team_id: int) -> Tuple[int,int,bool]:
    # returns (goals_for, goals_against, is_home)
    if match["home_team_id"] == team_id:
        return match["home_score"], match["away_score"], True
    return match["away_score"], match["home_score"], False

def estimate_lambdas(match_id: int, lookback: int = 10) -> Dict[str, float]:
    with get_db() as con:
        m = con.execute('SELECT * FROM matches WHERE id=?', (match_id,)).fetchone()
        if not m:
            raise ValueError("match_id not found")
        kickoff = m["kickoff_utc"]
        home_id = m["home_team_id"]
        away_id = m["away_team_id"]

        home_recent = _fetch_recent_team_matches(con, home_id, kickoff, lookback)
        away_recent = _fetch_recent_team_matches(con, away_id, kickoff, lookback)

        # home attack: combine overall GF and home-only GF
        def agg(team_id, recent):
            gf = ga = 0
            gf_home = ga_home = 0
            gf_away = ga_away = 0
            n = len(recent)
            n_home = n_away = 0
            for r in recent:
                f,a,is_home = _as_team_view(r, team_id)
                gf += f; ga += a
                if is_home:
                    gf_home += f; ga_home += a; n_home += 1
                else:
                    gf_away += f; ga_away += a; n_away += 1
            return {
                "n": n,
                "gf_avg": (gf / n) if n else None,
                "ga_avg": (ga / n) if n else None,
                "n_home": n_home,
                "gf_home_avg": (gf_home / n_home) if n_home else None,
                "ga_home_avg": (ga_home / n_home) if n_home else None,
                "n_away": n_away,
                "gf_away_avg": (gf_away / n_away) if n_away else None,
                "ga_away_avg": (ga_away / n_away) if n_away else None,
            }

        h = agg(home_id, home_recent)
        a = agg(away_id, away_recent)

        # fallback values if not enough data
        # league average
        league_id = m["competition_id"]
        league_avg = con.execute('''
            SELECT AVG(home_score) as avg_home, AVG(away_score) as avg_away
            FROM matches WHERE status='finished' AND competition_id=?
        ''', (league_id,)).fetchone()
        avg_home = float(league_avg["avg_home"] or 1.3)
        avg_away = float(league_avg["avg_away"] or 1.1)

        # Weighted blend:
        # home expected goals uses home team home-attack + away team away-defense, mixed with overall
        def blend(primary, fallback, w):
            if primary is None:
                return fallback
            return w*primary + (1-w)*fallback

        # attack/defense components with reasonable defaults
        home_attack = blend(h["gf_home_avg"], blend(h["gf_avg"], avg_home, 0.5), 0.6)
        away_defense = blend(a["ga_away_avg"], blend(a["ga_avg"], avg_home, 0.5), 0.6)

        away_attack = blend(a["gf_away_avg"], blend(a["gf_avg"], avg_away, 0.5), 0.6)
        home_defense = blend(h["ga_home_avg"], blend(h["ga_avg"], avg_away, 0.5), 0.6)

        # convert to lambdas: average of attack and opponent defense, with mild league anchor
        lam_home = 0.45*home_attack + 0.45*away_defense + 0.10*avg_home
        lam_away = 0.45*away_attack + 0.45*home_defense + 0.10*avg_away

        # clamp
        lam_home = max(0.2, min(3.5, lam_home))
        lam_away = max(0.2, min(3.5, lam_away))

        return {
            "lambda_home": lam_home,
            "lambda_away": lam_away,
            "home_n": h["n"] or 0,
            "away_n": a["n"] or 0,
            "home_gf_avg": h["gf_avg"],
            "home_ga_avg": h["ga_avg"],
            "away_gf_avg": a["gf_avg"],
            "away_ga_avg": a["ga_avg"],
            "home_gf_home_avg": h["gf_home_avg"],
            "away_ga_away_avg": a["ga_away_avg"],
            "away_gf_away_avg": a["gf_away_avg"],
            "home_ga_home_avg": h["ga_home_avg"],
            "league_avg_home": avg_home,
            "league_avg_away": avg_away,
        }
