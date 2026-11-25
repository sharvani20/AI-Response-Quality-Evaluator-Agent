/* ======================================================
   Evaluation.js — Single Evaluation Module
   Form submission, results rendering, score rings, history
   ====================================================== */

// ---- Score Ring SVG Builder ----
function createScoreRing(score, size = 100, strokeWidth = 6, fontSize = '1.8rem') {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 10) * circumference;
    const color = getScoreColor(score);

    return `
        <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
            <circle class="score-ring-bg"
                cx="${size / 2}" cy="${size / 2}" r="${radius}"
                stroke-width="${strokeWidth}" />
            <circle class="score-ring-fill"
                cx="${size / 2}" cy="${size / 2}" r="${radius}"
                stroke="${color}" stroke-width="${strokeWidth}"
                stroke-dasharray="${circumference}"
                stroke-dashoffset="${circumference}"
                transform="rotate(-90 ${size / 2} ${size / 2})"
                data-target-offset="${offset}" />
            <text class="verdict-score-text" x="${size / 2}" y="${size / 2}"
                text-anchor="middle" dominant-baseline="central"
                style="font-size:${fontSize}">${score.toFixed(1)}</text>
        </svg>
    `;
}

function createMiniScoreRing(score) {
    const size = 36;
    const strokeWidth = 3;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 10) * circumference;
    const color = getScoreColor(score);

    return `
        <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
            <circle class="mini-ring-bg"
                cx="${size / 2}" cy="${size / 2}" r="${radius}" />
            <circle class="mini-ring-fill"
                cx="${size / 2}" cy="${size / 2}" r="${radius}"
                stroke="${color}" stroke-width="${strokeWidth}"
                stroke-dasharray="${circumference}"
                stroke-dashoffset="${circumference}"
                stroke-linecap="round"
                transform="rotate(-90 ${size / 2} ${size / 2})"
                data-target-offset="${offset}" />
            <text class="mini-ring-text" x="${size / 2}" y="${size / 2}"
                text-anchor="middle" dominant-baseline="central">${score.toFixed(1)}</text>
        </svg>
    `;
}

// ---- Animate Score Rings ----
function animateScoreRings() {
    requestAnimationFrame(() => {
        document.querySelectorAll('[data-target-offset]').forEach(circle => {
            const targetOffset = circle.getAttribute('data-target-offset');
            setTimeout(() => {
                circle.style.strokeDashoffset = targetOffset;
            }, 100);
        });
    });
}

// ---- Render Evaluation Results ----
function renderResults(data) {
    const container = document.getElementById('eval-results');
    if (!container) return;

    // Build the overall verdict card
    const tierClass = getTierClass(data.quality_tier);
    const overallScore = data.overall_score || 0;

    let html = `
        <div class="verdict-card animate-in">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 0.75rem;">
                <span class="tier-badge ${tierClass}">${data.quality_tier || 'N/A'}</span>
                <button type="button" class="btn-secondary" onclick="clearEvalForm()" style="font-size: 0.75rem; padding: 0.35rem 0.75rem;" title="Clear form to evaluate another question">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    New Evaluation
                </button>
            </div>
            <div class="verdict-score-ring">
                ${createScoreRing(overallScore, 120, 7, '2rem')}
            </div>
            <div class="verdict-reasoning">${data.verdict_reasoning || ''}</div>
    `;

    // Recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        html += `
            <div class="verdict-recommendations">
                <h4>💡 Recommendations</h4>
                <ul>
                    ${data.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    html += `</div>`;

    // Dimension cards
    const dimensions = [
        { key: 'relevance', label: 'Relevance', icon: '🎯' },
        { key: 'accuracy', label: 'Accuracy', icon: '✅' },
        { key: 'hallucination', label: 'Hallucination Risk', icon: '⚠️' },
        { key: 'completeness', label: 'Completeness', icon: '📋' },
    ];

    html += `<div class="dimension-cards">`;

    dimensions.forEach((dim, index) => {
        const score = data[`${dim.key}_score`] || (data[dim.key] && data[dim.key].score) || 0;
        const reasoning = data[`${dim.key}_reasoning`] || (data[dim.key] && data[dim.key].reasoning) || '';
        const details = data[`${dim.key}_details`] || (data[dim.key] && data[dim.key].details) || [];
        const flaggedClaims = dim.key === 'hallucination'
            ? (data.flagged_claims || (data.hallucination && data.hallucination.flagged_claims) || [])
            : null;

        html += `
            <div class="dimension-card animate-in" style="animation-delay: ${(index + 1) * 0.1}s">
                <div class="dimension-header" onclick="this.parentElement.classList.toggle('expanded')">
                    <div class="dimension-info">
                        <div class="dimension-mini-ring">${createMiniScoreRing(score)}</div>
                        <span class="dimension-name">${dim.icon} ${dim.label}</span>
                    </div>
                    <span class="dimension-expand">▼</span>
                </div>
                <div class="dimension-body">
                    <p class="dimension-reasoning">${reasoning}</p>
        `;

        // Details list
        if (details && details.length > 0) {
            html += `<ul class="dimension-details">`;
            details.forEach(d => {
                html += `<li>${d}</li>`;
            });
            html += `</ul>`;
        }

        // Flagged claims table (hallucination only)
        if (flaggedClaims && flaggedClaims.length > 0) {
            html += `
                <div class="flagged-claims">
                    <h4>🔍 Claim Verification</h4>
                    <table class="claims-table">
                        <thead>
                            <tr><th>Claim</th><th>Status</th><th>Evidence</th></tr>
                        </thead>
                        <tbody>
            `;
            flaggedClaims.forEach(claim => {
                const statusClass = `claim-${claim.status || 'unverifiable'}`;
                html += `
                    <tr>
                        <td>${claim.claim || ''}</td>
                        <td><span class="claim-status ${statusClass}">${claim.status || 'unknown'}</span></td>
                        <td>${claim.evidence || '-'}</td>
                    </tr>
                `;
            });
            html += `</tbody></table></div>`;
        }

        html += `</div></div>`;
    });

    html += `</div>`;
    container.innerHTML = html;

    // Animate score rings after rendering
    animateScoreRings();
}

// ---- Clear / New Evaluation Form ----
function clearEvalForm() {
    const q = document.getElementById('eval-question');
    const r = document.getElementById('eval-response');
    const ref = document.getElementById('eval-reference');
    if (q) q.value = '';
    if (r) r.value = '';
    if (ref) ref.value = '';

    const qc = document.getElementById('question-count');
    const rc = document.getElementById('response-count');
    const refc = document.getElementById('reference-count');
    if (qc) qc.textContent = '0 characters';
    if (rc) rc.textContent = '0 characters';
    if (refc) refc.textContent = '0 characters';

    // Clear document badge and file input
    const docBadge = document.getElementById('eval-doc-badge');
    const fileInput = document.getElementById('eval-doc-upload');
    if (docBadge) docBadge.style.display = 'none';
    if (fileInput) fileInput.value = '';

    if (q) {
        q.focus();
        q.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    showToast('Form cleared. Ready for next evaluation.', 'info');
}

// ---- Document Upload Handler ----
function initDocUpload() {
    const fileInput = document.getElementById('eval-doc-upload');
    const docBadge = document.getElementById('eval-doc-badge');
    const docName = document.getElementById('eval-doc-name');
    const docRemove = document.getElementById('eval-doc-remove');
    const refTextarea = document.getElementById('eval-reference');
    const refCount = document.getElementById('reference-count');
    const btnText = document.getElementById('doc-btn-text');

    if (!fileInput) return;

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (btnText) btnText.textContent = 'Reading...';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/upload-document', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Upload failed with status ${res.status}`);
            }

            const data = await res.json();
            if (refTextarea) {
                refTextarea.value = data.text;
            }
            if (refCount) {
                refCount.textContent = `${data.char_count} characters`;
            }
            if (docBadge && docName) {
                docName.textContent = `${data.filename} (${data.char_count.toLocaleString()} chars)`;
                docBadge.style.display = 'inline-flex';
            }
            showToast(`Loaded "${data.filename}" (${data.char_count} chars)`, 'success');
        } catch (error) {
            showToast(`Failed to read document: ${error.message}`, 'error');
            fileInput.value = '';
        } finally {
            if (btnText) btnText.textContent = 'Upload Document';
        }
    });

    if (docRemove) {
        docRemove.addEventListener('click', () => {
            if (refTextarea) refTextarea.value = '';
            if (refCount) refCount.textContent = '0 characters';
            if (docBadge) docBadge.style.display = 'none';
            if (fileInput) fileInput.value = '';
            showToast('Document removed.', 'info');
        });
    }
}

// ---- Form Submission ----
function initEvalForm() {
    initDocUpload();
    const form = document.getElementById('eval-form');
    if (!form) return;

    const clearBtn = document.getElementById('eval-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearEvalForm);
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const question = document.getElementById('eval-question').value.trim();
        const aiResponse = document.getElementById('eval-response').value.trim();
        const reference = document.getElementById('eval-reference').value.trim();

        if (!question || !aiResponse) {
            showToast('Please fill in both the question and AI response.', 'error');
            return;
        }

        // Show loading
        const loading = document.getElementById('eval-loading');
        const results = document.getElementById('eval-results');
        const submitBtn = document.getElementById('eval-submit');

        loading.style.display = 'flex';
        results.style.display = 'none';
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20" style="animation: spin 1s linear infinite;">
                <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            Evaluating...
        `;

        // Animate agent labels
        const agentLabels = ['relevance', 'accuracy', 'hallucination', 'completeness', 'verdict'];
        agentLabels.forEach((a, i) => {
            const el = document.getElementById(`agent-status-${a}`);
            if (el) {
                setTimeout(() => { el.classList.add('active'); el.textContent = `🔄 ${el.textContent.substring(2)}`; }, i * 800);
            }
        });

        try {
            const data = await apiCall('/api/evaluate', {
                method: 'POST',
                body: JSON.stringify({
                    question,
                    ai_response: aiResponse,
                    reference: reference || null,
                }),
            });

            // Mark all agents as done
            agentLabels.forEach(a => {
                const el = document.getElementById(`agent-status-${a}`);
                if (el) { el.classList.remove('active'); el.classList.add('done'); el.textContent = `✅ ${el.textContent.substring(2)}`; }
            });

            setTimeout(() => {
                loading.style.display = 'none';
                results.style.display = 'block';
                renderResults(data);
                showToast(`Evaluation complete! Score: ${data.overall_score}/10 (${data.quality_tier})`, 'success');
                loadEvalHistory();
            }, 500);

        } catch (error) {
            showToast(`Evaluation failed: ${error.message}`, 'error');
            loading.style.display = 'none';
            results.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                    <path d="M22 2L11 13"/>
                    <path d="M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
                Run Evaluation
            `;
            // Reset agent labels
            agentLabels.forEach(a => {
                const el = document.getElementById(`agent-status-${a}`);
                if (el) {
                    el.classList.remove('active', 'done');
                    const name = a.charAt(0).toUpperCase() + a.slice(1);
                    el.textContent = `⏳ ${name === 'Hallucination' ? 'Hallucination Detector' : name + ' Judge'}`;
                    if (a === 'verdict') el.textContent = '⏳ Verdict Agent';
                }
            });
        }
    });
}

// ---- Evaluation History ----
async function loadEvalHistory() {
    const container = document.getElementById('eval-history');
    if (!container) return;

    try {
        const data = await apiCall('/api/evaluations?limit=10');
        const evaluations = data.evaluations || [];

        if (evaluations.length === 0) {
            container.innerHTML = '<p class="empty-state">No evaluations yet. Submit one above to get started.</p>';
            return;
        }

        container.innerHTML = evaluations.map(ev => {
            const score = ev.overall_score || 0;
            const color = getScoreColor(score);
            return `
                <div class="history-item" onclick="loadEvalDetail(${ev.id})">
                    <span class="history-question">${truncateText(ev.question, 50)}</span>
                    <span class="history-score" style="color:${color}; background:${color}15">${score.toFixed(1)}</span>
                </div>
            `;
        }).join('');
    } catch (error) {
        // Silently fail for history
    }
}

async function loadEvalDetail(evalId) {
    try {
        const data = await apiCall(`/api/evaluations/${evalId}`);
        const results = document.getElementById('eval-results');
        const loading = document.getElementById('eval-loading');
        if (loading) loading.style.display = 'none';
        if (results) results.style.display = 'block';

        // Also populate form fields so user can view/reuse the evaluated data
        const q = document.getElementById('eval-question');
        const r = document.getElementById('eval-response');
        const ref = document.getElementById('eval-reference');
        if (q && data.question) {
            q.value = data.question;
            const qc = document.getElementById('question-count');
            if (qc) qc.textContent = `${data.question.length} characters`;
        }
        if (r && data.ai_response) {
            r.value = data.ai_response;
            const rc = document.getElementById('response-count');
            if (rc) rc.textContent = `${data.ai_response.length} characters`;
        }
        if (ref) {
            ref.value = data.reference || '';
            const refc = document.getElementById('reference-count');
            if (refc) refc.textContent = `${(data.reference || '').length} characters`;
        }

        renderResults(data);
    } catch (error) {
        showToast(`Failed to load evaluation: ${error.message}`, 'error');
    }
}

// ---- Add CSS animation for spinner ----
const spinStyle = document.createElement('style');
spinStyle.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
document.head.appendChild(spinStyle);

// ---- Initialize ----
document.addEventListener('DOMContentLoaded', () => {
    initEvalForm();
});
