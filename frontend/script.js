const API_BASE = 'http://127.0.0.1:5000';

// ─── Condition Data ───────────────────────────────
const ALL_CONDITIONS = [
  // ── Female-priority ──
  { val: 'PCOS',                   label: 'PCOS',                   genders: ['female'] },
  { val: 'PCOD',                   label: 'PCOD',                   genders: ['female'] },
  { val: 'Endometriosis',          label: 'Endometriosis',          genders: ['female'] },
  { val: 'Pregnancy',              label: 'Pregnancy',              genders: ['female'] },
  { val: 'Postpartum',             label: 'Postpartum',             genders: ['female'] },
  { val: 'Menopause',              label: 'Menopause',              genders: ['female'] },
  { val: 'Osteoporosis',           label: 'Osteoporosis',           genders: ['female'] },
  { val: 'Breast Cancer',          label: 'Breast Cancer',          genders: ['female'] },
  { val: 'Cervical Cancer',        label: 'Cervical Cancer',        genders: ['female'] },
  { val: 'Ovarian Cysts',          label: 'Ovarian Cysts',          genders: ['female'] },
  { val: 'Iron Deficiency Anemia', label: 'Iron Deficiency Anemia', genders: ['female'] },
  { val: 'Lupus',                  label: 'Lupus',                  genders: ['female'] },

  // ── Male-priority ──
  { val: 'Prostate Enlargement',   label: 'Prostate Enlargement',   genders: ['male'] },
  { val: 'Prostate Cancer',        label: 'Prostate Cancer',        genders: ['male'] },
  { val: 'Erectile Dysfunction',   label: 'Erectile Dysfunction',   genders: ['male'] },
  { val: 'Low Testosterone',       label: 'Low Testosterone',       genders: ['male'] },
  { val: 'Gout',                   label: 'Gout',                   genders: ['male'] },
  { val: 'Sleep Apnea',            label: 'Sleep Apnea',            genders: ['male'] },
  { val: 'Kidney Stones',          label: 'Kidney Stones',          genders: ['male'] },

  // ── General (all) ──
  { val: 'Diabetes',               label: 'Diabetes',               genders: ['all'] },
  { val: 'Hypertension',           label: 'Hypertension',           genders: ['all'] },
  { val: 'Heart Disease',          label: 'Heart Disease',          genders: ['all'] },
  { val: 'Kidney Disease',         label: 'Kidney Disease',         genders: ['all'] },
  { val: 'Liver Disease',          label: 'Liver Disease',          genders: ['all'] },
  { val: 'Asthma',                 label: 'Asthma',                 genders: ['all'] },
  { val: 'Thyroid Disorder',       label: 'Thyroid Disorder',       genders: ['all'] },
  { val: 'COPD',                   label: 'COPD',                   genders: ['all'] },
  { val: 'Epilepsy',               label: 'Epilepsy',               genders: ['all'] },
  { val: 'Depression',             label: 'Depression',             genders: ['all'] },
  { val: 'Anxiety',                label: 'Anxiety',                genders: ['all'] },
  { val: 'Arthritis',              label: 'Arthritis',              genders: ['all'] },
  { val: 'High Cholesterol',       label: 'High Cholesterol',       genders: ['all'] },
  { val: 'Migraine',               label: 'Migraine',               genders: ['all'] },
  { val: 'Obesity',                label: 'Obesity',                genders: ['all'] },
  { val: 'Cancer (Other)',         label: 'Cancer (Other)',          genders: ['all'] },
  { val: 'HIV/AIDS',               label: 'HIV / AIDS',             genders: ['all'] },
  { val: 'Autoimmune Disorder',    label: 'Autoimmune',             genders: ['all'] },
];

const DOSAGE_PRESETS = [5, 10, 25, 50, 100, 200, 250, 500];

// ─── ML Risk Config ───────────────────────────────
const RISK_CONFIG = {
  // ── ML risk labels ──
  Critical: {
    icon: '⚠️', label: 'CRITICAL INTERACTION DETECTED',
    detail: 'ML model detected critical drug interactions',
    badge: '⚠ CRITICAL', cssClass: 'dangerous'
  },
  High: {
    icon: '⚠️', label: 'HIGH RISK INTERACTION DETECTED',
    detail: 'ML model flagged high-severity interaction(s)',
    badge: '⚠ HIGH RISK', cssClass: 'dangerous'
  },
  Moderate: {
    icon: '⚡', label: 'MODERATE RISK DETECTED',
    detail: 'ML model detected interactions requiring attention',
    badge: '⚡ MODERATE', cssClass: 'moderate'
  },
  Low: {
    icon: '✓', label: 'LOW RISK / COMBINATION APPEARS SAFE',
    detail: 'ML model found no significant interactions',
    badge: '✓ LOW RISK', cssClass: 'safe'
  },
  Unknown: {
    icon: '?', label: 'RISK UNKNOWN',
    detail: 'ML model unavailable — see AI explanation below',
    badge: '? UNKNOWN', cssClass: 'safe'
  },
  // ── Legacy API labels (backward-compat) ──
  dangerous:             { icon: '⚠️', label: 'DANGEROUS INTERACTION DETECTED',  detail: 'Critical interaction(s) found',                badge: '⚠ HIGH RISK', cssClass: 'dangerous' },
  moderate:              { icon: '⚡', label: 'MODERATE RISK DETECTED',           detail: 'Interaction(s) require attention',              badge: '⚡ MODERATE',  cssClass: 'moderate'  },
  safe:                  { icon: '✓',  label: 'COMBINATION APPEARS SAFE',         detail: 'No significant interactions detected',          badge: '✓ SAFE',       cssClass: 'safe'      },
  no_interactions_found: { icon: '✓',  label: 'NO INTERACTIONS FOUND',            detail: 'No recorded interactions for this combination', badge: '✓ CLEAR',      cssClass: 'safe'      },
};

// ─── State ────────────────────────────────────────
window.medicines          = [];
window.selectedGender     = null;
window.selectedConditions = new Set();

let allMedicinesList  = [];
let autocompleteIndex = -1;
let lastResult        = null;

// ─── Theme ────────────────────────────────────────
function toggleTheme() {
  const html   = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  document.getElementById('themeIcon').textContent = isDark ? '☽' : '☀';
  localStorage.setItem('pharmaTheme', isDark ? 'light' : 'dark');
}

function applyStoredTheme() {
  const saved = localStorage.getItem('pharmaTheme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  document.getElementById('themeIcon').textContent = saved === 'dark' ? '☀' : '☽';
}

// ─── On Load ──────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  applyStoredTheme();
  fetchMedicinesList();
  setupInputEvents();
  renderConditions(null);
  checkMLStatus();
});

// ─── ML Status Check ──────────────────────────────
async function checkMLStatus() {
  try {
    const res  = await fetch(`${API_BASE}/api/model-status`);
    const data = await res.json();
    const badge = document.getElementById('mlStatusBadge');
    if (!badge) return;
    if (data.ml_ready) {
      badge.textContent = '🤖 ML Active';
      badge.className   = 'ml-badge ml-active';
      badge.title       = 'Machine Learning model is loaded and scoring interactions';
    } else {
      badge.textContent = '⚠ ML Offline';
      badge.className   = 'ml-badge ml-offline';
      badge.title       = data.message || 'Run: python ml/train_model.py';
    }
    badge.style.display = 'inline-flex';
  } catch {
    // Silently ignore
  }
}

// ─── Fetch Medicine List ──────────────────────────
async function fetchMedicinesList() {
  try {
    const res  = await fetch(`${API_BASE}/api/medicines`);
    const data = await res.json();
    allMedicinesList = data.medicines || [];
  } catch {
    allMedicinesList = [
      'warfarin','aspirin','ibuprofen','paracetamol','metformin',
      'lisinopril','atorvastatin','simvastatin','amoxicillin','ciprofloxacin',
      'omeprazole','sertraline','fluoxetine','tramadol','digoxin',
      'amiodarone','amlodipine','levothyroxine','cetirizine','clarithromycin',
      'clopidogrel','methotrexate','lithium','fluconazole','naproxen',
      'verapamil','atenolol','sildenafil','nitrates','codeine',
      'prednisone','dexamethasone','losartan','furosemide','spironolactone',
      'clonazepam','diazepam','alprazolam','quetiapine','olanzapine',
    ];
  }
}

// ─── Gender Selection ─────────────────────────────
window.selectGender = function(btn) {
  document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  window.selectedGender = btn.dataset.val;
  renderConditions(window.selectedGender);
};

// ─── Condition Rendering ──────────────────────────
function renderConditions(gender) {
  const prioritySection = document.getElementById('prioritySection');
  const priorityChips   = document.getElementById('priorityChips');
  const generalChips    = document.getElementById('generalChips');
  const priorityLabel   = document.getElementById('priorityLabel');
  const generalLabel    = document.getElementById('generalLabel');
  const hint            = document.getElementById('conditionGenderHint');

  let priority = [];
  let general  = ALL_CONDITIONS.filter(c => c.genders.includes('all'));

  if (gender === 'female') {
    priority = ALL_CONDITIONS.filter(c => c.genders.includes('female'));
    priorityLabel.textContent = '♀ Common in Women';
    generalLabel.textContent  = 'General';
    hint.textContent = 'Showing women-specific conditions first';
    hint.classList.add('visible');
    prioritySection.style.display = 'block';
  } else if (gender === 'male') {
    priority = ALL_CONDITIONS.filter(c => c.genders.includes('male'));
    priorityLabel.textContent = '♂ Common in Men';
    generalLabel.textContent  = 'General';
    hint.textContent = 'Showing men-specific conditions first';
    hint.classList.add('visible');
    prioritySection.style.display = 'block';
  } else {
    prioritySection.style.display = 'none';
    hint.classList.remove('visible');
    generalLabel.textContent = 'All Conditions';
  }

  priorityChips.innerHTML = '';
  generalChips.innerHTML  = '';

  priority.forEach(c => priorityChips.appendChild(makeConditionChip(c, true)));
  general.forEach(c  => generalChips.appendChild(makeConditionChip(c, false)));
}

function makeConditionChip(cond, isPriority) {
  const btn = document.createElement('button');
  btn.className   = 'cond-chip' + (isPriority ? ' priority-chip' : '');
  btn.dataset.val = cond.val;
  btn.textContent = cond.label;
  if (window.selectedConditions.has(cond.val)) btn.classList.add('selected');
  btn.addEventListener('click', () => toggleCondition(btn));
  return btn;
}

window.toggleCondition = function(btn) {
  const val = btn.dataset.val;
  if (window.selectedConditions.has(val)) {
    window.selectedConditions.delete(val);
    btn.classList.remove('selected');
  } else {
    window.selectedConditions.add(val);
    btn.classList.add('selected');
  }
  document.querySelectorAll(`.cond-chip[data-val="${CSS.escape(val)}"]`).forEach(b => {
    b.classList.toggle('selected', window.selectedConditions.has(val));
  });
};

// ─── Input Events ─────────────────────────────────
function setupInputEvents() {
  const input   = document.getElementById('medicineInput');
  const wrapper = document.getElementById('tagWrapper');
  if (!input || !wrapper) return;

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
    } else if (e.key === 'Backspace' && input.value === '' && window.medicines.length > 0) {
      removeMedicine(window.medicines[window.medicines.length - 1].name);
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
    if (!e.target.closest('.med-tag')) {
      document.querySelectorAll('.dose-popover').forEach(p => p.style.display = 'none');
    }
  });
}

function updateAutocompleteActive(items) {
  items.forEach((item, i) => item.classList.toggle('active', i === autocompleteIndex));
}

function showAutocomplete(query) {
  const dropdown = document.getElementById('autocompleteDropdown');
  if (!query) { closeAutocomplete(); return; }

  const existingNames = window.medicines.map(m => m.name);
  const matches = allMedicinesList
    .filter(m => m.startsWith(query.toLowerCase()) && !existingNames.includes(m))
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

// ─── Medicine Management ──────────────────────────
window.addMedicine = function(name) {
  const normalized = name.toLowerCase().trim();
  if (!normalized || window.medicines.find(m => m.name === normalized)) {
    document.getElementById('medicineInput').value = '';
    closeAutocomplete();
    return;
  }
  window.medicines.push({ name: normalized, dosage: '' });
  renderMedicineTags();
  document.getElementById('medicineInput').value = '';
  closeAutocomplete();
  document.getElementById('medicineInput').focus();
};

window.removeMedicine = function(name) {
  window.medicines = window.medicines.filter(m => m.name !== name);
  renderMedicineTags();
};

window.updateDosage = function(name, val) {
  const med = window.medicines.find(m => m.name === name);
  if (med) med.dosage = val;
};

// ─── Medicine Tag Rendering ───────────────────────
function renderMedicineTags() {
  const container = document.getElementById('tagsContainer');
  if (!container) return;
  container.innerHTML = '';

  window.medicines.forEach(med => {
    const safeId = med.name.replace(/\W/g, '_');
    const tag    = document.createElement('div');
    tag.className   = 'med-tag';
    tag.dataset.med = med.name;
    tag.innerHTML = `
      <span class="med-tag-name">${med.name}</span>
      <div class="med-tag-dosage-wrap">
        <button class="dose-step" title="-5mg" onclick="stepDosage('${med.name}', -5)">−</button>
        <input
          id="dose-${safeId}"
          class="med-tag-dosage"
          type="text"
          inputmode="numeric"
          pattern="[0-9]*"
          placeholder="mg"
          value="${med.dosage}"
          title="Type dosage in mg"
          oninput="handleDosageInput('${med.name}', this)"
          onblur="finaliseDosage('${med.name}', this)"
          onkeydown="dosageKeydown(event, '${med.name}')"
        />
        <button class="dose-step" title="+5mg" onclick="stepDosage('${med.name}', 5)">+</button>
        <span class="med-tag-unit">mg</span>
        <button class="dose-preset-toggle" title="Common doses" onclick="toggleDosePopover('${med.name}', this)">▾</button>
      </div>
      <div class="dose-popover" id="popover-${safeId}" style="display:none">
        <span class="dose-popover-label">Common doses</span>
        <div class="dose-popover-grid">
          ${DOSAGE_PRESETS.map(p =>
            `<button class="dose-preset-btn" onclick="applyPreset('${med.name}', ${p})">${p}</button>`
          ).join('')}
        </div>
      </div>
      <button class="med-tag-remove" onclick="removeMedicine('${med.name}')" title="Remove">×</button>
    `;
    container.appendChild(tag);
  });
}

// ─── Dosage Helpers ───────────────────────────────
window.handleDosageInput = function(name, input) {
  input.value = input.value.replace(/[^0-9]/g, '');
  updateDosage(name, input.value);
};

window.finaliseDosage = function(name, input) {
  const val = parseInt(input.value, 10);
  if (!isNaN(val) && val > 0) {
    input.value = val;
    updateDosage(name, val);
  } else {
    input.value = '';
    updateDosage(name, '');
  }
};

window.dosageKeydown = function(e, name) {
  if (e.key === 'ArrowUp')   { e.preventDefault(); stepDosage(name, 5);  }
  if (e.key === 'ArrowDown') { e.preventDefault(); stepDosage(name, -5); }
  if (e.key === 'Enter')     { e.target.blur(); }
};

window.stepDosage = function(name, delta) {
  const med     = window.medicines.find(m => m.name === name);
  if (!med) return;
  const current = parseInt(med.dosage, 10) || 0;
  const next    = Math.max(1, current + delta);
  med.dosage    = next;
  const inp = document.getElementById(`dose-${name.replace(/\W/g, '_')}`);
  if (inp) inp.value = next;
};

window.applyPreset = function(name, value) {
  const med = window.medicines.find(m => m.name === name);
  if (!med) return;
  med.dosage = value;
  const inp = document.getElementById(`dose-${name.replace(/\W/g, '_')}`);
  if (inp) inp.value = value;
  const pop = document.getElementById(`popover-${name.replace(/\W/g, '_')}`);
  if (pop) pop.style.display = 'none';
};

window.toggleDosePopover = function(name, btn) {
  const safeId = name.replace(/\W/g, '_');
  const pop    = document.getElementById(`popover-${safeId}`);
  if (!pop) return;
  const isOpen = pop.style.display !== 'none';
  document.querySelectorAll('.dose-popover').forEach(p => p.style.display = 'none');
  pop.style.display = isOpen ? 'none' : 'block';
};

// ─── Patient Profile ──────────────────────────────
function getPatientProfile() {
  return {
    age:        document.getElementById('patientAge')?.value    || null,
    weight:     document.getElementById('patientWeight')?.value || null,
    gender:     window.selectedGender,
    conditions: [...window.selectedConditions],
    medicines:  window.medicines.map(m => ({
      name:   m.name,
      dosage: m.dosage ? `${m.dosage}mg` : null
    }))
  };
}

// ─── Build API Payload ────────────────────────────
function buildApiPayload(profile) {
  return {
    medicines: profile.medicines,
    patient: {
      age:        profile.age,
      weight:     profile.weight,
      gender:     profile.gender,
      conditions: profile.conditions
    },
    drugs: window.medicines.map(m => ({
      name:     m.name,
      quantity: parseInt(m.dosage, 10) || 1
    })),
    gender:     profile.gender,
    conditions: profile.conditions
  };
}

// ─── Main API Call ────────────────────────────────
async function checkInteractions() {
  if (window.medicines.length < 2) {
    shakeInput();
    showToast('Please add at least 2 medicines to check interactions.');
    return;
  }

  showLoading(true);
  hideResults();

  const profile = getPatientProfile();
  const payload = buildApiPayload(profile);

  try {
    const res = await fetch(`${API_BASE}/api/check`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
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
  renderMLSummary(data);
  renderAIExplanation(data);
  renderInteractionCards(data);
  renderMLPairBreakdown(data);
  renderStats(data);
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── Risk Banner ──────────────────────────────────
// Always driven by ML overall_risk (the single source of truth)
function renderRiskBanner(data) {
  const banner = document.getElementById('riskBanner');

  // ML overall_risk is the authoritative source ("High", "Critical", etc.)
  const mlRisk = data.ml_result?.overall_risk;
  const risk   = mlRisk || 'Low';

  const c = RISK_CONFIG[risk] || RISK_CONFIG['Low'];
  banner.className = 'risk-banner ' + c.cssClass;

  const interactionCount = data.ml_result?.pairs?.length ?? 0;
  const confidence       = Math.round((data.ml_result?.confidence || 0) * 100);
  const detail = `${interactionCount} interaction pair(s) analysed · ML confidence: ${confidence}%`;

  document.getElementById('riskIcon').textContent   = c.icon;
  document.getElementById('riskLabel').textContent  = c.label;
  document.getElementById('riskDetail').textContent = detail;
  document.getElementById('riskBadge').textContent  = c.badge;
}

// ─── ML Summary Panel ─────────────────────────────
function renderMLSummary(data) {
  let mlBox = document.getElementById('mlSummaryBox');
  if (!mlBox) {
    mlBox = document.createElement('div');
    mlBox.id = 'mlSummaryBox';
    mlBox.className = 'ml-summary-box';
    const banner = document.getElementById('riskBanner');
    if (banner && banner.parentNode) {
      banner.parentNode.insertBefore(mlBox, banner.nextSibling);
    }
  }

  const ml = data.ml_result;
  if (!ml || !ml.ml_used) {
    mlBox.style.display = 'none';
    return;
  }

  const confidence  = Math.round((ml.confidence || 0) * 100);
  const scoreColor  = ['var(--green)', 'var(--orange)', 'var(--red)', '#8b0000'];
  const score       = ml.overall_score ?? 0;

  mlBox.style.display = 'block';
  mlBox.innerHTML = `
    <div class="ml-summary-header">
      <span class="ml-icon">🤖</span>
      <span class="ml-title">ML Risk Analysis</span>
      <span class="ml-conf-badge" style="color:${scoreColor[score]}">
        ${ml.overall_risk} · ${confidence}% confidence
      </span>
    </div>
    <div class="ml-score-bar-wrap">
      <div class="ml-score-bar">
        <div class="ml-score-fill" style="width:${(score / 3) * 100}%; background:${scoreColor[score]}"></div>
      </div>
      <span class="ml-score-labels">
        <span>Low</span><span>Moderate</span><span>High</span><span>Critical</span>
      </span>
    </div>
  `;
}

// ─── AI Explanation ───────────────────────────────
function renderAIExplanation(data) {
  const box         = document.getElementById('aiBox');
  const explanation = data.ai_explanation || data.explanation;

  if (!explanation) {
    box.style.display = 'none';
    return;
  }

  document.getElementById('aiText').textContent = explanation;
  box.style.display = 'block';
}

// ─── Interaction Cards ────────────────────────────
//   ML "High"/"Critical" → "dangerous"
//   ML "Moderate"        → "moderate"
//   ML "Low"             → "safe"
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

  // Build ML pair lookup for mini badge
  const mlPairMap = {};
  (data.ml_result?.pairs || []).forEach(p => {
    const key = [p.drug1, p.drug2].sort().join('|');
    mlPairMap[key] = p;
  });

  list.innerHTML = data.interactions.map((item, i) => {
    const key    = [item.drug1, item.drug2].sort().join('|');
    const mlPair = mlPairMap[key];
    const mlTag  = mlPair
      ? `<span class="ml-pair-mini-badge" title="ML scored this pair">
           🤖 ML: ${mlPair.risk_label} (${Math.round(mlPair.confidence * 100)}%)
         </span>`
      : '';

    return `
      <div class="interaction-card ${item.severity}" style="animation-delay:${i * 0.07}s">
        <div class="card-header">
          <span class="drug-pair">
            ${item.drug1}<span class="plus"> + </span>${item.drug2}
          </span>
          <span class="severity-pill ${item.severity}">${item.severity}</span>
          ${mlTag}
        </div>
        ${item.dosage_warning ? `<p class="card-dosage-warn">⚠ ${item.dosage_warning}</p>` : ''}
        <p class="card-effect">${item.effect}</p>
        <p class="card-recommendation">${item.recommendation}</p>
      </div>
    `;
  }).join('');
}

// ─── ML Per-Pair Breakdown ────────────────────────
function renderMLPairBreakdown(data) {
  let mlSection = document.getElementById('mlPairSection');
  if (!mlSection) {
    mlSection = document.createElement('div');
    mlSection.id = 'mlPairSection';
    mlSection.className = 'ml-pair-section';
    const interactionsList = document.getElementById('interactionsList');
    if (interactionsList && interactionsList.parentNode) {
      interactionsList.parentNode.insertBefore(mlSection, interactionsList.nextSibling);
    }
  }

  const pairs = data.ml_result?.pairs;
  if (!pairs || pairs.length === 0) {
    mlSection.style.display = 'none';
    return;
  }

  const riskColor = {
    Low:      'var(--green)',
    Moderate: 'var(--orange)',
    High:     'var(--red)',
    Critical: '#8b0000'
  };

  mlSection.style.display = 'block';
  mlSection.innerHTML = `
    <h3 class="ml-section-title">🤖 ML Pair-Level Analysis</h3>
    <div class="ml-pair-grid">
      ${pairs.map(p => {
        const color       = riskColor[p.risk_label] || 'var(--text-muted)';
        const conf        = Math.round(p.confidence * 100);
        // ── Single winner bar only ──
        const winnerBar   = `
          <div class="ml-prob-row">
            <span class="ml-prob-label">${p.risk_label}</span>
            <div class="ml-prob-bar-wrap">
              <div class="ml-prob-bar" style="width:${conf}%; background:${color}"></div>
            </div>
            <span class="ml-prob-val">${conf}%</span>
          </div>`;

        return `
          <div class="ml-pair-card">
            <div class="ml-pair-card-header">
              <span class="ml-pair-names">${p.drug1} <span class="plus">+</span> ${p.drug2}</span>
              <span class="ml-pair-risk-badge" style="color:${color}">${p.risk_label}</span>
            </div>
            <div class="ml-pair-meta">
              Dosage: <strong>${p.qty1}mg + ${p.qty2}mg</strong>
              &nbsp;·&nbsp; Confidence: <strong>${conf}%</strong>
            </div>
            <div class="ml-prob-breakdown">${winnerBar}</div>
          </div>`;
      }).join('')}
    </div>
  `;
}

// ─── Stats Bar ────────────────────────────────────
function renderStats(data) {
  // Count by mapped severity (dangerous/moderate/safe) from interactions[]
  const dangerous = (data.interactions || []).filter(i => i.severity === 'dangerous').length;
  const moderate  = (data.interactions || []).filter(i => i.severity === 'moderate').length;
  const safe      = (data.interactions || []).filter(i => i.severity === 'safe').length;
  const profile   = getPatientProfile();

  const hasMeta  = profile.age || profile.gender || profile.conditions.length > 0;
  const metaHtml = hasMeta ? `
    <div class="stat-item patient-meta">
      <span class="stat-label">Checked for</span>
      <span class="stat-value patient-summary">
        ${[
          profile.age    ? `Age ${profile.age}` : '',
          profile.gender ? profile.gender.charAt(0).toUpperCase() + profile.gender.slice(1) : '',
          profile.conditions.length ? profile.conditions.join(', ') : ''
        ].filter(Boolean).join(' · ')}
      </span>
    </div>` : '';

  const mlStatHtml = data.ml_result?.ml_used ? `
    <div class="stat-item">
      <span class="stat-value" style="color:var(--accent)">${Math.round((data.ml_result.confidence || 0) * 100)}%</span>
      <span class="stat-label">ML Conf.</span>
    </div>` : '';

  document.getElementById('statsBar').innerHTML = `
    <div class="stat-item">
      <span class="stat-value">${window.medicines.length}</span>
      <span class="stat-label">Medicines</span>
    </div>
    <div class="stat-item">
      <span class="stat-value">${data.total_pairs_checked || data.ml_result?.pairs?.length || 0}</span>
      <span class="stat-label">Pairs</span>
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
    ${mlStatHtml}
    ${metaHtml}
  `;
}

// ─── History ──────────────────────────────────────
function saveToHistory(data) {
  try {
    const profile = getPatientProfile();
    let history   = JSON.parse(localStorage.getItem('pharmaHistory') || '[]');
    history.unshift({
      medicines:  (data.medicines_checked || window.medicines.map(m => m.name)),
      risk:       data.ml_result?.overall_risk || data.overall_risk,
      mlUsed:     data.ml_result?.ml_used || false,
      confidence: data.ml_result?.confidence || null,
      gender:     profile.gender,
      conditions: profile.conditions,
      time:       new Date().toLocaleString()
    });
    history = history.slice(0, 5);
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
    list.innerHTML = history.map(h => {
      const meta = [
        h.gender     ? h.gender : '',
        h.conditions?.length ? h.conditions.join(', ') : ''
      ].filter(Boolean).join(' · ');

      const confTag = h.mlUsed && h.confidence
        ? `<span class="history-conf">🤖 ${Math.round(h.confidence * 100)}%</span>`
        : '';

      return `
        <div class="history-item">
          <div>
            <span class="history-meds">${(h.medicines || []).join(', ')}</span>
            ${meta ? `<span class="history-meta">${meta}</span>` : ''}
          </div>
          <div style="display:flex;align-items:center;gap:6px">
            ${confTag}
            <span class="history-risk ${(h.risk || '').toLowerCase()}">${h.risk}</span>
          </div>
        </div>
      `;
    }).join('');
  } catch {
    list.innerHTML = '<p style="color:var(--text-muted)">Could not load history.</p>';
  }
}

// ─── WhatsApp Share ───────────────────────────────
function shareWhatsApp() {
  if (!lastResult) return;
  const profile = getPatientProfile();
  const meds    = window.medicines.map(m => m.dosage ? `${m.name} (${m.dosage}mg)` : m.name).join(', ');
  const risk    = (lastResult.ml_result?.overall_risk || lastResult.overall_risk || 'Unknown').toUpperCase();
  const conf    = lastResult.ml_result?.confidence
    ? ` (ML ${Math.round(lastResult.ml_result.confidence * 100)}% confidence)`
    : '';
  const explain = lastResult.ai_explanation || lastResult.explanation || '';

  const patientLine = [
    profile.age        ? `Age: ${profile.age}`                              : '',
    profile.gender     ? `Gender: ${profile.gender}`                        : '',
    profile.conditions.length ? `Conditions: ${profile.conditions.join(', ')}` : ''
  ].filter(Boolean).join(' | ');

  const text = [
    '🛡️ *PharmaShield AI Result*', '',
    `Medicines: ${meds}`,
    patientLine || '',
    `Risk Level: ${risk}${conf}`, '',
    explain, '',
    '_Checked via PharmaShield AI — for educational purposes only._'
  ].filter(l => l !== null).join('\n');

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
  window.medicines = [];
  renderMedicineTags();
  window.selectedGender = null;
  document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('active'));
  window.selectedConditions.clear();
  renderConditions(null);
  document.getElementById('patientAge').value    = '';
  document.getElementById('patientWeight').value = '';
  lastResult = null;
  document.getElementById('medicineInput').focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });

  const mlBox     = document.getElementById('mlSummaryBox');
  const mlSection = document.getElementById('mlPairSection');
  if (mlBox)     mlBox.style.display     = 'none';
  if (mlSection) mlSection.style.display = 'none';
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
  toast.className   = 'toast';
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
    background:var(--surface2); border:1px solid rgba(255,77,106,0.4);
    color:var(--red); padding:12px 20px; border-radius:10px;
    font-family:var(--font-mono); font-size:0.76rem;
    z-index:999; max-width:90vw; text-align:center;
    box-shadow:var(--shadow);
    animation:fadeUp 0.3s ease both;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
