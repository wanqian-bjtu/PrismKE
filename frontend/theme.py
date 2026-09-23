"""Visual tokens and responsive CSS for the PrismKE Gradio workspace."""

APP_CSS = r"""
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
}

.gradio-container {
  background: var(--prism-bg) !important;
  color: var(--prism-text) !important;
  padding: 0 !important;
  letter-spacing: 0 !important;
}

#workspace-sidebar {
  width: 300px !important;
  border-right: 1px solid var(--prism-border) !important;
  background: #eef2f6 !important;
}

#workspace-sidebar .wrap { gap: 9px !important; }
#workspace-sidebar .form { gap: 10px !important; }
.sidebar-status { color: var(--prism-muted); font-size: 13px; }

#workspace-brand {
  box-sizing: border-box;
  width: 100%;
  min-height: 142px;
  margin: 0;
  padding: 18px 28px 14px;
  align-items: center;
  justify-content: center;
  background: var(--prism-surface);
  border-bottom: 1px solid var(--prism-border);
  gap: 3px !important;
}

#workspace-logo {
  width: min(360px, 62vw) !important;
  max-height: 108px !important;
  margin: 0 auto !important;
  background: transparent !important;
}

#workspace-logo img {
  width: 100% !important;
  height: auto !important;
  max-height: 108px !important;
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
  width: min(1500px, calc(100% - 40px));
  margin: 0 auto;
  padding: 18px 0 34px;
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

.workspace-metrics {
  border: 1px solid var(--prism-border) !important;
  border-left: 4px solid var(--prism-blue) !important;
  border-radius: var(--prism-radius) !important;
  background: var(--prism-surface) !important;
  padding: 10px 14px !important;
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

.gradio-container table { font-size: 13px; }
.gradio-container .table-wrap { overflow-x: auto !important; }

@media (max-width: 900px) {
  #workspace-sidebar { width: min(320px, 88vw) !important; }
  #workspace-brand { min-height: 128px; padding: 14px 18px 12px; }
  #workspace-tabs { width: calc(100% - 24px); padding-top: 14px; }
  .workspace-page-header { align-items: flex-start; flex-direction: column; gap: 5px; }
  .workspace-page-header p { text-align: left; }
}

@media (max-width: 520px) {
  #workspace-sidebar:not(.open) {
    left: calc(12px - min(320px, 88vw)) !important;
  }
  #workspace-brand { min-height: 118px; padding: 12px 12px 10px; }
  #workspace-logo { width: min(250px, 78vw) !important; max-height: 84px !important; }
  #workspace-logo img { max-height: 84px !important; }
  .workspace-tagline { max-width: 330px; font-size: 12px; }
  .workspace-version { font-size: 11px; }
  #workspace-tabs { width: calc(100% - 16px); padding-bottom: 24px; }
  .workspace-page-header h1 { font-size: 21px; }
  .gradio-container { overflow-x: hidden !important; }
}
"""
