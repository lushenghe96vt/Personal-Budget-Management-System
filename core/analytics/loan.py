# ===============================================================
# File Name:       loan.py
# Author:          Sheng Lu
# Created:         11/24/2025
# Last Modified:   11/24/2025
# ===============================================================
# Description: contains functions regarding loan estimation tool
#
# Usage:
# - call calculate_loan() to get loan summary data incliding probable loan amount, 
#   probable APR, and probable monthly + total payment given a duration

# Notes:
# - 
#
# ===============================================================


def calculate_loan(
    income: float, credit_score: int, duration_months: int, amount_requested: float, loan_purpose: str,
    avg_balance: float, monthly_goal_tracker: int
) -> dict:
    """
    Calculates loan approval, APR, monthly payment, total payment, and internal score.
    Uses ONLY local data + user inputs (no external APIs).
    """

    # ---------------------------------------------------------
    # 0. Basic sanity checks
    # ---------------------------------------------------------
    if income <= 0:
        return {"approved": False, "reason": "Income must be greater than zero."}
    if amount_requested <= 0:
        return {"approved": False, "reason": "Loan amount must be positive."}
    if duration_months <= 0:
        return {"approved": False, "reason": "Duration must be at least 1 month."}

    # ---------------------------------------------------------
    # 1. Purpose → Risk Weight
    # ---------------------------------------------------------
    PURPOSE_WEIGHTS = {
        "Auto": 0.10,
        "Home": 0.15,
        "Education": 0.20,
        "Medical": 0.25,
        "Business": 0.30,
        "Debt Consolidation": 0.35,
        "Personal": 0.40,
    }

    risk_weight = PURPOSE_WEIGHTS.get(loan_purpose, 0.40)

    # ---------------------------------------------------------
    # 2. Stability & Behavior Factors (fixed logic)
    # ---------------------------------------------------------

    # Use balance relative to income but clamp
    balance_factor = min(max(avg_balance / (income * 3), 0), 1.0)

    # Track goal performance: convert months → score
    goal_factor = min(max(monthly_goal_tracker / 6, 0), 1.0)

    # ---------------------------------------------------------
    # 3. Score Calculation (fixed)
    # ---------------------------------------------------------

    # Credit score normalized 0–1
    credit_factor = max(min(credit_score / 850, 1.0), 0.0)

    # Reasonable "burden factor" instead of old income/(income+amt)
    burden_factor = min(income / (amount_requested * 5), 1.0)

    score = (
        0.45 * credit_factor +
        0.20 * balance_factor +
        0.15 * goal_factor +
        0.20 * burden_factor
    )

    # Apply purpose penalty (but clamp so it doesn't kill insane incomes)
    score = max(score - risk_weight * 0.3, 0.0)

    # ---------------------------------------------------------
    # 4. APR Tier (same structure as yours, but more realistic)
    # ---------------------------------------------------------
    if score >= 0.70:
        apr = 0.07
    elif score >= 0.55:
        apr = 0.12
    elif score >= 0.40:
        apr = 0.18
    else:
        return {
            "approved": False,
            "score": round(score, 3),
            "reason": "Financial score too low for approval.",
            "apr": None,
            "monthly_payment": None,
            "total_payment": None
        }

    # ---------------------------------------------------------
    # 5. Monthly Payment (safe version)
    # ---------------------------------------------------------
    monthly_rate = apr / 12

    if monthly_rate == 0:
        monthly_payment = amount_requested / duration_months
    else:
        try:
            monthly_payment = (
                (monthly_rate * amount_requested) /
                (1 - (1 + monthly_rate) ** (-duration_months))
            )
        except ZeroDivisionError:
            monthly_payment = amount_requested / duration_months

    total_payment = monthly_payment * duration_months

    # ---------------------------------------------------------
    # 6. Affordability + DTI check
    # ---------------------------------------------------------
    dti = monthly_payment / income  # debt-to-income (monthly)

    if dti > 1.0:
        return {
            "approved": False,
            "reason": "Requested monthly payment exceeds income.",
            "dti": round(dti, 4),
            "score": round(score, 3)
        }

    if dti > 0.45 and score < 0.55:
        # borderline case: reject only if both bad
        return {
            "approved": False,
            "reason": "Debt-to-income ratio too high for current financial profile.",
            "dti": round(dti, 4),
            "score": round(score, 3)
        }

    # ---------------------------------------------------------
    # 7. Final Response
    # ---------------------------------------------------------
    return {
        "approved": True,
        "score": round(score, 3),
        "apr": apr,
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "dti": round(dti, 4)
    }