"""Kite Connect API wrapper for fetching trades and positions."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from kiteconnect import KiteConnect, KiteTicker
from dotenv import load_dotenv
from database import TradingDatabase
import threading
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KiteClient:
    """Wrapper for Kite Connect API operations."""

    def __init__(self):
        """Initialize Kite Connect client with credentials from database or environment."""
        self.api_key = os.getenv("KITE_API_KEY")

        if not self.api_key:
            raise ValueError("KITE_API_KEY must be set in environment")

        # Initialize database first
        self.db = TradingDatabase()

        # Try to load access token from database first, fallback to environment
        self.access_token = self.db.get_setting("access_token")
        if not self.access_token:
            # Fallback to environment variable (for first-time setup)
            self.access_token = os.getenv("KITE_ACCESS_TOKEN")
            if self.access_token:
                # Save to database for future use
                self.db.save_setting("access_token", self.access_token)
                print("💾 Access token saved to database from environment")

        if not self.access_token:
            raise ValueError("No access token found. Please authenticate via /setup page")

        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(self.access_token)

        # Initialize KiteTicker for real-time updates
        self.ticker = None
        self.ticker_thread = None
        self.order_update_callback = None

        print(f"🔑 Using access token from database")

    def set_access_token(self, access_token: str) -> bool:
        """
        Set new access token and save to database.

        Args:
            access_token: New access token from OAuth flow

        Returns:
            bool: True if successful
        """
        try:
            self.access_token = access_token
            self.kite.set_access_token(access_token)
            self.db.save_setting("access_token", access_token)
            print("✅ Access token updated and saved to database")
            return True
        except Exception as e:
            print(f"❌ Failed to set access token: {e}")
            return False

    def is_token_valid(self) -> bool:
        """
        Check if current access token is valid.

        Returns:
            bool: True if token is valid
        """
        try:
            self.kite.profile()
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "token" in error_msg or "session" in error_msg or "invalid" in error_msg:
                print(f"⚠️ Access token is invalid or expired: {e}")
                return False
            # Other errors might not be token-related
            print(f"⚠️ API error (might not be token): {e}")
            return False

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

    def sync_positions(self) -> Dict:
        """
        Sync positions from Kite API to database.

        Returns:
            Dict with sync statistics
        """
        try:
            # Fetch all positions from Kite API
            positions_data = self.kite.positions()
            net_positions = positions_data.get("net", [])

            # Process and prepare positions for database
            positions_to_save = []
            for position in net_positions:
                positions_to_save.append({
                    "tradingsymbol": position.get("tradingsymbol"),
                    "exchange": position.get("exchange"),
                    "quantity": position.get("quantity", 0),
                    "average_price": position.get("average_price", 0),
                    "last_price": position.get("last_price", 0),
                    "pnl": position.get("pnl", 0),
                    "unrealised": position.get("unrealised", 0),
                    "realised": position.get("realised", 0),
                    "product": position.get("product"),
                    "multiplier": position.get("multiplier", 1),
                })

            # Save to database with current timestamp
            snapshot_timestamp = datetime.now().isoformat()
            saved_count = self.db.save_positions(positions_to_save, snapshot_timestamp)

            return {
                "success": True,
                "positions_saved": saved_count,
                "snapshot_timestamp": snapshot_timestamp
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_positions(self) -> Dict:
        """
        Fetch current open positions with P&L (with offline fallback).

        Returns:
            Dict containing positions and P&L data
        """
        api_success = False
        processed_positions = []
        from_cache = False

        # Try to fetch from API and sync to database
        try:
            positions = self.kite.positions()
            net_positions = positions.get("net", [])

            # Process positions
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

            # Save to database
            sync_result = self.sync_positions()
            api_success = True

        except Exception as e:
            print(f"⚠️ Kite API unavailable: {e}")
            print("📂 Falling back to cached positions from database...")

            # Fallback to database
            try:
                db_positions = self.db.get_open_positions()
                from_cache = True

                for db_pos in db_positions:
                    processed_positions.append({
                        "tradingsymbol": db_pos.get("tradingsymbol"),
                        "exchange": db_pos.get("exchange"),
                        "quantity": db_pos.get("quantity"),
                        "average_price": db_pos.get("average_price"),
                        "last_price": db_pos.get("last_price"),
                        "pnl": db_pos.get("pnl"),
                        "unrealised": db_pos.get("unrealised"),
                        "realised": db_pos.get("realised"),
                        "product": db_pos.get("product"),
                        "multiplier": db_pos.get("multiplier", 1),
                    })

            except Exception as db_error:
                return {
                    "success": False,
                    "error": f"API and database both failed. API: {str(e)}, DB: {str(db_error)}"
                }

        # Calculate total P&L
        total_pnl = sum(pos.get("pnl", 0) for pos in processed_positions)
        total_unrealised = sum(pos.get("unrealised", 0) for pos in processed_positions)

        result = {
            "success": True,
            "data": processed_positions,
            "summary": {
                "total_pnl": total_pnl,
                "total_unrealised": total_unrealised,
                "position_count": len(processed_positions)
            },
            "from_cache": from_cache
        }

        # Add cache info if using offline data
        if from_cache:
            last_sync = self.db.get_latest_snapshot_timestamp()
            result["cache_info"] = {
                "last_updated": last_sync,
                "offline_mode": True
            }

        return result

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

    def sync_orders_to_db(self) -> Dict:
        """
        Sync orders from Kite API to database.
        Uses trades() API to get ALL historical trades, then creates order entries.
        Also syncs today's orders from orders() API.

        Returns:
            Dict with sync statistics
        """
        try:
            new_orders = 0
            completed_orders = 0

            # STEP 1: Sync historical trades (all time)
            # The trades() API returns ALL executed trades, not just today
            try:
                print("📡 Fetching trades from Kite API...")
                api_trades = self.kite.trades()
                print(f"   ✅ Received {len(api_trades)} trades from API")

                if len(api_trades) == 0:
                    print("   ⚠️ WARNING: trades() API returned ZERO trades!")
                    print("   This might indicate:")
                    print("      - No trades in account")
                    print("      - API limitation (only returns current session)")
                    print("      - API error or rate limit")

                # Group trades by order_id to create order entries
                orders_from_trades = {}
                for trade in api_trades:
                    order_id = trade.get("order_id")
                    if not order_id:
                        continue

                    # If we haven't seen this order yet, create entry
                    if order_id not in orders_from_trades:
                        timestamp = trade.get('order_timestamp', trade.get('fill_timestamp'))
                        orders_from_trades[order_id] = {
                            "order_id": order_id,
                            "trade_id": trade.get("trade_id"),
                            "symbol": trade.get("tradingsymbol"),
                            "exchange": trade.get("exchange"),
                            "action": trade.get("transaction_type"),
                            "quantity": trade.get("quantity", 0),
                            "entry_price": trade.get("average_price", trade.get("price", 0)),
                            "order_type": "MARKET",  # trades don't have order_type
                            "product": trade.get("product"),
                            "status": "COMPLETE",  # trades are always completed
                            "timestamp": str(timestamp) if timestamp else datetime.now().isoformat()
                        }
                    else:
                        # Update quantity if there are multiple fills for same order
                        orders_from_trades[order_id]["quantity"] += trade.get("quantity", 0)

                # Save orders from trades
                for order_data in orders_from_trades.values():
                    existing = self.db.get_order_by_id(order_data["order_id"])
                    if not existing:
                        new_orders += 1
                        completed_orders += 1
                    self.db.save_order(order_data)

                print(f"   ✅ Processed {len(orders_from_trades)} unique orders from trades")
                print(f"   📊 New orders: {new_orders}")

            except Exception as trade_error:
                print(f"⚠️ Failed to sync trades: {trade_error}")
                import traceback
                traceback.print_exc()

            # STEP 2: Sync today's orders from orders() API (for pending/cancelled/rejected)
            try:
                print("📡 Fetching today's orders from Kite API...")
                api_orders = self.kite.orders()
                print(f"   ✅ Received {len(api_orders)} orders from API")

                for order in api_orders:
                    # Save all orders (complete, pending, cancelled, rejected)
                    if order.get("status") in ["COMPLETE", "CANCELLED", "REJECTED", "OPEN", "TRIGGER PENDING"]:
                        order_data = {
                            "order_id": order.get("order_id"),
                            "trade_id": order.get("trade_id"),
                            "symbol": order.get("tradingsymbol"),
                            "exchange": order.get("exchange"),
                            "action": order.get("transaction_type"),
                            "quantity": order.get("quantity", 0),
                            "entry_price": order.get("average_price", 0),
                            "order_type": order.get("order_type"),
                            "product": order.get("product"),
                            "status": order.get("status"),
                            "timestamp": str(order.get("order_timestamp", datetime.now().isoformat()))
                        }

                        # Check if this is a new order
                        existing = self.db.get_order_by_id(order_data["order_id"])
                        if not existing:
                            new_orders += 1
                            if order.get("status") == "COMPLETE":
                                completed_orders += 1

                        # Save to database (will update if exists)
                        self.db.save_order(order_data)

                print(f"   ✅ Synced {len(api_orders)} orders from orders() API (today)")

            except Exception as order_error:
                print(f"⚠️ Failed to sync today's orders: {order_error}")

            return {
                "success": True,
                "new_orders": new_orders,
                "completed_orders": completed_orders,
                "synced_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ CRITICAL ERROR in sync_orders_to_db: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def get_order_book(self) -> Dict:
        """
        Get all orders from Kite API.

        Returns:
            Dict containing order book
        """
        try:
            orders = self.kite.orders()
            return {
                "success": True,
                "data": orders
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_ltp(self, symbols: List[str]) -> Dict:
        """
        Get last traded price for given symbols.

        Args:
            symbols: List of symbols in format "EXCHANGE:SYMBOL" (e.g., ["NSE:SBIN", "NSE:INFY"])

        Returns:
            Dict with symbol prices
        """
        try:
            ltp_data = self.kite.ltp(symbols)
            return {
                "success": True,
                "data": ltp_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def start_websocket(self, order_callback: Callable):
        """
        Start WebSocket connection for real-time order updates.

        Args:
            order_callback: Callback function to handle order updates
        """
        if self.ticker is not None:
            logger.warning("⚠️ WebSocket already running")
            return

        self.order_update_callback = order_callback

        try:
            # Initialize KiteTicker
            self.ticker = KiteTicker(self.api_key, self.access_token)

            # Set up callbacks
            self.ticker.on_connect = self._on_connect
            self.ticker.on_close = self._on_close
            self.ticker.on_error = self._on_error
            self.ticker.on_reconnect = self._on_reconnect
            self.ticker.on_noreconnect = self._on_noreconnect
            self.ticker.on_order_update = self._on_order_update

            # Start ticker in a separate thread
            def run_ticker():
                try:
                    logger.info("🚀 Starting KiteTicker WebSocket...")
                    self.ticker.connect(threaded=False)
                except Exception as e:
                    logger.error(f"❌ KiteTicker error: {e}")

            self.ticker_thread = threading.Thread(target=run_ticker, daemon=True)
            self.ticker_thread.start()

            logger.info("✅ WebSocket thread started")

        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket: {e}")
            self.ticker = None

    def stop_websocket(self):
        """Stop WebSocket connection."""
        if self.ticker:
            try:
                logger.info("🛑 Stopping KiteTicker WebSocket...")
                self.ticker.close()
                self.ticker = None
                logger.info("✅ WebSocket stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping WebSocket: {e}")

    def _on_connect(self, ws, response):
        """Callback when WebSocket connects."""
        logger.info(f"🔗 WebSocket connected! Response: {response}")

    def _on_close(self, ws, code, reason):
        """Callback when WebSocket closes."""
        logger.warning(f"🔌 WebSocket closed. Code: {code}, Reason: {reason}")

    def _on_error(self, ws, code, reason):
        """Callback for WebSocket errors."""
        logger.error(f"❌ WebSocket error. Code: {code}, Reason: {reason}")

    def _on_reconnect(self, ws, attempts_count):
        """Callback when WebSocket reconnects."""
        logger.info(f"🔄 WebSocket reconnecting... Attempt #{attempts_count}")

    def _on_noreconnect(self, ws):
        """Callback when WebSocket fails to reconnect."""
        logger.error("❌ WebSocket failed to reconnect")

    def _on_order_update(self, ws, data):
        """
        Callback when order update is received.

        Args:
            ws: WebSocket instance
            data: Order update data
        """
        try:
            logger.info(f"📬 Order update received: {data}")

            # Call the registered callback with order data
            if self.order_update_callback:
                self.order_update_callback(data)

        except Exception as e:
            logger.error(f"❌ Error processing order update: {e}")
