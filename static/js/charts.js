/* ======================================================
   Charts.js — Chart.js Integration with Dark Theme
   Radar, Doughnut, Line, Bar charts
   ====================================================== */

// Chart.js global defaults for dark theme
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.08)';
Chart.defaults.font.family = "'Inter', sans-serif";

// Store chart instances for updates
const chartInstances = {};

// Color palette
const CHART_COLORS = {
    violet: { solid: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.2)' },
    cyan: { solid: '#06b6d4', bg: 'rgba(6, 182, 212, 0.2)' },
    emerald: { solid: '#10b981', bg: 'rgba(16, 185, 129, 0.2)' },
    amber: { solid: '#f59e0b', bg: 'rgba(245, 158, 11, 0.2)' },
    red: { solid: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)' },
    blue: { solid: '#3b82f6', bg: 'rgba(59, 130, 246, 0.2)' },
    orange: { solid: '#f97316', bg: 'rgba(249, 115, 22, 0.2)' },
};

const TIER_COLORS = {
    'Excellent': CHART_COLORS.emerald.solid,
    'Good': CHART_COLORS.blue.solid,
    'Fair': CHART_COLORS.amber.solid,
    'Poor': CHART_COLORS.orange.solid,
    'Failing': CHART_COLORS.red.solid,
};

// ---- Radar Chart: Dimension Breakdown ----
function createRadarChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Relevance', 'Accuracy', 'Hallucination', 'Completeness'],
            datasets: [{
                label: 'Average Score',
                data: [
                    data.average_relevance || 0,
                    data.average_accuracy || 0,
                    data.average_hallucination || 0,
                    data.average_completeness || 0,
                ],
                backgroundColor: 'rgba(139, 92, 246, 0.15)',
                borderColor: '#8b5cf6',
                borderWidth: 2,
                pointBackgroundColor: '#8b5cf6',
                pointBorderColor: '#0f172a',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.15)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.label}: ${ctx.parsed.r.toFixed(1)}/10`,
                    },
                },
            },
            scales: {
                r: {
                    min: 0,
                    max: 10,
                    ticks: {
                        stepSize: 2,
                        color: '#64748b',
                        backdropColor: 'transparent',
                        font: { size: 10 },
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.08)',
                    },
                    angleLines: {
                        color: 'rgba(148, 163, 184, 0.08)',
                    },
                    pointLabels: {
                        color: '#94a3b8',
                        font: { size: 12, weight: 500 },
                    },
                },
            },
        },
    });
}

// ---- Doughnut Chart: Quality Distribution ----
function createDoughnutChart(canvasId, distribution) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const labels = Object.keys(distribution);
    const values = Object.values(distribution);
    const colors = labels.map(l => TIER_COLORS[l] || '#64748b');

    if (labels.length === 0) {
        labels.push('No Data');
        values.push(1);
        colors.push('#1e293b');
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#0f172a',
                borderWidth: 3,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 11 },
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.15)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                },
            },
        },
    });
}

// ---- Line Chart: Score Trends ----
function createTrendsChart(canvasId, trends) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const labels = trends.map((t, i) => `#${t.id || i + 1}`);

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Overall',
                    data: trends.map(t => t.overall_score),
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#8b5cf6',
                },
                {
                    label: 'Relevance',
                    data: trends.map(t => t.relevance_score),
                    borderColor: '#a78bfa',
                    borderWidth: 1.5,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderDash: [4, 4],
                },
                {
                    label: 'Accuracy',
                    data: trends.map(t => t.accuracy_score),
                    borderColor: '#06b6d4',
                    borderWidth: 1.5,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderDash: [4, 4],
                },
                {
                    label: 'Hallucination',
                    data: trends.map(t => t.hallucination_score),
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderDash: [4, 4],
                },
                {
                    label: 'Completeness',
                    data: trends.map(t => t.completeness_score),
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderDash: [4, 4],
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'line',
                        font: { size: 11 },
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.15)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } },
                },
                y: {
                    min: 0,
                    max: 10,
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: { stepSize: 2, font: { size: 10 } },
                },
            },
        },
    });
}

// ---- Bar Chart: Score Distribution ----
function createHistogramChart(canvasId, distribution) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const buckets = ['1-2.9', '3-4.9', '5-6.9', '7-8.9', '9-10'];
    const colors = [
        CHART_COLORS.red.solid,
        CHART_COLORS.orange.solid,
        CHART_COLORS.amber.solid,
        CHART_COLORS.blue.solid,
        CHART_COLORS.emerald.solid,
    ];
    const bgColors = [
        CHART_COLORS.red.bg,
        CHART_COLORS.orange.bg,
        CHART_COLORS.amber.bg,
        CHART_COLORS.blue.bg,
        CHART_COLORS.emerald.bg,
    ];

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: buckets,
            datasets: [{
                label: 'Evaluations',
                data: buckets.map(b => distribution[b] || 0),
                backgroundColor: bgColors,
                borderColor: colors,
                borderWidth: 1.5,
                borderRadius: 6,
                barPercentage: 0.7,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(148, 163, 184, 0.15)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.parsed.y} evaluation(s)`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: {
                        stepSize: 1,
                        font: { size: 10 },
                        precision: 0,
                    },
                },
            },
        },
    });
}
