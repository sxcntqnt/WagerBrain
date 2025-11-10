from fractions import Fraction
from typing import Union
from WagerBrain.odds import OddsConverter
from WagerBrain.utils import MarketUtils


class ProbabilityCalculator:
    """
    Provides utilities for calculating implied probabilities from odds formats,
    expected value calculations, and converting probabilities back to odds.
    
    Includes ELO-based probability calculations for sports predictions.
    """

    def __init__(self):
        """Initialize the probability calculator with odds converter utility."""
        self.odds_converter = OddsConverter()

    def decimal_implied_win_prob(self, odds: Union[float, int, str]) -> float:
        """
        Calculate implied win probability from Decimal odds.

        Args:
            odds (float, int, str): Odds in Decimal format or convertible format.

        Returns:
            float: The implied win probability (0.0 to 1.0) rounded to 3 decimal places.
            
        Examples:
            >>> decimal_implied_win_prob(2.0)    # 50% probability
            0.5
            >>> decimal_implied_win_prob(1.5)    # 66.7% probability
            0.667
            >>> decimal_implied_win_prob('4/1')  # Fractional to probability
            0.2
        """
        decimal_odds_val = self.odds_converter.decimal_odds(odds)
        return round(1 / decimal_odds_val, 3)

    def american_implied_win_prob(self, odds: Union[int, str]) -> float:
        """
        Calculate implied win probability from American odds.

        Args:
            odds (int, str): Odds in American format (+150, -200, etc.)

        Returns:
            float: The implied win probability (0.0 to 1.0) rounded to 3 decimal places.
            
        Examples:
            >>> american_implied_win_prob(-200)  # 66.7% probability
            0.667
            >>> american_implied_win_prob(+150)  # 40% probability
            0.4
            >>> american_implied_win_prob('+300') # String input
            0.25
        """
        american_odds_val = self.odds_converter.american_odds(odds)
        
        if american_odds_val > 0:
            return round(100 / (american_odds_val + 100), 3)
        else:
            return round(abs(american_odds_val) / (abs(american_odds_val) + 100), 3)

    def fractional_implied_win_prob(self, odds: Union[str, Fraction]) -> float:
        """
        Calculate implied win probability from Fractional odds.

        Args:
            odds (str, Fraction): Odds in Fractional format ('3/1', Fraction(5,4), etc.)

        Returns:
            float: The implied win probability (0.0 to 1.0) rounded to 3 decimal places.
            
        Examples:
            >>> fractional_implied_win_prob('3/1')    # 25% probability
            0.25
            >>> fractional_implied_win_prob('1/2')    # 66.7% probability
            0.667
            >>> fractional_implied_win_prob(Fraction(5, 4))  # 44.4% probability
            0.444
        """
        odds_frac = self.odds_converter.fractional_odds(odds)
        return round(1 / ((odds_frac.numerator / odds_frac.denominator) + 1), 3)

    def stated_odds_ev(self, stake_win: float, profit_win: float, stake_lose: float, profit_lose: float) -> float:
        """
        Calculate Expected Value using implied win probabilities from bookmaker odds.
        Incorporates the vig (house edge) into the calculation.

        Args:
            stake_win (float): Amount wagered on the FAVORITE outcome
            profit_win (float): Net profit if FAVORITE wins
            stake_lose (float): Amount wagered on the UNDERDOG outcome  
            profit_lose (float): Net profit if UNDERDOG wins

        Returns:
            float: The expected value of wagering on the favorite outcome.
            
        Examples:
            >>> stated_odds_ev(100, 90, 100, 110)  # Typical -EV bet with vig
            -4.55
            >>> stated_odds_ev(100, 100, 100, 100) # Fair odds (rare in practice)
            0.0
        """
        payout_win = stake_win + profit_win
        payout_lose = stake_lose + profit_lose

        win_prob = MarketUtils.break_even_pct(stake_win, payout_win)
        lose_prob = MarketUtils.break_even_pct(stake_lose, payout_lose)

        return (win_prob * profit_win) - (lose_prob * stake_win)

    def true_odds_ev(self, stake: float, profit: float, prob: float) -> float:
        """
        Calculate Expected Value using user-calculated true probabilities.
        Use this when you have your own probability estimates rather than bookmaker implied probabilities.

        Args:
            stake (float): Amount wagered on the outcome
            profit (float): Net profit if the outcome wins
            prob (float): User-estimated probability of winning (0.0 to 1.0)

        Returns:
            float: The expected value of the wager.
            
        Examples:
            >>> true_odds_ev(100, 200, 0.6)   # Positive EV bet
            80.0
            >>> true_odds_ev(100, 150, 0.4)   # Negative EV bet
            -10.0
            >>> true_odds_ev(100, 200, 0.5)   # Fair bet
            50.0
        """
        return (profit * prob) - (stake * (1 - prob))

    def win_prob_to_odds(self, prob: float, odds_style: str = "a") -> Union[int, float, Fraction, None]:
        """
        Convert win probability to stated odds in specified format.

        Args:
            prob (float): Win probability (0.0 to 1.0)
            odds_style (str): Target format: 'a'/'american', 'd'/'decimal', 'f'/'fractional'

        Returns:
            Union[int, float, Fraction]: Odds in specified format, or None if invalid.
            
        Examples:
            >>> win_prob_to_odds(0.4, 'a')   # 40% to American
            150
            >>> win_prob_to_odds(0.667, 'd') # 66.7% to Decimal
            1.5
            >>> win_prob_to_odds(0.25, 'f')  # 25% to Fractional
            Fraction(3, 1)
        """
        try:
            if prob <= 0 or prob >= 1:
                raise ValueError("Probability must be between 0 and 1")

            odds_style = odds_style.lower()
            
            if odds_style in ["american", "amer", "a"]:
                if prob >= 0.50:
                    return int((prob / (1 - prob)) * -100)
                else:
                    return int(((1 - prob) / prob) * 100)

            elif odds_style in ["decimal", "dec", "d"]:
                return round(1 / prob, 2)

            elif odds_style in ["fractional", "frac", "f"]:
                if prob == 1.0:
                    return Fraction(0, 1)
                fractional_value = (1 / prob) - 1
                return Fraction(fractional_value).limit_denominator()

            else:
                raise ValueError(f"Unsupported odds style: {odds_style}")

        except (ValueError, ZeroDivisionError) as e:
            print(f"Error converting probability to odds: {e}")
            return None

    def elo_prob(self, elo_diff: float) -> float:
        """
        Calculate win probability based on ELO rating difference.

        Args:
            elo_diff (float): Team A's ELO rating minus Team B's ELO rating, 
                            adjusted for home advantage, injuries, etc.

        Returns:
            float: Win probability for Team A (0.0 to 1.0)
            
        Examples:
            >>> elo_prob(0)      # Equal ELO ratings
            0.5
            >>> elo_prob(100)    # Team A favored by 100 ELO points
            0.64
            >>> elo_prob(-150)   # Team A underdog by 150 ELO points
            0.3
        """
        return 1 / (10**(-elo_diff / 400) + 1)
