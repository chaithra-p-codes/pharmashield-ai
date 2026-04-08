// ================================================
//   PharmaShield AI — Frontend Logic
// ================================================

const API_BASE = 'http://localhost:5000';

let medicines        = [];
let allMedicinesList = [];
let autocompleteIndex = -1;
let lastResult       = null;

// ─── On Load ────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  fetchMedicinesList();
  setupInputEvents();
});

// ─── Fetch Medicine List for Autocomplete ───────
async function fetchMedicinesList() {
  try {
    const res  = await fetch(`${API_BASE}/api/medicines`);
    const data = await res.json();
    allMedicinesList = data.medicines || [];
  } catch {
    // Fallback if backend not running yet
    allMedicinesList = [
      'warfarin','aspirin','ibuprofen','paracetamol','metformin',
      'lisinopril','atorvastatin','simvastatin','amoxicillin','ciprofloxacin',
      'omeprazole','sertraline','fluoxetine','tramadol','digoxin',
      'amiodarone','amlodipine','levothyroxine','cetirizine','clarithromycin',
      'clopidogrel','methotrexate','lithium','fluconazole','naproxen',
      'verapamil','atenolol','sildenafil','nitrates','codeine'
    ];
  }
}

// ─── Input Events ────────────────────────────────
function setupInputEvents() {
  const input   = document.getElementById('medicineInput');
  const wrapper = document.getElementById('tagWrapper');

  wrapper.addEventListener('click', () => input.focus());

  input.addEventListener('keydown', (e) => {
    const dropdown = document.getElementById('autocompleteDropdown');
    const items    = dropdown.querySelectorAll('.autocomplete-item');

    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      if (autocompleteIndex >= 0 && items[autocompleteIndex]) {
        addMedicine(items[autocompleteIndex].dataset.value);
      } else {
        const val = input.value.replace(',', '').trim();
        if (val) addMedicine(val);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      autocompleteIndex = Math.min(autocompleteIndex + 1, items.length - 1);
      updateAutocompleteActive(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      autocompleteIndex = Math.max(autocompleteIndex - 1, -1);
      updateAutocompleteActive(items);
    } else if (e.key === 'Backspace' && input.value === '' && medicines.length > 0) {
      removeMedicine(medicines[medicines.length - 1]);
    } else if (e.key === 'Escape') {
      closeAutocomplete();
    }
  });

  input.addEventListener('input', () => {
    autocompleteIndex = -1;
    showAutocomplete(input.value.trim());
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('#tagWrapper') && !e.target.closest('#autocompleteDropdown')) {
      closeAutocomplete();
    }
  });
}

function updateAutocompleteActive(items) {
  items.forEach((item, i) => item.classList.toggle('active', i === autocompleteIndex));
}

function showAutocomplete(query) {
  const dropdown = document.getElementById('autocompleteDropdown');
  if (!query) { closeAutocomplete(); return; }

  const matches = allMedicinesList
    .filter(m => m.startsWith(query.toLowerCase()) && !medicines.includes(m))
    .slice(0, 6);

  if (!matches.length) { closeAutocomplete(); return; }

  dropdown.innerHTML = matches.map(m =>
    `<div class="autocomplete-item" data-value="${m}" onclick="addMedicine('${m}')">${m}</div>`
  ).join('');
  dropdown.classList.add('visible');
}

function closeAutocomplete() {
  const dropdown = document.getElementById('autocompleteDropdown');
  dropdown.classList.remove('visible');
  dropdown.innerHTML = '';
  autocompleteIndex  = -1;
}

// ─── Tag Management ──────────────────────────────
function addMedicine(name) {
  const normalized = name.toLowerCase().trim();
  if (!normalized || medicines.includes(normalized)) {
    document.getElementById('medicineInput').value = '';
    closeAutocomplete();
    return;
  }
  medicines.push(normalized);
  renderTags();
  document.getElementById('medicineInput').value = '';
  closeAutocomplete();
  document.getElementById('medicineInput').focus();
}

function removeMedicine(name) {
  medicines = medicines.filter(m => m !== name);
  renderTags();
}

function renderTags() {
  const container = document.getElementById('tagsContainer');
  container.innerHTML = medicines.map(m => `
    <span class="medicine-tag">
      ${m}
      <span class="remove-tag" onclick="removeMedicine('${m}')">×</span>
    </span>
  `).join('');
}

// ─── Get Patient Info ─────────────────────────────
function getPatientInfo() {
  return {
    age:       document.getElementById('patientAge').value       || '',
    weight:    document.getElementById('patientWeight').value    || '',
    condition: document.getElementById('patientCondition').value || 'None'
  };
}

// ─── Main API Call ────────────────────────────────
async function checkInteractions() {
  if (medicines.length < 2) {
    shakeInput();
    showToast('Please add at least 2 medicines to check interactions.');
    return;
  }

  showLoading(true);
  hideResults();

  try {
    const res = await fetch(`${API_BASE}/api/check`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        medicines,
        patient: getPatientInfo()
      })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    lastResult = data;

    showLoading(false);
    renderResults(data);
    saveToHistory(data);

  } catch (err) {
    showLoading(false);
    console.error('API error:', err);
    showToast('Could not connect to PharmaShield backend. Make sure Flask is running on port 5000.');
  }
}

// ─── Render Results ───────────────────────────────
function renderResults(data) {
  const section = document.getElementById('resultsSection');
  section.style.display = 'block';

  renderRiskBanner(data);
  renderAIExplanation(data);
  renderInteractionCards(data);
  renderStats(data);

  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderRiskBanner(data) {
  const banner = document.getElementById('riskBanner');
  const risk   = data.overall_risk;

  banner.className = 'risk-banner ' + risk;

  const config = {
    dangerous:            { icon: '⚠️', label: 'DANGEROUS INTERACTION DETECTED',  detail: `${data.interactions_found} critical interaction(s) found`, badge: '⚠ HIGH RISK' },
    moderate:             { icon: '⚡', label: 'MODERATE RISK DETECTED',           detail: `${data.interactions_found} interaction(s) require attention`, badge: '⚡ MODERATE' },
    safe:                 { icon: '✓',  label: 'COMBINATION APPEARS SAFE',         detail: 'No harmful interactions detected in database', badge: '✓ SAFE' },
    no_interactions_found:{ icon: '✓',  label: 'NO INTERACTIONS FOUND',            detail: 'These medicines have no recorded interactions', badge: '✓ CLEAR' }
  };

  const c = config[risk] || config['safe'];
  document.getElementById('riskIcon').textContent   = c.icon;
  document.getElementById('riskLabel').textContent  = c.label;
  document.getElementById('riskDetail').textContent = c.detail;
  document.getElementById('riskBadge').textContent  = c.badge;
}

function renderAIExplanation(data) {
  const box = document.getElementById('aiBox');
  if (data.ai_explanation) {
    document.getElementById('aiText').textContent = data.ai_explanation;
    box.style.display = 'block';
  } else {
    box.style.display = 'none';
  }
}

function renderInteractionCards(data) {
  const list = document.getElementById('interactionsList');

  if (!data.interactions || data.interactions.length === 0) {
    list.innerHTML = `
      <div class="interaction-card safe">
        <div class="card-header">
          <span class="drug-pair">All combinations checked</span>
          <span class="severity-pill safe">clear</span>
        </div>
        <p class="card-effect">No harmful interactions were found between the medicines you entered.</p>
      </div>`;
    return;
  }

  list.innerHTML = data.interactions.map((item, i) => `
    <div class="interaction-card ${item.severity}" style="animation-delay:${i * 0.07}s">
      <div class="card-header">
        <span class="drug-pair">
          ${item.drug1}<span class="plus"> + </span>${item.drug2}
        </span>
        <span class="severity-pill ${item.severity}">${item.severity}</span>
      </div>
      <p class="card-effect">${item.effect}</p>
      <p class="card-recommendation">${item.recommendation}</p>
    </div>
  `).join('');
}

function renderStats(data) {
  const dangerous = (data.interactions || []).filter(i => i.severity === 'dangerous').length;
  const moderate  = (data.interactions || []).filter(i => i.severity === 'moderate').length;
  const safe      = (data.interactions || []).filter(i => i.severity === 'safe').length;

  document.getElementById('statsBar').innerHTML = `
    <div class="stat-item">
      <span class="stat-value">${(data.medicines_checked || []).length}</span>
      <span class="stat-label">Medicines</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${data.total_pairs_checked || 0}</span>
      <span class="stat-label">Pairs Checked</span>
    </div>
    <div class="stat-item">
      <span class="stat-value" style="color:var(--red)">${dangerous}</span>
      <span class="stat-label">Dangerous</span>
    </div>
    <div class="stat-item">
      <span class="stat-value" style="color:var(--orange)">${moderate}</span>
      <span class="stat-label">Moderate</span>
    </div>
    <div class="stat-item">
      <span class="stat-value" style="color:var(--green)">${safe}</span>
      <span class="stat-label">Safe</span>
    </div>
  `;
}

// ─── History (localStorage) ───────────────────────
function saveToHistory(data) {
  try {
    let history = JSON.parse(localStorage.getItem('pharmaHistory') || '[]');
    history.unshift({
      medicines: data.medicines_checked,
      risk:      data.overall_risk,
      time:      new Date().toLocaleString()
    });
    history = history.slice(0, 5); // keep last 5
    localStorage.setItem('pharmaHistory', JSON.stringify(history));
  } catch {}
}

function toggleHistory() {
  const panel = document.getElementById('historyPanel');
  if (panel.style.display === 'none') {
    renderHistory();
    panel.style.display = 'block';
  } else {
    panel.style.display = 'none';
  }
}

function renderHistory() {
  const list = document.getElementById('historyList');
  try {
    const history = JSON.parse(localStorage.getItem('pharmaHistory') || '[]');
    if (!history.length) {
      list.innerHTML = '<p style="font-size:0.78rem;color:var(--text-muted);font-family:var(--font-mono)">No history yet.</p>';
      return;
    }
    list.innerHTML = history.map(h => `
      <div class="history-item">
        <span class="history-meds">${h.medicines.join(', ')}</span>
        <span class="history-risk ${h.risk}">${h.risk}</span>
      </div>
    `).join('');
  } catch {
    list.innerHTML = '<p style="color:var(--text-muted)">Could not load history.</p>';
  }
}

// ─── WhatsApp Share ───────────────────────────────
function shareWhatsApp() {
  if (!lastResult) return;

  const meds    = lastResult.medicines_checked.join(', ');
  const risk    = lastResult.overall_risk.toUpperCase();
  const explain = lastResult.ai_explanation || '';
  const text    = `🛡️ *PharmaShield AI Result*\n\nMedicines: ${meds}\nRisk Level: ${risk}\n\n${explain}\n\n_Checked via PharmaShield AI — for educational purposes only._`;

  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
}

// ─── UI Helpers ───────────────────────────────────
function showLoading(show) {
  document.getElementById('loadingState').style.display = show ? 'block' : 'none';
  document.getElementById('checkBtn').style.display     = show ? 'none'  : 'flex';
}

function hideResults() {
  document.getElementById('resultsSection').style.display = 'none';
}

function resetApp() {
  hideResults();
  medicines  = [];
  lastResult = null;
  renderTags();
  document.getElementById('medicineInput').focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function shakeInput() {
  const wrapper = document.getElementById('tagWrapper');
  wrapper.style.animation = 'none';
  wrapper.offsetHeight;
  wrapper.style.animation = 'shake 0.4s ease';
  setTimeout(() => wrapper.style.animation = '', 400);
}

function showToast(msg) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className  = 'toast';
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
    background:#0f1e35; border:1px solid rgba(255,77,106,0.4);
    color:#ff4d6a; padding:12px 20px; border-radius:10px;
    font-family:'Space Mono',monospace; font-size:0.76rem;
    z-index:999; max-width:90vw; text-align:center;
    box-shadow:0 10px 40px rgba(0,0,0,0.5);
    animation:fadeUp 0.3s ease both;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
