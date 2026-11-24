/* ======================================================
   Dashboard.js — Dashboard & Analytics Module
   Stat cards, dimension bars, chart init, auto-refresh
   ====================================================== */

let dashboardLoaded = false;

// ---- Load Dashboard Data ----
async function loadDashboard() {
    try {
        const [statsData, trendsData] = await Promise.all([
            apiCall('/api/dashboard/stats'),
            apiCall('/api/dashboard/trends'),
        ]);

        renderStatCards(statsData);
        renderDimensionBars(statsData);
        renderRecentEvaluations(statsData.recent_evaluations || []);

        // Create/update charts
        createRadarChart('chart-radar', statsData);
        createDoughnutChart('chart-doughnut', statsData.quality_distribution || {});
        createTrendsChart('chart-trends', trendsData.trends || []);
        createHistogramChart('chart-histogram', statsData.score_distribution || {});

        dashboardLoaded = true;
    } catch (error) {
        // Show empty state if no data
        console.log('Dashboard data not available yet:', error.message);
    }
}

// ---- Animated Counter ----
function animateCounter(elementId, targetValue, suffix = '', decimals = 0) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const startValue = 0;
    const duration = 1200;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const currentValue = startValue + (targetValue - startValue) * eased;

        el.textContent = decimals > 0
            ? currentValue.toFixed(decimals) + suffix
            : Math.round(currentValue) + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ---- Render Stat Cards ----
function renderStatCards(stats) {
    animateCounter('stat-total', stats.total_evaluations || 0);
    animateCounter('stat-avg-score', stats.average_overall_score || 0, '', 1);
    animateCounter('stat-pass-rate', stats.pass_rate || 0, '%', 1);
}

// ---- Render Dimension Bars ----
function renderDimensionBars(stats) {
    const dimensions = [
        { key: 'relevance', value: stats.average_relevance || 0 },
        { key: 'accuracy', value: stats.average_accuracy || 0 },
        { key: 'hallucination', value: stats.average_hallucination || 0 },
        { key: 'completeness', value: stats.average_completeness || 0 },
    ];

    dimensions.forEach(dim => {
        const valueEl = document.getElementById(`dim-avg-${dim.key}`);
        const barEl = document.getElementById(`dim-bar-${dim.key}`);

        if (valueEl) valueEl.textContent = dim.value.toFixed(1);
        if (barEl) {
            setTimeout(() => {
                barEl.style.width = `${(dim.value / 10) * 100}%`;
            }, 300);
        }
    });
}

// ---- Render Recent Evaluations ----
function renderRecentEvaluations(evaluations) {
    const container = document.getElementById('dashboard-recent');
    if (!container) return;

    if (evaluations.length === 0) {
        container.innerHTML = '<p class="empty-state">No evaluations yet. Run an evaluation to see data here.</p>';
        return;
    }

    container.innerHTML = evaluations.map(ev => {
        const score = ev.overall_score || 0;
        const color = getScoreColor(score);
        const tierClass = getTierClass(ev.quality_tier);

        return `
            <div class="recent-item">
                <span class="recent-question">${truncateText(ev.question, 60)}</span>
                <div class="recent-meta">
                    <span class="recent-date">${formatDate(ev.created_at)}</span>
                    <span class="tier-badge ${tierClass}" style="font-size:0.6rem; padding:0.15rem 0.5rem;">${ev.quality_tier || 'N/A'}</span>
                    <span class="history-score" style="color:${color}; background:${color}15">${score.toFixed(1)}</span>
                </div>
            </div>
        `;
    }).join('');
}

// ---- Initialize ----
document.addEventListener('DOMContentLoaded', () => {
    // Dashboard loads on tab activation (see app.js)
});
