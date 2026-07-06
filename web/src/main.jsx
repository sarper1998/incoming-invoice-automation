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

function App() {
  const [secret, setSecret] = useState(() => sessionStorage.getItem(STORAGE_KEY) || "");
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

  useEffect(() => {
    fetch("/health")
      .then((response) => response.json())
      .then(setHealth)
      .catch((error) => setHealth({ status: "error", error: error.message }));
  }, []);

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
    setNotice({ type: "ok", text: "Secret kaydedildi." });
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
      setNotice({ type: "warn", text: "PDF secilmedi." });
      return;
    }
    const body = new FormData();
    body.append("file", file);
    try {
      const result = await callJson("/api/extract", { method: "POST", body });
      setExtractResult(result);
      setNotice({ type: "ok", text: `${result.invoiceCount || 0} fatura okundu.` });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function runJob(path) {
    try {
      const result = await callJson(path, { method: "POST" });
      setJobResult(result);
      setNotice({ type: "ok", text: "Islem tamamlandi." });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function loadMapping() {
    try {
      const result = await callJson("/api/mapping");
      setMappingMeta(result);
      setMappingText(JSON.stringify(result.data || {}, null, 2));
      setNotice({ type: "ok", text: "Mapping yuklendi." });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  async function saveMapping() {
    let parsed;
    try {
      parsed = JSON.parse(mappingText);
    } catch (error) {
      setNotice({ type: "error", text: `JSON hatasi: ${error.message}` });
      return;
    }
    try {
      const result = await callJson("/api/mapping", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed)
      });
      setMappingMeta(result);
      setNotice({ type: "ok", text: "Mapping kaydedildi." });
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
      setNotice({ type: "ok", text: "Ayarlar yuklendi." });
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
      setNotice({ type: "ok", text: "Ayarlar kaydedildi." });
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
      setNotice({ type: "ok", text: `${result.deleted || 0} log silindi.` });
    } catch (error) {
      setNotice({ type: "error", text: error.message });
    }
  }

  const activeMailbox = settings.graphMailbox || "Mailbox secilmedi";
  const pollerState = settings.mailPollerEnabled ? "Aktif" : "Kapali";
  const sapState = settings.sapMode || "dry-run";

  return (
    <main className="shell">
      <header className="topbar" role="banner">
        <div className="brand">
          <FileText size={28} aria-hidden="true" />
          <div>
            <h1>Fatura Otomasyonu</h1>
            <span className="subline">SAP S/4HANA Cloud Public Edition</span>
          </div>
        </div>
        <div className="statusStrip">
          <StatusChip health={health} />
          <div className="secretBox">
            <KeyRound size={16} aria-hidden="true" />
            <input
              type="password"
              value={secret}
              onChange={(event) => setSecret(event.target.value)}
              placeholder="Worker secret"
              aria-label="Worker secret"
            />
            <button type="button" className="iconButton" onClick={saveSecret} title="Secret kaydet">
              <Save size={17} aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      <section className="objectHeader" aria-label="Uygulama ozeti">
        <div>
          <span className="eyebrow">Gelen fatura otomatik kayit</span>
          <h2>Mailden SAP tedarikci faturasi olusturma</h2>
        </div>
        <div className="objectFacts">
          <ObjectFact label="Mailbox" value={activeMailbox} />
          <ObjectFact label="Poller" value={pollerState} tone={settings.mailPollerEnabled ? "positive" : "critical"} />
          <ObjectFact label="SAP Mode" value={sapState} />
        </div>
      </section>

      <section className="tabs" aria-label="Ana gorunum">
        <TabButton active={activeTab === "settings"} onClick={() => setActiveTab("settings")} icon={<Settings2 size={16} />} label="Ayarlar" />
        <TabButton active={activeTab === "logs"} onClick={() => setActiveTab("logs")} icon={<ClipboardList size={16} />} label="Loglar" />
        <TabButton active={activeTab === "pdf"} onClick={() => setActiveTab("pdf")} icon={<Upload size={16} />} label="PDF Test" />
        <TabButton active={activeTab === "jobs"} onClick={() => setActiveTab("jobs")} icon={<Activity size={16} />} label="Isler" />
        <TabButton active={activeTab === "mapping"} onClick={() => setActiveTab("mapping")} icon={<FolderSync size={16} />} label="Mapping" />
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
        />
      )}

      {activeTab === "pdf" && (
        <section className="grid two">
          <div className="panel">
            <PanelTitle icon={<Upload size={18} />} title="PDF Test" />
            <div className="fileRow">
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
              <button type="button" onClick={extractPdf} disabled={busy === "/api/extract"}>
                <Play size={17} aria-hidden="true" />
                Parse Et
              </button>
            </div>
            <Summary result={extractResult} />
          </div>
          <InvoiceTable result={extractResult} />
        </section>
      )}

      {activeTab === "jobs" && (
        <section className="grid two">
          <div className="panel">
            <PanelTitle icon={<Inbox size={18} />} title="Isler" />
            <div className="actionGrid">
              <button type="button" onClick={() => runJob("/jobs/process-mail")} disabled={busy === "/jobs/process-mail"}>
                <Inbox size={17} aria-hidden="true" />
                Inbox Isle
              </button>
              <button type="button" onClick={() => runJob("/jobs/process-manual")} disabled={busy === "/jobs/process-manual"}>
                <RefreshCcw size={17} aria-hidden="true" />
                Manual Tekrar
              </button>
            </div>
            <JobSummary result={jobResult} />
          </div>
          <JsonPanel title="Son Islem" value={jobResult} />
        </section>
      )}

      {activeTab === "mapping" && (
        <section className="grid mappingGrid">
          <div className="panel">
            <PanelTitle icon={<FolderSync size={18} />} title="Mapping JSON" />
            <div className="toolbar">
              <button type="button" onClick={loadMapping} disabled={busy === "/api/mapping"}>
                <RefreshCcw size={17} aria-hidden="true" />
                Yukle
              </button>
              <button type="button" onClick={saveMapping} disabled={busy === "/api/mapping" || mappingMeta?.readOnly}>
                <Save size={17} aria-hidden="true" />
                Kaydet
              </button>
            </div>
            {mappingMeta && (
              <div className="metaLine">
                <span>{mappingMeta.source}</span>
                {mappingMeta.readOnly && <strong>Read-only</strong>}
              </div>
            )}
            <textarea
              value={mappingText}
              onChange={(event) => setMappingText(event.target.value)}
              spellCheck="false"
              aria-label="Mapping JSON"
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

function ObjectFact({ label, value, tone = "" }) {
  return (
    <div className={`objectFact ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SettingsView({ settings, settingsMeta, updateSetting, loadSettings, saveSettings, busy }) {
  return (
    <section className="grid settingsGrid">
      <div className="panel">
        <PanelTitle icon={<Mail size={18} />} title="Mail Okuma" />
        <div className="toolbar">
          <button type="button" onClick={loadSettings} disabled={busy === "/api/settings"}>
            <RefreshCcw size={17} aria-hidden="true" />
            Yukle
          </button>
          <button type="button" onClick={saveSettings} disabled={busy === "/api/settings"}>
            <Save size={17} aria-hidden="true" />
            Kaydet
          </button>
        </div>
        {settingsMeta && <div className="metaLine"><span>{settingsMeta.source}</span></div>}
        <div className="formGrid">
          <TextField label="Okunacak mailbox" value={settings.graphMailbox} onChange={(value) => updateSetting("graphMailbox", value)} />
          <TextField label="Okunacak klasor" value={settings.graphSourceFolder} onChange={(value) => updateSetting("graphSourceFolder", value)} />
          <TextField label="Processed klasoru" value={settings.graphProcessedFolder} onChange={(value) => updateSetting("graphProcessedFolder", value)} />
          <TextField label="Manual klasoru" value={settings.graphManualFolder} onChange={(value) => updateSetting("graphManualFolder", value)} />
          <TextField label="Error klasoru" value={settings.graphErrorFolder} onChange={(value) => updateSetting("graphErrorFolder", value)} />
          <TextField label="Konu filtreleri" value={settings.graphSubjectKeywords} onChange={(value) => updateSetting("graphSubjectKeywords", value)} />
          <NumberField label="Run basina mail" value={settings.graphMaxMessages} min="1" onChange={(value) => updateSetting("graphMaxMessages", value)} />
          <NumberField label="Poll saniye" value={settings.mailPollIntervalSeconds} min="30" onChange={(value) => updateSetting("mailPollIntervalSeconds", value)} />
          <ToggleField label="Otomatik poller" checked={settings.mailPollerEnabled} onChange={(value) => updateSetting("mailPollerEnabled", value)} />
        </div>
      </div>

      <div className="panel">
        <PanelTitle icon={<KeyRound size={18} />} title="Microsoft Graph" />
        <div className="formGrid single">
          <TextField label="Tenant ID" value={settings.graphTenantId} onChange={(value) => updateSetting("graphTenantId", value)} />
          <TextField label="Client ID" value={settings.graphClientId} onChange={(value) => updateSetting("graphClientId", value)} />
          <SecretField
            label="Client secret"
            value={settings.graphClientSecret}
            configured={settings.graphClientSecretConfigured}
            onChange={(value) => updateSetting("graphClientSecret", value)}
          />
        </div>
      </div>

      <div className="panel">
        <PanelTitle icon={<UserRound size={18} />} title="SAP Kayit" />
        <div className="formGrid single">
          <TextField label="SAP mode" value={settings.sapMode} onChange={(value) => updateSetting("sapMode", value)} />
          <TextField label="Kayit kullanicisi" value={settings.sapPostingUser} onChange={(value) => updateSetting("sapPostingUser", value)} />
          <TextField label="SAP base URL" value={settings.sapBaseUrl} onChange={(value) => updateSetting("sapBaseUrl", value)} />
          <TextField label="SAP auth URL" value={settings.sapAuthUrl} onChange={(value) => updateSetting("sapAuthUrl", value)} />
          <TextField label="SAP comm. user" value={settings.sapClientId} onChange={(value) => updateSetting("sapClientId", value)} />
          <SecretField
            label="SAP comm. password"
            value={settings.sapClientSecret}
            configured={settings.sapClientSecretConfigured}
            onChange={(value) => updateSetting("sapClientSecret", value)}
          />
        </div>
      </div>
    </section>
  );
}

function LogsView({ logType, setLogType, logs, logMeta, loadLogs, clearLogs, busy }) {
  return (
    <section className="grid mappingGrid">
      <div className="panel">
        <PanelTitle icon={<ClipboardList size={18} />} title="Loglar" />
        <div className="toolbar splitToolbar">
          <div className="segmented" aria-label="Log tipi">
            <button type="button" className={logType === "mail_read" ? "active" : ""} onClick={() => setLogType("mail_read")}>
              <Mail size={16} aria-hidden="true" />
              Okunan Mailler
            </button>
            <button type="button" className={logType === "sap_record" ? "active" : ""} onClick={() => setLogType("sap_record")}>
              <UserRound size={16} aria-hidden="true" />
              SAP Kayitlari
            </button>
          </div>
          <div className="toolbar">
            <button type="button" onClick={() => loadLogs(logType)} disabled={busy.startsWith("/api/logs")}>
              <RefreshCcw size={17} aria-hidden="true" />
              Yenile
            </button>
            <button type="button" className="dangerButton" onClick={clearLogs} disabled={busy.startsWith("/api/logs")}>
              <Trash2 size={17} aria-hidden="true" />
              Temizle
            </button>
          </div>
        </div>
        {logMeta && <div className="metaLine"><span>{logMeta.source} / {logMeta.type}</span></div>}
        <LogTable type={logType} logs={logs} />
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

function SecretField({ label, value, configured, onChange }) {
  return (
    <label className="field">
      <span>
        {label}
        {configured && <strong className="configuredBadge">set</strong>}
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

function LogTable({ type, logs }) {
  const isMail = type === "mail_read";
  return (
    <div className="tableWrap">
      <table className="logTable">
        <thead>
          <tr>
            <th>Zaman</th>
            {isMail ? (
              <>
                <th>Mailbox</th>
                <th>Konu</th>
                <th>Gonderen</th>
                <th>Klasor</th>
                <th>PDF</th>
              </>
            ) : (
              <>
                <th>Fatura</th>
                <th>Tedarikci</th>
                <th>Tutar</th>
                <th>Durum</th>
                <th>Kullanici</th>
                <th>Eksik Mapping</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {logs.length === 0 && (
            <tr>
              <td colSpan={isMail ? 6 : 7} className="emptyCell">Kayit yok</td>
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

function Summary({ result }) {
  if (!result) return null;
  return (
    <div className="summaryGrid">
      <Metric label="Fatura" value={result.invoiceCount ?? 0} />
      <Metric label="Validasyon" value={result.validationPassed ? "Gecti" : "Kontrol"} />
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

function InvoiceTable({ result }) {
  const invoices = result?.invoices || [];
  return (
    <div className="panel tablePanel">
      <PanelTitle icon={<FileText size={18} />} title="Faturalar" />
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>No</th>
              <th>Tedarikci</th>
              <th>TCKN/VKN</th>
              <th>Tutar</th>
              <th>Durum</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 && (
              <tr>
                <td colSpan="5" className="emptyCell">Kayit yok</td>
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
                    {invoice.validationPassed ? "OK" : "Kontrol"}
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

function JobSummary({ result }) {
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
