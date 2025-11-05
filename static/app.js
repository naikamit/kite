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
    const totalSteps = 4;

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
                    <div class="slider-input-group">
                        <input type="range" id="target-slider" class="price-slider"
                               min="${targetMin}" max="${targetMax}" step="0.05"
                               value="${defaultTarget}"
                               oninput="syncSliderToInput('target', this.value)">
                        <input type="number" id="target-input" class="price-number-input"
                               step="0.05" value="${defaultTarget}"
                               oninput="syncInputToSlider('target', this.value)" required>
                    </div>
                    <small class="input-hint">Drag slider or type precise value • Suggested: ₹${isBuy ? (entryPrice * 1.02).toFixed(2) : (entryPrice * 0.98).toFixed(2)} (2% ${isBuy ? 'above' : 'below'})</small>
                </div>

                <div class="form-group">
                    <label>Stop Loss *</label>
                    <div class="slider-input-group">
                        <input type="range" id="sl-slider" class="price-slider"
                               min="${slMin}" max="${slMax}" step="0.05"
                               value="${defaultSL}"
                               oninput="syncSliderToInput('sl', this.value)">
                        <input type="number" id="sl-input" class="price-number-input"
                               step="0.05" value="${defaultSL}"
                               oninput="syncInputToSlider('sl', this.value)" required>
                    </div>
                    <small class="input-hint">Drag slider or type precise value • Suggested: ₹${isBuy ? (entryPrice * 0.98).toFixed(2) : (entryPrice * 1.02).toFixed(2)} (2% ${isBuy ? 'below' : 'above'})</small>
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
                ${currentStep > 1 ? '<button class="btn btn-secondary" onclick="wizardPrevious()">← Back</button>' : '<button class="btn btn-secondary" onclick="closeLogModal()">Skip</button>'}
                ${currentStep < totalSteps
                    ? '<button class="btn btn-primary" onclick="wizardNext()">Next →</button>'
                    : '<button class="btn btn-success" onclick="wizardSubmit()">Save Log</button>'}
            </div>
        </div>
    `;

    // Initialize R:R calculation if on step 3
    if (currentStep === 3) {
        setTimeout(() => updateRiskReward(), 100);
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
    const color = ratio >= 2 ? 'var(--success-green)' : ratio >= 1 ? 'var(--warning-orange)' : 'var(--error-red)';
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
function wizardNext() {
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

// Wizard submit
async function wizardSubmit() {
    // Collect data from step 4
    const notesInput = document.getElementById('notes-input');
    wizardState.data.notes = notesInput?.value.trim() || null;

    const logData = {
        order_id: wizardState.orderId,
        target_price: wizardState.data.target_price,
        stop_loss: wizardState.data.stop_loss,
        emotion: wizardState.data.emotions.join(', ') || null,  // Join multiple emotions
        strategy: wizardState.data.setup,  // Using setup as strategy
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
            closeLogModal();
            loadUnloggedOrdersBanner();
            loadMonitoredPositions();
        } else {
            showToast(result.error || 'Failed to save log', 'error');
        }
    } catch (error) {
        console.error('Failed to submit trade log:', error);
        showToast('Failed to submit trade log', 'error');
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
