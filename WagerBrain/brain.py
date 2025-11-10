from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Union, Dict, Callable, Optional, Literal, List, Tuple
from decimal import Decimal, getcontext
from datetime import datetime
from threading import RLock
from pathlib import Path
import json
from WagerBrain.odds import OddsConverter
from WagerBrain.utils import MarketUtils, setup_logger, GlobalLogWriter
from WagerBrain.wagr import HistoryBuffer, Wager
from WagerBrain.risk import DynamicRiskManager, RISK_PRESETS
from WagerBrain.probs import ProbabilityCalculator
from WagerBrain.payouts import PayoutCalculator

# ————————————————————————————————
# 6. THE THUGNIFICENT BRAIN — 9.9/10
# ————————————————————————————————
class BnkRllBrn:
    """
    The final betting engine.

    Features:
    - Dynamic risk management
    - Auto-reset Fibonacci
    - Thread-safe operations
    - Auto-flush logging
    - Full I/O guard
    - 10/10 reliability
    """

    _lock = RLock()

    def __init__(
        self,
        bankroll: Union[float, Decimal],
        profile: str = "balanced",
        max_risk_pct: float = 0.35,
        log_file: str = "bets.jsonl",
        min_bankroll: float = 100.0,
        log_level: str = "INFO",
    ):
        with self._lock:
            self.bank = Decimal(str(bankroll))
            self.peak = self.bank
            self.min_bank = Decimal(str(min_bankroll))
            self.logger = setup_logger(log_level)
            self.history = HistoryBuffer(10_000, Path(log_file))
            self.writer = GlobalLogWriter(Path(log_file))
            self.risk = DynamicRiskManager(RISK_PRESETS[profile.lower()], max_risk_pct)
            self._stats = {"placed": 0, "total_ev": Decimal("0")}
            self.fib_streak = 0
            self.logger.info("WagerBrain v18 — nrBllRkB 10/10")
            self.odds_converter = OddsConverter()
            self.prob_calc = ProbabilityCalculator()
            self.payout_calc = PayoutCalculator()
            self.utils = MarketUtils()
            self.wager = Wager

    # ————————————————————————————————
    # INTERNAL UTILITIES
    # ————————————————————————————————

    def _check_bank(self) -> None:
        """Halt if bankroll is below minimum."""
        if self.bank < self.min_bank:
            raise ValueError(f"Bankroll ${self.bank:.2f} < minimum ${self.min_bank}")

    def _kelly_core(
        self, p: float, odds: "Number", true_p: Optional[float] = None
    ) -> Tuple[Decimal, float]:
        """
        Kelly Criterion with optional true_prob for sharper EV precision.
        Returns (kelly_fraction, expected_value).
        """
        dec = Decimal(str(self.odds_converter.decimal_odds(odds)))
        profit = float(dec - 1)
        use_prob = true_p if true_p is not None else p
        ev = self.prob_calc.true_odds_ev(stake=1.0, profit=profit, prob=use_prob)
        if ev <= 0:
            return Decimal("0"), ev

        b = dec - 1
        p_dec = Decimal(str(p))
        q = Decimal(1) - p_dec
        return (b * p_dec - q) / b, ev

    def _record(self, wager: "Wager", won: bool = False) -> None:
        """Thread-safe recording with stat updates."""
        with self._lock:
            self.history.append(wager)
            if wager.amount > 0:
                self._stats["placed"] += 1
                self._stats["total_ev"] += wager.amount * Decimal(str(wager.ev))
                self.peak = max(self.peak, self.bank)
                if won:
                    self.fib_streak = 0

            self.risk.update(self.bank)
            self.logger.info(
                f"BET | {wager.strategy:8} | ${wager.amount:>8,.0f} | "
                f"{wager.risk.upper():6} | {wager.why}"
            )

            if self.writer:
                json_wager = {
                    k: str(v) if isinstance(v, Decimal) else v
                    for k, v in wager.dict().items()
                }
                self.writer.write(json_wager)

    # ————————————————————————————————
    # STRATEGIES - ORIGINAL
    # ————————————————————————————————

    def ev_kelly(
        self, p: float, odds: "Number", aggression: float = 2.0, true_p: Optional[float] = None
    ) -> "Wager":
        """EV³-powered Kelly. Supports true_prob for sharper edge detection."""
        self._check_bank()
        kelly_f, ev = self._kelly_core(p, odds, true_p)

        if ev <= 0.015:
            wager = Wager("EV-Kelly", Decimal("0"), "EV < 1.5% — No edge", "low", 0, ev, 0)
        else:
            weight = 1 + (ev ** aggression) * 8
            weighted_f = kelly_f * Decimal(str(weight))
            pct = min(float(weighted_f), 1.0)
            amount = self.risk.cap(
                (self.bank * Decimal(str(pct))).quantize(Decimal("0.01")), self.bank
            )
            wager = Wager(
                "EV-Kelly", amount, f"EV×{weight:.1f}",
                self.risk.level(pct), pct, ev, weight
            )

        self._record(wager)
        return wager

    def pure_kelly(self, p: float, odds: "Number", true_p: Optional[float] = None) -> "Wager":
        """Pure Kelly Criterion (no EV aggression weighting)."""
        self._check_bank()
        kelly_f, ev = self._kelly_core(p, odds, true_p)

        if ev <= 0:
            wager = Wager("pure_kelly", Decimal("0"), "EV <= 0 — No edge", "low", 0, ev, 0)
        else:
            pct = min(float(kelly_f), 1.0)
            amount = self.risk.cap(
                (self.bank * Decimal(str(pct))).quantize(Decimal("0.01")), self.bank
            )
            wager = Wager(
                "pure_kelly", amount, f"Pure Kelly {pct:.1%}",
                self.risk.level(pct), pct, ev, 1.0
            )

        self._record(wager)
        return wager

    def fib(
        self, odds: "Number", won_last: bool = False, unit: float = 0.01, p: Optional[float] = None
    ) -> "Wager":
        """Fibonacci strategy with win-reset, streak cap, and optional edge gate."""
        reset_forced = False
        if won_last:
            self.fib_streak = 0

        if self.fib_streak > 12:
            self.logger.warning("Fib streak > 12 — FORCING RESET")
            self.fib_streak = 0
            reset_forced = True

        skip_fib = False
        if p is not None:
            implied_p = self.prob_calc.american_implied_win_prob(odds)
            if p < implied_p:
                self.logger.info(f"Fib skipped: p {p:.1%} < implied {implied_p:.1%} (no edge)")
                skip_fib = True

        if skip_fib:
            amount = Decimal("0")
            why = "No edge — Skip (p < implied)"
        else:
            a, b = 1, 1
            for _ in range(self.fib_streak):
                a, b = b, a + b
            raw = self.bank * Decimal(str(unit)) * Decimal(str(b))
            amount = self.risk.cap(raw.quantize(Decimal("0.01")), self.bank)
            why = f"Fib×{b} (s={self.fib_streak})"
            if reset_forced:
                why += " — FORCING RESET"

        pct = float(amount / self.bank) if amount > 0 else 0
        risk_level = "SKIP" if skip_fib else self.risk.level(pct)
        wager = Wager("fib", amount, why, risk_level, pct, 0, 0)
        self._record(wager)

        if not skip_fib and not won_last and not reset_forced:
            self.fib_streak += 1
        return wager

    def elo_kelly(
        self, elo_diff: float, odds: "Number", aggression: float = 2.0, true_p: Optional[float] = None
    ) -> "Wager":
        """ELO-derived probability → EV-powered Kelly."""
        p = self.prob_calc.elo_prob(elo_diff)
        return self.ev_kelly(p, odds, aggression, true_p)

    def parlay_bet(self, odds_list: List["Number"], base_pct: float = 0.02) -> "Wager":
        """Parlay multi-leg odds (no vig adj for one-sided; cap at 5%)."""
        self._check_bank()
        parlay_dec = self.odds_converter.parlay_odds(odds_list)
        juice = 0.0
        adj_pct = base_pct * (1 - juice)
        amount = (self.bank * Decimal(str(adj_pct))).quantize(Decimal("0.01"))
        amount = self.risk.cap(amount, self.bank)
        pct = float(amount / self.bank)
        wager = Wager(
            "parlay", amount, f"Parlay {parlay_dec:.2f} dec (no vig)",
            self.risk.level(pct), pct, 0, 0
        )
        self._record(wager)
        return wager

    def margin_bet(self, fav_odds: "Number", dog_odds: "Number", base_pct: float = 0.02) -> "Wager":
        """Bet sizing inverse to bookmaker margin (fairer = bigger)."""
        self._check_bank()
        margin = self.utils.bookmaker_margin(fav_odds, dog_odds)
        adj_pct = base_pct / max(margin + 0.01, 0.01)
        amount = self.risk.cap((self.bank * Decimal(str(adj_pct))).quantize(Decimal("0.01")), self.bank)
        pct = float(amount / self.bank)
        wager = Wager(
            "margin", amount, f"Low margin {margin:.1%} adj",
            self.risk.level(pct), pct, 0, 0
        )
        self._record(wager)
        return wager

    def _vig_adjusted_bet(
        self,
        odds: "Number | tuple",
        base_pct: float = 0.02,
        commish: float | None = None,
    ) -> "Wager":
        """
        Vig-aware bet that adjusts stake size based on bookmaker's margin (vig)
        and optionally exchange commission.
        """
        self._check_bank()
        u_american = None
        juice = margin = commission_adj = 0.0

        try:
            if isinstance(odds, (tuple, list)):
                fav_odds, dog_odds, *rest = odds
                draw_odds = rest[0] if rest else None
                margin = bookmaker_margin(fav_odds, dog_odds, draw_odds)
                commission_adj = bookmaker_commission(fav_odds, dog_odds, commish, draw_odds) if commish else margin
                juice = commission_adj
                mirror_label = "3-way market" if draw_odds else "2-way market"
            else:
                dec_odds = self.odds_converter.decimal_odds(odds)
                f_stake, u_stake = 1.0, 1.0
                f_payout = self.payout_calc.decimal_payout(f_stake, dec_odds)
                if dec_odds < 2.0:
                    u_american = int(100 * (dec_odds - 1))
                else:
                    u_american = int(-100 * dec_odds / (dec_odds - 1))
                u_dec = self.odds_converter.decimal_odds(u_american)
                u_payout = self.payout_calc.decimal_payout(u_stake, u_dec)
                juice = self.utils.vig(f_stake, f_payout, u_stake, u_payout)
                mirror_label = f"mirror {u_american}"

            adj_pct = base_pct * (1 - max(juice, 0))
            amount = (self.bank * Decimal(str(adj_pct))).quantize(Decimal("0.01"))
            amount = self.risk.cap(amount, self.bank)
            pct = float(amount / self.bank)

            wager = Wager(
                "vig",
                amount,
                (
                    f"Vig-adj {juice:.1%} edge | "
                    f"Book margin {margin:.1%} | "
                    f"Commish adj {commission_adj:.1%} ({mirror_label})"
                ),
                self.risk.level(pct),
                pct,
                0,
                0,
            )

            self._record(wager)
            return wager

        except Exception as e:
            self.logger.error(f"Vig computation failed: {e}", exc_info=True)
            raise

    # ————————————————————————————————
    # NEW BETTING SYSTEMS INTEGRATION
    # ————————————————————————————————

    def five_bet_labouchere_bankroll(self, target: float) -> list[float]:
        """
        Generate a 5-bet Labouchere sequence scaled to a target win amount.
        """
        labouchere_ratios = [0.1, 0.2, 0.4, 0.2, 0.1]
        return [target * ratio for ratio in labouchere_ratios]

    def labouchere_bet(self, target: float, odds: "Number") -> list["Wager"]:
        """
        Execute Labouchere sequence as a series of wagers.
        """
        self._check_bank()
        sequence = self.five_bet_labouchere_bankroll(target)
        wagers = []

        for stake in sequence:
            amount = self.risk.cap(Decimal(str(stake)), self.bank)
            pct_bank = float(amount / self.bank)
            wager = Wager(
                strategy="labouchere",
                amount=amount,
                why=f"Labouchere sequence (target ${target})",
                risk=self.risk.level(pct_bank),
                pct_bank=pct_bank,
                ev=0,
                kelly_f=0
            )
            self._record(wager)
            wagers.append(wager)

        return wagers

    def martingale_bet(self, base_bet: float, consecutive_losses: int, multiplier: float = 2.0) -> "Wager":
        """
        Martingale progression system - double bet after each loss.
        """
        self._check_bank()
        # Calculate bet amount using the progression formula
        bet_amount = base_bet * (multiplier ** consecutive_losses)
        amount = self.risk.cap(Decimal(str(bet_amount)), self.bank)
        pct = float(amount / self.bank)

        wager = Wager(
            "martingale",
            amount,
            f"Martingale ×{multiplier} after {consecutive_losses} losses",
            self.risk.level(pct),
            pct,
            0,
            0
        )
        self._record(wager)
        return wager

    def dalembert_bet(self, base_bet: float, wins: int, losses: int) -> "Wager":
        """
        D'Alembert progression system - increase bet after losses, decrease after wins.
        """
        self._check_bank()
        # D'Alembert formula: base_bet + (losses * unit) - (wins * unit)
        # Using 10% of base_bet as the unit
        unit = base_bet * 0.1
        bet_amount = base_bet + (losses * unit) - (wins * unit)
        # Ensure bet doesn't go below minimum
        bet_amount = max(bet_amount, base_bet * 0.1)
        amount = self.risk.cap(Decimal(str(bet_amount)), self.bank)
        pct = float(amount / self.bank)

        wager = Wager(
            "dalembert",
            amount,
            f"D'Alembert: {wins} wins, {losses} losses",
            self.risk.level(pct),
            pct,
            0,
            0
        )
        self._record(wager)
        return wager

    def reverse_labouchere_sequence(self, target: float, num_bets: int = 5) -> list[float]:
        """
        Generate Reverse Labouchere sequence.
        """
        if num_bets == 5:
            ratios = [0.2, 0.3, 0.5, 0.3, 0.2]
        else:
            # For other lengths, create symmetric sequence
            mid_point = num_bets // 2
            ratios = [0.1 * (i + 1) for i in range(mid_point + 1)]
            if num_bets % 2 == 0:
                ratios = ratios + ratios[-2::-1]
            else:
                ratios = ratios + ratios[-1::-1]
        
        return [target * ratio for ratio in ratios]

    def reverse_labouchere_bet(self, target: float, num_bets: int = 5) -> list["Wager"]:
        """
        Reverse Labouchere system - increasing bets on wins.
        """
        self._check_bank()
        sequence = self.reverse_labouchere_sequence(target, num_bets)
        wagers = []

        for stake in sequence:
            amount = self.risk.cap(Decimal(str(stake)), self.bank)
            pct_bank = float(amount / self.bank)
            wager = Wager(
                strategy="reverse_labouchere",
                amount=amount,
                why=f"Reverse Labouchere (target ${target})",
                risk=self.risk.level(pct_bank),
                pct_bank=pct_bank,
                ev=0,
                kelly_f=0
            )
            self._record(wager)
            wagers.append(wager)

        return wagers

    def flat_bet(self, fixed_amount: float) -> "Wager":
        """
        Flat betting - fixed dollar amount regardless of bankroll.
        """
        self._check_bank()
        amount = self.risk.cap(Decimal(str(fixed_amount)), self.bank)
        pct = float(amount / self.bank)

        wager = Wager(
            "flat",
            amount,
            f"Flat betting ${fixed_amount} fixed ({pct:.1%} of bankroll)",
            self.risk.level(pct),
            pct,
            0,
            0
        )
        self._record(wager)
        return wager

    def percentage_bet(self, bet_pct: float) -> "Wager":
        """
        Percentage betting - fixed percentage of current bankroll.
        """
        self._check_bank()
        # Calculate bet amount as percentage of current bankroll
        bet_amount = float(self.bank) * bet_pct
        amount = self.risk.cap(Decimal(str(bet_amount)), self.bank)
        pct = float(amount / self.bank)

        wager = Wager(
            "percentage",
            amount,
            f"Percentage betting {bet_pct:.1%} of ${self.bank:,.0f} bankroll",
            self.risk.level(pct),
            pct,
            0,
            0
        )
        self._record(wager)
        return wager

    def fixed_unit_bet(self, unit_size: float, num_units: int = 1) -> "Wager":
        """
        Fixed unit betting - based on fixed unit size.
        """
        self._check_bank()
        bet_amount = unit_size * num_units
        amount = self.risk.cap(Decimal(str(bet_amount)), self.bank)
        pct = float(amount / self.bank)

        wager = Wager(
            "fixed_unit",
            amount,
            f"Fixed unit: {num_units} × ${unit_size}",
            self.risk.level(pct),
            pct,
            0,
            0
        )
        self._record(wager)
        return wager

    # ————————————————————————————————
    # ROUTER + BANK MGMT - UPDATED
    # ————————————————————————————————

    def bet(self, strategy: str, **kwargs) -> "Wager":
        """Single entry point for all strategies."""
        strategies = {
            "ev": lambda: self.ev_kelly(kwargs["p"], kwargs["o"], kwargs.get("agg", 2.0), kwargs.get("true_p")),
            "fib": lambda: self.fib(kwargs["o"], kwargs.get("won", False), kwargs.get("unit", 0.01), kwargs.get("p")),
            "vig": lambda: self._vig_adjusted_bet(kwargs["odds"], kwargs.get("base_pct", 0.02)),
            "pure_kelly": lambda: self.pure_kelly(kwargs["p"], kwargs["o"], kwargs.get("true_p")),
            "elo_kelly": lambda: self.elo_kelly(kwargs["elo_diff"], kwargs["o"], kwargs.get("agg", 2.0), kwargs.get("true_p")),
            "parlay_bet": lambda: self.parlay_bet(kwargs["odds_list"], kwargs.get("base_pct", 0.02)),
            "margin_bet": lambda: self.margin_bet(kwargs["fav_odds"], kwargs["dog_odds"], kwargs.get("base_pct", 0.02)),
            "labouchere": lambda: self.labouchere_bet(kwargs["target"], kwargs["odds"]),
            "martingale": lambda: self.martingale_bet(kwargs["base_bet"], kwargs.get("losses", 0), kwargs.get("multiplier", 2.0)),
            "dalembert": lambda: self.dalembert_bet(kwargs["base_bet"], kwargs.get("wins", 0), kwargs.get("losses", 0)),
            "reverse_labouchere": lambda: self.reverse_labouchere_bet(kwargs["target"], kwargs.get("num_bets", 5)),
            "flat": lambda: self.flat_bet(kwargs["fixed_amount"]),  
            "percentage": lambda: self.percentage_bet(kwargs["bet_pct"]),
            "fixed_unit": lambda: self.fixed_unit_bet(kwargs["unit_size"], kwargs.get("num_units", 1))
        }

        if strategy not in strategies:
            raise ValueError(f"Invalid strategy. Use: {', '.join(strategies.keys())}")

        return strategies[strategy]()
    def update_bank(self, new: Decimal, won: bool = False) -> None:
        """Update bankroll and reset Fibonacci on win."""
        with self._lock:
            self.bank = new
            if won:
                self.fib_streak = 0
            self.logger.info(f"Bankroll → ${self.bank:,.0f}")

    # ————————————————————————————————
    # SUMMARY + SHUTDOWN
    # ————————————————————————————————

    def summary(self) -> None:
        """Print final performance report with vig/BE insights."""
        dd = float((self.peak - self.bank) / self.peak) * 100 if self.peak > 0 else 0
        placed_bets = [w for w in self.history.buffer if w.amount > 0]
        total_wagered = sum(float(w.amount) for w in placed_bets)
        roi = (float(self.bank - self.peak) / total_wagered * 100) if total_wagered > 0 else 0

        avg_vig, avg_be = 0.0, 0.0
        if placed_bets:
            sample_odds = [getattr(w, "odds", None) for w in placed_bets[:10] if getattr(w, "odds", None)]
            if sample_odds:
                avg_vig = sum(
                    self.utils.vig(1, self.payout_calc.decimal_payout(1, self.odds_converter.decimal_odds(o)), 1, self.payout_calc.decimal_payout(1, self.odds_converter.decimal_odds(o)))
                    for o in sample_odds
                ) / len(sample_odds)
                avg_be = sum(
                    break_even_pct(1, self.payout_calc.decimal_payout(1, self.odds_converter.decimal_odds(o))) for o in sample_odds
                ) / len(sample_odds)
            else:
                self.logger.warning("Sample odds unavailable — add 'odds' to Wager for accurate avg vig/BE")

        print("\nETERNAL 10/10 SUMMARY")
        print(f" Bets placed : {self._stats['placed']}")
        print(f" Final bank  : ${self.bank:,.0f}")
        print(f" Peak        : ${self.peak:,.0f}")
        print(f" Drawdown    : {dd:.1f}%")
        print(f" ROI         : {roi:.1f}%")
        print(f" Total EV    : ${self._stats['total_ev']:,.0f}")
        print(f" Avg Vig     : {avg_vig:.1%} | Avg BE Win% : {avg_be:.1%}")

    def shutdown(self) -> None:
        """Graceful exit with safe file flush."""
        if self.writer:
            self.writer.stop()
        if hasattr(self.history, "flush_file") and self.history.flush_file:
            self.history.flush()
