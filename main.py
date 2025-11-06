"""FastAPI application for Kite Connect Analytics Dashboard."""

import os
import json
from datetime import datetime, time as dt_time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from kiteconnect import KiteConnect
from kite_client import KiteClient
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import uvicorn

# AI Coach imports
from coach_system_prompt import SelfImprovingCoach, CoachMemory
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic package not installed. Run: pip install anthropic")

# Initialize FastAPI app
app = FastAPI(title="Kite Connect Analytics MVP")

# App version (timestamp of startup)
APP_VERSION = datetime.now().isoformat()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Kite client
print("🔍 Checking environment variables...")
print(f"   KITE_API_KEY: {'✓ Set' if os.getenv('KITE_API_KEY') else '✗ Missing'}")
print(f"   KITE_API_SECRET: {'✓ Set' if os.getenv('KITE_API_SECRET') else '✗ Missing'}")

try:
    kite_client = KiteClient()
    print("✅ Kite Connect client initialized successfully")

    # Verify token is valid
    if not kite_client.is_token_valid():
        print("⚠️ Access token is invalid or expired. User will be redirected to /setup")
        # Don't set to None, keep client but it will redirect on dashboard access

except Exception as e:
    print(f"❌ Failed to initialize Kite Connect client: {e}")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error details: {str(e)}")
    print(f"   User will be redirected to /setup page")
    kite_client = None

# Initialize background scheduler
scheduler = BackgroundScheduler()

# Store for new order notifications (simple in-memory for MVP)
new_order_notifications = []


def handle_order_update(order_data):
    """
    Callback for real-time order updates from WebSocket.

    Args:
        order_data: Order update from KiteTicker
    """
    try:
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🔔 WEBSOCKET ORDER UPDATE RECEIVED")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   Data: {json.dumps(order_data, indent=2)}")

        # Check if order is completed
        status = order_data.get("status")
        print(f"   Status: {status}")

        if status in ["COMPLETE", "CANCELLED", "REJECTED"]:
            order_id = order_data.get("order_id")
            symbol = order_data.get("tradingsymbol")

            print(f"   ✅ Order {status}: {symbol} (ID: {order_id})")

            # Save order to database
            order_to_save = {
                "order_id": order_id,
                "trade_id": order_data.get("exchange_order_id"),
                "symbol": symbol,
                "exchange": order_data.get("exchange"),
                "action": order_data.get("transaction_type"),
                "quantity": order_data.get("filled_quantity", 0),
                "entry_price": order_data.get("average_price", 0),
                "order_type": order_data.get("order_type"),
                "product": order_data.get("product"),
                "status": status,
                "timestamp": order_data.get("exchange_timestamp", datetime.now().isoformat())
            }

            kite_client.db.save_order(order_to_save)
            print(f"   💾 Saved order {order_id} to database")

            # Add to notification queue if completed successfully
            if status == "COMPLETE":
                notification = {
                    "order_id": order_id,
                    "symbol": order_to_save["symbol"],
                    "action": order_to_save["action"],
                    "quantity": order_to_save["quantity"],
                    "price": order_to_save["entry_price"],
                    "timestamp": datetime.now().isoformat()
                }

                # Only add if not already in queue
                if not any(n["order_id"] == order_id for n in new_order_notifications):
                    new_order_notifications.append(notification)
                    print(f"   🔔 Added to notification queue (Total: {len(new_order_notifications)})")
                    print(f"   📬 Browser will pick this up on next /api/notifications poll")
                else:
                    print(f"   ⚠️ Notification already exists for this order")
        else:
            print(f"   ℹ️ Status '{status}' - Not adding notification (only COMPLETE/CANCELLED/REJECTED)")

        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except Exception as e:
        print(f"❌ Error handling order update: {e}")
        import traceback
        traceback.print_exc()


def is_market_hours() -> bool:
    """Check if current time is during market hours (9:15 AM - 3:30 PM IST)."""
    now = datetime.now().time()
    market_open = dt_time(9, 15)
    market_close = dt_time(15, 30)
    return market_open <= now <= market_close


def sync_orders_job():
    """Background job to sync orders from Kite API (fallback for WebSocket)."""
    if not kite_client:
        return

    try:
        print(f"📥 [POLLING FALLBACK] Syncing orders from Kite API at {datetime.now().strftime('%H:%M:%S')}...")
        result = kite_client.sync_orders_to_db()

        if result.get("success"):
            new_completed = result.get("completed_orders", 0)
            new_orders = result.get("new_orders", 0)

            if new_completed > 0:
                print(f"   ✨ {new_completed} new completed order(s) detected via polling!")

                # Get unlogged orders for notifications
                unlogged = kite_client.db.get_unlogged_orders(limit=10)
                print(f"   📋 Found {len(unlogged)} unlogged order(s)")

                for order in unlogged:
                    # Add to notification queue
                    notification = {
                        "order_id": order["order_id"],
                        "symbol": order["symbol"],
                        "action": order["action"],
                        "quantity": order["quantity"],
                        "price": order["entry_price"],
                        "timestamp": datetime.now().isoformat()
                    }
                    # Only add if not already in queue
                    if not any(n["order_id"] == order["order_id"] for n in new_order_notifications):
                        new_order_notifications.append(notification)
                        print(f"   🔔 Added notification for {order['symbol']} (Order: {order['order_id']})")
                    else:
                        print(f"   ⚠️ Notification already exists for {order['symbol']}")

                print(f"   📬 Notification queue size: {len(new_order_notifications)}")

            print(f"   ℹ️ Sync complete: {new_orders} new order(s), {new_completed} completed")
        else:
            print(f"⚠️ Order sync failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ Order sync job error: {e}")
        import traceback
        traceback.print_exc()


def monitor_positions_job():
    """Background job to monitor open positions and send alerts."""
    if not kite_client or not is_market_hours():
        return

    try:
        print("👁️ Monitoring open positions...")
        monitored = kite_client.db.get_active_monitored_positions()

        if not monitored:
            return

        # Get current prices for all monitored symbols
        symbols = [f"{p['exchange']}:{p['symbol']}" for p in monitored]
        ltp_result = kite_client.get_ltp(symbols)

        if not ltp_result.get("success"):
            print(f"⚠️ Failed to fetch LTP: {ltp_result.get('error')}")
            return

        ltp_data = ltp_result.get("data", {})

        for position in monitored:
            symbol_key = f"{position['exchange']}:{position['symbol']}"
            if symbol_key not in ltp_data:
                continue

            current_price = ltp_data[symbol_key]["last_price"]
            entry_price = position["entry_price"]
            quantity = position["quantity"]
            target = position["target_price"]
            stop_loss = position["stop_loss"]

            # Calculate unrealized P&L
            unrealized_pnl = (current_price - entry_price) * quantity

            # Update position price
            kite_client.db.update_monitored_position_price(
                position["id"], current_price, unrealized_pnl
            )

            # Check alert conditions
            alerts_sent = json.loads(position.get("alerts_sent", "{}"))

            # Target proximity alert (95% of target)
            if not alerts_sent.get("target_alert"):
                if (entry_price < target and current_price >= target * 0.95) or \
                   (entry_price > target and current_price <= target * 1.05):
                    print(f"🎯 Target alert: {position['symbol']} @ ₹{current_price} (Target: ₹{target})")
                    alerts_sent["target_alert"] = True
                    kite_client.db.update_monitoring_alerts(position["id"], json.dumps(alerts_sent))

            # Stop loss proximity alert (within 2%)
            if not alerts_sent.get("sl_alert"):
                if (entry_price > stop_loss and current_price <= stop_loss * 1.02) or \
                   (entry_price < stop_loss and current_price >= stop_loss * 0.98):
                    print(f"🛑 Stop loss alert: {position['symbol']} @ ₹{current_price} (SL: ₹{stop_loss})")
                    alerts_sent["sl_alert"] = True
                    kite_client.db.update_monitoring_alerts(position["id"], json.dumps(alerts_sent))

        print(f"   Monitored {len(monitored)} position(s)")

    except Exception as e:
        print(f"❌ Position monitoring job error: {e}")


# Start background jobs
if kite_client:
    # Start WebSocket for real-time order updates
    try:
        print("🚀 Starting WebSocket for real-time order updates...")
        kite_client.start_websocket(order_callback=handle_order_update)
        print("✅ WebSocket started for instant order notifications")
    except Exception as e:
        print(f"⚠️ WebSocket failed to start: {e}")
        print("   Falling back to polling mode")

    # Sync orders every 5 minutes (fallback for WebSocket)
    # Reduced from 30 seconds since WebSocket provides real-time updates
    scheduler.add_job(
        func=sync_orders_job,
        trigger=IntervalTrigger(minutes=5),
        id="sync_orders",
        name="Sync orders from Kite API (fallback)",
        replace_existing=True
    )

    # Monitor positions every 1 minute (only during market hours)
    scheduler.add_job(
        func=monitor_positions_job,
        trigger=IntervalTrigger(minutes=1),
        id="monitor_positions",
        name="Monitor open positions",
        replace_existing=True
    )

    scheduler.start()
    print("✅ Background jobs started")
    print("   - Order sync: every 5 minutes (fallback for WebSocket)")
    print("   - Position monitoring: every 1 minute (market hours only)")
    print("   - Real-time order updates: via WebSocket ⚡")
else:
    print("⚠️ Background jobs not started (Kite client unavailable)")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard page."""
    # If no kite client or token is invalid, redirect to setup
    if not kite_client:
        return RedirectResponse(url="/setup")

    # Check if token is valid
    if not kite_client.is_token_valid():
        print("🔄 Token invalid, redirecting to setup for re-authentication")
        return RedirectResponse(url="/setup")

    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/raw", response_class=HTMLResponse)
async def raw_data(request: Request):
    """Serve the raw historical data viewer page."""
    if not kite_client:
        return templates.TemplateResponse("raw.html", {
            "request": request,
            "error": "Kite client not initialized"
        })

    return templates.TemplateResponse("raw.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Serve the admin panel with all API endpoints."""
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Serve the test order emulation page."""
    return templates.TemplateResponse("test.html", {"request": request})


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Serve the OAuth setup page."""
    api_key = os.getenv("KITE_API_KEY", "")
    has_token = bool(os.getenv("KITE_ACCESS_TOKEN"))
    return templates.TemplateResponse("setup.html", {
        "request": request,
        "api_key": api_key,
        "has_token": has_token
    })


@app.get("/callback")
async def oauth_callback(request: Request, request_token: str = None, status: str = None):
    """Handle OAuth callback from Kite Connect."""
    global kite_client

    if status != "success" or not request_token:
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "error": "OAuth authorization failed or was cancelled",
            "api_key": os.getenv("KITE_API_KEY", ""),
            "has_token": False
        })

    api_key = os.getenv("KITE_API_KEY")
    api_secret = os.getenv("KITE_API_SECRET")

    if not api_key or not api_secret:
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "error": "KITE_API_KEY and KITE_API_SECRET must be set in environment variables",
            "api_key": "",
            "has_token": False
        })

    try:
        # Generate access token
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]

        # Save token to database
        if kite_client:
            kite_client.set_access_token(access_token)
        else:
            # Reinitialize kite_client if it was None
            try:
                kite_client = KiteClient()
                kite_client.set_access_token(access_token)
                print("✅ Kite client reinitialized with new token")
            except Exception as init_error:
                print(f"⚠️ Could not reinitialize client: {init_error}")

        # Return success message
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "success": True,
            "access_token": access_token,
            "api_key": api_key,
            "has_token": True,
            "message": "Access token generated and saved! Your dashboard is now ready."
        })

    except Exception as e:
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "error": f"Failed to generate access token: {str(e)}",
            "api_key": api_key,
            "has_token": False
        })


@app.post("/postback")
async def postback_handler(request: Request):
    """Handle postback from Kite Connect for order updates."""
    # This is optional - just log the postback for now
    try:
        data = await request.json()
        print(f"📬 Postback received: {data}")
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Postback error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/version")
async def get_version():
    """Get current app version for update detection."""
    return {
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Check API and Kite Connect health status."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Kite client not initialized. Check your API credentials."
            }
        )

    connection_status = kite_client.check_connection()

    return {
        "status": "healthy" if connection_status.get("connected") else "error",
        "kite_connected": connection_status.get("connected", False),
        "user_id": connection_status.get("user_id"),
        "error": connection_status.get("error")
    }


@app.get("/api/profile")
async def get_profile():
    """Get user profile information."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.get_profile()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/trades")
async def get_todays_trades():
    """Get all trades from today."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.get_todays_trades()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/positions")
async def get_positions():
    """Get current open positions with P&L."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.get_positions()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/holdings")
async def get_holdings():
    """Get holdings (long-term investments)."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.get_holdings()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/funds")
async def get_funds():
    """Get account funds and margins."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.get_funds()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data for charts and visualizations."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.get_analytics()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.post("/api/cash-flow")
async def add_cash_flow(request: Request):
    """
    Add a cash flow entry (deposit/withdrawal).

    Body: {
        "date": "2025-10-30",
        "amount": 10000,
        "type": "deposit" or "withdrawal",
        "description": "Optional description"
    }
    """
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        data = await request.json()
        flow_date = data.get("date")
        amount = float(data.get("amount", 0))
        flow_type = data.get("type", "deposit")
        description = data.get("description", "")

        # Validate inputs
        if not flow_date or amount == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "date and amount are required"}
            )

        if flow_type not in ["deposit", "withdrawal"]:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "type must be 'deposit' or 'withdrawal'"}
            )

        # For withdrawals, make amount negative
        if flow_type == "withdrawal" and amount > 0:
            amount = -amount

        # Save to database
        kite_client.db.save_cash_flow(flow_date, amount, flow_type, description)

        return {
            "success": True,
            "message": f"{flow_type.capitalize()} of ₹{abs(amount)} recorded for {flow_date}"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/snapshot")
async def create_snapshot(request: Request):
    """
    Create or update a daily snapshot.

    Body: {
        "date": "2025-10-30",
        "account_value": 105000,
        "total_pnl": 5000,
        "realized_pnl": 3000,
        "unrealized_pnl": 2000,
        "trade_count": 10,
        "position_count": 3
    }
    """
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        data = await request.json()
        snapshot_date = data.get("date")
        account_value = float(data.get("account_value", 0))

        if not snapshot_date or account_value == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "date and account_value are required"}
            )

        # Save snapshot
        kite_client.db.save_daily_snapshot(
            snapshot_date=snapshot_date,
            account_value=account_value,
            total_pnl=float(data.get("total_pnl", 0)),
            realized_pnl=float(data.get("realized_pnl", 0)),
            unrealized_pnl=float(data.get("unrealized_pnl", 0)),
            trade_count=int(data.get("trade_count", 0)),
            position_count=int(data.get("position_count", 0))
        )

        return {
            "success": True,
            "message": f"Snapshot saved for {snapshot_date}"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/sync-trades")
async def sync_trades():
    """Manually trigger trade sync from Kite API to database."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.sync_trades()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/sync-orders")
async def sync_orders():
    """Manually trigger full order sync (historical + today) from Kite API."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    print("🔄 Manual full order sync triggered...")
    result = kite_client.sync_orders_to_db()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/sync-positions")
async def sync_positions():
    """Manually trigger position sync from Kite API to database."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    result = kite_client.sync_positions()

    if not result.get("success"):
        return JSONResponse(
            status_code=500,
            content=result
        )

    return result


@app.get("/api/raw/trades")
async def get_raw_trades(
    start_date: str = None,
    end_date: str = None,
    symbol: str = None,
    limit: int = 1000
):
    """Get raw trade data with optional filters."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        from datetime import datetime, timedelta

        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().date().isoformat()
        if not start_date:
            start_date = (datetime.now().date() - timedelta(days=30)).isoformat()

        # Get trades from database
        if symbol:
            trades = kite_client.db.get_trades_by_date_range(start_date, end_date)
            trades = [t for t in trades if t.get("tradingsymbol") == symbol]
        else:
            trades = kite_client.db.get_trades_by_date_range(start_date, end_date)

        # Limit results
        trades = trades[:limit]

        return {
            "success": True,
            "data": trades,
            "count": len(trades),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "symbol": symbol,
                "limit": limit
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/raw/positions")
async def get_raw_positions(days: int = 30, symbol: str = None):
    """Get raw position snapshots with optional filters."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        if symbol:
            positions = kite_client.db.get_position_history(symbol, days=days)
        else:
            # Get all positions from last N days
            from datetime import datetime, timedelta
            start_date = (datetime.now().date() - timedelta(days=days)).isoformat()

            with kite_client.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM positions
                    WHERE snapshot_date >= ?
                    ORDER BY snapshot_timestamp DESC
                    LIMIT 1000
                """, (start_date,))
                rows = cursor.fetchall()
                positions = [dict(row) for row in rows]

        return {
            "success": True,
            "data": positions,
            "count": len(positions),
            "filters": {
                "days": days,
                "symbol": symbol
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# Trading Log API Endpoints

@app.get("/api/notifications")
async def get_notifications():
    """Get pending order notifications for the user."""
    count = len(new_order_notifications)
    if count > 0:
        print(f"📬 GET /api/notifications - Returning {count} notification(s)")
    return {
        "success": True,
        "notifications": new_order_notifications,
        "count": count
    }


@app.post("/api/notifications/clear")
async def clear_notification(request: Request):
    """Clear a notification by order_id."""
    try:
        data = await request.json()
        order_id = data.get("order_id")

        global new_order_notifications
        initial_count = len(new_order_notifications)
        new_order_notifications = [n for n in new_order_notifications if n["order_id"] != order_id]
        cleared_count = initial_count - len(new_order_notifications)

        print(f"🗑️ POST /api/notifications/clear - Cleared notification for order {order_id} ({cleared_count} removed)")

        return {"success": True}
    except Exception as e:
        print(f"❌ Error clearing notification: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/unlogged-orders")
async def get_unlogged_orders():
    """Get orders that haven't been logged yet."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        orders = kite_client.db.get_unlogged_orders(limit=50)
        return {
            "success": True,
            "data": orders,
            "count": len(orders)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/trade-log")
async def save_trade_log(request: Request):
    """Save trade log entry for an order."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        data = await request.json()
        order_id = data.get("order_id")
        target_price = float(data.get("target_price"))
        stop_loss = float(data.get("stop_loss"))

        print(f"📝 POST /api/trade-log - Order {order_id}")
        print(f"   Target: ₹{target_price}, SL: ₹{stop_loss}")
        print(f"   Emotion: {data.get('emotion')}, Strategy: {data.get('strategy')}")

        # Validate required fields
        if not order_id or not target_price or not stop_loss:
            print(f"❌ Validation failed: Missing required fields")
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "order_id, target_price, and stop_loss are required"}
            )

        # Get order details
        order = kite_client.db.get_order_by_id(order_id)
        if not order:
            print(f"❌ Order {order_id} not found in database")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Order not found"}
            )

        print(f"   Order found: {order['symbol']} {order['action']} @ ₹{order['entry_price']} (Qty: {order['quantity']})")

        # Calculate risk/reward
        entry_price = order["entry_price"]
        quantity = order["quantity"]
        action = order["action"]

        if action == "BUY":
            risk_amount = abs(entry_price - stop_loss) * quantity
            reward_amount = abs(target_price - entry_price) * quantity
        else:  # SELL
            risk_amount = abs(stop_loss - entry_price) * quantity
            reward_amount = abs(entry_price - target_price) * quantity

        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        print(f"   R:R = 1:{risk_reward_ratio:.2f} (Risk: ₹{risk_amount:.2f}, Reward: ₹{reward_amount:.2f})")

        # Save trade log
        log_data = {
            "order_id": order_id,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_amount": risk_amount,
            "reward_amount": reward_amount,
            "risk_reward_ratio": risk_reward_ratio,
            "emotion": data.get("emotion"),
            "strategy": data.get("strategy"),
            "notes": data.get("notes")
        }

        log_id = kite_client.db.save_trade_log(log_data)

        if log_id:
            print(f"✅ Trade log saved with ID: {log_id}")

            # Add to position monitoring
            monitoring_data = {
                "order_id": order_id,
                "symbol": order["symbol"],
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": entry_price,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "unrealized_pnl": 0
            }
            kite_client.db.save_monitored_position(monitoring_data)
            print(f"📊 Added {order['symbol']} to position monitoring")

            return {
                "success": True,
                "log_id": log_id,
                "message": "Trade logged successfully"
            }
        else:
            print(f"❌ Failed to save trade log to database")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to save trade log"}
            )

    except Exception as e:
        print(f"❌ Error saving trade log: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/coach")
async def ask_coach(request: Request):
    """
    AI Coaching endpoint using Claude.

    Provides personalized trading psychology feedback based on:
    - User's trading history and patterns
    - Long-term conversational memory
    - Current journey stage (activation → mastery)
    """
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    if not ANTHROPIC_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Anthropic API not available. Install: pip install anthropic"}
        )

    try:
        data = await request.json()
        user_message = data.get("message", "")
        user_id = data.get("user_id", "default_user")
        session_id = data.get("session_id")
        trade_context = data.get("trade_context")  # Optional: trade details for post-trade coaching

        print(f"💬 Coach request from {user_id}: {user_message[:50]}...")

        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_api_key_here":
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "ANTHROPIC_API_KEY not set in environment. Get your key at https://console.anthropic.com/"
                }
            )

        # Initialize coach and memory
        coach = SelfImprovingCoach(kite_client.db)
        memory = CoachMemory(kite_client.db)

        # Build personalized system prompt with memory
        system_prompt = coach.build_prompt_with_memory(
            user_id=user_id,
            current_message=user_message,
            memory_manager=memory
        )

        # Add trade context if provided (for post-trade coaching)
        if trade_context:
            user_message = f"{user_message}\n\nTrade context:\n{trade_context}"

        # Call Claude API
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Latest Claude model
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        coach_response = response.content[0].text

        print(f"🤖 Coach response: {coach_response[:100]}...")

        # Save conversation to database
        conversation_id = kite_client.db.save_conversation(
            user_id=user_id,
            user_message=user_message,
            coach_response=coach_response,
            session_id=session_id
        )

        # Extract and save any new memories from user message
        memory.extract_and_save_insights(
            user_id=user_id,
            user_message=user_message,
            use_llm=False  # Using keyword matching for now
        )

        return {
            "success": True,
            "response": coach_response,
            "conversation_id": conversation_id
        }

    except Exception as e:
        print(f"❌ Error in coach endpoint: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/trade-logs")
async def get_trade_logs(limit: int = 100):
    """Get all trade logs."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        logs = kite_client.db.get_all_trade_logs(limit=limit)
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/trade-logs/open")
async def get_open_trade_logs():
    """Get only open trade logs."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        logs = kite_client.db.get_open_trade_logs()
        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/monitored-positions")
async def get_monitored_positions():
    """Get actively monitored positions with current prices."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        positions = kite_client.db.get_active_monitored_positions()
        return {
            "success": True,
            "data": positions,
            "count": len(positions)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/test/create-order")
async def create_test_order(request: Request):
    """Create a test/fake order for testing the logging flow."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        import random
        import string

        data = await request.json()

        # Generate fake order ID (TEST prefix to identify test orders)
        order_id = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}{''.join(random.choices(string.digits, k=4))}"

        # Create order data
        order_data = {
            "order_id": order_id,
            "trade_id": f"T{order_id}",
            "symbol": data.get("symbol"),
            "exchange": data.get("exchange"),
            "action": data.get("action"),
            "quantity": int(data.get("quantity")),
            "entry_price": float(data.get("entry_price")),
            "order_type": "MARKET",
            "product": data.get("product"),
            "status": "COMPLETE",
            "timestamp": datetime.now().isoformat()
        }

        # Save to database
        success = kite_client.db.save_order(order_data)

        if success:
            # Add to notification queue
            global new_order_notifications
            notification = {
                "order_id": order_id,
                "symbol": order_data["symbol"],
                "action": order_data["action"],
                "quantity": order_data["quantity"],
                "price": order_data["entry_price"],
                "timestamp": datetime.now().isoformat()
            }
            new_order_notifications.append(notification)

            print(f"✅ Test order created: {order_id}")

            return {
                "success": True,
                "order_id": order_id,
                "message": "Test order created successfully",
                "order": order_data
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to save test order"}
            )

    except Exception as e:
        print(f"❌ Error creating test order: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/stats")
async def get_stats():
    """Get database statistics for debugging."""
    if not kite_client:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Kite client not initialized"}
        )

    try:
        with kite_client.db.get_connection() as conn:
            cursor = conn.cursor()

            # Count total orders
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            total_orders = cursor.fetchone()["count"]

            # Count unlogged orders
            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE logged = 0 AND status = 'COMPLETE'")
            unlogged = cursor.fetchone()["count"]

            # Count logged orders
            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE logged = 1")
            logged = cursor.fetchone()["count"]

            # Count trade logs
            cursor.execute("SELECT COUNT(*) as count FROM trade_logs")
            trade_logs = cursor.fetchone()["count"]

            # Get sample unlogged orders
            cursor.execute("""
                SELECT order_id, symbol, action, quantity, entry_price, timestamp, status
                FROM orders
                WHERE logged = 0 AND status = 'COMPLETE'
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            sample_unlogged = [dict(row) for row in cursor.fetchall()]

            return {
                "success": True,
                "stats": {
                    "total_orders": total_orders,
                    "unlogged_orders": unlogged,
                    "logged_orders": logged,
                    "trade_logs_count": trade_logs,
                    "sample_unlogged": sample_unlogged
                }
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"🚀 Starting Kite Connect Analytics Dashboard on port {port}...")
    print(f"📊 Access dashboard at: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
