from fractions import Fraction
from math import gcd
import numpy as np
from typing import Union


class OddsConverter:
    """
    Provides utilities to convert between different gambling odds formats:
    American, Decimal, Fractional, and Parlay calculations.

    Methods:
        american_odds(odds) -> int:
            Converts odds to American format.
        decimal_odds(odds) -> float:
            Converts odds to Decimal format.
        fractional_odds(odds) -> Fraction:
            Converts odds to Fractional format.
        parlay_odds(odds_list) -> float:
            Calculates parlay odds in Decimal format.
        convert_odds(odds, style='a') -> Union[int, float, Fraction, None]:
            Generic converter to desired style.
    """

    def american_odds(self, odds: Union[int, float, str]) -> int:
        """
        Convert numeric or fractional odds to American format.

        Args:
            odds (int, float, str): Input odds (decimal float, integer, or string like '5/4' or '-150').

        Returns:
            int: Odds in American format.
        """
        # Handle string inputs like "-150", "+150", "150"
        if isinstance(odds, str):
            # Check if it's a fractional odds string
            if "/" in odds:
                odds_frac = Fraction(odds)
                frac = odds_frac.numerator / odds_frac.denominator
                return int(frac * 100) if odds_frac.numerator >= odds_frac.denominator else int(-100 / frac)
            
            # Handle American odds as strings ("-150", "+150", "150")
            try:
                # Remove + sign if present and convert to int
                if odds.startswith('+'):
                    return int(odds[1:])
                elif odds.startswith('-'):
                    return int(odds)
                else:
                    # Assume positive if no sign
                    return int(odds)
            except ValueError:
                raise ValueError(f"Unsupported odds format: {odds}")

        elif isinstance(odds, int):
            return odds

        elif isinstance(odds, float):
            if odds > 2.0:
                return int((odds - 1) * 100)
            else:
                return int(-100 / (odds - 1))

        else:
            raise ValueError(f"Unsupported odds format: {odds}")

    def decimal_odds(self, odds: Union[int, float, str]) -> float:
        """
        Convert numeric or fractional odds to Decimal format.

        Args:
            odds (int, float, str): Input odds (American int, decimal float, fractional string, or American str).

        Returns:
            float: Odds in Decimal format.
        """
        if isinstance(odds, float):
            return odds

        elif isinstance(odds, int):
            if odds >= 100:
                return 1 + (odds / 100.0)
            elif odds <= -101:
                return 1 + (100.0 / abs(odds))
            else:
                return float(odds)

        elif isinstance(odds, str):
            if "/" in odds:
                return round(float(Fraction(odds)) + 1, 2)
            
            # Handle American odds as strings
            try:
                if odds.startswith('+'):
                    val = int(odds[1:])
                    return 1 + (val / 100.0)
                elif odds.startswith('-'):
                    val = int(odds[1:])
                    if val < 100:
                        raise ValueError(f"Invalid negative American odds: {odds} (must be <= -100)")
                    return 1 + (100.0 / val)
                else:
                    # Assume it's a number string
                    val = int(odds)
                    if val >= 100:
                        return 1 + (val / 100.0)
                    elif val <= -101:
                        return 1 + (100.0 / abs(val))
                    else:
                        return float(val)
            except ValueError:
                raise ValueError(f"Unsupported odds format: {odds}")

        raise ValueError(f"Unsupported odds format: {odds}")

    def fractional_odds(self, odds: Union[int, float, str]) -> Fraction:
        """
        Convert numeric or fractional odds to Fraction format.

        Args:
            odds (int, float, str): Input odds (decimal float, integer, or string like '5/4').

        Returns:
            Fraction: Odds as a Fraction.
        """
        if isinstance(odds, str):
            return Fraction(odds)

        elif isinstance(odds, int):
            if odds > 0:
                g_cd = gcd(odds, 100)
                return Fraction(odds // g_cd, 100 // g_cd)
            else:
                g_cd = gcd(100, abs(odds))
                return Fraction(-100 // g_cd, abs(odds) // g_cd)

        elif isinstance(odds, float):
            new_odds = int(round((odds - 1) * 100))
            g_cd = gcd(abs(new_odds), 100)
            return Fraction(abs(new_odds) // g_cd, 100 // g_cd) * (1 if new_odds >= 0 else -1)

        else:
            raise ValueError(f"Unsupported odds format: {odds}")

    def parlay_odds(self, odds_list: list) -> float:
        """
        Compute combined parlay odds from a list of odds.

        Args:
            odds_list (list): List of odds in any format (int, float, str).

        Returns:
            float: Parlay odds in Decimal format.
        """
        return np.prod([self.decimal_odds(x) for x in odds_list])

    def convert_odds(self, odds: Union[int, float, str], style: str = 'a') -> Union[int, float, Fraction, None]:
        """
        Convert odds to a specified format (American, Decimal, Fractional).

        Args:
            odds (int, float, str, list): Input odds or list of odds.
            style (str): Target format: 'a'/'american', 'd'/'decimal', 'f'/'fractional'.

        Returns:
            Union[int, float, Fraction, None]: Converted odds or None if invalid.
        """
        try:
            style_lower = style.lower()
            if style_lower in ['a', 'amer', 'american']:
                return self.american_odds(odds)
            elif style_lower in ['d', 'dec', 'decimal']:
                return self.decimal_odds(odds)
            elif style_lower in ['f', 'frac', 'fractional']:
                return self.fractional_odds(odds)
        except (ValueError, KeyError, NameError):
            return None
