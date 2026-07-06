import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  FileText,
  FolderSync,
  Inbox,
  KeyRound,
  Languages,
  Mail,
  Play,
  RefreshCcw,
  Save,
  Settings2,
  Trash2,
  Upload,
  UserRound
} from "lucide-react";
import "./styles.css";

const STORAGE_KEY = "incomingInvoiceWorkerSecret";
const LANGUAGE_KEY = "incomingInvoiceLanguage";
const DEFAULT_MAPPING = {
  companyCodes: {
    "2222222222": ""
  },
  currency: "TRY",
  documentType: "",
  postingMode: "",
  defaultGlAccount: "",
  defaultCostCenter: "",
  defaultPaymentTerms: "",
  taxCodes: {
    "20": ""
  },
  suppliers: {
    "1111111111": {
      name: "EXAMPLE SUPPLIER",
      sapSupplierId: "",
      glAccount: "",
      costCenter: "",
      taxCode: "",
      paymentTerms: ""
    }
  }
};
const DEFAULT_SETTINGS = {
  graphTenantId: "",
  graphClientId: "",
  graphClientSecret: "",
  graphClientSecretConfigured: false,
  graphMailbox: "",
  graphSourceFolder: "Inbox",
  graphProcessedFolder: "Processed",
  graphManualFolder: "Manual",
  graphErrorFolder: "Error",
  graphMaxMessages: 10,
  graphSubjectKeywords: "e-Fatura,e-Arsiv,Fatura",
  mailPollerEnabled: true,
  mailPollIntervalSeconds: 300,
  sapMode: "dry-run",
  sapBaseUrl: "",
  sapAuthUrl: "",
  sapClientId: "",
  sapClientSecret: "",
  sapClientSecretConfigured: false,
  sapPostingUser: ""
};
const UI_TEXT = {
  en: {
    language: "Language",
    appTitle: "Invoice Automation",
    subline: "SAP S/4HANA Cloud Public Edition",
    workerSecret: "Worker secret",
    saveSecretTitle: "Save secret",
    secretSaved: "Secret saved.",
    appSummary: "Application summary",
    eyebrow: "Incoming invoice automation",
    headline: "Create SAP supplier invoices from mailbox",
    mailboxNotSelected: "Mailbox not selected",
    active: "Active",
    off: "Off",
    mainView: "Main view",
    settings: "Settings",
    logs: "Logs",
    pdfTest: "PDF Test",
    jobs: "Jobs",
    mapping: "Mapping",
    load: "Load",
    save: "Save",
    refresh: "Refresh",
    clear: "Clear",
    mailReading: "Mail Reading",
    graphMailbox: "Mailbox to read",
    graphSourceFolder: "Source folder",
    graphProcessedFolder: "Processed folder",
    graphManualFolder: "Manual folder",
    graphErrorFolder: "Error folder",
    graphSubjectKeywords: "Subject filters",
    graphMaxMessages: "Mails per run",
    mailPollIntervalSeconds: "Poll seconds",
    mailPollerEnabled: "Automatic poller",
    microsoftGraph: "Microsoft Graph",
    graphTenantId: "Tenant ID",
    graphClientId: "Client ID",
    graphClientSecret: "Client secret",
    sapPosting: "SAP Posting",
    sapMode: "SAP mode",
    sapPostingUser: "Posting user",
    sapBaseUrl: "SAP base URL",
    sapAuthUrl: "SAP auth URL",
    sapClientId: "SAP comm. user",
    sapClientSecret: "SAP comm. password",
    pdfNotSelected: "PDF was not selected.",
    invoicesRead: "{count} invoice(s) read.",
    parse: "Parse",
    processDone: "Process completed.",
    processInbox: "Process Inbox",
    retryManual: "Retry Manual",
    lastRun: "Last Run",
    mappingJson: "Mapping JSON",
    mappingJsonAria: "Mapping JSON",
    mappingLoaded: "Mapping loaded.",
    mappingSaved: "Mapping saved.",
    jsonError: "JSON error: {message}",
    settingsLoaded: "Settings loaded.",
    settingsSaved: "Settings saved.",
    logType: "Log type",
    readMails: "Read Mails",
    sapRecords: "SAP Records",
    logsTitle: "Logs",
    logDeleted: "{count} log(s) deleted.",
    timestamp: "Time",
    mailbox: "Mailbox",
    subject: "Subject",
    sender: "Sender",
    folder: "Folder",
    pdf: "PDF",
    invoice: "Invoice",
    supplier: "Supplier",
    amount: "Amount",
    status: "Status",
    user: "User",
    missingMapping: "Missing Mapping",
    noRecords: "No records",
    invoiceMetric: "Invoice",
    validation: "Validation",
    passed: "Passed",
    review: "Review",
    invoices: "Invoices",
    number: "No",
    supplierTaxId: "TCKN/VKN",
    set: "set",
    readOnly: "Read-only"
  },
  tr: {
    language: "Dil",
    appTitle: "Fatura Otomasyonu",
    subline: "SAP S/4HANA Cloud Public Edition",
    workerSecret: "Worker secret",
    saveSecretTitle: "Secret kaydet",
    secretSaved: "Secret kaydedildi.",
    appSummary: "Uygulama ozeti",
    eyebrow: "Gelen fatura otomatik kayit",
    headline: "Mailden SAP tedarikci faturasi olusturma",
    mailboxNotSelected: "Mailbox secilmedi",
    active: "Aktif",
    off: "Kapali",
    mainView: "Ana gorunum",
    settings: "Ayarlar",
    logs: "Loglar",
    pdfTest: "PDF Test",
    jobs: "Isler",
    mapping: "Mapping",
    load: "Yukle",
    save: "Kaydet",
    refresh: "Yenile",
    clear: "Temizle",
    mailReading: "Mail Okuma",
    graphMailbox: "Okunacak mailbox",
    graphSourceFolder: "Okunacak klasor",
    graphProcessedFolder: "Processed klasoru",
    graphManualFolder: "Manual klasoru",
    graphErrorFolder: "Error klasoru",
    graphSubjectKeywords: "Konu filtreleri",
    graphMaxMessages: "Run basina mail",
    mailPollIntervalSeconds: "Poll saniye",
    mailPollerEnabled: "Otomatik poller",
    microsoftGraph: "Microsoft Graph",
    graphTenantId: "Tenant ID",
    graphClientId: "Client ID",
    graphClientSecret: "Client secret",
    sapPosting: "SAP Kayit",
    sapMode: "SAP mode",
    sapPostingUser: "Kayit kullanicisi",
    sapBaseUrl: "SAP base URL",
    sapAuthUrl: "SAP auth URL",
    sapClientId: "SAP comm. user",
    sapClientSecret: "SAP comm. password",
    pdfNotSelected: "PDF secilmedi.",
    invoicesRead: "{count} fatura okundu.",
    parse: "Parse Et",
    processDone: "Islem tamamlandi.",
    processInbox: "Inbox Isle",
    retryManual: "Manual Tekrar",
    lastRun: "Son Islem",
    mappingJson: "Mapping JSON",
    mappingJsonAria: "Mapping JSON",
    mappingLoaded: "Mapping yuklendi.",
    mappingSaved: "Mapping kaydedildi.",
    jsonError: "JSON hatasi: {message}",
    settingsLoaded: "Ayarlar yuklendi.",
    settingsSaved: "Ayarlar kaydedildi.",
    logType: "Log tipi",
    readMails: "Okunan Mailler",
    sapRecords: "SAP Kayitlari",
    logsTitle: "Loglar",
    logDeleted: "{count} log silindi.",
    timestamp: "Zaman",
    mailbox: "Mailbox",
    subject: "Konu",
    sender: "Gonderen",
    folder: "Klasor",
    pdf: "PDF",
    invoice: "Fatura",
    supplier: "Tedarikci",
    amount: "Tutar",
    status: "Durum",
    user: "Kullanici",
    missingMapping: "Eksik Mapping",
    noRecords: "Kayit yok",
    invoiceMetric: "Fatura",
    validation: "Validasyon",
    passed: "Gecti",
    review: "Kontrol",
    invoices: "Faturalar",
    number: "No",
    supplierTaxId: "TCKN/VKN",
    set: "set",
    readOnly: "Read-only"
  }
};

function formatText(template, values = {}) {
  return template.replace(/\{(\w+)\}/g, (_, key) => values[key] ?? "");
}

function App() {
  const [secret, setSecret] = useState(() => sessionStorage.getItem(STORAGE_KEY) || "");
  const [language, setLanguage] = useState(() => localStorage.getItem(LANGUAGE_KEY) || "en");
  const [health, setHealth] = useState({ status: "checking" });
  const [activeTab, setActiveTab] = useState("settings");
  const [file, setFile] = useState(null);
  const [extractResult, setExtractResult] = useState(null);
  const [jobResult, setJobResult] = useState(null);
  const [mappingText, setMappingText] = useState(JSON.stringify(DEFAULT_MAPPING, null, 2));
  const [mappingMeta, setMappingMeta] = useState(null);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [settingsMeta, setSettingsMeta] = useState(null);
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [logType, setLogType] = useState("mail_read");
  const [logs, setLogs] = useState([]);
  const [logMeta, setLogMeta] = useState(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState(null);
  const text = UI_TEXT[language] || UI_TEXT.en;
  const t = (key) => text[key] || UI_TEXT.en[key] || key;

  useEffect(() => {
    fetch("/health")
      .then((response) => response.json())
      .then(setHealth)
      .catch((error) => setHealth({ status: "error", error: error.message }));
  }, []);

  useEffect(() => {
    localStorage.setItem(LANGUAGE_KEY, language);
  }, [language]);

  useEffect(() => {
    if (!secret) return;
    if (activeTab === "settings" && !settingsLoaded) {
      loadSettings();
    }
    if (activeTab === "logs") {
      loadLogs(logType);
    }
  }, [activeTab, logType, secret, settingsLoaded]);

  const authHeaders = useMemo(
    () => ({
      Authorization: `Bearer ${secret}`
    }),
    [secret]
  );

  function saveSecret() {
    sessionStorage.setItem(STORAGE_KEY, secret);
    setSettingsLoaded(false);
    setNotice({ type: "ok", text: t("secretSaved") });
  }

  async function callJson(path, options = {}) {
    setBusy(path);
    setNotice(null);
    try {
      const response = await fetch(path, {
        ...options,
        headers: {
          ...(options.headers || {}),
          ...authHeaders
        }
      });
      const text = await response.text();
      const payload = text ? JSON.parse(text) : {};
      if (!response.ok) {
        throw new Error(payload.error || response.statusText);
      }
      return payload;
    } finally {
      setBusy("");
    }
  }

  async function extractPdf() {
    if (!file) {
      setNotice({ type: "warn", text: t("pdfNotSelected") });
      return;
    }
    const body = new FormData();
    body.append("file", file);
    try {
      const result = await callJson("/api/extract", { method: "POST", body });
      setExtractResult(result);
      setNotice({ type: "ok", text: formatText(t("invoicesRead"), { count: result.invoiceCount || 0 }) });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function runJob(path) {
    try {
      const result = await callJson(path, { method: "POST" });
      setJobResult(result);
      setNotice({ type: "ok", text: t("processDone") });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function loadMapping() {
    try {
      const result = await callJson("/api/mapping");
      setMappingMeta(result);
      setMappingText(JSON.stringify(result.data || {}, null, 2));
      setNotice({ type: "ok", text: t("mappingLoaded") });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function saveMapping() {
    let parsed;
    try {
      parsed = JSON.parse(mappingText);
    } catch (error) {
      setNotice({ type: "error", text: formatText(t("jsonError"), { message: error.message }) });
      return;
    }
    try {
      const result = await callJson("/api/mapping", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed)
      });
      setMappingMeta(result);
      setNotice({ type: "ok", text: t("mappingSaved") });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function loadSettings() {
    try {
      const result = await callJson("/api/settings");
      setSettings({ ...DEFAULT_SETTINGS, ...(result.data || {}) });
      setSettingsMeta(result);
      setSettingsLoaded(true);
      setNotice({ type: "ok", text: t("settingsLoaded") });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function saveSettings() {
    try {
      const result = await callJson("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      setSettings({ ...DEFAULT_SETTINGS, ...(result.data || {}) });
      setSettingsMeta(result);
      setSettingsLoaded(true);
      setNotice({ type: "ok", text: t("settingsSaved") });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  function updateSetting(key, value) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  async function loadLogs(type = logType) {
    try {
      const result = await callJson(`/api/logs?type=${encodeURIComponent(type)}&limit=200`);
      setLogs(result.items || []);
      setLogMeta(result);
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function clearLogs() {
    try {
      const result = await callJson(`/api/logs?type=${encodeURIComponent(logType)}`, { method: "DELETE" });
      setLogs([]);
      setNotice({ type: "ok", text: formatText(t("logDeleted"), { count: result.deleted || 0 }) });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  const activeMailbox = settings.graphMailbox || t("mailboxNotSelected");
  const pollerState = settings.mailPollerEnabled ? t("active") : t("off");
  const sapState = settings.sapMode || "dry-run";

  return (
    <main className="shell">
      <header className="topbar" role="banner">
        <div className="brand">
          <FileText size={28} aria-hidden="true" />
          <div>
            <h1>{t("appTitle")}</h1>
            <span className="subline">{t("subline")}</span>
          </div>
        </div>
        <div className="statusStrip">
          <LanguageSwitch language={language} setLanguage={setLanguage} label={t("language")} />
          <StatusChip health={health} />
          <div className="secretBox">
            <KeyRound size={16} aria-hidden="true" />
            <input
              type="password"
              value={secret}
              onChange={(event) => setSecret(event.target.value)}
              placeholder={t("workerSecret")}
              aria-label={t("workerSecret")}
            />
            <button type="button" className="iconButton" onClick={saveSecret} title={t("saveSecretTitle")}>
              <Save size={17} aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      <section className="objectHeader" aria-label={t("appSummary")}>
        <div>
          <span className="eyebrow">{t("eyebrow")}</span>
          <h2>{t("headline")}</h2>
        </div>
        <div className="objectFacts">
          <ObjectFact label="Mailbox" value={activeMailbox} />
          <ObjectFact label="Poller" value={pollerState} tone={settings.mailPollerEnabled ? "positive" : "critical"} />
          <ObjectFact label="SAP Mode" value={sapState} />
        </div>
      </section>

      <section className="tabs" aria-label={t("mainView")}>
        <TabButton active={activeTab === "settings"} onClick={() => setActiveTab("settings")} icon={<Settings2 size={16} />} label={t("settings")} />
        <TabButton active={activeTab === "logs"} onClick={() => setActiveTab("logs")} icon={<ClipboardList size={16} />} label={t("logs")} />
        <TabButton active={activeTab === "pdf"} onClick={() => setActiveTab("pdf")} icon={<Upload size={16} />} label={t("pdfTest")} />
        <TabButton active={activeTab === "jobs"} onClick={() => setActiveTab("jobs")} icon={<Activity size={16} />} label={t("jobs")} />
        <TabButton active={activeTab === "mapping"} onClick={() => setActiveTab("mapping")} icon={<FolderSync size={16} />} label={t("mapping")} />
      </section>

      {notice && <Notice notice={notice} />}

      {activeTab === "settings" && (
        <SettingsView
          settings={settings}
          settingsMeta={settingsMeta}
          updateSetting={updateSetting}
          loadSettings={loadSettings}
          saveSettings={saveSettings}
          busy={busy}
          t={t}
        />
      )}

      {activeTab === "logs" && (
        <LogsView
          logType={logType}
          setLogType={setLogType}
          logs={logs}
          logMeta={logMeta}
          loadLogs={loadLogs}
          clearLogs={clearLogs}
          busy={busy}
          t={t}
        />
      )}

      {activeTab === "pdf" && (
        <section className="grid two">
          <div className="panel">
            <PanelTitle icon={<Upload size={18} />} title={t("pdfTest")} />
            <div className="fileRow">
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
              <button type="button" onClick={extractPdf} disabled={busy === "/api/extract"}>
                <Play size={17} aria-hidden="true" />
                {t("parse")}
              </button>
            </div>
            <Summary result={extractResult} t={t} />
          </div>
          <InvoiceTable result={extractResult} t={t} />
        </section>
      )}

      {activeTab === "jobs" && (
        <section className="grid two">
          <div className="panel">
            <PanelTitle icon={<Inbox size={18} />} title={t("jobs")} />
            <div className="actionGrid">
              <button type="button" onClick={() => runJob("/jobs/process-mail")} disabled={busy === "/jobs/process-mail"}>
                <Inbox size={17} aria-hidden="true" />
                {t("processInbox")}
              </button>
              <button type="button" onClick={() => runJob("/jobs/process-manual")} disabled={busy === "/jobs/process-manual"}>
                <RefreshCcw size={17} aria-hidden="true" />
                {t("retryManual")}
              </button>
            </div>
            <JobSummary result={jobResult} t={t} />
          </div>
          <JsonPanel title={t("lastRun")} value={jobResult} />
        </section>
      )}

      {activeTab === "mapping" && (
        <section className="grid mappingGrid">
          <div className="panel">
            <PanelTitle icon={<FolderSync size={18} />} title={t("mappingJson")} />
            <div className="toolbar">
              <button type="button" onClick={loadMapping} disabled={busy === "/api/mapping"}>
                <RefreshCcw size={17} aria-hidden="true" />
                {t("load")}
              </button>
              <button type="button" onClick={saveMapping} disabled={busy === "/api/mapping" || mappingMeta?.readOnly}>
                <Save size={17} aria-hidden="true" />
                {t("save")}
              </button>
            </div>
            {mappingMeta && (
              <div className="metaLine">
                <span>{mappingMeta.source}</span>
                {mappingMeta.readOnly && <strong>{t("readOnly")}</strong>}
              </div>
            )}
            <textarea
              value={mappingText}
              onChange={(event) => setMappingText(event.target.value)}
              spellCheck="false"
              aria-label={t("mappingJsonAria")}
            />
          </div>
        </section>
      )}
    </main>
  );
}

function TabButton({ active, onClick, icon, label }) {
  return (
    <button className={active ? "active" : ""} onClick={onClick}>
      {icon}
      {label}
    </button>
  );
}

function LanguageSwitch({ language, setLanguage, label }) {
  return (
    <div className="languageSwitch" aria-label={label}>
      <Languages size={16} aria-hidden="true" />
      <button type="button" className={language === "en" ? "active" : ""} onClick={() => setLanguage("en")}>
        EN
      </button>
      <button type="button" className={language === "tr" ? "active" : ""} onClick={() => setLanguage("tr")}>
        TR
      </button>
    </div>
  );
}

function ObjectFact({ label, value, tone = "" }) {
  return (
    <div className={`objectFact ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SettingsView({ settings, settingsMeta, updateSetting, loadSettings, saveSettings, busy, t }) {
  return (
    <section className="grid settingsGrid">
      <div className="panel">
        <PanelTitle icon={<Mail size={18} />} title={t("mailReading")} />
        <div className="toolbar">
          <button type="button" onClick={loadSettings} disabled={busy === "/api/settings"}>
            <RefreshCcw size={17} aria-hidden="true" />
            {t("load")}
          </button>
          <button type="button" onClick={saveSettings} disabled={busy === "/api/settings"}>
            <Save size={17} aria-hidden="true" />
            {t("save")}
          </button>
        </div>
        {settingsMeta && <div className="metaLine"><span>{settingsMeta.source}</span></div>}
        <div className="formGrid">
          <TextField label={t("graphMailbox")} value={settings.graphMailbox} onChange={(value) => updateSetting("graphMailbox", value)} />
          <TextField label={t("graphSourceFolder")} value={settings.graphSourceFolder} onChange={(value) => updateSetting("graphSourceFolder", value)} />
          <TextField label={t("graphProcessedFolder")} value={settings.graphProcessedFolder} onChange={(value) => updateSetting("graphProcessedFolder", value)} />
          <TextField label={t("graphManualFolder")} value={settings.graphManualFolder} onChange={(value) => updateSetting("graphManualFolder", value)} />
          <TextField label={t("graphErrorFolder")} value={settings.graphErrorFolder} onChange={(value) => updateSetting("graphErrorFolder", value)} />
          <TextField label={t("graphSubjectKeywords")} value={settings.graphSubjectKeywords} onChange={(value) => updateSetting("graphSubjectKeywords", value)} />
          <NumberField label={t("graphMaxMessages")} value={settings.graphMaxMessages} min="1" onChange={(value) => updateSetting("graphMaxMessages", value)} />
          <NumberField label={t("mailPollIntervalSeconds")} value={settings.mailPollIntervalSeconds} min="30" onChange={(value) => updateSetting("mailPollIntervalSeconds", value)} />
          <ToggleField label={t("mailPollerEnabled")} checked={settings.mailPollerEnabled} onChange={(value) => updateSetting("mailPollerEnabled", value)} />
        </div>
      </div>

      <div className="panel">
        <PanelTitle icon={<KeyRound size={18} />} title={t("microsoftGraph")} />
        <div className="formGrid single">
          <TextField label={t("graphTenantId")} value={settings.graphTenantId} onChange={(value) => updateSetting("graphTenantId", value)} />
          <TextField label={t("graphClientId")} value={settings.graphClientId} onChange={(value) => updateSetting("graphClientId", value)} />
          <SecretField
            label={t("graphClientSecret")}
            value={settings.graphClientSecret}
            configured={settings.graphClientSecretConfigured}
            onChange={(value) => updateSetting("graphClientSecret", value)}
            setLabel={t("set")}
          />
        </div>
      </div>

      <div className="panel">
        <PanelTitle icon={<UserRound size={18} />} title={t("sapPosting")} />
        <div className="formGrid single">
          <TextField label={t("sapMode")} value={settings.sapMode} onChange={(value) => updateSetting("sapMode", value)} />
          <TextField label={t("sapPostingUser")} value={settings.sapPostingUser} onChange={(value) => updateSetting("sapPostingUser", value)} />
          <TextField label={t("sapBaseUrl")} value={settings.sapBaseUrl} onChange={(value) => updateSetting("sapBaseUrl", value)} />
          <TextField label={t("sapAuthUrl")} value={settings.sapAuthUrl} onChange={(value) => updateSetting("sapAuthUrl", value)} />
          <TextField label={t("sapClientId")} value={settings.sapClientId} onChange={(value) => updateSetting("sapClientId", value)} />
          <SecretField
            label={t("sapClientSecret")}
            value={settings.sapClientSecret}
            configured={settings.sapClientSecretConfigured}
            onChange={(value) => updateSetting("sapClientSecret", value)}
            setLabel={t("set")}
          />
        </div>
      </div>
    </section>
  );
}

function LogsView({ logType, setLogType, logs, logMeta, loadLogs, clearLogs, busy, t }) {
  return (
    <section className="grid mappingGrid">
      <div className="panel">
        <PanelTitle icon={<ClipboardList size={18} />} title={t("logsTitle")} />
        <div className="toolbar splitToolbar">
          <div className="segmented" aria-label={t("logType")}>
            <button type="button" className={logType === "mail_read" ? "active" : ""} onClick={() => setLogType("mail_read")}>
              <Mail size={16} aria-hidden="true" />
              {t("readMails")}
            </button>
            <button type="button" className={logType === "sap_record" ? "active" : ""} onClick={() => setLogType("sap_record")}>
              <UserRound size={16} aria-hidden="true" />
              {t("sapRecords")}
            </button>
          </div>
          <div className="toolbar">
            <button type="button" onClick={() => loadLogs(logType)} disabled={busy.startsWith("/api/logs")}>
              <RefreshCcw size={17} aria-hidden="true" />
              {t("refresh")}
            </button>
            <button type="button" className="dangerButton" onClick={clearLogs} disabled={busy.startsWith("/api/logs")}>
              <Trash2 size={17} aria-hidden="true" />
              {t("clear")}
            </button>
          </div>
        </div>
        {logMeta && <div className="metaLine"><span>{logMeta.source} / {logMeta.type}</span></div>}
        <LogTable type={logType} logs={logs} t={t} />
      </div>
    </section>
  );
}

function TextField({ label, value, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function NumberField({ label, value, min, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type="number" min={min} value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function SecretField({ label, value, configured, onChange, setLabel }) {
  return (
    <label className="field">
      <span>
        {label}
        {configured && <strong className="configuredBadge">{setLabel}</strong>}
      </span>
      <input type="password" value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function ToggleField({ label, checked, onChange }) {
  return (
    <label className="toggleField">
      <input type="checkbox" checked={Boolean(checked)} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function LogTable({ type, logs, t }) {
  const isMail = type === "mail_read";
  return (
    <div className="tableWrap">
      <table className="logTable">
        <thead>
          <tr>
            <th>{t("timestamp")}</th>
            {isMail ? (
              <>
                <th>{t("mailbox")}</th>
                <th>{t("subject")}</th>
                <th>{t("sender")}</th>
                <th>{t("folder")}</th>
                <th>{t("pdf")}</th>
              </>
            ) : (
              <>
                <th>{t("invoice")}</th>
                <th>{t("supplier")}</th>
                <th>{t("amount")}</th>
                <th>{t("status")}</th>
                <th>{t("user")}</th>
                <th>{t("missingMapping")}</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {logs.length === 0 && (
            <tr>
              <td colSpan={isMail ? 6 : 7} className="emptyCell">{t("noRecords")}</td>
            </tr>
          )}
          {logs.map((item) => (
            <tr key={item.id}>
              <td>{formatDate(item.timestamp)}</td>
              {isMail ? (
                <>
                  <td>{item.mailbox}</td>
                  <td>{item.subject}</td>
                  <td>{item.sender}</td>
                  <td>{item.sourceFolder} {"->"} {item.destinationFolder}</td>
                  <td>{item.pdfAttachmentCount}</td>
                </>
              ) : (
                <>
                  <td>{item.invoiceNo}</td>
                  <td>{item.sellerName || item.sellerTaxId}</td>
                  <td>{item.payableTotal} {item.currency}</td>
                  <td><span className={item.status === "processed" ? "pill ok" : "pill warn"}>{item.status}</span></td>
                  <td>{item.postingUser}</td>
                  <td>{(item.missingMappings || []).join(", ")}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function StatusChip({ health }) {
  const ok = health.status === "ok";
  return (
    <div className={`statusChip ${ok ? "ok" : "warn"}`}>
      {ok ? <CheckCircle2 size={16} aria-hidden="true" /> : <AlertTriangle size={16} aria-hidden="true" />}
      <span>{ok ? `OK ${health.version}` : health.status}</span>
    </div>
  );
}

function PanelTitle({ icon, title }) {
  return (
    <div className="panelTitle">
      {icon}
      <h2>{title}</h2>
    </div>
  );
}

function Notice({ notice }) {
  return <div className={`notice ${notice.type}`}>{notice.text}</div>;
}

function Summary({ result, t }) {
  if (!result) return null;
  return (
    <div className="summaryGrid">
      <Metric label={t("invoiceMetric")} value={result.invoiceCount ?? 0} />
      <Metric label={t("validation")} value={result.validationPassed ? t("passed") : t("review")} />
      <Metric label="XML" value={result.embeddedXmlFiles?.length ?? 0} />
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function InvoiceTable({ result, t }) {
  const invoices = result?.invoices || [];
  return (
    <div className="panel tablePanel">
      <PanelTitle icon={<FileText size={18} />} title={t("invoices")} />
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>{t("number")}</th>
              <th>{t("supplier")}</th>
              <th>{t("supplierTaxId")}</th>
              <th>{t("amount")}</th>
              <th>{t("status")}</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 && (
              <tr>
                <td colSpan="5" className="emptyCell">{t("noRecords")}</td>
              </tr>
            )}
            {invoices.map((invoice) => (
              <tr key={`${invoice.invoiceNo}-${invoice.ettn}`}>
                <td>{invoice.invoiceNo}</td>
                <td>{invoice.sellerName}</td>
                <td>{invoice.sellerTaxId}</td>
                <td>{invoice.payableTotal} {invoice.currency}</td>
                <td>
                  <span className={invoice.validationPassed ? "pill ok" : "pill warn"}>
                    {invoice.validationPassed ? "OK" : t("review")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function JobSummary({ result, t }) {
  if (!result) return null;
  const attachments = result.processed?.flatMap((item) => item.attachments || []) || [];
  const manualCount = attachments.filter((item) => item.status === "manual").length;
  const processedCount = attachments.filter((item) => item.status === "processed").length;
  const errorCount = attachments.filter((item) => item.status === "error").length;
  return (
    <div className="summaryGrid">
      <Metric label="Mail" value={result.messageCount ?? 0} />
      <Metric label="Processed" value={processedCount} />
      <Metric label="Manual" value={manualCount} />
      <Metric label="Error" value={errorCount} />
    </div>
  );
}

function JsonPanel({ title, value }) {
  return (
    <div className="panel jsonPanel">
      <PanelTitle icon={<FileText size={18} />} title={title} />
      <pre>{value ? JSON.stringify(value, null, 2) : "{}"}</pre>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
