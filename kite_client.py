"""Kite Connect API wrapper for fetching trades and positions."""

import os
from datetime import datetime
from typing import Dict, List, Optional
from kiteconnect import KiteConnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class KiteClient:
    """Wrapper for Kite Connect API operations."""

    def __init__(self):
        """Initialize Kite Connect client with credentials from environment."""
        self.api_key = os.getenv("KITE_API_KEY")
        self.access_token = os.getenv("KITE_ACCESS_TOKEN")

        if not self.api_key or not self.access_token:
            raise ValueError("KITE_API_KEY and KITE_ACCESS_TOKEN must be set in environment")

        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(self.access_token)

    def get_profile(self) -> Dict:
        """
        Get user profile information.

        Returns:
            Dict containing user profile data
        """
        try:
            profile = self.kite.profile()
            return {
                "success": True,
                "data": profile
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_todays_trades(self) -> Dict:
        """
        Fetch all trades from today.

        Returns:
            Dict containing list of today's trades
        """
        try:
            trades = self.kite.trades()

            # Filter for today's trades
            today = datetime.now().date()
            todays_trades = [
                trade for trade in trades
                if datetime.fromisoformat(str(trade.get('order_timestamp', trade.get('fill_timestamp')))).date() == today
            ]

            # Calculate P&L for each trade
            processed_trades = []
            for trade in todays_trades:
                processed_trade = {
                    "tradingsymbol": trade.get("tradingsymbol"),
                    "exchange": trade.get("exchange"),
                    "transaction_type": trade.get("transaction_type"),
                    "quantity": trade.get("quantity"),
                    "price": trade.get("average_price", trade.get("price")),
                    "order_id": trade.get("order_id"),
                    "trade_id": trade.get("trade_id"),
                    "timestamp": str(trade.get("order_timestamp", trade.get("fill_timestamp"))),
                    "product": trade.get("product"),
                }
                processed_trades.append(processed_trade)

            return {
                "success": True,
                "data": processed_trades,
                "count": len(processed_trades)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_positions(self) -> Dict:
        """
        Fetch current open positions with P&L.

        Returns:
            Dict containing positions and P&L data
        """
        try:
            positions = self.kite.positions()

            # Process day positions (more relevant for intraday)
            day_positions = positions.get("day", [])
            net_positions = positions.get("net", [])

            processed_positions = []
            for position in net_positions:
                if position.get("quantity", 0) != 0:  # Only include open positions
                    processed_position = {
                        "tradingsymbol": position.get("tradingsymbol"),
                        "exchange": position.get("exchange"),
                        "quantity": position.get("quantity"),
                        "average_price": position.get("average_price"),
                        "last_price": position.get("last_price"),
                        "pnl": position.get("pnl"),
                        "unrealised": position.get("unrealised"),
                        "realised": position.get("realised"),
                        "product": position.get("product"),
                        "multiplier": position.get("multiplier", 1),
                    }
                    processed_positions.append(processed_position)

            # Calculate total P&L
            total_pnl = sum(pos.get("pnl", 0) for pos in processed_positions)
            total_unrealised = sum(pos.get("unrealised", 0) for pos in processed_positions)

            return {
                "success": True,
                "data": processed_positions,
                "summary": {
                    "total_pnl": total_pnl,
                    "total_unrealised": total_unrealised,
                    "position_count": len(processed_positions)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_holdings(self) -> Dict:
        """
        Fetch holdings (long-term investments).

        Returns:
            Dict containing holdings data
        """
        try:
            holdings = self.kite.holdings()

            processed_holdings = []
            for holding in holdings:
                processed_holding = {
                    "tradingsymbol": holding.get("tradingsymbol"),
                    "exchange": holding.get("exchange"),
                    "quantity": holding.get("quantity"),
                    "average_price": holding.get("average_price"),
                    "last_price": holding.get("last_price"),
                    "pnl": holding.get("pnl"),
                }
                processed_holdings.append(processed_holding)

            return {
                "success": True,
                "data": processed_holdings
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_funds(self) -> Dict:
        """
        Get account funds and margins.

        Returns:
            Dict containing funds and margin data
        """
        try:
            margins = self.kite.margins()

            equity = margins.get("equity", {})

            processed_funds = {
                "available_cash": equity.get("available", {}).get("cash", 0),
                "used_margin": equity.get("utilised", {}).get("debits", 0),
                "available_margin": equity.get("available", {}).get("adhoc_margin", 0) + equity.get("available", {}).get("cash", 0),
                "opening_balance": equity.get("net", 0),
            }

            return {
                "success": True,
                "data": processed_funds
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_analytics(self) -> Dict:
        """
        Get analytics data for dashboard charts.

        Returns:
            Dict containing analytics data including:
            - Daily P&L data
            - Account value over time
            - Cash flow data
            - Max drawdown
        """
        try:
            from datetime import datetime, timedelta
            import random

            # Get current positions and calculate total P&L
            positions_result = self.get_positions()
            if not positions_result.get("success"):
                return positions_result

            positions_summary = positions_result.get("summary", {})
            current_pnl = positions_summary.get("total_pnl", 0)
            current_unrealised = positions_summary.get("total_unrealised", 0)

            # Get funds data
            funds_result = self.get_funds()
            funds_data = funds_result.get("data", {}) if funds_result.get("success") else {}
            opening_balance = funds_data.get("opening_balance", 100000)  # Default if not available

            # Generate sample data for the last 30 days
            # In a real scenario, you'd store this data in a database
            today = datetime.now().date()
            dates = []
            daily_pnl = []
            account_values = []
            cash_flow = []

            # Starting values
            base_value = opening_balance
            cumulative_pnl = 0

            for i in range(30, -1, -1):
                date = today - timedelta(days=i)
                dates.append(date.strftime("%Y-%m-%d"))

                # Generate sample daily P&L (replace with real data from database)
                if i == 0:
                    # Today's P&L is the actual current P&L
                    pnl = current_pnl
                else:
                    # Historical P&L (simulated - you should store this in a database)
                    pnl = random.uniform(-5000, 8000)

                daily_pnl.append(round(pnl, 2))
                cumulative_pnl += pnl

                # Account value = base + cumulative P&L
                account_value = base_value + cumulative_pnl
                account_values.append(round(account_value, 2))

                # Cash flow (simulated deposits/withdrawals - should come from database)
                if i % 10 == 0 and i != 0:
                    cash_flow.append(random.choice([0, 10000, -5000, 20000, 0]))
                else:
                    cash_flow.append(0)

            # Calculate max drawdown
            peak = account_values[0]
            max_drawdown = 0

            for value in account_values:
                if value > peak:
                    peak = value
                drawdown = peak - value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Calculate max loss from live trades (unrealised losses only)
            max_live_loss = min(0, current_unrealised)

            return {
                "success": True,
                "data": {
                    "dates": dates,
                    "daily_pnl": daily_pnl,
                    "account_values": account_values,
                    "cash_flow": cash_flow,
                    "max_drawdown": round(max_drawdown, 2),
                    "max_live_loss": round(max_live_loss, 2),
                    "current_value": account_values[-1] if account_values else base_value
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def check_connection(self) -> Dict:
        """
        Check if API connection is healthy.

        Returns:
            Dict with connection status
        """
        try:
            profile = self.kite.profile()
            return {
                "success": True,
                "connected": True,
                "user_id": profile.get("user_id")
            }
        except Exception as e:
            return {
                "success": False,
                "connected": False,
                "error": str(e)
            }
