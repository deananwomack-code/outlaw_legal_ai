document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('legal-form');
    const addEvidenceBtn = document.getElementById('add-evidence');
    const evidenceContainer = document.getElementById('evidence-container');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const resultsContent = document.getElementById('results-content');
    const submitBtn = document.getElementById('submit-btn');

    let evidenceCount = 0;

    addEvidenceBtn.addEventListener('click', function() {
        evidenceCount++;
        const evidenceItem = document.createElement('div');
        evidenceItem.className = 'evidence-item';
        evidenceItem.innerHTML = `
            <input type="text" name="evidence_label_${evidenceCount}" placeholder="Label (e.g., Payment proof)">
            <input type="text" name="evidence_desc_${evidenceCount}" placeholder="Description (e.g., Bank transfer receipt)">
            <button type="button" class="btn-remove" onclick="this.parentElement.remove()">X</button>
        `;
        evidenceContainer.appendChild(evidenceItem);
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
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
                alert('PDF downloaded successfully!');
            } else {
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Analysis failed');
                
                loading.classList.add('hidden');
                displayResults(data.data);
                results.classList.remove('hidden');
            }
        } catch (error) {
            loading.classList.add('hidden');
            form.classList.remove('hidden');
            submitBtn.disabled = false;
            alert('Error: ' + error.message);
        }
    });

    function displayResults(data) {
        let html = '';

        html += `
            <div class="result-section">
                <h3>Case Information</h3>
                <div class="result-card">
                    <strong>Jurisdiction:</strong> ${data.jurisdiction}<br>
                    <strong>County:</strong> ${data.county}
                </div>
                <div class="result-card">
                    <strong>Facts:</strong> ${data.facts}
                </div>
            </div>
        `;

        html += `<div class="result-section"><h3>Applicable Statutes</h3>`;
        data.statutes.forEach(statute => {
            html += `
                <div class="result-card">
                    <strong>${statute.citation}</strong> - ${statute.title}<br>
                    <em>${statute.summary}</em>
                </div>
            `;
        });
        html += `</div>`;

        html += `<div class="result-section"><h3>Procedural Rules</h3>`;
        data.procedures.forEach(proc => {
            html += `
                <div class="result-card">
                    <strong>${proc.name}:</strong> ${proc.description}
                </div>
            `;
        });
        html += `</div>`;

        html += `<div class="result-section"><h3>Risk Assessment</h3>`;
        data.risks.forEach(risk => {
            html += `
                <div class="result-card risk-${risk.severity}">
                    <strong>[${risk.severity.toUpperCase()}]</strong> ${risk.description}<br>
                    <em>Mitigation: ${risk.mitigation}</em>
                </div>
            `;
        });
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
            <div style="margin-top: 2rem; text-align: center;">
                <button onclick="location.reload()" class="btn-primary" style="max-width: 300px;">New Analysis</button>
            </div>
        `;

        resultsContent.innerHTML = html;
    }
});
