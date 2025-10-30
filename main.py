"""FastAPI application for Kite Connect Analytics Dashboard."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
    return templates.TemplateResponse("dashboard.html", {"request": request})


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


if __name__ == "__main__":
    print("🚀 Starting Kite Connect Analytics Dashboard on port 8001...")
    print("📊 Access dashboard at: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
