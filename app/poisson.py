import math
from typing import Tuple

def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def prob_total_leq_2(lam_home: float, lam_away: float, max_k: int = 10) -> float:
    # P(H + A <= 2) by summation
    p = 0.0
    # truncate at max_k to keep it fast; for typical lambdas, k>10 negligible
    for h in range(0, max_k + 1):
        for a in range(0, max_k + 1):
            if h + a <= 2:
                p += poisson_pmf(h, lam_home) * poisson_pmf(a, lam_away)
    return p

def prob_over_25(lam_home: float, lam_away: float) -> float:
    return max(0.0, min(1.0, 1.0 - prob_total_leq_2(lam_home, lam_away)))

def prob_btts_yes(lam_home: float, lam_away: float) -> float:
    # P(H>=1 and A>=1) = 1 - P(H=0) - P(A=0) + P(H=0,A=0)
    p_h0 = math.exp(-lam_home)
    p_a0 = math.exp(-lam_away)
    p_both0 = math.exp(-(lam_home + lam_away))
    p = 1.0 - p_h0 - p_a0 + p_both0
    return max(0.0, min(1.0, p))
