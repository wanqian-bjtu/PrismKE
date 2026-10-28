"""Visual tokens and responsive CSS for the PrismKE Gradio workspace."""

APP_CSS = r"""
.prismke-export-link {
  display: flex;
  min-height: 44px;
  width: 100%;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: var(--prism-blue, #0758d8);
  color: #fff !important;
  font-weight: 650;
  text-decoration: none !important;
}

.prismke-export-link:focus-visible {
  outline: 3px solid var(--prism-amber, #e9a21a);
  outline-offset: 2px;
}

:root {
  --prism-bg: #f4f6f8;
  --prism-surface: #ffffff;
  --prism-surface-muted: #f8fafc;
  --prism-text: #172033;
  --prism-muted: #64748b;
  --prism-border: #dbe1e8;
  --prism-blue: #0758d8;
  --prism-blue-soft: #eaf2ff;
  --prism-cyan: #08a9d6;
  --prism-amber: #e9a21a;
  --prism-danger: #c53b45;
  --prism-radius: 6px;
  --prism-sidebar-width: max(260px, 20vw);
  --prism-topbar-height: clamp(48px, 5dvh, 72px);
  --prism-brand-content-height: clamp(132px, 15dvh, 230px);
  --prism-brand-gap: clamp(8px, 1dvh, 16px);
  --prism-header-height: calc(
    var(--prism-topbar-height) + var(--prism-brand-content-height)
  );
}

.gradio-container {
  box-sizing: border-box !important;
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  background: var(--prism-bg) !important;
  color: var(--prism-text) !important;
  padding: 0 !important;
  letter-spacing: 0 !important;
}

.gradio-container > .main {
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

.gradio-container .sidebar-parent {
  padding-left: var(--prism-sidebar-width) !important;
  transition: padding-left 180ms ease;
}

.gradio-container .sidebar-parent:has(#workspace-sidebar:not(.open)) {
  padding-left: 0 !important;
}

.gradio-container .sidebar-parent main > .column:has(> #workspace-header) {
  gap: 0 !important;
}

#workspace-sidebar {
  width: var(--prism-sidebar-width) !important;
  min-width: 10vw !important;
  max-width: 30vw !important;
  height: 100dvh !important;
  overflow-x: hidden !important;
  overflow-y: auto !important;
  scrollbar-width: thin;
  scrollbar-color: #9aa6b4 transparent;
  border-right: 1px solid var(--prism-border) !important;
  background: #eef2f6 !important;
}

#workspace-sidebar.open {
  left: 0 !important;
  transform: translateX(0) !important;
  visibility: visible !important;
  pointer-events: auto !important;
}

#workspace-sidebar:not(.open) {
  left: 0 !important;
  transform: translateX(-100%) !important;
  visibility: hidden !important;
  pointer-events: none !important;
}
#workspace-sidebar::-webkit-scrollbar { width: 7px; }
#workspace-sidebar::-webkit-scrollbar-track { background: transparent; }
#workspace-sidebar::-webkit-scrollbar-thumb {
  background: #9aa6b4;
  border: 2px solid transparent;
  border-radius: 8px;
  background-clip: padding-box;
}
#workspace-sidebar > .wrap { width: 100%; padding: 14px 14px 22px !important; }
#workspace-sidebar .wrap { gap: 9px !important; }
#workspace-sidebar .form { width: 100%; gap: 10px !important; margin-inline: auto; }
#workspace-sidebar .block { width: 100%; margin-inline: auto; }
#workspace-sidebar label > span { text-align: left; }

#workspace-sidebar .sidebar-url-field textarea {
  field-sizing: content;
  min-height: 76px !important;
  max-height: none !important;
  height: auto !important;
  overflow-y: hidden !important;
  overflow-wrap: anywhere !important;
  word-break: break-all !important;
  white-space: pre-wrap !important;
  resize: vertical;
}
.sidebar-status {
  color: var(--prism-muted);
  font-size: 13px;
  text-align: center;
}

.sidebar-status p { text-align: center; }

#workspace-sidebar-toggle {
  position: fixed !important;
  z-index: 2147483647 !important;
  top: 12px !important;
  left: 12px !important;
  width: 36px !important;
  min-width: 36px !important;
  height: 36px !important;
  min-height: 36px !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 1px solid var(--prism-border) !important;
  border-radius: 6px !important;
  background: var(--prism-surface) !important;
  color: var(--prism-text) !important;
  box-shadow: 0 1px 3px rgba(23, 32, 51, 0.12) !important;
  font-size: 0 !important;
  line-height: 1 !important;
  pointer-events: auto !important;
  transition: left 180ms ease, border-color 120ms ease;
}

#workspace-sidebar-toggle::before {
  content: "›";
  font-size: 26px;
  font-weight: 500;
  line-height: 1;
}

body:has(#workspace-sidebar.open) #workspace-sidebar-toggle {
  left: calc(var(--prism-sidebar-width) + 8px) !important;
}

body:has(#workspace-sidebar.open) #workspace-sidebar-toggle::before {
  content: "‹";
}

#workspace-sidebar-toggle:hover,
#workspace-sidebar-toggle:focus-visible {
  border-color: var(--prism-blue) !important;
}

#workspace-resizer {
  position: absolute;
  z-index: 50;
  top: 0;
  right: -6px;
  width: 12px;
  height: 100%;
  cursor: col-resize;
  touch-action: none;
  outline: none;
}

#workspace-resizer::after {
  content: "";
  position: absolute;
  top: 18%;
  bottom: 18%;
  left: 5px;
  width: 2px;
  border-radius: 2px;
  background: transparent;
}

#workspace-resizer:hover::after,
#workspace-resizer:focus-visible::after,
#workspace-resizer[data-dragging="true"]::after { background: var(--prism-blue); }

#workspace-header {
  position: relative;
  box-sizing: border-box;
  flex: 0 0 var(--prism-header-height) !important;
  width: 100%;
  height: var(--prism-header-height) !important;
  min-height: var(--prism-header-height) !important;
  max-height: var(--prism-header-height) !important;
  margin: 0;
  padding: 0;
  gap: 0 !important;
  background: var(--prism-bg);
  border: 0;
}

#workspace-topbar {
  box-sizing: border-box;
  flex: 0 0 var(--prism-topbar-height) !important;
  width: 100%;
  height: var(--prism-topbar-height) !important;
  min-height: var(--prism-topbar-height) !important;
  max-height: var(--prism-topbar-height) !important;
  margin: 0;
  padding: 0 5%;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: nowrap;
  background: var(--prism-bg);
  border: 0;
}

#workspace-brand {
  position: relative;
  box-sizing: border-box;
  container-type: inline-size;
  flex: 0 0 var(--prism-brand-content-height) !important;
  width: 100%;
  height: var(--prism-brand-content-height) !important;
  min-height: var(--prism-brand-content-height) !important;
  max-height: var(--prism-brand-content-height) !important;
  margin: 0;
  padding: clamp(6px, 0.6dvh, 10px) 5%;
  align-items: center;
  justify-content: center;
  background: var(--prism-bg);
  border: 0;
  gap: 3px !important;
}

#language-switch {
  position: relative !important;
  z-index: 60;
  top: auto;
  right: auto;
  flex: 0 0 112px !important;
  width: 112px !important;
  min-width: 112px !important;
  height: 36px !important;
  min-height: 36px !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 0 !important;
  overflow: hidden !important;
  overscroll-behavior: none;
  scrollbar-width: none;
  border: 1px solid #b9c8dc !important;
  border-radius: 20px !important;
  background: #e8eef8 !important;
  box-shadow: none !important;
  cursor: pointer;
}

#prismke-workspace:not(.i18n-ready) { visibility: hidden; }

#language-switch::before {
  content: "";
  position: absolute;
  z-index: 1;
  top: 2px;
  left: 2px;
  width: 53px;
  height: 30px;
  border-radius: 17px;
  background: #ffffff;
  box-shadow: 0 1px 4px rgba(23, 32, 51, 0.22);
  transition: transform 180ms ease;
  pointer-events: none;
}

#language-switch:has(input:checked)::before { transform: translateX(54px); }

#language-switch::after {
  content: "EN\00a0\00a0\00a0\00a0\00a0\00a0\00a0 CH";
  position: absolute;
  z-index: 2;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--prism-blue);
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0;
  pointer-events: none;
}

#language-switch .wrap,
#language-switch label {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  min-width: 0 !important;
  min-height: 0 !important;
  max-width: 100% !important;
  max-height: 100% !important;
  box-sizing: border-box !important;
  line-height: 0 !important;
  overflow: hidden !important;
  overscroll-behavior: none;
  scrollbar-width: none;
  cursor: pointer !important;
}

#language-switch::-webkit-scrollbar,
#language-switch .wrap::-webkit-scrollbar,
#language-switch label::-webkit-scrollbar { display: none !important; }

#language-switch input[type="checkbox"] {
  position: absolute !important;
  z-index: 4 !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  overflow: hidden !important;
  opacity: 0 !important;
  cursor: pointer !important;
}

#language-switch span { display: none !important; }

#language-switch:focus-within {
  outline: 3px solid rgba(233, 162, 26, 0.42) !important;
  outline-offset: 2px;
}

.toast-wrap,
.toast-container { top: calc(var(--prism-topbar-height) + 8px) !important; }

#workspace-logo {
  flex: 0 0 auto !important;
  width: min(
    36cqw,
    calc((var(--prism-brand-content-height) - 62px) * 3),
    620px
  ) !important;
  max-width: 90cqw !important;
  max-height: none !important;
  margin: 0 auto !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
}

#workspace-logo > div,
#workspace-logo .image-container { padding: 0 !important; }

#workspace-logo img {
  width: 100% !important;
  height: auto !important;
  max-height: none !important;
  object-fit: contain !important;
  background: transparent !important;
}

.workspace-tagline {
  margin: 0 !important;
  color: #344159;
  font-size: 14px;
  line-height: 1.4;
  text-align: center;
}

.workspace-version {
  margin: 2px 0 0 !important;
  color: var(--prism-muted);
  font-size: 12px;
  line-height: 1.2;
  text-align: center;
}

#workspace-tabs {
  box-sizing: border-box;
  flex: 1 1 auto !important;
  width: 90%;
  max-width: none;
  margin: var(--prism-brand-gap) auto 0;
  padding: clamp(14px, 2vh, 24px) 0 34px;
}

#workspace-tabs > .tab-wrapper > .tab-container[role="tablist"],
#workspace-tabs > .tab-wrapper > .overflow-menu { display: none !important; }

.workspace-page-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 18px;
  margin: 0 0 16px;
  padding: 0 0 12px;
  border-bottom: 1px solid var(--prism-border);
}

.workspace-page-header h1 {
  margin: 0;
  color: var(--prism-text);
  font-size: 24px;
  line-height: 1.25;
  letter-spacing: 0;
}

.workspace-page-header p {
  margin: 0;
  color: var(--prism-muted);
  font-size: 13px;
  text-align: right;
}

.block.workspace-metrics {
  border: 1px solid var(--prism-border) !important;
  border-left: 4px solid var(--prism-blue) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface) !important;
  padding: 10px 14px !important;
}

.block.workspace-metrics .prose.workspace-metrics {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  padding: 0 !important;
}

.schema-validation-valid {
  display: block;
  overflow-wrap: anywhere;
  color: #166534;
  font-weight: 650;
  line-height: 1.55;
}

.result-insight {
  border: 1px solid var(--prism-border) !important;
  border-left: 4px solid var(--prism-blue) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface) !important;
  padding: 12px 14px !important;
}

.candidate-preview-row {
  align-items: stretch !important;
}

.candidate-preview-row > * {
  min-width: 0 !important;
}

.browser-bridge {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  min-width: 0 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

#batch-files-table .batch-status-actions {
  align-items: center;
  display: inline-flex;
  gap: 8px;
  min-width: max-content;
}

#batch-files-table .batch-inline-review-button {
  align-items: center;
  background: var(--prism-blue, #145fe2);
  border: 1px solid var(--prism-blue, #145fe2);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-weight: 650;
  justify-content: center;
  line-height: 1.15;
  min-height: 28px;
  padding: 4px 10px;
  white-space: nowrap;
}

#batch-files-table .batch-inline-review-button:hover {
  background: #0f4fbe;
  border-color: #0f4fbe;
}

#batch-files-table .batch-inline-review-button:focus-visible {
  outline: 3px solid rgba(245, 174, 42, 0.55);
  outline-offset: 2px;
}

.result-export-panel {
  display: grid !important;
  grid-template-columns: minmax(260px, 1fr) minmax(220px, 0.45fr) minmax(280px, 0.8fr);
  align-items: end !important;
  gap: 12px !important;
  padding: 12px !important;
  border: 1px solid var(--prism-border) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface) !important;
}

.compact-action-row {
  align-items: stretch !important;
  flex-wrap: nowrap !important;
  gap: 12px !important;
}

.compact-action-fields {
  display: flex !important;
  flex: 4 1 0 !important;
  align-items: center !important;
  gap: 18px !important;
  min-width: 0 !important;
  min-height: 64px !important;
  padding: 10px 14px !important;
  border: 1px solid var(--prism-border) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface) !important;
}

.compact-action-row > button.compact-action-button {
  flex: 1 1 0 !important;
  align-self: stretch !important;
  height: auto !important;
  min-height: 64px !important;
  margin: 0 !important;
}

.compact-inline-field,
.compact-inline-field > .form {
  display: grid !important;
  grid-template-columns: max-content minmax(0, 1fr) !important;
  align-items: center !important;
  gap: 10px !important;
  width: 100% !important;
  min-width: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
}

.compact-inline-label-host {
  width: auto !important;
  min-width: max-content !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
}

.compact-inline-label {
  display: block;
  color: var(--body-text-color-subdued);
  font-size: var(--text-sm);
  line-height: 1.25;
  white-space: nowrap;
}

.compact-inline-field > .block,
.compact-inline-field > .form > .block {
  min-width: 0 !important;
  margin: 0 !important;
}

.compact-inline-checkbox,
.compact-inline-checkbox > .form {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  white-space: nowrap;
}

#build-primary-row,
#media-evidence-row,
#visual-review-evidence-row {
  align-items: stretch !important;
  flex-wrap: nowrap !important;
}

#build-primary-row > *,
#media-evidence-row > *,
#visual-review-evidence-row > * {
  min-width: 0 !important;
}

#build-input-panel,
#build-status-panel {
  align-self: stretch !important;
}

#build-status-panel {
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
}

#build-status-panel > .workspace-metrics {
  flex: 0 0 auto !important;
  height: auto !important;
  min-height: 0 !important;
}

#build-technical-detail {
  position: relative !important;
  align-self: stretch !important;
  flex: 0 0 auto !important;
  height: auto !important;
  min-height: 0 !important;
  max-height: 48px !important;
}

#build-technical-detail:has(button[aria-expanded="true"]),
#build-technical-detail:has(> button.open),
#build-technical-detail:has(details[open]),
#build-technical-detail[open] {
  display: flex !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  min-height: 0 !important;
  max-height: none !important;
}

#build-technical-detail:has(button[aria-expanded="true"]) > :last-child,
#build-technical-detail:has(> button.open) > :last-child,
#build-technical-detail:has(details[open]) > :last-child,
#build-technical-detail[open] > :last-child,
#build-run-summary {
  flex: 1 1 auto !important;
  min-height: 0 !important;
}

#media-preview,
#visual-review-preview {
  align-self: stretch !important;
  height: clamp(280px, 34dvh, 420px) !important;
  min-height: clamp(280px, 34dvh, 420px) !important;
  max-height: clamp(280px, 34dvh, 420px) !important;
}

#media-preview .image-container,
#media-preview .wrap,
#visual-review-preview .image-container,
#visual-review-preview .wrap {
  height: 100% !important;
  min-height: 0 !important;
}

#media-detail,
#visual-review-detail {
  position: relative !important;
  align-self: flex-start !important;
  display: flex !important;
  flex: 1 1 0 !important;
  flex-direction: column !important;
  width: 100% !important;
  min-width: 0 !important;
  height: auto !important;
  min-height: 0 !important;
  max-height: 48px !important;
  overflow: hidden !important;
}

#media-detail:has(> button.open),
#visual-review-detail:has(> button.open) {
  align-self: stretch !important;
  height: clamp(280px, 34dvh, 420px) !important;
  min-height: clamp(280px, 34dvh, 420px) !important;
  max-height: clamp(280px, 34dvh, 420px) !important;
}

.evidence-detail-panel .fill-detail-content,
.evidence-detail-panel .fill-detail-content > .wrap,
.evidence-detail-panel .fill-detail-content .json-container {
  flex: 1 1 auto !important;
  height: 100% !important;
  min-height: 0 !important;
}

.evidence-detail-panel .fill-detail-content .json-container {
  overflow: auto !important;
}

#build-technical-detail:has(> button.open) > [data-testid="accordion-content"],
.evidence-detail-panel:has(> button.open) > [data-testid="accordion-content"] {
  display: flex !important;
  position: absolute !important;
  inset: 40px 12px 11px !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  width: auto !important;
  height: auto !important;
  min-height: 0 !important;
  min-width: 0 !important;
  margin: 0 !important;
  overflow: auto !important;
}

#build-technical-detail:has(> button.open)
  > [data-testid="accordion-content"]
  > .column,
.evidence-detail-panel:has(> button.open)
  > [data-testid="accordion-content"]
  > .column {
  display: flex !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  align-items: stretch !important;
  width: 100% !important;
  min-height: 0 !important;
  min-width: 0 !important;
  margin: 0 !important;
}

#build-run-summary,
#media-detail-json,
#visual-review-detail-json {
  flex: 1 1 auto !important;
  width: 100% !important;
  height: auto !important;
  max-height: none !important;
  min-height: 0 !important;
  min-width: 0 !important;
  margin: 0 !important;
}

#agent-trace-table,
#agent-trace-table.table-wrap,
#agent-trace-table .table-wrap,
#agent-trace-table .virtual-table-viewport,
#agent-trace-table table {
  width: 100% !important;
  min-width: 100% !important;
}

#case-filter-row {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(150px, auto) !important;
  align-items: stretch !important;
  flex-wrap: nowrap !important;
  gap: 18px !important;
  width: 100% !important;
  min-width: 0 !important;
  min-height: 64px !important;
  padding: 10px 14px !important;
  border: 1px solid var(--prism-border) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface) !important;
}

#case-filter-row > * { min-width: 0 !important; }

#settings-outcome.block {
  height: auto !important;
  min-height: 0 !important;
  overflow: visible !important;
}

#settings-outcome .prose {
  overflow: visible !important;
  white-space: normal !important;
  overflow-wrap: anywhere;
}

.workspace-panel {
  border-top: 1px solid var(--prism-border);
  padding-top: 14px;
}

.technical-detail {
  border: 1px solid var(--prism-border) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface-muted) !important;
}

.gradio-container button,
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container .wrap {
  border-radius: var(--prism-radius) !important;
}

.gradio-container button.primary {
  background: var(--prism-blue) !important;
  border-color: var(--prism-blue) !important;
}

.gradio-container button.stop {
  background: var(--prism-danger) !important;
  border-color: var(--prism-danger) !important;
}

.gradio-container button:focus-visible,
.gradio-container input:focus-visible,
.gradio-container textarea:focus-visible {
  outline: 3px solid rgba(7, 88, 216, 0.24) !important;
  outline-offset: 1px;
}

table { font-size: 13px; }
.table-wrap { overflow-x: auto !important; }

@media (max-width: 900px) {
  #workspace-header {
    --prism-topbar-height: clamp(46px, 5dvh, 60px);
    --prism-brand-content-height: clamp(132px, 15dvh, 190px);
    --prism-header-height: calc(
      var(--prism-topbar-height) + var(--prism-brand-content-height)
    );
  }
  .gradio-container .sidebar-parent { padding-left: 0 !important; }
  #workspace-sidebar {
    width: min(320px, 88vw) !important;
    min-width: min(320px, 88vw) !important;
    max-width: min(320px, 88vw) !important;
  }
  body:has(#workspace-sidebar.open) #workspace-sidebar-toggle {
    left: calc(min(320px, 88vw) + 8px) !important;
  }
  #workspace-resizer { display: none; }
  #workspace-header,
  #workspace-topbar,
  #workspace-brand {
    width: 100%;
    margin-left: 0;
  }
  #workspace-topbar { padding: 0 18px; }
  #workspace-brand { padding: 8px 5%; }
  #language-switch {
    top: auto;
    right: auto;
  }
  #workspace-tabs { width: 90%; padding-top: 14px; }
  #workspace-tabs {
    max-width: none;
    margin: var(--prism-brand-gap) auto 0;
  }
  .workspace-page-header { align-items: flex-start; flex-direction: column; gap: 5px; }
  .workspace-page-header p { text-align: left; }
}

@media (max-width: 520px) {
  #workspace-header {
    --prism-topbar-height: 48px;
    --prism-brand-content-height: 140px;
    --prism-brand-gap: 8px;
    --prism-header-height: calc(
      var(--prism-topbar-height) + var(--prism-brand-content-height)
    );
  }
  #workspace-tabs { margin-top: 8px; }
  #workspace-topbar { padding: 0 12px; }
  #language-switch {
    top: auto;
    right: auto;
    flex-basis: 92px !important;
    width: 92px !important;
    min-width: 92px !important;
    height: 32px !important;
    min-height: 32px !important;
  }
  #language-switch::before {
    width: 43px;
    height: 26px;
  }
  #language-switch:has(input:checked)::before { transform: translateX(44px); }
  #language-switch::after {
    content: "EN\00a0\00a0\00a0\00a0\00a0 CH";
    font-size: 12px;
    line-height: 1;
  }
  #workspace-sidebar.open {
    left: 0 !important;
    transform: translateX(0) !important;
  }
  #workspace-brand {
    padding: 8px 5%;
  }
  #workspace-logo {
    width: min(62cqw, calc((var(--prism-brand-content-height) - 64px) * 3), 280px) !important;
    max-width: 62cqw !important;
    margin-top: 0 !important;
  }
  .workspace-tagline { max-width: 330px; font-size: 12px; }
  .workspace-version { font-size: 11px; }
  #workspace-tabs { width: 90%; padding-bottom: 24px; }
  .workspace-page-header h1 { font-size: 21px; }
  .compact-action-row,
  #build-primary-row,
  #media-evidence-row,
  #visual-review-evidence-row,
  #case-filter-row {
    flex-direction: column !important;
    flex-wrap: wrap !important;
  }
  .candidate-preview-row {
    flex-direction: column !important;
  }
  .result-export-panel {
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
  }
  .compact-action-fields {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 10px !important;
    min-height: 0 !important;
  }
  button.compact-action-button {
    width: 100% !important;
    height: 44px !important;
    min-height: 44px !important;
    flex: 0 0 44px !important;
  }
  .compact-inline-field,
  .compact-inline-field > .form {
    grid-template-columns: minmax(88px, max-content) minmax(0, 1fr) !important;
  }
  #media-preview,
  #visual-review-preview {
    width: 100% !important;
    height: auto !important;
    min-height: 240px !important;
    max-height: none !important;
  }
  #media-detail,
  #visual-review-detail,
  #media-detail:has(> button.open),
  #visual-review-detail:has(> button.open) {
    align-self: stretch !important;
    width: 100% !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
  }
  #case-filter-row .checkbox-container {
    align-self: stretch !important;
    flex: 1 1 auto !important;
    width: 100% !important;
  }
  #case-filter-row {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 10px !important;
    width: 100% !important;
  }
  .table-wrap {
    max-width: 100% !important;
    overflow-x: auto !important;
  }
  .table-wrap table {
    width: max-content !important;
    min-width: 100% !important;
  }
  .table-wrap th,
  .table-wrap td {
    min-width: 96px;
    white-space: nowrap !important;
    word-break: normal !important;
  }
  .table-wrap .header.text.wrap {
    white-space: nowrap !important;
    word-break: normal !important;
  }
  #agent-trace-table,
  #agent-trace-table.table-wrap,
  #agent-trace-table .table-wrap {
    max-width: 100% !important;
    overflow-x: auto !important;
  }
  #agent-trace-table table {
    width: 720px !important;
    min-width: 720px !important;
  }
  #prismke-workspace { overflow-x: hidden !important; }
}

@media (prefers-reduced-motion: reduce) {
  .gradio-container .sidebar-parent,
  #workspace-sidebar-toggle,
  #language-switch::before { transition: none; }
}
"""
