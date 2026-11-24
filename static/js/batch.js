/* ======================================================
   Batch.js — Batch Evaluation Module
   Drag-and-drop upload, progress polling, results table
   ====================================================== */

let currentBatchJobId = null;
let batchPollInterval = null;

// ---- Drag and Drop Upload ----
function initDropZone() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('batch-file-input');
    if (!dropZone || !fileInput) return;

    // Click to browse
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
            e.target.value = ''; // Reset input
        }
    });
}

// ---- File Upload Handler ----
async function handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
        showToast('Please upload a CSV file.', 'error');
        return;
    }

    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showToast('File too large. Maximum size is 5MB.', 'error');
        return;
    }

    showToast(`Uploading ${file.name}...`, 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const data = await apiCall('/api/batch/upload', {
            method: 'POST',
            body: formData,
        });

        currentBatchJobId = data.job_id;
        showToast(`Batch job created! Processing ${data.total_items} items...`, 'success');

        if (data.warnings && data.warnings.length > 0) {
            data.warnings.forEach(w => showToast(w, 'info', 6000));
        }

        // Show progress
        showBatchProgress(0, data.total_items);

        // Start polling
        startPolling(data.job_id, data.total_items);

    } catch (error) {
        showToast(`Upload failed: ${error.message}`, 'error');
    }
}

// ---- Progress Tracking ----
function showBatchProgress(completed, total) {
    const progressEl = document.getElementById('batch-progress');
    const progressText = document.getElementById('batch-progress-text');
    const progressCount = document.getElementById('batch-progress-count');
    const progressBar = document.getElementById('batch-progress-bar');

    if (!progressEl) return;

    progressEl.style.display = 'block';
    progressText.textContent = completed >= total ? 'Completed!' : 'Processing evaluations...';
    progressCount.textContent = `${completed}/${total}`;
    progressBar.style.width = `${total > 0 ? (completed / total) * 100 : 0}%`;
}

// ---- Polling ----
function startPolling(jobId, totalItems) {
    if (batchPollInterval) clearInterval(batchPollInterval);

    batchPollInterval = setInterval(async () => {
        try {
            const data = await apiCall(`/api/batch/jobs/${jobId}`);
            const job = data.job;
            const completed = job.completed_items + (job.failed_items || 0);

            showBatchProgress(completed, job.total_items);

            if (job.status === 'completed' || job.status === 'failed') {
                clearInterval(batchPollInterval);
                batchPollInterval = null;

                if (job.status === 'completed') {
                    showToast('Batch evaluation complete!', 'success');
                } else {
                    showToast('Batch evaluation finished with some errors.', 'error');
                }

                // Show results
                renderBatchResults(data.results, jobId);
                loadBatchHistory();
            }
        } catch (error) {
            // Continue polling on error
        }
    }, 3000);
}

// ---- Render Batch Results ----
function renderBatchResults(results, jobId) {
    const card = document.getElementById('batch-results-card');
    const tbody = document.getElementById('batch-results-body');
    const downloadBtn = document.getElementById('batch-download-btn');

    if (!card || !tbody) return;

    card.style.display = 'block';

    tbody.innerHTML = results.map((r, i) => {
        const tierClass = getTierClass(r.quality_tier);
        const overall = r.overall_score || 0;
        const relevance = r.relevance_score || 0;
        const accuracy = r.accuracy_score || 0;
        const hallucination = r.hallucination_score || 0;
        const completeness = r.completeness_score || 0;

        return `
            <tr class="animate-in" style="animation-delay: ${i * 0.05}s; cursor:pointer;"
                onclick="toggleBatchRow(this, ${r.id || 0})">
                <td>${i + 1}</td>
                <td title="${(r.question || '').replace(/"/g, '&quot;')}">${truncateText(r.question, 40)}</td>
                <td class="score-cell" style="color:${getScoreColor(overall)}">${overall.toFixed(1)}</td>
                <td><span class="tier-badge ${tierClass}" style="font-size:0.65rem; padding:0.2rem 0.6rem;">${r.quality_tier || 'N/A'}</span></td>
                <td class="score-cell" style="color:${getScoreColor(relevance)}">${relevance.toFixed(1)}</td>
                <td class="score-cell" style="color:${getScoreColor(accuracy)}">${accuracy.toFixed(1)}</td>
                <td class="score-cell" style="color:${getScoreColor(hallucination)}">${hallucination.toFixed(1)}</td>
                <td class="score-cell" style="color:${getScoreColor(completeness)}">${completeness.toFixed(1)}</td>
            </tr>
            <tr class="batch-detail-row" id="batch-detail-${r.id}" style="display:none;">
                <td colspan="8" style="padding:1rem;">
                    <div style="font-size:0.8rem; color:var(--text-secondary);">
                        <strong>Question:</strong> ${r.question || ''}<br><br>
                        <strong>AI Response:</strong> ${truncateText(r.ai_response || '', 300)}<br><br>
                        <strong>Verdict:</strong> ${r.verdict_reasoning || 'N/A'}
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    // Download button
    if (downloadBtn) {
        downloadBtn.onclick = () => downloadBatchResults(jobId);
    }
}

function toggleBatchRow(row, evalId) {
    const detailRow = document.getElementById(`batch-detail-${evalId}`);
    if (detailRow) {
        detailRow.style.display = detailRow.style.display === 'none' ? 'table-row' : 'none';
    }
}

// ---- Download Results ----
async function downloadBatchResults(jobId) {
    try {
        const blob = await apiCall(`/api/batch/jobs/${jobId}/download`);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `batch_${jobId}_results.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('Download started!', 'success');
    } catch (error) {
        showToast(`Download failed: ${error.message}`, 'error');
    }
}

// ---- Batch History ----
async function loadBatchHistory() {
    const container = document.getElementById('batch-history');
    if (!container) return;

    try {
        const data = await apiCall('/api/batch/jobs');
        const jobs = data.jobs || [];

        if (jobs.length === 0) {
            container.innerHTML = '<p class="empty-state">No batch jobs yet.</p>';
            return;
        }

        container.innerHTML = jobs.map(job => {
            const statusColors = {
                pending: 'var(--text-muted)',
                processing: 'var(--accent-secondary)',
                completed: 'var(--score-excellent)',
                failed: 'var(--score-failing)',
            };
            const statusColor = statusColors[job.status] || 'var(--text-muted)';

            return `
                <div class="history-item" onclick="loadBatchJob(${job.id})">
                    <div>
                        <span class="history-question">${job.filename}</span>
                        <span style="font-size:0.7rem; color:var(--text-muted); display:block; margin-top:2px;">
                            ${job.completed_items}/${job.total_items} items • ${formatDate(job.created_at)}
                        </span>
                    </div>
                    <span class="history-score" style="color:${statusColor}; background:${statusColor}15; text-transform:capitalize;">${job.status}</span>
                </div>
            `;
        }).join('');
    } catch (error) {
        // Silently fail
    }
}

async function loadBatchJob(jobId) {
    try {
        const data = await apiCall(`/api/batch/jobs/${jobId}`);
        currentBatchJobId = jobId;

        const job = data.job;
        showBatchProgress(job.completed_items, job.total_items);

        if (data.results && data.results.length > 0) {
            renderBatchResults(data.results, jobId);
        }

        if (job.status === 'processing') {
            startPolling(jobId, job.total_items);
        }
    } catch (error) {
        showToast(`Failed to load batch job: ${error.message}`, 'error');
    }
}

// ---- Initialize ----
document.addEventListener('DOMContentLoaded', () => {
    initDropZone();
});
