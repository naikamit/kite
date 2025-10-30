"""FastAPI application for Kite Connect Analytics Dashboard."""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from kiteconnect import KiteConnect
from kite_client import KiteClient
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="Kite Connect Analytics MVP")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Kite client
try:
    kite_client = KiteClient()
    print("✅ Kite Connect client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Kite Connect client: {e}")
    kite_client = None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard page."""
    # If no access token is set, redirect to setup page
    if not os.getenv("KITE_ACCESS_TOKEN"):
        return RedirectResponse(url="/setup")
    return templates.TemplateResponse("dashboard.html", {"request": request})


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

        # Return the token to display to user
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "success": True,
            "access_token": access_token,
            "api_key": api_key,
            "has_token": True,
            "message": "Access token generated successfully! Add it to your Render environment variables."
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"🚀 Starting Kite Connect Analytics Dashboard on port {port}...")
    print(f"📊 Access dashboard at: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
