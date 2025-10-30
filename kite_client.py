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
