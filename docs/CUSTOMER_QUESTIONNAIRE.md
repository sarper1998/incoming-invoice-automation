# Customer Questionnaire - Incoming Invoice Automation

Bu dokuman implementasyon oncesi musteriden alinacak bilgileri standartlastirir. Amac, mailbox, SAP Public Cloud, BTP ve kullanici yetki detaylarini eksiksiz toplamak.

## 1. Genel Kapsam

- Sirket adi:
- SAP S/4HANA Cloud tenant tipi: DEV / TEST / PROD
- Fatura tipi: e-Fatura / e-Arsiv / ikisi de
- Gunluk ortalama fatura adedi:
- PDF disinda XML attachment bekleniyor mu?
- Tek mailbox mi, birden fazla mailbox mi?
- Manuel kontrol yapacak ekip:
- Canliya gecis hedef tarihi:

## 2. Mail Provider Secimi

- Mail altyapisi:
  - Microsoft 365 / Exchange Online
  - Google Workspace / Gmail
  - Diger
- Fatura mail adresi:
- Okunacak klasor/label:
- Islenen mail klasoru/label:
- Manuel kontrol klasoru/label:
- Hata klasoru/label:
- Konu filtresi: orn. `e-Fatura,e-Arsiv,Fatura`
- Attachment tipi: PDF zorunlu mu?
- Mail tasima/label degistirme izni var mi?

## 3. Microsoft 365 / Microsoft Graph Gereksinimleri

Bu repo su anda Microsoft Graph connector ile calisir.

Musteriden alinacaklar:

- Azure tenant ID
- Entra application/client ID
- Client secret veya certificate bilgisi
- Okunacak mailbox SMTP adresi
- Graph API permission:
  - Application permission: `Mail.ReadWrite`
  - Admin consent verilmis olmali
- Mailbox scope kisiti:
  - Exchange Online Application RBAC veya Application Access Policy kullanilacak mi?
  - Sadece ilgili fatura mailbox'ina erisim verilecek mi?
- Secret expiry tarihi:
- Secret renewal owner:
- Graph app owner/contact:

Microsoft admin tarafinda beklenen isler:

1. Entra admin center'da App Registration olustur.
2. Microsoft Graph application permission olarak `Mail.ReadWrite` ekle.
3. Admin consent ver.
4. Client secret veya certificate uret.
5. Exchange Online tarafinda app erisimini sadece fatura mailbox'i ile sinirla.
6. Mailbox icinde `Processed`, `Manual`, `Error` klasorlerini hazirla.

Uygulama ayarlari:

```text
GRAPH_TENANT_ID=<tenant-id>
GRAPH_CLIENT_ID=<client-id>
GRAPH_CLIENT_SECRET=<secret>
GRAPH_MAILBOX=<invoice-mailbox@domain.com>
GRAPH_SOURCE_FOLDER=Inbox
GRAPH_PROCESSED_FOLDER=Processed
GRAPH_MANUAL_FOLDER=Manual
GRAPH_ERROR_FOLDER=Error
GRAPH_SUBJECT_KEYWORDS=e-Fatura,e-Arsiv,Fatura
```

## 4. Google Workspace / Gmail Gereksinimleri

Bu repo su anda Gmail connector implementasyonu icermez. Google Workspace icin ayni mimari Gmail API connector ile genisletilir.

Kurumsal backend otomasyon icin onerilen model:

- Google Cloud Project
- Gmail API enabled
- Service Account
- Domain-wide Delegation enabled
- Workspace Admin Console'da service account client ID icin Gmail API scope yetkisi
- Impersonate edilecek fatura mailbox'i

Gerekli Gmail scope secimi:

- Sadece okuma icin: `https://www.googleapis.com/auth/gmail.readonly`
- Maili label/tasima benzeri isaretlemek icin: `https://www.googleapis.com/auth/gmail.modify`

Bu senaryo maili isledikten sonra `Processed`, `Manual`, `Error` label'larina tasimak veya label degistirmek istedigi icin pratikte `gmail.modify` gerekir.

Musteriden alinacaklar:

- Google Workspace domain:
- Google Cloud project ID:
- Service account email:
- Service account client ID:
- Service account JSON key teslim yontemi:
- Domain-wide delegation aktif mi?
- Admin Console'da yetkilendirilen scopes:
- Impersonate edilecek mailbox:
- Gmail labels:
  - Source label:
  - Processed label:
  - Manual label:
  - Error label:
- API/security approval owner:
- Service account key rotation owner:

Google admin tarafinda beklenen isler:

1. Google Cloud Project olustur.
2. Gmail API'yi enable et.
3. Service Account olustur.
4. Domain-wide Delegation'i aktif et.
5. Workspace Admin Console > Security > API Controls > Domain-wide Delegation altinda service account client ID'yi ekle.
6. Scope olarak minimum ihtiyaca gore `gmail.modify` veya `gmail.readonly` tanimla.
7. Fatura mailbox'i ve label'lari hazirla.

Onerilen future config:

```text
MAIL_PROVIDER=google
GOOGLE_WORKSPACE_DOMAIN=<domain.com>
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=<secure-path>
GOOGLE_IMPERSONATED_USER=<invoice-mailbox@domain.com>
GOOGLE_SOURCE_LABEL=INBOX
GOOGLE_PROCESSED_LABEL=Processed
GOOGLE_MANUAL_LABEL=Manual
GOOGLE_ERROR_LABEL=Error
GOOGLE_SUBJECT_KEYWORDS=e-Fatura,e-Arsiv,Fatura
```

## 5. SAP S/4HANA Cloud Public Edition Gereksinimleri

Fiori app'leri:

- `Maintain Communication Users`
- `Communication Systems`
- `Communication Arrangements`
- `Custom Tiles`
- `Manage Launchpad Spaces`
- `Manage Launchpad Pages`
- `Maintain Business Roles`
- `Maintain Business Users`

Musteriden alinacaklar:

- SAP tenant URL:
- Communication scenario:
  - Supplier Invoice Integration / `SAP_COM_0057`
- Communication user:
- Communication user password teslim yontemi:
- Communication system ID:
- Communication arrangement name:
- Supplier invoice inbound service URL:
- Flexible Workflow aktif mi?
- Testte olusturulacak fatura icin sirket kodu:
- Test supplier/BP:
- Test GL account:
- Test cost center:
- Test tax code:
- Test payment terms:

Kurulum adimlari:

1. `Maintain Communication Users` app'inde inbound teknik kullanici olustur.
2. `Communication Systems` app'inde BTP uygulamasi icin system olustur.
3. `Users for Inbound Communication` sekmesine teknik kullaniciyi ekle.
4. `Communication Arrangements` app'inde Supplier Invoice Integration senaryosu ile arrangement olustur.
5. Inbound service URL'yi not al.
6. Uygulama UI'sinda `SAP base URL`, `SAP comm. user`, `SAP comm. password`, `Kayit kullanicisi` alanlarini doldur.

## 6. Launchpad Aktivasyonu

Bir kere kurulacak yapi:

1. `Custom Tiles`
   - Title: `Fatura Otomasyonu`
   - URL: BTP route
   - Target: yeni sekme onerilir
2. `Manage Launchpad Spaces`
   - Space: `Fatura Otomasyonu` veya mevcut finans space'i
3. `Manage Launchpad Pages`
   - Page: `Gelen Fatura Otomasyonu`
   - Custom tile page'e eklenir
4. `Maintain Business Roles`
   - Role: `Z_BR_FATURA_OTOMASYONU`
   - Space/page ve ilgili catalog/tile yetkisi role'e atanir
5. `Maintain Business Users`
   - Uygulamayi kullanacak kisilere business role atanir

Yeni kullanici ekleme:

1. `Maintain Business Users` ac.
2. Kullaniciya `Z_BR_FATURA_OTOMASYONU` role'unu ata.
3. Kullanici Launchpad'de ilgili Space/Page altinda tile'i gorur.

## 7. BTP / Runtime Gereksinimleri

- BTP subaccount:
- Cloud Foundry org:
- Cloud Foundry space:
- App route/domain:
- App memory/disk beklentisi:
- Runtime ayar/log saklama:
  - Demo: local CF instance diskindeki `data/`
  - Production: HANA/PostgreSQL/Object Store gibi kalici servis onerilir
- Authentication modeli:
  - Demo: Worker secret
  - Production: XSUAA/App Router/IAS SSO onerilir

## 8. Uygulamayi Calistirma

Developer/build:

```powershell
uv run --extra test pytest
.\scripts\build-ui.ps1
mbt build -p cf
cf deploy mta_archives\incoming-invoice-automation_0.1.0.mtar
```

Admin UI:

1. BTP route'u ac.
2. `Worker secret` gir ve kaydet.
3. `Ayarlar` sekmesinde mailbox, Graph/SAP bilgilerini gir.
4. `Kaydet`.
5. `Isler > Inbox Isle` ile manuel test et.
6. `Loglar > Okunan Mailler` ve `SAP Kayitlari` ekranlarini kontrol et.
7. Eksik mapping varsa `Mapping` sekmesinde duzelt.
8. `Isler > Manual Tekrar` ile yeniden dene.

## 9. Kaynaklar

- SAP Custom Tiles: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0f69f8fb28ac4bf48d2b57b9637e81fa/16b1df7ce64b4bef98071fde8e716332.html
- SAP Spaces and Pages: https://help.sap.com/docs/SAP_S4HANA_CLOUD/4fc8d03390c342da8a60f8ee387bca1a/f78a65b96121447e8b276c6dec94d637.html
- Microsoft Graph permissions: https://learn.microsoft.com/en-us/graph/permissions-reference
- Exchange app RBAC: https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac
- Gmail API scopes: https://developers.google.com/workspace/gmail/api/auth/scopes
- Google Workspace domain-wide delegation: https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation
