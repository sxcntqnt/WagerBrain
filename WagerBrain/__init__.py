"""
WagerBrain Package

A sports betting math toolkit providing:

- Odds conversions (American, Decimal, Fractional, Parlay)
- Payouts and profits
- Implied probabilities, Expected Value (EV), ELO win chances
- Utilities: bookmaker margin, vig, commission, break-even % calculations
- Full betting engine: BnkRllBrn, DynamicRiskManager, Risk Presets
- Wager tracking: Wager, HistoryBuffer
- Logging: GlobalLogWriter, setup_logger
"""

# -------------------------
# Core Classes
# -------------------------
from .odds import OddsConverter
from .payouts import PayoutCalculator
from .probs import ProbabilityCalculator
from .utils import MarketUtils, GlobalLogWriter, setup_logger
from .risk import DynamicRiskManager, RISK_PRESETS
from .wagr import HistoryBuffer, Wager
from .brain import BnkRllBrn
# -------------------------
# Module-level function aliases
# -------------------------
# Odds
american_odds = OddsConverter.american_odds
decimal_odds = OddsConverter.decimal_odds
fractional_odds = OddsConverter.fractional_odds
parlay_odds = OddsConverter.parlay_odds
convert_odds = OddsConverter.convert_odds

# Payouts
american_payout = PayoutCalculator.american_payout
decimal_payout = PayoutCalculator.decimal_payout
fractional_payout = PayoutCalculator.fractional_payout
american_profit = PayoutCalculator.american_profit
decimal_profit = PayoutCalculator.decimal_profit
fractional_profit = PayoutCalculator.fractional_profit
get_payout = PayoutCalculator.get_payout
get_profit = PayoutCalculator.get_profit
parlay_profit = PayoutCalculator.parlay_profit
parlay_payout = PayoutCalculator.parlay_payout

# Probabilities
decimal_implied_win_prob = ProbabilityCalculator.decimal_implied_win_prob
american_implied_win_prob = ProbabilityCalculator.american_implied_win_prob
fractional_implied_win_prob = ProbabilityCalculator.fractional_implied_win_prob
stated_odds_ev = ProbabilityCalculator.stated_odds_ev
true_odds_ev = ProbabilityCalculator.true_odds_ev
win_prob_to_odds = ProbabilityCalculator.win_prob_to_odds
elo_prob = ProbabilityCalculator.elo_prob

# Utilities
break_even_pct = MarketUtils.break_even_pct
vig = MarketUtils.vig
bookmaker_margin = MarketUtils.bookmaker_margin
bookmaker_commission = MarketUtils.bookmaker_commission

# -------------------------
# Exports
# -------------------------
__all__ = [
    # Core classes
    "OddsConverter",
    "PayoutCalculator",
    "ProbabilityCalculator",
    "MarketUtils",
    "GlobalLogWriter",
    "setup_logger",
    "BnkRllBrn",
    "DynamicRiskManager",
    "RISK_PRESETS",
    "HistoryBuffer",
    "Wager",

    # Odds functions
    "american_odds",
    "decimal_odds",
    "fractional_odds",
    "parlay_odds",
    "convert_odds",

    # Payouts functions
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

    # Probabilities functions
    "decimal_implied_win_prob",
    "american_implied_win_prob",
    "fractional_implied_win_prob",
    "stated_odds_ev",
    "true_odds_ev",
    "win_prob_to_odds",
    "elo_prob",

    # Utilities
    "break_even_pct",
    "vig",
    "bookmaker_margin",
    "bookmaker_commission",
]

__version__ = "2.0.0"

