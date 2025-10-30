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
