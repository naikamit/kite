// Kite Connect Analytics Dashboard - Frontend Logic

// State management
let isLoading = false;

// Toast notification system
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    toast.innerHTML = `
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Format currency
function formatCurrency(value) {
    if (value === null || value === undefined) return '₹ 0.00';
    return `₹ ${parseFloat(value).toFixed(2)}`;
}

// Format number
function formatNumber(value) {
    if (value === null || value === undefined) return '0';
    return value.toLocaleString();
}

// Format datetime
function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Get P&L class based on value
function getPnLClass(value) {
    if (value > 0) return 'pnl-positive';
    if (value < 0) return 'pnl-negative';
    return 'pnl-neutral';
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        const statusIndicator = document.getElementById('connection-status');
        const statusText = statusIndicator.querySelector('.status-text');

        if (data.kite_connected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = `Connected (${data.user_id})`;
            return true;
        } else {
            statusIndicator.className = 'status-indicator error';
            statusText.textContent = 'Connection Error';
            showToast('Failed to connect to Kite API', 'error');
            return false;
        }
    } catch (error) {
        console.error('Health check failed:', error);
        const statusIndicator = document.getElementById('connection-status');
        statusIndicator.className = 'status-indicator error';
        statusIndicator.querySelector('.status-text').textContent = 'Offline';
        return false;
    }
}

// Load user profile
async function loadProfile() {
    try {
        const response = await fetch('/api/profile');
        const result = await response.json();

        if (result.success && result.data) {
            const profile = result.data;
            document.getElementById('user-id').textContent = profile.user_id || '-';
            document.getElementById('user-name').textContent = profile.user_name || '-';
            document.getElementById('user-email').textContent = profile.email || '-';
            document.getElementById('profile-card').style.display = 'block';
        }
    } catch (error) {
        console.error('Failed to load profile:', error);
    }
}

// Load today's trades
async function loadTrades() {
    const loadingEl = document.getElementById('trades-loading');
    const errorEl = document.getElementById('trades-error');
    const emptyEl = document.getElementById('trades-empty');
    const tableEl = document.getElementById('trades-table-container');
    const tbodyEl = document.getElementById('trades-tbody');
    const countEl = document.getElementById('trades-count');
    const totalTradesEl = document.getElementById('total-trades');

    // Show loading state
    loadingEl.style.display = 'flex';
    errorEl.style.display = 'none';
    emptyEl.style.display = 'none';
    tableEl.style.display = 'none';

    try {
        const response = await fetch('/api/trades');
        const result = await response.json();

        loadingEl.style.display = 'none';

        if (!result.success) {
            errorEl.textContent = result.error || 'Failed to load trades';
            errorEl.style.display = 'block';
            return;
        }

        const trades = result.data || [];
        countEl.textContent = trades.length;
        totalTradesEl.textContent = formatNumber(trades.length);

        if (trades.length === 0) {
            emptyEl.style.display = 'block';
            return;
        }

        // Populate table
        tbodyEl.innerHTML = '';
        trades.forEach(trade => {
            const row = document.createElement('tr');
            const typeClass = trade.transaction_type === 'BUY' ? 'trade-buy' : 'trade-sell';

            row.innerHTML = `
                <td><strong>${trade.tradingsymbol}</strong></td>
                <td class="${typeClass}">${trade.transaction_type}</td>
                <td>${formatNumber(trade.quantity)}</td>
                <td>${formatCurrency(trade.price)}</td>
                <td>${formatTime(trade.timestamp)}</td>
                <td><span style="color: var(--text-muted); font-size: 12px;">${trade.product}</span></td>
            `;

            tbodyEl.appendChild(row);
        });

        tableEl.style.display = 'block';

    } catch (error) {
        console.error('Failed to load trades:', error);
        loadingEl.style.display = 'none';
        errorEl.textContent = 'Network error: Failed to fetch trades';
        errorEl.style.display = 'block';
    }
}

// Load current positions
async function loadPositions() {
    const loadingEl = document.getElementById('positions-loading');
    const errorEl = document.getElementById('positions-error');
    const emptyEl = document.getElementById('positions-empty');
    const gridEl = document.getElementById('positions-grid');
    const countEl = document.getElementById('positions-count');
    const totalPositionsEl = document.getElementById('total-positions');
    const totalPnlEl = document.getElementById('total-pnl');

    // Show loading state
    loadingEl.style.display = 'flex';
    errorEl.style.display = 'none';
    emptyEl.style.display = 'none';
    gridEl.style.display = 'none';

    try {
        const response = await fetch('/api/positions');
        const result = await response.json();

        loadingEl.style.display = 'none';

        if (!result.success) {
            errorEl.textContent = result.error || 'Failed to load positions';
            errorEl.style.display = 'block';
            return;
        }

        const positions = result.data || [];
        const summary = result.summary || {};

        countEl.textContent = positions.length;
        totalPositionsEl.textContent = formatNumber(positions.length);

        // Update total P&L
        const totalPnl = summary.total_pnl || 0;
        totalPnlEl.textContent = formatCurrency(totalPnl);
        totalPnlEl.className = `summary-value ${getPnLClass(totalPnl)}`;

        if (positions.length === 0) {
            emptyEl.style.display = 'block';
            return;
        }

        // Populate positions grid
        gridEl.innerHTML = '';
        positions.forEach(position => {
            const posCard = document.createElement('div');
            posCard.className = 'position-card';

            const pnl = position.pnl || 0;
            const pnlClass = getPnLClass(pnl);

            posCard.innerHTML = `
                <div class="position-header">
                    <div class="position-symbol">${position.tradingsymbol}</div>
                    <div class="position-exchange">${position.exchange}</div>
                </div>
                <div class="position-details">
                    <div class="position-detail">
                        <div class="position-detail-label">Quantity</div>
                        <div class="position-detail-value">${formatNumber(position.quantity)}</div>
                    </div>
                    <div class="position-detail">
                        <div class="position-detail-label">Avg Price</div>
                        <div class="position-detail-value">${formatCurrency(position.average_price)}</div>
                    </div>
                    <div class="position-detail">
                        <div class="position-detail-label">Last Price</div>
                        <div class="position-detail-value">${formatCurrency(position.last_price)}</div>
                    </div>
                    <div class="position-detail">
                        <div class="position-detail-label">Product</div>
                        <div class="position-detail-value" style="font-size: 12px;">${position.product}</div>
                    </div>
                </div>
                <div class="position-pnl">
                    <div class="position-pnl-label">P&L</div>
                    <div class="position-pnl-value ${pnlClass}">${formatCurrency(pnl)}</div>
                </div>
            `;

            gridEl.appendChild(posCard);
        });

        gridEl.style.display = 'grid';

    } catch (error) {
        console.error('Failed to load positions:', error);
        loadingEl.style.display = 'none';
        errorEl.textContent = 'Network error: Failed to fetch positions';
        errorEl.style.display = 'block';
    }
}

// Refresh all data
async function refreshDashboard() {
    if (isLoading) return;

    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.disabled = true;
    isLoading = true;

    try {
        const isHealthy = await checkHealth();

        if (!isHealthy) {
            showToast('Cannot refresh: API connection failed', 'error');
            return;
        }

        // Load all data in parallel
        await Promise.all([
            loadProfile(),
            loadTrades(),
            loadPositions()
        ]);

        showToast('Dashboard refreshed successfully', 'success');
    } catch (error) {
        console.error('Refresh failed:', error);
        showToast('Failed to refresh dashboard', 'error');
    } finally {
        refreshBtn.disabled = false;
        isLoading = false;
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing Kite Connect Analytics Dashboard...');

    // Setup refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', refreshDashboard);

    // Initial load
    await refreshDashboard();

    console.log('✅ Dashboard initialized');
});
