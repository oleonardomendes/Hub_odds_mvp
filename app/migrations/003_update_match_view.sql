DROP VIEW IF EXISTS match_view;

CREATE VIEW match_view AS
SELECT m.id, m.competition_id,
       c.name AS competition_name, c.country, c.season_year,
       m.kickoff_utc, m.status,
       th.name AS home_team_name, ta.name AS away_team_name,
       m.home_team_id, m.away_team_id,
       m.home_score, m.away_score,
       m.provider_id AS provider_id
FROM matches m
JOIN competitions c ON c.id = m.competition_id
JOIN teams th ON th.id = m.home_team_id
JOIN teams ta ON ta.id = m.away_team_id;