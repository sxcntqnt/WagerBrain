from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext

# ————————————————————————————————
# 2. DYNAMIC RISK MANAGER — SELF-HEALING
# ————————————————————————————————
@dataclass(frozen=True)
class RiskThresholds:
    """
    Risk classification bands as % of bankroll.
    - low:   ≤5%  → safe grind
    - med:   ≤15% → balanced
    - high:  ≤30% → aggressive
    - insane: >30% → moonshot
    """
    low: float = 0.05
    med: float = 0.15
    high: float = 0.30

RISK_PRESETS = {
    "balanced": RiskThresholds(0.05, 0.15, 0.30),
    "aggressive": RiskThresholds(0.10, 0.25, 0.50),
}

class DynamicRiskManager:
    """
    Adapts risk in real-time based on drawdown.
    - Peak tracking
    - 20%+ drawdown → cuts max risk 50%
    - Self-healing: recovers aggression as bank grows
    """
    def __init__(self, base: RiskThresholds, max_risk_pct: float):
        self.base = base
        self.max_risk = min(1.0, max(0.01, float(max_risk_pct)))
        self.peak = Decimal("0")
        self.drawdown = 0.0

    def update(self, bank: Decimal) -> None:
        """Update peak and calculate current drawdown %."""
        self.peak = max(self.peak, bank)
        self.drawdown = float((self.peak - bank) / self.peak) if self.peak > 0 else 0

    def level(self, pct: float) -> str:
        """Classify risk with drawdown penalty."""
        adj = pct * (1 + self.drawdown * 2)
        if adj <= self.base.low: return "low"
        if adj <= self.base.med: return "medium"
        if adj <= self.base.high: return "high"
        return "insane"

    def cap(self, amount: Decimal, bank: Decimal) -> Decimal:
        """Apply hard cap + drawdown protection."""
        cap = bank * Decimal(str(self.max_risk))
        if self.drawdown > 0.20:
            cap *= Decimal("0.5")
            logging.getLogger("WagerBrain").info("DRAWDOWN >20% — RISK CUT 50%")
        return min(amount, cap)

