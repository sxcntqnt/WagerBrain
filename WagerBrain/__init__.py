"""
WagerBrain Package

A sports betting math toolkit providing:

- Odds conversions (American, Decimal, Fractional, Parlay)
- Payouts and profits
- Implied probabilities, Expected Value (EV), ELO win chances
- Utilities: bookmaker margin, vig, commission, break-even % calculations
"""

from .odds import (
    american_odds,
    decimal_odds,
    fractional_odds,
    parlay_odds,
    convert_odds,
)

from .payouts import (
    american_payout,
    decimal_payout,
    fractional_payout,
    american_profit,
    decimal_profit,
    fractional_profit,
    get_payout,
    get_profit,
    parlay_profit,
    parlay_payout,
)

from .probs import (
    decimal_implied_win_prob,
    american_implied_win_prob,
    fractional_implied_win_prob,
    stated_odds_ev,
    true_odds_ev,
    win_prob_to_odds,
    elo_prob,
)

from .utils import (
    break_even_pct,
    vig,
    bookmaker_margin,
    bookmaker_commission,
)

__all__ = [
    # Odds
    "american_odds",
    "decimal_odds",
    "fractional_odds",
    "parlay_odds",
    "convert_odds",

    # Payouts
    "american_payout",
    "decimal_payout",
    "fractional_payout",
    "american_profit",
    "decimal_profit",
    "fractional_profit",
    "get_payout",
    "get_profit",
    "parlay_profit",
    "parlay_payout",

    # Probabilities
    "decimal_implied_win_prob",
    "american_implied_win_prob",
    "fractional_implied_win_prob",
    "stated_odds_ev",
    "true_odds_ev",
    "win_prob_to_odds",
    "elo_prob",

    # Utils
    "break_even_pct",
    "vig",
    "bookmaker_margin",
    "bookmaker_commission",
]

__version__ = "0.1.0"

