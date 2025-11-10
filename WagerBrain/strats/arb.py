from WagerBrain import ProbabilityCalculator, OddsConverter

class ArbitrageCalculator:
    """
    Advanced arbitrage detection and calculation system.
    Supports 2-way and 3-way markets with multi-book arbitrage.
    """
    
    def __init__(self):
        """Initialize with WagerBrain utilities."""
        self.prob_calc = ProbabilityCalculator()
        self.odds_converter = OddsConverter()
    
    def arb_percentage(self, odds):
        """
        Calculate arbitrage percentage and implied probabilities for 2-way or 3-way markets.

        Args:
            odds: List of odds [outcome1, outcome2] for 2-way or [outcome1, outcome2, outcome3] for 3-way

        Returns:
            dict: {
                'arb_percent': total implied probability,
                'probabilities': [prob1, prob2, (prob3)],
                'market_type': '2-way' or '3-way',
                'vig': bookmaker margin
            }
            
        Raises:
            ValueError: If odds input is invalid
        """
        if not isinstance(odds, list) or len(odds) not in [2, 3]:
            raise ValueError("Odds input must be a list of length 2 (2-way) or 3 (3-way)")

        market_type = '3-way' if len(odds) == 3 else '2-way'
        
        # Calculate implied probabilities for all outcomes
        probabilities = []
        for odd in odds:
            prob = self.prob_calc.decimal_implied_win_prob(odd)
            probabilities.append(prob)
        
        arb_percent = sum(probabilities)
        vig = arb_percent - 1 if arb_percent > 1 else 0
        
        return {
            'arb_percent': arb_percent,
            'probabilities': probabilities,
            'market_type': market_type,
            'vig': vig
        }

    def arb_profit(self, arb_data, stake):
        """
        Calculate riskless profit from arbitrage opportunity.

        Args:
            arb_data: Dictionary from arb_percentage()
            stake: Total amount to wager across all positions

        Returns:
            float: Riskless profit if executed
        """
        if arb_data['arb_percent'] >= 1.0:
            return 0  # No arbitrage opportunity
            
        return stake / arb_data['arb_percent'] - stake

    def calculate_stakes(self, arb_data, stake):
        """
        Calculate optimal stake allocation for arbitrage.
        
        Args:
            arb_data: Dictionary from arb_percentage()
            stake: Total wager amount
            
        Returns:
            list: Stake amounts for each outcome
        """
        if arb_data['arb_percent'] >= 1.0:
            return None
            
        stakes = []
        for prob in arb_data['probabilities']:
            outcome_stake = (prob * stake) / arb_data['arb_percent']
            stakes.append(round(outcome_stake, 2))
            
        return stakes

    def basic_arbitrage(self, odds, stake):
        """
        Basic arbitrage calculator for 2-way and 3-way markets.

        Args:
            odds: List of odds for outcomes [outcome1, outcome2] or [outcome1, outcome2, outcome3]
            stake: Total amount to wager across all positions

        Returns:
            dict: Arbitrage opportunity details or None if no arb exists
        """
        try:
            if not isinstance(odds, list) or len(odds) not in [2, 3]:
                return None

            arb_data = self.arb_percentage(odds)

            # No arbitrage if combined probability >= 100%
            if arb_data['arb_percent'] >= 1.0:
                return None
                
            profit = self.arb_profit(arb_data, stake)
            stakes = self.calculate_stakes(arb_data, stake)
            roi = (profit / stake) * 100
            
            return {
                'profit': round(profit, 2),
                'stakes': stakes,
                'total_stake': stake,
                'arb_percent': round(arb_data['arb_percent'], 4),
                'vig': round(arb_data['vig'], 4),
                'market_type': arb_data['market_type'],
                'probabilities': [round(p, 4) for p in arb_data['probabilities']],
                'roi': round(roi, 2)
            }
            
        except Exception as e:
            print(f"Arbitrage calculation error: {e}")
            return None

    def three_way_arbitrage(self, home_odds, draw_odds, away_odds, stake):
        """
        Specialized 3-way market arbitrage calculator for soccer/football.

        Args:
            home_odds: Odds for home team win
            draw_odds: Odds for draw
            away_odds: Odds for away team win
            stake: Total wager amount

        Returns:
            dict: 3-way arbitrage opportunity
        """
        return self.basic_arbitrage([home_odds, draw_odds, away_odds], stake)

    def multi_book_arbitrage(self, odds_matrix, stake, market_type='2-way'):
        """
        Advanced arbitrage across multiple books for better prices.

        Args:
            odds_matrix: List of odds lists from different books
                        [[book1_home, book1_away], [book2_home, book2_away], ...]
            stake: Total wager amount
            market_type: '2-way' or '3-way'

        Returns:
            dict: Best arbitrage opportunity across books
        """
        best_arb = None
        best_profit = 0
        
        for i, book1_odds in enumerate(odds_matrix):
            for j, book2_odds in enumerate(odds_matrix):
                if i != j:  # Different books
                    # Take best odds from each book
                    if market_type == '2-way':
                        combined_odds = [max(book1_odds[0], book2_odds[0]), 
                                       max(book1_odds[1], book2_odds[1])]
                    else:  # 3-way
                        combined_odds = [max(book1_odds[0], book2_odds[0]),
                                       max(book1_odds[1], book2_odds[1]),
                                       max(book1_odds[2], book2_odds[2])]
                    
                    arb_opp = self.basic_arbitrage(combined_odds, stake)
                    if arb_opp and arb_opp['profit'] > best_profit:
                        best_profit = arb_opp['profit']
                        best_arb = arb_opp
                        best_arb['books_used'] = [i, j]
                        best_arb['combined_odds'] = combined_odds
        
        return best_arb

    def surebet_scanner(self, odds_list, min_roi=0.01):
        """
        Scan multiple arbitrage opportunities and filter by minimum ROI.

        Args:
            odds_list: List of odds sets to scan
            min_roi: Minimum ROI percentage to consider (default 1%)

        Returns:
            list: Profitable arbitrage opportunities
        """
        opportunities = []
        
        for odds_set in odds_list:
            # Test with standard $100 stake for comparison
            arb_opp = self.basic_arbitrage(odds_set, 100)
            if arb_opp and arb_opp['roi'] >= min_roi:
                opportunities.append(arb_opp)
                
        # Sort by ROI descending
        opportunities.sort(key=lambda x: x['roi'], reverse=True)
        return opportunities

# For backward compatibility
_arb_calculator = ArbitrageCalculator()
arb_percentage = _arb_calculator.arb_percentage
arb_profit = _arb_calculator.arb_profit
basic_arbitrage = _arb_calculator.basic_arbitrage
