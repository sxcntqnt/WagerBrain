from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
from typing import Union, Dict, Callable, Optional, Literal
from contextlib import contextmanager
from pathlib import Path
from collections import deque
from threading import Thread, RLock, Condition
import atexit
from datetime import datetime
import json


# ————————————————————————————————
# 3. WAGER — IMMUTABLE RECORD
# ————————————————————————————————
@dataclass(frozen=True)  # Immutable
class Wager:
    """Immutable, serializable record of a single bet."""
    strategy: str
    amount: Decimal
    why: str
    risk: str  # e.g., "LOW", "SKIP"
    pct_bank: float  # % of bank risked
    ev: float  # Expected value (unit)
    kelly_f: float  # Kelly fraction/weight
    odds: Optional[Union[str, int, float, list]] = None  # Odds (single or list for parlay/margin)
    win_rate: Optional[float] = None  # Estimated p (win prob)
    bookie: str = "Generic"  # Default; override for specific
    timestamp: str = ""
    outcome: Optional[str] = None  # Post-bet: "win", "loss", "push"
    
    def __post_init__(self) -> None:
        if self.timestamp == "":
            object.__setattr__(self, 'timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def dict(self) -> dict:
        d = asdict(self)
        # Str-ify Decimals for JSON
        if 'amount' in d:
            d['amount'] = str(d['amount'])
        return d

# ————————————————————————————————
# 4. HISTORY BUFFER — AUTO-FLUSH + I/O GUARD
# ————————————————————————————————
class HistoryBuffer:
    """
    Memory-efficient bet storage.
    - Max 10,000 bets in RAM
    - Auto-flush to disk
    - Full I/O error handling
    - atexit flush
    """
    def __init__(self, max_size: int = 10_000, flush_file: Optional[Path] = None):
        self.buffer = deque(maxlen=max_size)
        self.flush_file = flush_file
        self.lock = RLock()
        if flush_file:
            atexit.register(self.flush)

    @contextmanager
    def _safe_open(self, mode: str = "a"):
        """Context manager with full I/O error handling."""
        try:
            with open(self.flush_file, mode) as f:
                yield f
        except PermissionError:
            logging.getLogger("WagerBrain").error("PERMISSION DENIED: Cannot write to log file")
            raise
        except OSError as e:
            logging.getLogger("WagerBrain").error(f"DISK ERROR: {e}")
            raise
        except Exception as e:
            logging.getLogger("WagerBrain").error(f"UNEXPECTED I/O ERROR: {e}")
            raise

    def append(self, wager: Wager) -> None:
        with self.lock:
            self.buffer.append(wager)
            if len(self.buffer) == self.buffer.maxlen and self.flush_file:
                self._flush()

    def _flush(self) -> None:
        if not self.flush_file:
            return
        try:
            with self._safe_open() as f:
                for w in list(self.buffer):
                    json.dump(w.dict(), f)
                    f.write("\n")
            self.buffer.clear()
            logging.getLogger("WagerBrain").debug("History flushed to disk")
        except Exception:
            pass  # Already logged in _safe_open

    def flush(self) -> None:
        self._flush()

    def __len__(self) -> int: return len(self.buffer)
    def __iter__(self): return iter(self.buffer)

