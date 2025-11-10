from fractions import Fraction
from typing import Union, List
from WagerBrain.odds import OddsConverter


class PayoutCalculator:
    """
    Provides utilities for calculating payouts and profits from wagers.
    Supports American, Decimal, and Fractional odds formats.
    
    Payout = Stake + Profit
    Profit = Payout - Stake
    """

    def __init__(self):
        """Initialize the payout calculator with odds converter utility."""
        self.odds_converter = OddsConverter()

    def american_payout(self, stake: float, odds: Union[int, str]) -> float:
        """
        Calculate total payout for American odds format.

        Args:
            stake (float): Amount wagered
            odds (int, str): Odds in American format (+150, -200, etc.)

        Returns:
            float: Total payout (stake + profit)
            
        Examples:
            >>> american_payout(100, +150)  # $100 at +150
            250.0
            >>> american_payout(100, -200)  # $100 at -200
            150.0
            >>> american_payout(50, '+300') # String input
            200.0
        """
        if odds > 0:
            return (stake * (odds / 100)) + stake
        else:
            return abs((stake / (odds / 100))) + stake

    def decimal_payout(self, stake: float, odds: Union[float, int]) -> float:
        """
        Calculate total payout for Decimal odds format.

        Args:
            stake (float): Amount wagered
            odds (float, int): Odds in Decimal format (2.5, 1.8, etc.)

        Returns:
            float: Total payout (stake * odds)
            
        Examples:
            >>> decimal_payout(100, 2.5)  # $100 at 2.5
            250.0
            >>> decimal_payout(100, 1.5)  # $100 at 1.5
            150.0
            >>> decimal_payout(50, 3.0)   # $50 at 3.0
            150.0
        """
        return stake * odds

    def fractional_payout(self, stake: float, odds: Union[str, Fraction]) -> float:
        """
        Calculate total payout for Fractional odds format.

        Args:
            stake (float): Amount wagered
            odds (str, Fraction): Odds in Fractional format ('3/1', '1/2', etc.)

        Returns:
            float: Total payout (stake + profit)
            
        Examples:
            >>> fractional_payout(100, '3/1')  # $100 at 3/1
            400.0
            >>> fractional_payout(100, '1/2')  # $100 at 1/2
            150.0
            >>> fractional_payout(50, Fraction(5, 4))  # $50 at 5/4
            112.5
        """
        odds_frac = Fraction(odds)
        return (stake * (odds_frac.numerator / odds_frac.denominator)) + stake

    def american_profit(self, stake: float, odds: Union[int, str]) -> float:
        """
        Calculate net profit for American odds format.

        Args:
            stake (float): Amount wagered
            odds (int, str): Odds in American format (+150, -200, etc.)

        Returns:
            float: Net profit (payout - stake)
            
        Examples:
            >>> american_profit(100, +150)  # $100 at +150
            150.0
            >>> american_profit(100, -200)  # $100 at -200
            50.0
            >>> american_profit(50, '+300') # String input
            150.0
        """
        if odds > 0:
            return stake * (odds / 100)
        else:
            return abs(stake / (odds / 100))

    def decimal_profit(self, stake: float, odds: Union[float, int]) -> float:
        """
        Calculate net profit for Decimal odds format.

        Args:
            stake (float): Amount wagered
            odds (float, int): Odds in Decimal format (2.5, 1.8, etc.)

        Returns:
            float: Net profit (payout - stake)
            
        Examples:
            >>> decimal_profit(100, 2.5)  # $100 at 2.5
            150.0
            >>> decimal_profit(100, 1.5)  # $100 at 1.5
            50.0
            >>> decimal_profit(50, 3.0)   # $50 at 3.0
            100.0
        """
        return stake * (odds - 1)

    def fractional_profit(self, stake: float, odds: Union[str, Fraction]) -> float:
        """
        Calculate net profit for Fractional odds format.

        Args:
            stake (float): Amount wagered
            odds (str, Fraction): Odds in Fractional format ('3/1', '1/2', etc.)

        Returns:
            float: Net profit (payout - stake)
            
        Examples:
            >>> fractional_profit(100, '3/1')  # $100 at 3/1
            300.0
            >>> fractional_profit(100, '1/2')  # $100 at 1/2
            50.0
            >>> fractional_profit(50, Fraction(5, 4))  # $50 at 5/4
            62.5
        """
        odds_frac = Fraction(odds)
        return stake * (odds_frac.numerator / odds_frac.denominator)

    def get_payout(self, odds: Union[int, float, str, Fraction], stake: float, odds_style: str = 'a') -> Union[float, None]:
        """
        Calculate total payout for any odds format.

        Args:
            odds (int, float, str, Fraction): Odds in any supported format
            stake (float): Amount wagered
            odds_style (str): Format of input odds: 'a'/'american', 'd'/'decimal', 'f'/'fractional'

        Returns:
            float: Total payout (stake + profit), or None if invalid
            
        Examples:
            >>> get_payout(+150, 100, 'a')    # American odds
            250.0
            >>> get_payout(2.5, 100, 'd')     # Decimal odds
            250.0
            >>> get_payout('3/1', 100, 'f')   # Fractional odds
            400.0
        """
        try:
            odds_style = odds_style.lower()
            
            if odds_style in ["american", "amer", "a"]:
                return self.american_payout(stake, odds)
            elif odds_style in ["decimal", "dec", "d"]:
                return self.decimal_payout(stake, odds)
            elif odds_style in ["fractional", "frac", "f"]:
                return self.fractional_payout(stake, odds)
            else:
                raise ValueError(f"Unsupported odds style: {odds_style}")
                
        except (ValueError, ZeroDivisionError) as e:
            print(f"Error calculating payout: {e}")
            return None

    def get_profit(self, odds: Union[int, float, str, Fraction], stake: float, odds_style: str = 'a') -> Union[float, None]:
        """
        Calculate net profit for any odds format.

        Args:
            odds (int, float, str, Fraction): Odds in any supported format
            stake (float): Amount wagered
            odds_style (str): Format of input odds: 'a'/'american', 'd'/'decimal', 'f'/'fractional'

        Returns:
            float: Net profit (payout - stake), or None if invalid
            
        Examples:
            >>> get_profit(+150, 100, 'a')    # American odds
            150.0
            >>> get_profit(2.5, 100, 'd')     # Decimal odds
            150.0
            >>> get_profit('3/1', 100, 'f')   # Fractional odds
            300.0
        """
        try:
            odds_style = odds_style.lower()
            
            if odds_style in ["american", "amer", "a"]:
                return self.american_profit(stake, odds)
            elif odds_style in ["decimal", "dec", "d"]:
                return self.decimal_profit(stake, odds)
            elif odds_style in ["fractional", "frac", "f"]:
                return self.fractional_profit(stake, odds)
            else:
                raise ValueError(f"Unsupported odds style: {odds_style}")
                
        except (ValueError, ZeroDivisionError) as e:
            print(f"Error calculating profit: {e}")
            return None

    def parlay_profit(self, odds: List[Union[int, float, str, Fraction]], stake: float) -> float:
        """
        Calculate net profit for a parlay wager.

        Args:
            odds (list): List of odds for wagers in the parlay
            stake (float): Amount wagered on the parlay

        Returns:
            float: Net profit (payout - stake)
            
        Examples:
            >>> parlay_profit([+150, -200], 100)  # American odds parlay
            175.0
            >>> parlay_profit([2.5, 1.5], 100)    # Decimal odds parlay
            275.0
            >>> parlay_profit(['3/1', '1/2'], 100) # Fractional odds parlay
            525.0
        """
        parlay_odds = self.odds_converter.parlay_odds(odds)
        return (parlay_odds * stake) - stake

    def parlay_payout(self, odds: List[Union[int, float, str, Fraction]], stake: float) -> float:
        """
        Calculate total payout for a parlay wager.

        Args:
            odds (list): List of odds for wagers in the parlay
            stake (float): Amount wagered on the parlay

        Returns:
            float: Total payout (stake + profit)
            
        Examples:
            >>> parlay_payout([+150, -200], 100)  # American odds parlay
            275.0
            >>> parlay_payout([2.5, 1.5], 100)    # Decimal odds parlay
            375.0
            >>> parlay_payout(['3/1', '1/2'], 100) # Fractional odds parlay
            625.0
        """
        parlay_odds = self.odds_converter.parlay_odds(odds)
        return parlay_odds * stake
