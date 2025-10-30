"""Kite Connect API wrapper for fetching trades and positions."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from kiteconnect import KiteConnect
from dotenv import load_dotenv
from database import TradingDatabase

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

        # Initialize database
        self.db = TradingDatabase()

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

    def sync_trades(self) -> Dict:
        """
        Sync trades from Kite API to database (incremental).

        Returns:
            Dict with sync statistics
        """
        try:
            # Fetch all trades from Kite API
            # Note: Kite API doesn't support date filtering, so we get all trades
            api_trades = self.kite.trades()

            # Process and prepare trades for database
            trades_to_save = []
            for trade in api_trades:
                timestamp = trade.get('order_timestamp', trade.get('fill_timestamp'))
                if timestamp:
                    trade_date = datetime.fromisoformat(str(timestamp)).date()

                    trades_to_save.append({
                        "trade_id": trade.get("trade_id"),
                        "order_id": trade.get("order_id"),
                        "tradingsymbol": trade.get("tradingsymbol"),
                        "exchange": trade.get("exchange"),
                        "transaction_type": trade.get("transaction_type"),
                        "quantity": trade.get("quantity"),
                        "price": trade.get("average_price", trade.get("price")),
                        "product": trade.get("product"),
                        "timestamp": str(timestamp),
                        "trade_date": str(trade_date)
                    })

            # Save to database (will ignore duplicates)
            new_count = self.db.save_trades(trades_to_save)
            total_count = self.db.get_total_trade_count()

            return {
                "success": True,
                "new_trades": new_count,
                "total_trades": total_count,
                "synced_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_todays_trades(self) -> Dict:
        """
        Fetch today's trades from database (with auto-sync).

        Returns:
            Dict containing list of today's trades
        """
        try:
            # First, sync new trades from API
            sync_result = self.sync_trades()
            if not sync_result.get("success"):
                print(f"Warning: Trade sync failed: {sync_result.get('error')}")

            # Get today's date
            today = str(datetime.now().date())

            # Fetch today's trades from database
            db_trades = self.db.get_trades_for_date(today)

            # Format trades for API response
            processed_trades = []
            for trade in db_trades:
                processed_trades.append({
                    "tradingsymbol": trade.get("tradingsymbol"),
                    "exchange": trade.get("exchange"),
                    "transaction_type": trade.get("transaction_type"),
                    "quantity": trade.get("quantity"),
                    "price": trade.get("price"),
                    "order_id": trade.get("order_id"),
                    "trade_id": trade.get("trade_id"),
                    "timestamp": trade.get("timestamp"),
                    "product": trade.get("product"),
                })

            return {
                "success": True,
                "data": processed_trades,
                "count": len(processed_trades),
                "synced": sync_result.get("new_trades", 0) if sync_result.get("success") else None
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
        Get analytics data for dashboard charts from database.

        Returns:
            Dict containing analytics data including:
            - Daily P&L data
            - Account value over time
            - Cash flow data
            - Max drawdown
        """
        try:
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

            # Generate date range for last 30 days
            today = datetime.now().date()
            dates = []
            for i in range(30, -1, -1):
                date = today - timedelta(days=i)
                dates.append(date.strftime("%Y-%m-%d"))

            # Get daily snapshots from database
            db_snapshots = self.db.get_daily_snapshots(days=30)
            snapshots_by_date = {snap["snapshot_date"]: snap for snap in db_snapshots}

            # Get cash flow from database
            db_cash_flow = self.db.get_daily_cash_flow_totals(days=30)

            # Get daily P&L from database (calculated from trades)
            db_daily_pnl = self.db.calculate_daily_pnl(days=30)

            # Build arrays for charts
            daily_pnl = []
            account_values = []
            cash_flow = []

            base_value = opening_balance
            cumulative_pnl = 0

            for date_str in dates:
                # Get P&L for this date
                if date_str in db_daily_pnl:
                    pnl = db_daily_pnl[date_str]
                elif date_str == str(today):
                    # Today's P&L from current positions
                    pnl = current_pnl
                else:
                    # No data for this date
                    pnl = 0

                daily_pnl.append(round(pnl, 2))
                cumulative_pnl += pnl

                # Get account value (use snapshot if available, otherwise calculate)
                if date_str in snapshots_by_date:
                    account_value = snapshots_by_date[date_str]["account_value"]
                else:
                    account_value = base_value + cumulative_pnl

                account_values.append(round(account_value, 2))

                # Get cash flow for this date
                cash_flow_amount = db_cash_flow.get(date_str, 0)
                cash_flow.append(round(cash_flow_amount, 2))

                # Adjust base value if there's cash flow
                if cash_flow_amount != 0:
                    base_value += cash_flow_amount

            # Calculate max drawdown
            peak = account_values[0] if account_values else base_value
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
                    "current_value": account_values[-1] if account_values else base_value,
                    "has_historical_data": len(db_snapshots) > 0 or len(db_daily_pnl) > 0
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
