# Kite Connect Analytics Dashboard MVP

A lightweight, real-time trading analytics dashboard for Zerodha Kite Connect API. View today's trades, current positions, and P&L with a clean, dark-themed interface.

## Features

- **Real-time Data**: Fetch today's trades and current positions from Kite Connect API
- **User Profile**: Display account information to confirm API connection
- **P&L Tracking**: View profit/loss for individual positions and overall summary
- **Dark Theme**: Easy-on-the-eyes interface inspired by modern trading platforms
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Manual Refresh**: Button to fetch latest data on demand
- **Error Handling**: Clear error messages and toast notifications

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **API**: Kite Connect (pykiteconnect)
- **Server**: Uvicorn ASGI server

## Project Structure

```
kite/
├── main.py                 # FastAPI application
├── kite_client.py          # Kite Connect API wrapper
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── templates/
│   └── dashboard.html     # Dashboard UI
└── static/
    ├── style.css          # Dark theme styling
    └── app.js             # Frontend logic
```

## Prerequisites

- Python 3.8 or higher
- Zerodha Kite Connect account
- Active Kite Connect API subscription

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd kite
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your Kite Connect credentials:

```env
KITE_API_KEY=your_api_key_here
KITE_ACCESS_TOKEN=your_access_token_here
```

### 4. Get Kite Connect API Credentials

#### Step 1: Get API Key

1. Go to [Kite Connect](https://kite.zerodha.com/)
2. Login and navigate to your developer console
3. Create a new app or use an existing one
4. Copy the **API Key**

#### Step 2: Generate Access Token

The access token needs to be generated through OAuth flow:

1. Open your browser and visit:
   ```
   https://kite.zerodha.com/connect/login?api_key=YOUR_API_KEY&v=3
   ```
   Replace `YOUR_API_KEY` with your actual API key

2. Login with your Zerodha credentials

3. After authorization, you'll be redirected to:
   ```
   https://your-redirect-url?request_token=XXXXXX&action=login&status=success
   ```

4. Copy the `request_token` from the URL

5. Use this token to generate access token using a helper script:

```python
from kiteconnect import KiteConnect

api_key = "your_api_key"
api_secret = "your_api_secret"  # Get from developer console
request_token = "request_token_from_redirect"

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]
print(f"Access Token: {access_token}")
```

6. Copy the access token to your `.env` file

**Note**: Access tokens expire daily. You'll need to regenerate them each day.

## Usage

### Start the server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Access the dashboard

Open your browser and navigate to:

```
http://localhost:8001
```

### API Endpoints

The application exposes the following REST API endpoints:

- `GET /` - Dashboard UI
- `GET /api/health` - Check API connection status
- `GET /api/profile` - Get user profile information
- `GET /api/trades` - Get today's trades
- `GET /api/positions` - Get current positions with P&L
- `GET /api/holdings` - Get holdings (long-term investments)

## Features Overview

### Dashboard Sections

1. **Header**
   - Connection status indicator
   - Refresh button for manual data updates

2. **Account Information**
   - User ID, name, and email
   - Confirms successful API connection

3. **Summary Cards**
   - Today's trade count
   - Open positions count
   - Total P&L (color-coded: green for profit, red for loss)

4. **Today's Trades Table**
   - Symbol, transaction type (BUY/SELL)
   - Quantity, price, timestamp
   - Product type (MIS, CNC, NRML)

5. **Current Positions Grid**
   - Position cards with symbol and exchange
   - Quantity, average price, last price
   - Individual P&L for each position

### UI Features

- **Loading States**: Spinners during API calls
- **Error Messages**: Clear error display for failed requests
- **Toast Notifications**: Success/error feedback for user actions
- **Empty States**: Friendly messages when no data available
- **Responsive Design**: Adapts to different screen sizes

## Development

### Project Dependencies

```txt
fastapi==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # ASGI server
kiteconnect==4.2.0        # Kite Connect API client
python-dotenv==1.0.0      # Environment variable management
jinja2==3.1.2             # Template engine
```

### Code Structure

#### `kite_client.py`

Wrapper class for Kite Connect API operations:
- `get_profile()` - Fetch user profile
- `get_todays_trades()` - Get today's trades with filtering
- `get_positions()` - Get positions with P&L calculation
- `get_holdings()` - Get long-term holdings
- `check_connection()` - Health check for API connection

#### `main.py`

FastAPI application with endpoints for:
- Serving dashboard UI
- API health checks
- Data fetching routes

#### `static/app.js`

Frontend JavaScript handling:
- API calls using Fetch API
- DOM manipulation for data display
- Toast notification system
- Loading states and error handling

#### `static/style.css`

Dark theme styling with:
- CSS custom properties for theming
- Responsive grid layouts
- Animation keyframes
- Mobile-first design

## Troubleshooting

### Common Issues

**1. "KITE_API_KEY and KITE_ACCESS_TOKEN must be set in environment"**

Solution: Make sure you've created a `.env` file with valid credentials.

**2. "Failed to connect to Kite API"**

Solutions:
- Verify your API key is correct
- Check if access token has expired (regenerate daily)
- Ensure you have active Kite Connect API subscription
- Check internet connectivity

**3. "No trades found for today"**

This is normal if you haven't placed any trades today. Try placing a test trade in Kite.

**4. Port 8001 already in use**

Solution: Change the port in `main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8002)  # Use different port
```

## Limitations (MVP Scope)

- No auto-refresh (manual refresh button only)
- No historical data beyond today
- No data persistence/storage
- No advanced analytics or charts
- Single user only (no multi-user support)
- No OAuth flow automation (manual token generation)

## Future Enhancements

Potential features for future versions:
- Auto-refresh with WebSocket support
- Historical trade analysis
- Advanced P&L calculations and reports
- Charts and visualizations
- Database integration for data persistence
- Multi-user authentication system
- Automated OAuth token refresh
- Real-time market data integration

## Security Notes

- Never commit your `.env` file with real credentials
- Keep your access tokens secure and private
- Regenerate access tokens regularly
- Use HTTPS in production environments
- Consider implementing rate limiting for API calls

## License

MIT License - Feel free to use and modify for your needs.

## Support

For issues with:
- **This application**: Open an issue in this repository
- **Kite Connect API**: Visit [Kite Connect Documentation](https://kite.trade/docs/connect/v3/)
- **Zerodha support**: Contact [Zerodha Support](https://support.zerodha.com/)

## Disclaimer

This is an educational project and not affiliated with Zerodha. Use at your own risk. Always verify trades and positions through official Zerodha platforms before making financial decisions.

## Credits

Built with Kite Connect API by Zerodha.
