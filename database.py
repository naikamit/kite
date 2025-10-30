"""Database module for persisting Kite trading data."""

import os
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional
from contextlib import contextmanager


class TradingDatabase:
    """SQLite database for storing trading history and analytics."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        # Use /app/data for Render, data/ for local
        if db_path is None:
            if os.path.exists("/app/data"):
                db_path = "/app/data/trading.db"
            else:
                db_path = "data/trading.db"
                # Ensure local data directory exists
                os.makedirs("data", exist_ok=True)

        self.db_path = db_path
        print(f"📁 Database location: {self.db_path}")
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    order_id TEXT,
                    tradingsymbol TEXT NOT NULL,
                    exchange TEXT,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    product TEXT,
                    timestamp TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on trade_date for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_date
                ON trades(trade_date)
            """)

            # Create index on timestamp for incremental sync
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp
                ON trades(timestamp)
            """)

            # Positions table (snapshots over time)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tradingsymbol TEXT NOT NULL,
                    exchange TEXT,
                    product TEXT,
                    quantity INTEGER NOT NULL,
                    average_price REAL NOT NULL,
                    last_price REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    unrealised REAL DEFAULT 0,
                    realised REAL DEFAULT 0,
                    multiplier REAL DEFAULT 1,
                    is_open INTEGER DEFAULT 1,
                    snapshot_date TEXT NOT NULL,
                    snapshot_timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on snapshot_timestamp for latest positions
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_positions_timestamp
                ON positions(snapshot_timestamp)
            """)

            # Create index on symbol for querying position history
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_positions_symbol
                ON positions(tradingsymbol, snapshot_date)
            """)

            # Create index on is_open for filtering open positions
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_positions_open
                ON positions(is_open)
            """)

            # Daily snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_snapshots (
                    snapshot_date TEXT PRIMARY KEY,
                    account_value REAL NOT NULL,
                    total_pnl REAL DEFAULT 0,
                    realized_pnl REAL DEFAULT 0,
                    unrealized_pnl REAL DEFAULT 0,
                    trade_count INTEGER DEFAULT 0,
                    position_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Cash flow table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cash_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flow_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    flow_type TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on flow_date
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cash_flow_date
                ON cash_flow(flow_date)
            """)

    def save_trades(self, trades: List[Dict]) -> int:
        """
        Save trades to database (insert or ignore duplicates).

        Args:
            trades: List of trade dictionaries

        Returns:
            Number of new trades inserted
        """
        if not trades:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0

            for trade in trades:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO trades
                        (trade_id, order_id, tradingsymbol, exchange,
                         transaction_type, quantity, price, product,
                         timestamp, trade_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trade.get("trade_id"),
                        trade.get("order_id"),
                        trade.get("tradingsymbol"),
                        trade.get("exchange"),
                        trade.get("transaction_type"),
                        trade.get("quantity"),
                        trade.get("price"),
                        trade.get("product"),
                        trade.get("timestamp"),
                        trade.get("trade_date")
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    print(f"Error saving trade {trade.get('trade_id')}: {e}")

            return inserted

    def get_last_trade_timestamp(self) -> Optional[str]:
        """Get the timestamp of the most recent trade in database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(timestamp) as last_timestamp
                FROM trades
            """)
            row = cursor.fetchone()
            return row["last_timestamp"] if row else None

    def get_trades_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get trades within a date range."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                WHERE trade_date BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """, (start_date, end_date))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_trades_for_date(self, trade_date: str) -> List[Dict]:
        """Get all trades for a specific date."""
        return self.get_trades_by_date_range(trade_date, trade_date)

    def get_daily_trade_counts(self, days: int = 30) -> Dict[str, int]:
        """Get trade counts grouped by date for last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT trade_date, COUNT(*) as count
                FROM trades
                WHERE trade_date >= date('now', '-' || ? || ' days')
                GROUP BY trade_date
                ORDER BY trade_date
            """, (days,))

            rows = cursor.fetchall()
            return {row["trade_date"]: row["count"] for row in rows}

    def save_positions(self, positions: List[Dict], snapshot_timestamp: str = None) -> int:
        """
        Save position snapshots to database.

        Args:
            positions: List of position dictionaries
            snapshot_timestamp: ISO timestamp for this snapshot (defaults to now)

        Returns:
            Number of positions inserted
        """
        if not positions:
            return 0

        from datetime import datetime
        if not snapshot_timestamp:
            snapshot_timestamp = datetime.now().isoformat()

        snapshot_date = snapshot_timestamp.split('T')[0]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0

            for position in positions:
                try:
                    is_open = 1 if position.get("quantity", 0) != 0 else 0

                    cursor.execute("""
                        INSERT INTO positions
                        (tradingsymbol, exchange, product, quantity, average_price,
                         last_price, pnl, unrealised, realised, multiplier,
                         is_open, snapshot_date, snapshot_timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        position.get("tradingsymbol"),
                        position.get("exchange"),
                        position.get("product"),
                        position.get("quantity", 0),
                        position.get("average_price", 0),
                        position.get("last_price", 0),
                        position.get("pnl", 0),
                        position.get("unrealised", 0),
                        position.get("realised", 0),
                        position.get("multiplier", 1),
                        is_open,
                        snapshot_date,
                        snapshot_timestamp
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"Error saving position {position.get('tradingsymbol')}: {e}")

            return inserted

    def get_latest_positions(self) -> List[Dict]:
        """Get the most recent position snapshot for all symbols."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get the latest snapshot timestamp
            cursor.execute("""
                SELECT MAX(snapshot_timestamp) as latest
                FROM positions
            """)
            row = cursor.fetchone()
            latest_timestamp = row["latest"] if row else None

            if not latest_timestamp:
                return []

            # Get all positions from that snapshot
            cursor.execute("""
                SELECT * FROM positions
                WHERE snapshot_timestamp = ?
                ORDER BY tradingsymbol
            """, (latest_timestamp,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_open_positions(self) -> List[Dict]:
        """Get latest snapshot of all open positions (quantity != 0)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get the latest snapshot timestamp
            cursor.execute("""
                SELECT MAX(snapshot_timestamp) as latest
                FROM positions
            """)
            row = cursor.fetchone()
            latest_timestamp = row["latest"] if row else None

            if not latest_timestamp:
                return []

            # Get open positions from latest snapshot
            cursor.execute("""
                SELECT * FROM positions
                WHERE snapshot_timestamp = ?
                AND is_open = 1
                ORDER BY tradingsymbol
            """, (latest_timestamp,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_position_history(self, tradingsymbol: str, days: int = 30) -> List[Dict]:
        """Get position history for a specific symbol."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM positions
                WHERE tradingsymbol = ?
                AND snapshot_date >= date('now', '-' || ? || ' days')
                ORDER BY snapshot_timestamp DESC
            """, (tradingsymbol, days))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_latest_snapshot_timestamp(self) -> Optional[str]:
        """Get the timestamp of the most recent position snapshot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(snapshot_timestamp) as latest
                FROM positions
            """)
            row = cursor.fetchone()
            return row["latest"] if row else None

    def save_daily_snapshot(self, snapshot_date: str, account_value: float,
                           total_pnl: float = 0, realized_pnl: float = 0,
                           unrealized_pnl: float = 0, trade_count: int = 0,
                           position_count: int = 0):
        """Save or update daily snapshot."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO daily_snapshots
                (snapshot_date, account_value, total_pnl, realized_pnl,
                 unrealized_pnl, trade_count, position_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_date, account_value, total_pnl, realized_pnl,
                  unrealized_pnl, trade_count, position_count))

    def get_daily_snapshots(self, days: int = 30) -> List[Dict]:
        """Get daily snapshots for last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_snapshots
                WHERE snapshot_date >= date('now', '-' || ? || ' days')
                ORDER BY snapshot_date
            """, (days,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def save_cash_flow(self, flow_date: str, amount: float,
                      flow_type: str, description: str = ""):
        """Save a cash flow entry (deposit/withdrawal)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cash_flow (flow_date, amount, flow_type, description)
                VALUES (?, ?, ?, ?)
            """, (flow_date, amount, flow_type, description))

    def get_cash_flow(self, days: int = 30) -> List[Dict]:
        """Get cash flow entries for last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM cash_flow
                WHERE flow_date >= date('now', '-' || ? || ' days')
                ORDER BY flow_date
            """, (days,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_daily_cash_flow_totals(self, days: int = 30) -> Dict[str, float]:
        """Get cash flow totals grouped by date for last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT flow_date, SUM(amount) as total
                FROM cash_flow
                WHERE flow_date >= date('now', '-' || ? || ' days')
                GROUP BY flow_date
                ORDER BY flow_date
            """, (days,))

            rows = cursor.fetchall()
            return {row["flow_date"]: row["total"] for row in rows}

    def calculate_daily_pnl(self, days: int = 30) -> Dict[str, float]:
        """
        Calculate daily P&L from trades (simplified calculation).
        For a more accurate P&L, use daily_snapshots.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    trade_date,
                    SUM(CASE
                        WHEN transaction_type = 'SELL' THEN quantity * price
                        WHEN transaction_type = 'BUY' THEN -quantity * price
                        ELSE 0
                    END) as daily_pnl
                FROM trades
                WHERE trade_date >= date('now', '-' || ? || ' days')
                GROUP BY trade_date
                ORDER BY trade_date
            """, (days,))

            rows = cursor.fetchall()
            return {row["trade_date"]: row["daily_pnl"] for row in rows}

    def get_total_trade_count(self) -> int:
        """Get total number of trades in database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM trades")
            row = cursor.fetchone()
            return row["count"] if row else 0
