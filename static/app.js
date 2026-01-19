document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('legal-form');
    const addEvidenceBtn = document.getElementById('add-evidence');
    const evidenceContainer = document.getElementById('evidence-container');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const resultsContent = document.getElementById('results-content');
    const submitBtn = document.getElementById('submit-btn');
    const factsTextarea = document.getElementById('facts');
    const factsCounter = document.getElementById('facts-counter');
    const jurisdictionInput = document.getElementById('jurisdiction');
    const countyInput = document.getElementById('county');

    let evidenceCount = 0;

    function updateCharCounter() {
        const length = factsTextarea.value.length;
        const minLength = 20;
        
        if (length < minLength) {
            factsCounter.textContent = `${length} / ${minLength} characters minimum`;
            factsCounter.className = 'char-counter' + (length > 0 ? ' warning' : '');
        } else {
            factsCounter.textContent = `${length} characters`;
            factsCounter.className = 'char-counter';
        }
    }

    factsTextarea.addEventListener('input', updateCharCounter);
    updateCharCounter();

    function validateField(input, errorId) {
        const errorEl = document.getElementById(errorId);
        if (!input.value.trim()) {
            input.classList.add('error');
            if (errorEl) errorEl.classList.add('visible');
            return false;
        } else {
            input.classList.remove('error');
            if (errorEl) errorEl.classList.remove('visible');
            return true;
        }
    }

    function validateFacts() {
        const errorEl = document.getElementById('facts-error');
        if (factsTextarea.value.length < 20) {
            factsTextarea.classList.add('error');
            if (errorEl) errorEl.classList.add('visible');
            return false;
        } else {
            factsTextarea.classList.remove('error');
            if (errorEl) errorEl.classList.remove('visible');
            return true;
        }
    }

    jurisdictionInput.addEventListener('blur', () => validateField(jurisdictionInput, 'jurisdiction-error'));
    countyInput.addEventListener('blur', () => validateField(countyInput, 'county-error'));
    factsTextarea.addEventListener('blur', validateFacts);

    jurisdictionInput.addEventListener('input', () => {
        if (jurisdictionInput.value.trim()) {
            jurisdictionInput.classList.remove('error');
            const errorEl = document.getElementById('jurisdiction-error');
            if (errorEl) errorEl.classList.remove('visible');
        }
    });

    countyInput.addEventListener('input', () => {
        if (countyInput.value.trim()) {
            countyInput.classList.remove('error');
            const errorEl = document.getElementById('county-error');
            if (errorEl) errorEl.classList.remove('visible');
        }
    });

    addEvidenceBtn.addEventListener('click', function() {
        evidenceCount++;
        const evidenceItem = document.createElement('div');
        evidenceItem.className = 'evidence-item';
        evidenceItem.innerHTML = `
            <input type="text" name="evidence_label_${evidenceCount}" placeholder="Label (e.g., Payment proof)">
            <input type="text" name="evidence_desc_${evidenceCount}" placeholder="Description (e.g., Bank transfer receipt)">
            <button type="button" class="btn-remove" aria-label="Remove evidence item">X</button>
        `;
        
        const removeBtn = evidenceItem.querySelector('.btn-remove');
        removeBtn.addEventListener('click', function() {
            evidenceItem.style.animation = 'fadeIn 0.3s ease reverse';
            setTimeout(() => evidenceItem.remove(), 280);
        });
        
        evidenceContainer.appendChild(evidenceItem);
        evidenceItem.querySelector('input').focus();
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const isJurisdictionValid = validateField(jurisdictionInput, 'jurisdiction-error');
        const isCountyValid = validateField(countyInput, 'county-error');
        const isFactsValid = validateFacts();
        
        if (!isJurisdictionValid || !isCountyValid || !isFactsValid) {
            const firstError = form.querySelector('.error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
            return;
        }
        
        const formData = new FormData(form);
        const outputFormat = formData.get('requested_output');
        
        const evidence = [];
        const evidenceItems = evidenceContainer.querySelectorAll('.evidence-item');
        evidenceItems.forEach(item => {
            const label = item.querySelector('input[name^="evidence_label"]').value;
            const description = item.querySelector('input[name^="evidence_desc"]').value;
            if (label && description) {
                evidence.push({ label, description });
            }
        });

        const payload = {
            jurisdiction: formData.get('jurisdiction'),
            county: formData.get('county'),
            facts: formData.get('facts'),
            evidence: evidence,
            requested_output: outputFormat
        };

        form.classList.add('hidden');
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        submitBtn.disabled = true;

        try {
            const response = await fetch('/legal-support', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (outputFormat === 'pdf') {
                if (!response.ok) throw new Error('Failed to generate PDF');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `OutlawLegalAI_${payload.county}_Report.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                
                loading.classList.add('hidden');
                form.classList.remove('hidden');
                submitBtn.disabled = false;
                showNotification('PDF downloaded successfully!', 'success');
            } else {
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Analysis failed');
                
                loading.classList.add('hidden');
                displayResults(data.data);
                results.classList.remove('hidden');
                
                setTimeout(() => {
                    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            }
        } catch (error) {
            loading.classList.add('hidden');
            form.classList.remove('hidden');
            submitBtn.disabled = false;
            showNotification('Error: ' + error.message, 'error');
        }
    });

    function showNotification(message, type) {
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close" aria-label="Close notification">&times;</button>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            border-radius: 8px;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        `;
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'fadeIn 0.3s ease reverse';
            setTimeout(() => notification.remove(), 280);
        });
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'fadeIn 0.3s ease reverse';
                setTimeout(() => notification.remove(), 280);
            }
        }, 5000);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function displayResults(data) {
        let html = '';

        html += `
            <div class="result-section">
                <h3>Case Information</h3>
                <div class="result-card">
                    <strong>Jurisdiction:</strong> ${escapeHtml(data.jurisdiction)}<br>
                    <strong>County:</strong> ${escapeHtml(data.county)}
                </div>
                <div class="result-card">
                    <strong>Facts:</strong> ${escapeHtml(data.facts)}
                </div>
            </div>
        `;

        html += `<div class="result-section"><h3>Applicable Statutes</h3>`;
        if (data.statutes && data.statutes.length > 0) {
            data.statutes.forEach(statute => {
                html += `
                    <div class="result-card">
                        <strong>${escapeHtml(statute.citation)}</strong> - ${escapeHtml(statute.title)}<br>
                        <em>${escapeHtml(statute.summary)}</em>
                    </div>
                `;
            });
        } else {
            html += `<div class="result-card"><em>No specific statutes identified</em></div>`;
        }
        html += `</div>`;

        html += `<div class="result-section"><h3>Procedural Rules</h3>`;
        if (data.procedures && data.procedures.length > 0) {
            data.procedures.forEach(proc => {
                html += `
                    <div class="result-card">
                        <strong>${escapeHtml(proc.name)}:</strong> ${escapeHtml(proc.description)}
                    </div>
                `;
            });
        } else {
            html += `<div class="result-card"><em>No specific procedures identified</em></div>`;
        }
        html += `</div>`;

        html += `<div class="result-section"><h3>Risk Assessment</h3>`;
        if (data.risks && data.risks.length > 0) {
            data.risks.forEach(risk => {
                const severityClass = risk.severity.toLowerCase();
                html += `
                    <div class="result-card risk-${severityClass}">
                        <span class="risk-badge ${severityClass}">${escapeHtml(risk.severity)}</span>
                        ${escapeHtml(risk.description)}<br>
                        <em>Mitigation: ${escapeHtml(risk.mitigation)}</em>
                    </div>
                `;
            });
        } else {
            html += `<div class="result-card risk-low"><span class="risk-badge low">LOW</span> No significant risks identified</div>`;
        }
        html += `</div>`;

        html += `
            <div class="result-section">
                <h3>Case Strength Score</h3>
                <div class="score-grid">
                    <div class="score-item overall-score">
                        <div class="score-value">${data.score.overall}</div>
                        <div class="score-label">Overall Score</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">${data.score.element_score}</div>
                        <div class="score-label">Element Coverage</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">${data.score.evidence_score}</div>
                        <div class="score-label">Evidence Strength</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">${data.score.clarity_score}</div>
                        <div class="score-label">Clarity Score</div>
                    </div>
                </div>
            </div>
        `;

        html += `
            <div class="action-buttons">
                <button id="new-analysis-btn" class="btn-primary">New Analysis</button>
                <button id="print-results-btn" class="btn-outline">Print Results</button>
            </div>
        `;

        resultsContent.innerHTML = html;
        
        document.getElementById('new-analysis-btn').addEventListener('click', function() {
            results.classList.add('hidden');
            form.classList.remove('hidden');
            form.reset();
            updateCharCounter();
            submitBtn.disabled = false;
            
            setTimeout(() => {
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        });
        
        document.getElementById('print-results-btn').addEventListener('click', function() {
            window.print();
        });
    }
});
