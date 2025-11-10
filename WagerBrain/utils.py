from WagerBrain.odds import OddsConverter
import logging
from logging import Logger
from threading import Thread, RLock, Condition
from pathlib import Path
from contextlib import contextmanager
from queue import SimpleQueue
import json

class MarketUtils:
    """
    Utility class for market and wagering calculations including:
    - Break-even percentages
    - Bookmaker vig/margin
    - Commission-adjusted odds
    """
    def __init__(self):
        """Initialize the utils with odds converter utility."""
        self.odds_converter = OddsConverter()

    @staticmethod
    def break_even_pct(stake: float, payout: float) -> float:
        """
        Calculate the break-even probability given a stake and total payout.

        Args:
            stake (float): Currency amount wagered.
            payout (float): Total amount paid out (stake + profit).

        Returns:
            float: Required win percentage to break even (>100% if bookmaker edge exists).
        """
        return stake / payout

    @staticmethod
    def vig(f_stake: float, f_payout: float, u_stake: float, u_payout: float) -> float:
        """
        Calculate bookmaker vig (margin) for a 2-way market.

        Args:
            f_stake (float): Amount bet on favorite.
            f_payout (float): Total payout on favorite.
            u_stake (float): Amount bet on underdog.
            u_payout (float): Total payout on underdog.

        Returns:
            float: Bookmaker edge (% of wager paid to bookmaker).
        """
        return (MarketUtils.break_even_pct(f_stake, f_payout) + MarketUtils.break_even_pct(u_stake, u_payout)) - 1

    def bookmaker_margin(self, fav_odds, dog_odds, draw_odds=None) -> float:  # REMOVED @staticmethod
        """
        Calculate bookmaker margin (edge) for a 2-way or 3-way market.

        Args:
            fav_odds: Odds on favorite (int American, float Decimal, str, or Fraction).
            dog_odds: Odds on underdog.
            draw_odds: Optional. Odds on draw (for 3-way market).

        Returns:
            float: Bookmaker's margin as a decimal.
        """
        fav_dec = self.odds_converter.decimal_odds(fav_odds)
        dog_dec = self.odds_converter.decimal_odds(dog_odds)

        if draw_odds is None:
            return (1 / fav_dec + 1 / dog_dec) - 1
        else:
            draw_dec = self.odds_converter.decimal_odds(draw_odds)  # FIXED: Use self.odds_converter
            return (1 / fav_dec + 1 / dog_dec + 1 / draw_dec) - 1

    def bookmaker_commission(self, fav_odds, dog_odds, commish: float, draw_odds=None) -> float:  # REMOVED @staticmethod
        """
        Calculate true bookmaker/exchange cost adjusted for commission.

        Args:
            fav_odds: Market odds on favorite.
            dog_odds: Market odds on underdog.
            commish: Exchange commission percentage.
            draw_odds: Optional. Market odds on draw outcome.

        Returns:
            float: Edge to bookmaker/exchange after commission adjustment.
        """
        fav_dec = 1 + ((1 - (commish / 100)) * (self.odds_converter.decimal_odds(fav_odds) - 1))  # FIXED: Use self.odds_converter
        dog_dec = 1 + ((1 - (commish / 100)) * (self.odds_converter.decimal_odds(dog_odds) - 1))  # FIXED: Use self.odds_converter

        if draw_odds is None:
            return ((1 / fav_dec * 100 + 1 / dog_dec * 100) - 100) / 100
        else:
            draw_dec = 1 + ((1 - (commish / 100)) * (self.odds_converter.decimal_odds(draw_odds) - 1))  # FIXED: Use self.odds_converter
            return ((1 / fav_dec * 100 + 1 / dog_dec * 100 + 1 / draw_dec * 100) - 100) / 100

# ————————————————————————————————
# 1. BULLETPROOF LOGGING
# ————————————————————————————————
def setup_logger(level: str = "INFO") -> Logger:
    """
    Configure the root logger with clean, colored, timestamped output.
    Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    logger = logging.getLogger("WagerBrain")
    logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        "%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]
    return logger


# ————————————————————————————————
# 5. GLOBAL LOGGER — BULLETPROOF
# ————————————————————————————————
class GlobalLogWriter:
    """Singleton async JSONL logger. Zero leaks. Full I/O guard."""
    _instance = None
    _lock = Condition()

    def __new__(cls, path: Path):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.path = path
                cls._instance.queue = SimpleQueue()
                cls._instance.thread = Thread(target=cls._instance._run, daemon=True)
                cls._instance.thread.start()
            return cls._instance

    @contextmanager
    def _safe_write(self):
        try:
            with open(self.path, "a") as f:
                yield f
        except Exception as e:
            logging.getLogger("WagerBrain").error(f"LOG WRITE FAILED: {e}")

    def _run(self) -> None:
        while True:
            data = self.queue.get()
            if data is None: break
            try:
                with self._safe_write() as f:
                    json.dump(data, f)
                    f.write("\n")
            except Exception:
                pass

    def write(self, data): self.queue.put(data)
    def stop(self):
        self.queue.put(None)
        self.thread.join()


