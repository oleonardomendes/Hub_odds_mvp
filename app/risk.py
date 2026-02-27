from typing import Tuple, List, Dict

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def compute_confidence(edge: float, home_n: int, away_n: int, lam_home: float, lam_away: float) -> Tuple[int, str]:
    # Simple, explainable scoring focused on risk reduction:
    # - more data => higher confidence
    # - extreme lambdas => more variance => lower confidence
    # - tiny edge => lower confidence
    score = 50

    # data adequacy
    score += clamp((min(home_n, 10) - 3) * 3, 0, 21)
    score += clamp((min(away_n, 10) - 3) * 3, 0, 21)

    # edge contribution (cap to avoid overconfidence)
    score += clamp(edge * 250, -15, 20)  # edge in probability points

    # variance penalty: very high expected goals increases volatility
    total_lam = lam_home + lam_away
    if total_lam >= 3.2:
        score -= 8
    if total_lam >= 4.0:
        score -= 8

    # low-sample penalty
    if home_n < 5 or away_n < 5:
        score -= 12
    if home_n < 3 or away_n < 3:
        score -= 15

    score = int(clamp(score, 0, 100))

    if score >= 75:
        return score, "BAIXO"
    if score >= 55:
        return score, "MEDIO"
    return score, "ALTO"
