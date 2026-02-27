from typing import List, Dict, Optional
from .db import get_db

def list_competitions():
    with get_db() as con:
        rows = con.execute("SELECT id, name, country, season_year FROM competitions ORDER BY country, name").fetchall()
        return [dict(r) for r in rows]

def search_matches(q: str = "", competition_id: Optional[int] = None, limit: int = 50):
    with get_db() as con:
        where = ["1=1"]
        params = []
        if competition_id is not None:
            where.append("competition_id = ?")
            params.append(competition_id)
        if q:
            where.append("(home_team_name LIKE ? OR away_team_name LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        sql = f'''
        SELECT id, competition_id, competition_name, kickoff_utc, status,
               home_team_name, away_team_name, home_score, away_score
        FROM match_view
        WHERE {" AND ".join(where)}
        ORDER BY kickoff_utc ASC
        LIMIT ?
        '''
        params.append(limit)
        rows = con.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

def get_match(match_id: int) -> Dict:
    with get_db() as con:
        row = con.execute("SELECT * FROM match_view WHERE id=?", (match_id,)).fetchone()
        if not row:
            raise ValueError("match not found")
        return dict(row)
