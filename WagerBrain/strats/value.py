import numpy as np
import pandas as pd
from WagerBrain import ProbabilityCalculator, OddsConverter

class ValueBetFinder:
    """
    Advanced value betting detection system.
    Supports 2-way and 3-way markets with sophisticated edge calculation.
    """
    
    def __init__(self):
        """Initialize with WagerBrain utilities."""
        self.prob_calc = ProbabilityCalculator()
        self.odds_converter = OddsConverter()
    
    def calculate_true_probabilities_3way(self, df, home_col='Home Score', away_col='Away Score'):
        """
        Calculate true probabilities for 3-way markets from historical data.

        Args:
            df: DataFrame with match results
            home_col: Column name for home team scores
            away_col: Column name for away team scores

        Returns:
            dict: True probabilities for home win, draw, away win
        """
        try:
            total_matches = len(df)
            if total_matches == 0:
                return None
                
            home_wins = len(df[df[home_col] > df[away_col]])
            draws = len(df[df[home_col] == df[away_col]])
            away_wins = len(df[df[home_col] < df[away_col]])
            
            return {
                'home_win': home_wins / total_matches,
                'draw': draws / total_matches,
                'away_win': away_wins / total_matches
            }
            
        except Exception as e:
            print(f"Error calculating true probabilities: {e}")
            return None

    def value_bet_3way(self, true_probs, market_odds, min_edge=0.02):
        """
        Identify value bets in 3-way markets.

        Args:
            true_probs: Dictionary of true probabilities {'home_win': x, 'draw': y, 'away_win': z}
            market_odds: List of market odds [home_odds, draw_odds, away_odds]
            min_edge: Minimum required edge to consider a value bet

        Returns:
            dict: Value bet opportunities
        """
        value_bets = {}
        
        try:
            # Calculate implied probabilities from market odds
            market_probs = [
                self.prob_calc.decimal_implied_win_prob(market_odds[0]),
                self.prob_calc.decimal_implied_win_prob(market_odds[1]),
                self.prob_calc.decimal_implied_win_prob(market_odds[2])
            ]
            
            # Compare true probabilities with market probabilities
            outcomes = ['home_win', 'draw', 'away_win']
            true_prob_list = [true_probs['home_win'], true_probs['draw'], true_probs['away_win']]
            
            for i, (true_prob, market_prob) in enumerate(zip(true_prob_list, market_probs)):
                edge = true_prob - market_prob
                if edge >= min_edge:
                    value_bets[outcomes[i]] = {
                        'true_probability': round(true_prob, 4),
                        'market_probability': round(market_prob, 4),
                        'edge': round(edge, 4),
                        'odds': market_odds[i],
                        'expected_value': round((true_prob * (market_odds[i] - 1)) - (1 - true_prob), 4)
                    }
                    
            return value_bets
            
        except Exception as e:
            print(f"Error in value_bet_3way: {e}")
            return {}

    def kelly_3way(self, true_probs, market_odds, bankroll):
        """
        Calculate Kelly-optimal stakes for 3-way markets.

        Args:
            true_probs: True probabilities for each outcome
            market_odds: Market odds for each outcome
            bankroll: Available bankroll

        Returns:
            dict: Kelly-optimal stakes for each outcome
        """
        kelly_stakes = {}
        
        try:
            outcomes = ['home_win', 'draw', 'away_win']
            true_prob_list = [true_probs['home_win'], true_probs['draw'], true_probs['away_win']]
            
            for i, (true_prob, odds) in enumerate(zip(true_prob_list, market_odds)):
                # Kelly Criterion for binary outcomes (we bet on one outcome at a time)
                # For 3-way, we calculate Kelly for each outcome independently
                b = odds - 1  # decimal odds profit
                p = true_prob
                q = 1 - true_prob
                
                kelly_fraction = (b * p - q) / b
                
                # Only bet positive edges
                if kelly_fraction > 0:
                    stake = bankroll * kelly_fraction
                    kelly_stakes[outcomes[i]] = {
                        'stake': round(stake, 2),
                        'kelly_fraction': round(kelly_fraction, 4),
                        'edge': round((b * p - q), 4)
                    }
                else:
                    kelly_stakes[outcomes[i]] = {
                        'stake': 0,
                        'kelly_fraction': 0,
                        'edge': round((b * p - q), 4)
                    }
                    
            return kelly_stakes
            
        except Exception as e:
            print(f"Error calculating Kelly stakes: {e}")
            return {}

    def spread_home_dog_to_fav(self, df):
        """
        Detect value when home team moves from underdog to favorite.
        Updated for 3-way market context.
        """
        try:
            # How Often Does the Home Team Win When They Move From Dog to Fav
            idx = np.where((df['Home Spread Close'] < 0) & (df['Home Score'] > df['Away Score']))
            home_flip_spread_win = df.loc[idx]

            idc = np.where((df['Home Spread Close'] < 0))
            home_flip_spread_total = df.loc[idc]

            if len(home_flip_spread_total) == 0:
                return None
                
            home_win_prob = len(home_flip_spread_win) / len(home_flip_spread_total)
            
            # For 3-way context, we might want draw and away win probabilities too
            draws = len(df[(df['Home Spread Close'] < 0) & (df['Home Score'] == df['Away Score'])])
            away_wins = len(df[(df['Home Spread Close'] < 0) & (df['Home Score'] < df['Away Score'])])
            
            total_games = len(home_flip_spread_total)
            
            return {
                'home_win': home_win_prob,
                'draw': draws / total_games,
                'away_win': away_wins / total_games,
                'total_games': total_games
            }
            
        except KeyError as e:
            print(f"Missing required column in DataFrame: {e}")
            return None
        except Exception as e:
            print(f"Error in spread_home_dog_to_fav: {e}")
            return None

    def spread_home_fav_to_dog(self, df):
        """
        Detect value when home team moves from favorite to underdog.
        Updated for 3-way market context.
        """
        try:
            # How Often Does the Home Team Win When They Move From Fav to Dog
            idx = np.where((df['Home Spread Close'] >= 0) & (df['Home Score'] > df['Away Score']))
            home_flip_spread_win = df.loc[idx]

            idc = np.where((df['Home Spread Close'] >= 0))
            home_flip_spread_total = df.loc[idc]

            if len(home_flip_spread_total) == 0:
                return None
                
            home_win_prob = len(home_flip_spread_win) / len(home_flip_spread_total)
            
            # Calculate all outcome probabilities for 3-way context
            draws = len(df[(df['Home Spread Close'] >= 0) & (df['Home Score'] == df['Away Score'])])
            away_wins = len(df[(df['Home Spread Close'] >= 0) & (df['Home Score'] < df['Away Score'])])
            
            total_games = len(home_flip_spread_total)
            
            return {
                'home_win': home_win_prob,
                'draw': draws / total_games,
                'away_win': away_wins / total_games,
                'total_games': total_games
            }
            
        except KeyError as e:
            print(f"Missing required column in DataFrame: {e}")
            return None
        except Exception as e:
            print(f"Error in spread_home_fav_to_dog: {e}")
            return None

    def comprehensive_value_analysis(self, df, current_odds_3way, bankroll, min_edge=0.02):
        """
        Comprehensive value analysis for 3-way markets.

        Args:
            df: Historical data DataFrame
            current_odds_3way: Current 3-way market odds [home, draw, away]
            bankroll: Available bankroll
            min_edge: Minimum edge threshold

        Returns:
            dict: Complete value analysis
        """
        analysis = {}
        
        try:
            # Calculate true probabilities from historical data
            true_probs = self.calculate_true_probabilities_3way(df)
            if not true_probs:
                return analysis
            
            # Find value bets
            value_bets = self.value_bet_3way(true_probs, current_odds_3way, min_edge)
            
            # Calculate Kelly stakes
            kelly_stakes = self.kelly_3way(true_probs, current_odds_3way, bankroll)
            
            # Specialized strategy analysis
            dog_to_fav_probs = self.spread_home_dog_to_fav(df)
            fav_to_dog_probs = self.spread_home_fav_to_dog(df)
            
            analysis = {
                'true_probabilities': {k: round(v, 4) for k, v in true_probs.items()},
                'market_probabilities': [round(self.prob_calc.decimal_implied_win_prob(odd), 4) for odd in current_odds_3way],
                'value_bets': value_bets,
                'kelly_stakes': kelly_stakes,
                'specialized_strategies': {
                    'home_dog_to_fav': dog_to_fav_probs,
                    'home_fav_to_dog': fav_to_dog_probs
                },
                'market_analysis': {
                    'total_vig': round(sum([self.prob_calc.decimal_implied_win_prob(odd) for odd in current_odds_3way]) - 1, 4),
                    'fair_odds': [round(1/prob, 2) for prob in true_probs.values()]
                }
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error in comprehensive_value_analysis: {e}")
            return {}

# For backward compatibility
_value_finder = ValueBetFinder()
spread_home_dog_to_fav = _value_finder.spread_home_dog_to_fav
spread_home_fav_to_dog = _value_finder.spread_home_fav_to_dog
