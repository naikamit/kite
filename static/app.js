// Kite Connect Analytics Dashboard - Frontend Logic

// State management
let isLoading = false;
let currentVersion = null;
let updateCheckInterval = null;

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

// Show offline mode banner
function showOfflineMode(lastUpdated) {
    let banner = document.getElementById('offline-banner');

    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.className = 'offline-banner';

        const container = document.querySelector('.container');
        container.insertBefore(banner, container.firstChild);
    }

    const timeAgo = lastUpdated ? `Last updated: ${new Date(lastUpdated).toLocaleString()}` : 'Using cached data';

    banner.innerHTML = `
        <div class="offline-content">
            <span class="offline-icon">⚠️</span>
            <span class="offline-text">Offline Mode - ${timeAgo}</span>
        </div>
    `;
    banner.style.display = 'block';
}

// Hide offline mode banner
function hideOfflineMode() {
    const banner = document.getElementById('offline-banner');
    if (banner) {
        banner.style.display = 'none';
    }
}

// Check for app updates
async function checkForUpdates() {
    try {
        const response = await fetch('/api/version');
        const data = await response.json();

        if (!currentVersion) {
            // First load, store version
            currentVersion = data.version;
            return;
        }

        if (data.version !== currentVersion) {
            // New version detected!
            showUpdateNotification();
            // Stop checking once update detected
            if (updateCheckInterval) {
                clearInterval(updateCheckInterval);
            }
        }
    } catch (error) {
        console.error('Update check failed:', error);
    }
}

// Show update notification banner
function showUpdateNotification() {
    let banner = document.getElementById('update-banner');

    if (banner) {
        return; // Already showing
    }

    banner = document.createElement('div');
    banner.id = 'update-banner';
    banner.className = 'update-banner';

    banner.innerHTML = `
        <div class="update-content">
            <span class="update-icon">🔄</span>
            <span class="update-text">New version available! Reload to see latest changes.</span>
            <div class="update-actions">
                <button class="btn btn-primary" onclick="window.location.reload()">Reload Now</button>
                <button class="btn btn-secondary" onclick="dismissUpdate()">Dismiss</button>
            </div>
        </div>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(banner, container.firstChild);
}

// Dismiss update notification
function dismissUpdate() {
    const banner = document.getElementById('update-banner');
    if (banner) {
        banner.remove();
    }
}

// Start update checking (poll every 60 seconds)
function startUpdateCheck() {
    // Initial version fetch
    checkForUpdates();

    // Poll every 60 seconds
    updateCheckInterval = setInterval(checkForUpdates, 60000);
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
        const fromCache = result.from_cache || false;
        const cacheInfo = result.cache_info || null;

        countEl.textContent = positions.length;
        totalPositionsEl.textContent = formatNumber(positions.length);

        // Update total P&L
        const totalPnl = summary.total_pnl || 0;
        totalPnlEl.textContent = formatCurrency(totalPnl);
        totalPnlEl.className = `summary-value ${getPnLClass(totalPnl)}`;

        // Show offline mode indicator if using cached data
        if (fromCache && cacheInfo) {
            showOfflineMode(cacheInfo.last_updated);
        } else {
            hideOfflineMode();
        }

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

// Chart instances
let accountValueChart = null;
let cashFlowChart = null;
let dailyPnlChart = null;

// Load and render analytics charts
async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const result = await response.json();

        if (!result.success) {
            console.error('Failed to load analytics:', result.error);
            return;
        }

        const data = result.data;

        // Update max drawdown display
        const maxDrawdownEl = document.getElementById('max-drawdown');
        const drawdown = data.max_live_loss || data.max_drawdown;
        maxDrawdownEl.textContent = formatCurrency(drawdown);
        maxDrawdownEl.className = `summary-value ${getPnLClass(drawdown)}`;

        // Render charts
        renderAccountValueChart(data.dates, data.account_values);
        renderCashFlowChart(data.dates, data.cash_flow);
        renderDailyPnlChart(data.dates, data.daily_pnl);

    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// Render Account Value Line Chart
function renderAccountValueChart(dates, values) {
    const ctx = document.getElementById('account-value-chart');
    if (!ctx) return;

    // Destroy existing chart
    if (accountValueChart) {
        accountValueChart.destroy();
    }

    accountValueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Account Value',
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1f2e',
                    titleColor: '#e6e8eb',
                    bodyColor: '#e6e8eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '₹ ' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ba3af',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ba3af',
                        callback: function(value) {
                            return '₹ ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Render Cash Flow Bar Chart
function renderCashFlowChart(dates, cashFlow) {
    const ctx = document.getElementById('cash-flow-chart');
    if (!ctx) return;

    // Destroy existing chart
    if (cashFlowChart) {
        cashFlowChart.destroy();
    }

    // Separate deposits and withdrawals
    const deposits = cashFlow.map(val => val > 0 ? val : 0);
    const withdrawals = cashFlow.map(val => val < 0 ? val : 0);

    cashFlowChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Deposits',
                    data: deposits,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10b981',
                    borderWidth: 1
                },
                {
                    label: 'Withdrawals',
                    data: withdrawals,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: '#ef4444',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#e6e8eb',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1a1f2e',
                    titleColor: '#e6e8eb',
                    bodyColor: '#e6e8eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += '₹ ' + Math.abs(context.parsed.y).toLocaleString();
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: false,
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ba3af',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    stacked: false,
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ba3af',
                        callback: function(value) {
                            return '₹ ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Render Daily P&L Bar Chart
function renderDailyPnlChart(dates, pnlValues) {
    const ctx = document.getElementById('daily-pnl-chart');
    if (!ctx) return;

    // Destroy existing chart
    if (dailyPnlChart) {
        dailyPnlChart.destroy();
    }

    // Color bars based on positive/negative
    const backgroundColors = pnlValues.map(val =>
        val >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)'
    );
    const borderColors = pnlValues.map(val =>
        val >= 0 ? '#10b981' : '#ef4444'
    );

    dailyPnlChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Daily P&L',
                data: pnlValues,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1f2e',
                    titleColor: '#e6e8eb',
                    bodyColor: '#e6e8eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            const prefix = value >= 0 ? '+' : '';
                            return prefix + '₹ ' + value.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ba3af',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ba3af',
                        callback: function(value) {
                            const prefix = value >= 0 ? '+' : '';
                            return prefix + '₹ ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
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
            loadPositions(),
            loadAnalytics()
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

// Trading Log Functions

// Request browser notification permission
async function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
    return Notification.permission === 'granted';
}

// Show browser notification
function showBrowserNotification(title, body, data = {}) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: body,
            icon: '/static/icon.png',
            tag: data.order_id || 'trade-notification',
            requireInteraction: true,
            data: data
        });

        notification.onclick = function() {
            window.focus();
            if (data.order_id) {
                showLogModal(data.order_id);
            }
            notification.close();
        };
    }
}

// Poll for new order notifications
let notificationPollInterval = null;
async function pollNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const result = await response.json();

        if (result.success && result.notifications.length > 0) {
            // Show browser notifications
            result.notifications.forEach(notif => {
                showBrowserNotification(
                    `${notif.symbol} ${notif.action} executed`,
                    `₹${notif.price} × ${notif.quantity} shares`,
                    notif
                );
            });

            // Update unlogged orders banner
            loadUnloggedOrdersBanner();
        }
    } catch (error) {
        console.error('Failed to poll notifications:', error);
    }
}

// Start notification polling
function startNotificationPolling() {
    // Poll every 10 seconds
    notificationPollInterval = setInterval(pollNotifications, 10000);
}

// Load and show unlogged orders banner
async function loadUnloggedOrdersBanner() {
    try {
        const response = await fetch('/api/unlogged-orders');
        const result = await response.json();

        if (result.success && result.count > 0) {
            showUnloggedBanner(result.data);
        } else {
            hideUnloggedBanner();
        }
    } catch (error) {
        console.error('Failed to load unlogged orders:', error);
    }
}

// Show unlogged orders banner
function showUnloggedBanner(orders) {
    let banner = document.getElementById('unlogged-banner');

    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'unlogged-banner';
        banner.className = 'unlogged-banner';
        const container = document.querySelector('.container');
        container.insertBefore(banner, container.firstChild);
    }

    banner.innerHTML = `
        <div class="unlogged-content">
            <span class="unlogged-icon">📝</span>
            <span class="unlogged-text">You have ${orders.length} trade(s) waiting to be logged!</span>
            <button class="btn btn-primary" onclick="showLogModal('${orders[0].order_id}')">Log Now</button>
        </div>
    `;
    banner.style.display = 'flex';
}

// Hide unlogged orders banner
function hideUnloggedBanner() {
    const banner = document.getElementById('unlogged-banner');
    if (banner) {
        banner.style.display = 'none';
    }
}

// Setup patterns for trade logging (grouped by direction)
const SETUP_PATTERNS = {
    bullish: [
        'Double Bottom',
        'Three White Soldiers',
        'Bulls Counter Attack',
        'Rounding Bottom',
        'Genuine BO',
        'Gap Up',
        'Mother Candle (Bullish Reversal)',
        '3rd Wave Setup (Bullish)',
        'Ending Diagonal Setup (Bullish)',
        'Triangle Breakout Setup (Bullish)'
    ],
    bearish: [
        'Double Top',
        'Three Black Crows',
        'Bears Counter Attack',
        'Rounding Top',
        'Genuine BD',
        'Gap Down',
        'Mother Candle (Bearish Reversal)',
        '3rd Wave Setup (Bearish)',
        'Ending Diagonal Setup (Bearish)',
        'Triangle Breakout Setup (Bearish)'
    ],
    neutral: [
        'Sandwich Pattern',
        'Fake BO',
        'Fake BD',
        'Mother Candle (Continuation)'
    ]
};

// Trade log wizard state
let wizardState = {
    orderId: null,
    order: null,
    currentStep: 1,
    data: {
        setup: null,
        target_price: null,
        stop_loss: null,
        emotions: [],  // Changed to array for multi-select
        notes: null
    }
};

// Show log entry modal (wizard)
async function showLogModal(orderId) {
    try {
        // Fetch order details
        const response = await fetch('/api/unlogged-orders');
        const result = await response.json();

        if (!result.success) {
            showToast('Failed to load order details', 'error');
            return;
        }

        const order = result.data.find(o => o.order_id === orderId);
        if (!order) {
            showToast('Order not found', 'error');
            return;
        }

        // Initialize wizard state
        wizardState = {
            orderId: orderId,
            order: order,
            currentStep: 1,
            data: {
                setup: null,
                target_price: null,
                stop_loss: null,
                emotions: [],
                notes: null
            }
        };

        // Create modal
        const modal = document.createElement('div');
        modal.id = 'log-modal';
        modal.className = 'modal';
        document.body.appendChild(modal);

        // Render first step
        renderWizardStep();

        // Show modal with animation
        setTimeout(() => modal.classList.add('show'), 10);

        // Clear notification for this order
        await fetch('/api/notifications/clear', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({order_id: orderId})
        });

    } catch (error) {
        console.error('Failed to show log modal:', error);
        showToast('Failed to show log modal', 'error');
    }
}

// Render current wizard step
function renderWizardStep() {
    const modal = document.getElementById('log-modal');
    if (!modal) return;

    const { currentStep, order } = wizardState;
    const totalSteps = 5;  // Added step 5 for coach chat

    let stepContent = '';

    // Step 1: Order Info
    if (currentStep === 1) {
        stepContent = `
            <div class="wizard-step">
                <h4>Order Details</h4>
                <div class="order-info-card">
                    <div class="info-row">
                        <span class="info-label">Symbol</span>
                        <span class="info-value"><strong>${order.symbol}</strong></span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Action</span>
                        <span class="info-value trade-${order.action.toLowerCase()}">${order.action}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Quantity</span>
                        <span class="info-value">${order.quantity}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Entry Price</span>
                        <span class="info-value">₹${order.entry_price}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Time</span>
                        <span class="info-value">${new Date(order.timestamp).toLocaleString()}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Step 2: Setup Selection
    if (currentStep === 2) {
        const bullishButtons = SETUP_PATTERNS.bullish.map(s =>
            `<button type="button" class="setup-btn setup-bullish${wizardState.data.setup === s ? ' selected' : ''}"
                     onclick="selectSetup('${s}')">${s}</button>`
        ).join('');

        const bearishButtons = SETUP_PATTERNS.bearish.map(s =>
            `<button type="button" class="setup-btn setup-bearish${wizardState.data.setup === s ? ' selected' : ''}"
                     onclick="selectSetup('${s}')">${s}</button>`
        ).join('');

        const neutralButtons = SETUP_PATTERNS.neutral.map(s =>
            `<button type="button" class="setup-btn setup-neutral${wizardState.data.setup === s ? ' selected' : ''}"
                     onclick="selectSetup('${s}')">${s}</button>`
        ).join('');

        stepContent = `
            <div class="wizard-step wizard-step-scrollable">
                <h4>📊 What's your setup?</h4>

                <div class="setup-group">
                    <h5 class="setup-group-title bullish-title">📈 Bullish Setups</h5>
                    <div class="setup-buttons">
                        ${bullishButtons}
                    </div>
                </div>

                <div class="setup-group">
                    <h5 class="setup-group-title bearish-title">📉 Bearish Setups</h5>
                    <div class="setup-buttons">
                        ${bearishButtons}
                    </div>
                </div>

                <div class="setup-group">
                    <h5 class="setup-group-title neutral-title">↔️ Neutral/Other Setups</h5>
                    <div class="setup-buttons">
                        ${neutralButtons}
                    </div>
                </div>

                <div class="setup-group">
                    <h5 class="setup-group-title">✏️ Custom Setup</h5>
                    <input type="text" id="custom-setup-input" class="custom-setup-input"
                           placeholder="Type your own setup name..."
                           value="${wizardState.data.setup && !SETUP_PATTERNS.bullish.includes(wizardState.data.setup) && !SETUP_PATTERNS.bearish.includes(wizardState.data.setup) && !SETUP_PATTERNS.neutral.includes(wizardState.data.setup) ? wizardState.data.setup : ''}"
                           oninput="handleCustomSetup(this)">
                </div>
            </div>
        `;
    }

    // Step 3: Target & Stop Loss
    if (currentStep === 3) {
        const entryPrice = parseFloat(order.entry_price);
        const isBuy = order.action === 'BUY';

        // Smart defaults: 2% for target and SL
        const defaultTarget = wizardState.data.target_price || (isBuy
            ? (entryPrice * 1.02).toFixed(2)
            : (entryPrice * 0.98).toFixed(2));
        const defaultSL = wizardState.data.stop_loss || (isBuy
            ? (entryPrice * 0.98).toFixed(2)
            : (entryPrice * 1.02).toFixed(2));

        // Calculate range for sliders (±10% from entry)
        const targetMin = (entryPrice * 0.90).toFixed(2);
        const targetMax = (entryPrice * 1.10).toFixed(2);
        const slMin = (entryPrice * 0.90).toFixed(2);
        const slMax = (entryPrice * 1.10).toFixed(2);

        stepContent = `
            <div class="wizard-step">
                <h4>🎯 Set your levels</h4>
                <div class="entry-price-reminder">
                    Entry: ₹${entryPrice}
                </div>

                <div class="form-group">
                    <label>Target Price *</label>
                    <input type="number" id="target-input" class="price-number-input-large"
                           step="0.05" value="${defaultTarget}"
                           oninput="syncInputToSlider('target', this.value)" required>
                    <input type="range" id="target-slider" class="price-slider-full"
                           min="${targetMin}" max="${targetMax}" step="0.05"
                           value="${defaultTarget}"
                           oninput="syncSliderToInput('target', this.value)">
                    <small class="input-hint">Suggested: ₹${isBuy ? (entryPrice * 1.02).toFixed(2) : (entryPrice * 0.98).toFixed(2)} (2% ${isBuy ? 'above' : 'below'})</small>
                </div>

                <div class="form-group">
                    <label>Stop Loss *</label>
                    <input type="number" id="sl-input" class="price-number-input-large"
                           step="0.05" value="${defaultSL}"
                           oninput="syncInputToSlider('sl', this.value)" required>
                    <input type="range" id="sl-slider" class="price-slider-full"
                           min="${slMin}" max="${slMax}" step="0.05"
                           value="${defaultSL}"
                           oninput="syncSliderToInput('sl', this.value)">
                    <small class="input-hint">Suggested: ₹${isBuy ? (entryPrice * 0.98).toFixed(2) : (entryPrice * 1.02).toFixed(2)} (2% ${isBuy ? 'below' : 'above'})</small>
                </div>

                <div class="risk-reward-display" id="rr-display">
                    Risk:Reward = 1:1
                </div>
            </div>
        `;
    }

    // Step 4: Emotion & Notes
    if (currentStep === 4) {
        const emotions = [
            { id: 'disciplined', icon: '📊', label: 'Disciplined' },
            { id: 'calm', icon: '😌', label: 'Calm' },
            { id: 'fomo', icon: '😤', label: 'FOMO' },
            { id: 'greed', icon: '🤑', label: 'Greed' },
            { id: 'fear', icon: '😨', label: 'Fear' },
            { id: 'anxiety', icon: '😰', label: 'Anxiety' },
            { id: 'uncertain', icon: '🤔', label: 'Uncertain' },
            { id: 'revenge', icon: '😡', label: 'Revenge' }
        ];

        const emotionButtons = emotions.map(e => {
            const isSelected = wizardState.data.emotions.includes(e.id);
            return `
                <button type="button" class="emotion-btn-multi${isSelected ? ' selected' : ''}"
                        data-emotion="${e.id}" onclick="toggleEmotion(this)">
                    <span class="emotion-icon">${e.icon}</span>
                    <span class="emotion-label">${e.label}</span>
                </button>
            `;
        }).join('');

        stepContent = `
            <div class="wizard-step">
                <h4>😊 How are you feeling?</h4>
                <p class="emotion-hint">Select all that apply - we're complex humans!</p>
                <div class="emotion-grid">
                    ${emotionButtons}
                </div>
                <div class="form-group">
                    <label>💭 Trade Notes (optional)</label>
                    <textarea id="notes-input" rows="4" placeholder="Why did you take this trade? Any observations?">${wizardState.data.notes || ''}</textarea>
                </div>
            </div>
        `;
    }

    // Step 5: Chat with Coach
    if (currentStep === 5) {
        stepContent = `
            <div class="wizard-step wizard-step-scrollable">
                <h4>🧠 Chat with Your Coach</h4>
                <div id="coach-chat-container" class="coach-chat-container">
                    <div class="coach-initial-message" id="coach-initial-message">
                        <div class="coach-message-header">
                            <div class="coach-avatar">🎯</div>
                            <div class="coach-name">Trading Coach</div>
                        </div>
                        <div class="coach-message-content" id="coach-initial-content">
                            <div class="loading-animation">
                                <span class="dot"></span>
                                <span class="dot"></span>
                                <span class="dot"></span>
                            </div>
                            <p class="loading-text">Analyzing your trade...</p>
                        </div>
                    </div>
                    <div id="coach-chat-messages"></div>
                </div>
                <div class="coach-input-container">
                    <textarea id="coach-input" rows="2" placeholder="Ask the coach anything..." disabled></textarea>
                    <button class="btn btn-primary" onclick="sendCoachMessage()" disabled id="send-coach-btn">Send</button>
                </div>
            </div>
        `;
    }

    modal.innerHTML = `
        <div class="modal-content wizard-modal">
            <div class="modal-header">
                <div>
                    <h3>📝 Log Your Trade</h3>
                    <div class="wizard-progress">Step ${currentStep} of ${totalSteps}</div>
                </div>
                <button class="modal-close" onclick="closeLogModal()">×</button>
            </div>
            <div class="modal-body">
                ${stepContent}
            </div>
            <div class="wizard-nav">
                ${currentStep > 1 && currentStep < 5 ? '<button class="btn btn-secondary" onclick="wizardPrevious()">← Back</button>' : (currentStep === 5 ? '' : '<button class="btn btn-secondary" onclick="closeLogModal()">Skip</button>')}
                ${currentStep < 4
                    ? '<button class="btn btn-primary" onclick="wizardNext()">Next →</button>'
                    : (currentStep === 4 ? '<button class="btn btn-success" onclick="wizardNext()">Save & Continue →</button>' : '<button class="btn btn-primary" onclick="closeLogModal()">Done</button>')}
            </div>
        </div>
    `;

    // Initialize R:R calculation if on step 3
    if (currentStep === 3) {
        setTimeout(() => updateRiskReward(), 100);
    }

    // Initialize coach chat if on step 5
    if (currentStep === 5) {
        setTimeout(() => initializeCoachChat(), 100);
    }
}

// Select setup pattern
function selectSetup(setupName) {
    // Deselect all setup buttons
    document.querySelectorAll('.setup-btn').forEach(btn => btn.classList.remove('selected'));

    // Select this button
    const button = event.target.closest('.setup-btn');
    if (button) {
        button.classList.add('selected');
    }

    // Clear custom input
    const customInput = document.getElementById('custom-setup-input');
    if (customInput) {
        customInput.value = '';
    }

    wizardState.data.setup = setupName;
}

// Handle custom setup input
function handleCustomSetup(input) {
    const value = input.value.trim();

    // Deselect all preset buttons
    document.querySelectorAll('.setup-btn').forEach(btn => btn.classList.remove('selected'));

    wizardState.data.setup = value || null;
}

// Sync slider value to number input
function syncSliderToInput(field, value) {
    const input = document.getElementById(`${field}-input`);
    if (input) {
        input.value = value;
        updateRiskReward();
    }
}

// Sync number input to slider
function syncInputToSlider(field, value) {
    const slider = document.getElementById(`${field}-slider`);
    if (slider) {
        slider.value = value;
        updateRiskReward();
    }
}

// Update Risk:Reward ratio
function updateRiskReward() {
    const targetInput = document.getElementById('target-input');
    const slInput = document.getElementById('sl-input');
    const rrDisplay = document.getElementById('rr-display');

    if (!targetInput || !slInput || !rrDisplay) return;

    const entryPrice = parseFloat(wizardState.order.entry_price);
    const targetPrice = parseFloat(targetInput.value);
    const stopLoss = parseFloat(slInput.value);
    const isBuy = wizardState.order.action === 'BUY';

    if (isNaN(targetPrice) || isNaN(stopLoss)) {
        rrDisplay.textContent = 'Risk:Reward = -';
        return;
    }

    const reward = isBuy ? (targetPrice - entryPrice) : (entryPrice - targetPrice);
    const risk = isBuy ? (entryPrice - stopLoss) : (stopLoss - entryPrice);

    if (risk <= 0 || reward <= 0) {
        rrDisplay.innerHTML = '<span style="color: var(--error-red);">⚠️ Check your levels</span>';
        return;
    }

    const ratio = (reward / risk).toFixed(2);
    const color = ratio > 3 ? 'var(--success-green)' : ratio >= 2 ? 'var(--warning-orange)' : 'var(--error-red)';
    rrDisplay.innerHTML = `<span style="color: ${color};">Risk:Reward = 1:${ratio}</span>`;
}

// Toggle emotion (multi-select)
function toggleEmotion(button) {
    const emotion = button.dataset.emotion;
    const isSelected = button.classList.contains('selected');

    if (isSelected) {
        // Deselect
        button.classList.remove('selected');
        wizardState.data.emotions = wizardState.data.emotions.filter(e => e !== emotion);
    } else {
        // Select
        button.classList.add('selected');
        wizardState.data.emotions.push(emotion);
    }
}

// Wizard navigation: Next
async function wizardNext() {
    const { currentStep } = wizardState;

    // Validate current step before proceeding
    if (currentStep === 2) {
        if (!wizardState.data.setup) {
            showToast('Please select a setup or enter a custom one', 'error');
            return;
        }
    }

    if (currentStep === 3) {
        const targetInput = document.getElementById('target-input');
        const slInput = document.getElementById('sl-input');

        if (!targetInput.value || !slInput.value) {
            showToast('Please enter target and stop loss', 'error');
            return;
        }

        wizardState.data.target_price = parseFloat(targetInput.value);
        wizardState.data.stop_loss = parseFloat(slInput.value);

        // Validate levels
        const entryPrice = parseFloat(wizardState.order.entry_price);
        const isBuy = wizardState.order.action === 'BUY';
        const reward = isBuy ? (wizardState.data.target_price - entryPrice) : (entryPrice - wizardState.data.target_price);
        const risk = isBuy ? (entryPrice - wizardState.data.stop_loss) : (wizardState.data.stop_loss - entryPrice);

        if (risk <= 0 || reward <= 0) {
            showToast('Invalid target/SL levels. Please check your entry.', 'error');
            return;
        }
    }

    // Step 4 → 5: Save trade log before moving to coach chat
    if (currentStep === 4) {
        // Validate emotions
        if (wizardState.data.emotions.length === 0) {
            showToast('Please select at least one emotion', 'error');
            return;
        }

        // Collect notes
        const notesInput = document.getElementById('notes-input');
        wizardState.data.notes = notesInput?.value.trim() || null;

        // Save trade log
        const success = await saveTradeLogToAPI();
        if (!success) {
            return; // Don't proceed if save failed
        }
    }

    // Move to next step
    wizardState.currentStep++;
    renderWizardStep();
}

// Wizard navigation: Previous
function wizardPrevious() {
    // Save current step data if on step 4
    if (wizardState.currentStep === 4) {
        const notesInput = document.getElementById('notes-input');
        if (notesInput) {
            wizardState.data.notes = notesInput.value.trim() || null;
        }
    }

    wizardState.currentStep--;
    renderWizardStep();
}

// Save trade log to API (extracted for step 4 → 5 transition)
async function saveTradeLogToAPI() {
    const logData = {
        order_id: wizardState.orderId,
        target_price: wizardState.data.target_price,
        stop_loss: wizardState.data.stop_loss,
        emotion: wizardState.data.emotions.join(', ') || null,
        strategy: wizardState.data.setup,
        notes: wizardState.data.notes
    };

    try {
        const response = await fetch('/api/trade-log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logData)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Trade logged successfully!', 'success');
            wizardState.logId = result.log_id;  // Store log ID for coach context
            loadUnloggedOrdersBanner();
            loadMonitoredPositions();
            return true;
        } else {
            showToast(result.error || 'Failed to save log', 'error');
            return false;
        }
    } catch (error) {
        console.error('Failed to submit trade log:', error);
        showToast('Failed to submit trade log', 'error');
        return false;
    }
}

// Initialize coach chat (called when step 5 is shown)
async function initializeCoachChat() {
    const order = wizardState.order;

    // Build trade context for coach
    const tradeContext = `
Trade: ${order.symbol} ${order.action}
Entry: ₹${order.entry_price}, Target: ₹${wizardState.data.target_price}, SL: ₹${wizardState.data.stop_loss}
Quantity: ${order.quantity}
Setup: ${wizardState.data.setup}
Emotions: ${wizardState.data.emotions.join(', ')}
Notes: ${wizardState.data.notes || 'None'}
`.trim();

    try {
        const response = await fetch('/api/coach', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: "I just logged a trade. What do you think about it?",
                trade_context: tradeContext,
                user_id: "default_user"
            })
        });

        const result = await response.json();

        const contentDiv = document.getElementById('coach-initial-content');
        if (result.success) {
            contentDiv.innerHTML = `<p>${result.response}</p>`;

            // Enable chat input
            document.getElementById('coach-input').disabled = false;
            document.getElementById('send-coach-btn').disabled = false;
        } else {
            contentDiv.innerHTML = `<p class="error-message">❌ ${result.error || 'Failed to get coaching feedback'}</p>`;
        }
    } catch (error) {
        console.error('Failed to get coach feedback:', error);
        const contentDiv = document.getElementById('coach-initial-content');
        contentDiv.innerHTML = `<p class="error-message">❌ Failed to connect to coach. ${error.message}</p>`;
    }
}

// Send additional message to coach
async function sendCoachMessage() {
    const input = document.getElementById('coach-input');
    const message = input.value.trim();

    if (!message) return;

    // Disable input while processing
    input.disabled = true;
    document.getElementById('send-coach-btn').disabled = true;

    // Add user message to chat
    const chatMessages = document.getElementById('coach-chat-messages');
    chatMessages.innerHTML += `
        <div class="user-message">
            <div class="user-message-content">${message}</div>
        </div>
    `;

    // Clear input
    input.value = '';

    // Add loading indicator
    chatMessages.innerHTML += `
        <div class="coach-message" id="coach-loading">
            <div class="coach-message-header">
                <div class="coach-avatar">🎯</div>
                <div class="coach-name">Trading Coach</div>
            </div>
            <div class="coach-message-content">
                <div class="loading-animation">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        </div>
    `;

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/coach', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: message,
                user_id: "default_user"
            })
        });

        const result = await response.json();

        // Remove loading indicator
        document.getElementById('coach-loading')?.remove();

        if (result.success) {
            chatMessages.innerHTML += `
                <div class="coach-message">
                    <div class="coach-message-header">
                        <div class="coach-avatar">🎯</div>
                        <div class="coach-name">Trading Coach</div>
                    </div>
                    <div class="coach-message-content">
                        <p>${result.response}</p>
                    </div>
                </div>
            `;
        } else {
            chatMessages.innerHTML += `
                <div class="coach-message">
                    <div class="coach-message-content error-message">
                        ❌ ${result.error || 'Failed to get response'}
                    </div>
                </div>
            `;
        }

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error('Failed to send message to coach:', error);
        document.getElementById('coach-loading')?.remove();

        chatMessages.innerHTML += `
            <div class="coach-message">
                <div class="coach-message-content error-message">
                    ❌ Failed to connect: ${error.message}
                </div>
            </div>
        `;
    } finally {
        // Re-enable input
        input.disabled = false;
        document.getElementById('send-coach-btn').disabled = false;
        input.focus();
    }
}

// Close log modal
function closeLogModal() {
    const modal = document.getElementById('log-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
}

// Load and display monitored positions
async function loadMonitoredPositions() {
    try {
        const response = await fetch('/api/monitored-positions');
        const result = await response.json();

        if (result.success && result.count > 0) {
            showMonitoredPositionsWidget(result.data);
        }
    } catch (error) {
        console.error('Failed to load monitored positions:', error);
    }
}

// Show monitored positions widget
function showMonitoredPositionsWidget(positions) {
    let widget = document.getElementById('monitored-positions-widget');

    if (!widget) {
        widget = document.createElement('div');
        widget.id = 'monitored-positions-widget';
        widget.className = 'monitored-widget';

        const container = document.querySelector('.container');
        const chartsSection = document.querySelector('.charts-section');
        if (chartsSection) {
            container.insertBefore(widget, chartsSection);
        } else {
            container.appendChild(widget);
        }
    }

    let html = `
        <h3>🔄 Monitored Positions (${positions.length})</h3>
        <div class="monitored-grid">
    `;

    positions.forEach(pos => {
        const pnl = pos.unrealized_pnl || 0;
        const pnlClass = getPnLClass(pnl);

        html += `
            <div class="monitored-card">
                <div class="monitored-header">
                    <strong>${pos.symbol}</strong>
                    <span class="${pnlClass}">${formatCurrency(pnl)}</span>
                </div>
                <div class="monitored-details">
                    <div>Entry: ₹${pos.entry_price}</div>
                    <div>Current: ₹${pos.current_price || pos.entry_price}</div>
                    <div>Target: ₹${pos.target_price}</div>
                    <div>SL: ₹${pos.stop_loss}</div>
                </div>
            </div>
        `;
    });

    html += `</div>`;
    widget.innerHTML = html;
    widget.style.display = 'block';
}

// Sync all historical orders
async function syncHistoricalOrders() {
    const syncBtn = document.getElementById('sync-orders-btn');
    syncBtn.disabled = true;
    syncBtn.innerHTML = '<span class="btn-icon">⏳</span> Syncing...';

    try {
        const response = await fetch('/api/sync-orders');
        const result = await response.json();

        if (result.success) {
            showToast(`Synced ${result.new_orders} new orders from history!`, 'success');
            // Reload unlogged orders banner to show new orders
            await loadUnloggedOrdersBanner();
        } else {
            showToast(`Sync failed: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to sync orders:', error);
        showToast('Failed to sync historical orders', 'error');
    } finally {
        syncBtn.disabled = false;
        syncBtn.innerHTML = '<span class="btn-icon">⬇</span> Sync History';
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing Kite Connect Analytics Dashboard...');

    // Setup refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', refreshDashboard);

    // Setup sync orders button
    const syncBtn = document.getElementById('sync-orders-btn');
    syncBtn.addEventListener('click', syncHistoricalOrders);

    // Request notification permission
    await requestNotificationPermission();

    // Start update checking
    startUpdateCheck();

    // Start notification polling
    startNotificationPolling();

    // Initial load
    await refreshDashboard();

    // Load trading log widgets
    loadUnloggedOrdersBanner();
    loadMonitoredPositions();

    console.log('✅ Dashboard initialized');
});

// ============================================================================
// PWA FUNCTIONALITY
// ============================================================================

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker
            .register('/static/service-worker.js')
            .then((registration) => {
                console.log('✅ ServiceWorker registered:', registration.scope);

                // Check for updates periodically
                setInterval(() => {
                    registration.update();
                }, 60000); // Check every minute
            })
            .catch((error) => {
                console.error('❌ ServiceWorker registration failed:', error);
            });
    });
}

// PWA Install Prompt
let deferredPrompt;
const installButton = document.createElement('button');
installButton.id = 'pwa-install-btn';
installButton.className = 'btn btn-primary pwa-install-btn';
installButton.style.display = 'none';
installButton.innerHTML = `
    <span class="btn-icon">📱</span>
    Install App
`;

// Add install button to header
window.addEventListener('DOMContentLoaded', () => {
    const headerActions = document.querySelector('.header-actions');
    if (headerActions) {
        headerActions.insertBefore(installButton, headerActions.firstChild);
    }
});

// Listen for beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('💡 PWA install prompt available');

    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();

    // Store the event for later use
    deferredPrompt = e;

    // Show install button
    installButton.style.display = 'inline-flex';
});

// Handle install button click
installButton.addEventListener('click', async () => {
    if (!deferredPrompt) {
        return;
    }

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user's response
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
        console.log('✅ User accepted PWA install');
        showToast('App installed! Check your home screen.', 'success');
    } else {
        console.log('❌ User dismissed PWA install');
    }

    // Clear the deferredPrompt
    deferredPrompt = null;

    // Hide the install button
    installButton.style.display = 'none';
});

// Listen for app installation
window.addEventListener('appinstalled', (e) => {
    console.log('✅ PWA installed successfully');
    showToast('App installed successfully!', 'success');

    // Hide install button
    installButton.style.display = 'none';

    // Clear the deferredPrompt
    deferredPrompt = null;
});

// Check if already running as PWA
function isPWA() {
    return (
        window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
    );
}

// Show welcome message if running as PWA
if (isPWA()) {
    console.log('🚀 Running as PWA');

    // Add PWA-specific styles or features
    document.body.classList.add('pwa-mode');
}

// Online/Offline status
window.addEventListener('online', () => {
    console.log('🌐 Back online');
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    console.log('📴 Gone offline');
    showToast('You are offline. Some features may be limited.', 'warning');
});
