# Mailden SAP S/4HANA Cloud'a Gelen Fatura Otomasyonu

SAP S/4HANA Cloud Public Edition kullanan sirketlerde gelen fatura sureci hala cok sik mailbox, PDF, manuel kontrol ve SAP ekranlari arasinda ilerliyor. Bu calismada amacimiz bu sureci clean-core yaklasimiyla, dusuk maliyetli ve izlenebilir bir BTP uygulamasina almakti.

## Problem

Standart e-fatura PDF'leri belirli bir sirket mailbox'ina geliyor. Operasyon ekibi bu PDF'leri aciyor, fatura bilgilerini kontrol ediyor, tedarikci ve vergi mapping'lerini buluyor, sonra SAP tarafinda supplier invoice yaratma surecini tetikliyor.

Bu modelde temel problemler:

- Mailbox takip isi manuel
- PDF okuma ve veri cikarma manuel
- Tedarikci/BP, tax code, company code mapping hatalari riski yuksek
- Hangi mailin islendigi ve hangi faturanin SAP'ye gonderildigi net izlenemiyor
- SAP Public Cloud'da clean-core disina cikmadan entegrasyon yapmak gerekiyor

## Cozum

SAP BTP Cloud Foundry uzerinde bir Python + React uygulamasi hazirladik.

Uygulamanin akisi:

1. Belirlenen mailbox okunur.
2. PDF attachment'lar indirilir.
3. E-fatura PDF'i parse edilir.
4. QR/PDF metni uzerinden fatura no, ETTN, VKN/TCKN, tutar, para birimi, KDV gibi alanlar cikarilir.
5. SAP mapping kontrolu yapilir.
6. Mapping tam ise SAP Supplier Invoice create sureci tetiklenmeye hazir hale gelir.
7. Mapping eksikse fatura manuel kontrole duser.
8. Mail `Processed`, `Manual` veya `Error` klasorune tasinir.
9. Okunan mailler ve SAP kayit denemeleri ayri ayri loglanir.

Su anki guvenli fazda uygulama `dry-run` modda calisir. Yani fatura parse edilir, mapping kontrol edilir ve SAP kayit payload'i hazirlanir; gercek supplier invoice create cagrisi SAP API payload'i onaylandiktan sonra acilir.

## Mimari

Backend:

- Python
- Flask
- Microsoft Graph mailbox worker
- PDF parser
- SAP mapping resolver
- Activity log

Frontend:

- React
- Fiori benzeri shell, object header, tab bar ve kart/form yapisi
- Ayarlar, Loglar, PDF Test, Isler, Mapping ekranlari

BTP:

- Cloud Foundry app
- Job Scheduler kullanmadan lightweight poller
- Diger servis maliyeti olmadan ilk demo/runtime

SAP S/4HANA Cloud Public Edition:

- Communication User
- Communication System
- Communication Arrangement
- Supplier Invoice Integration
- Flexible Workflow ile sonraki onay sureci

## Microsoft 365 Senaryosu

Mevcut implementasyon Microsoft Graph ile calisir.

Gerekenler:

- Microsoft Entra App Registration
- Tenant ID
- Client ID
- Client Secret veya certificate
- Microsoft Graph Application Permission: `Mail.ReadWrite`
- Admin consent
- Okunacak mailbox
- Mailbox klasorleri: `Inbox`, `Processed`, `Manual`, `Error`
- Tercihen Exchange Online Application RBAC veya Application Access Policy ile app'in sadece ilgili mailbox'a sinirlanmasi

Uygulama ayarlari React UI'den girilebilir:

- Okunacak mailbox
- Okunacak klasor
- Konu filtreleri
- Poller acik/kapali
- Graph tenant/client/secret

## Google Workspace / Gmail Senaryosu

Bu repo su anda Microsoft Graph connector ile gelir. Ancak ayni mimari Google Workspace icin Gmail API connector ile genisletilebilir.

Google tarafinda kurumsal backend otomasyon icin tipik model:

- Google Cloud Project
- Gmail API enabled
- Service Account
- Domain-wide Delegation
- Workspace Admin Console'da scope yetkilendirmesi
- Impersonate edilecek fatura mailbox'i

Gmail API scope secimi:

- Sadece okuma: `gmail.readonly`
- Maili islendikten sonra label/tasima mantigi: `gmail.modify`

Bu senaryoda mail islendikten sonra `Processed`, `Manual`, `Error` label'lari kullanilacagi icin pratikte `gmail.modify` gerekir.

Onerilen Google config:

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

## SAP Public Cloud Aktivasyonu

SAP tarafinda kullandigimiz Fiori app'leri:

- `Maintain Communication Users`
- `Communication Systems`
- `Communication Arrangements`
- `Custom Tiles`
- `Manage Launchpad Spaces`
- `Manage Launchpad Pages`
- `Maintain Business Roles`
- `Maintain Business Users`

Teknik entegrasyon adimlari:

1. `Maintain Communication Users` ile inbound teknik kullanici olusturulur.
2. `Communication Systems` icinde BTP uygulamasi icin system tanimlanir.
3. Inbound user bu communication system'e atanir.
4. `Communication Arrangements` icinde Supplier Invoice Integration senaryosu olusturulur.
5. Inbound service URL uygulamanin `SAP base URL` alanina girilir.
6. `SAP comm. user` ve `SAP comm. password` alanlari communication user ile doldurulur.
7. `SAP mode` once `dry-run` tutulur.
8. Payload ve mapping onaylandiktan sonra gercek create modu acilir.

Launchpad'e app olarak ekleme:

1. `Custom Tiles` ile BTP route'a giden tile olusturulur.
2. `Manage Launchpad Spaces` ile ilgili space hazirlanir.
3. `Manage Launchpad Pages` ile page olusturulur ve tile page'e eklenir.
4. `Maintain Business Roles` ile ornegin `Z_BR_FATURA_OTOMASYONU` role'u olusturulur.
5. Bu role'e ilgili space/page ve tile yetkisi eklenir.
6. `Maintain Business Users` ile kullanicilara role atanir.

Buradaki onemli nokta: her kullanici icin tile/page ayri ayri yapilmaz. Space/page/tile bir kere business role'a baglanir. Sonra yeni kullanici geldikce sadece business role atanir.

## Uygulama Nasil Calistirilir?

Build ve deploy:

```powershell
uv run --extra test pytest
.\scripts\build-ui.ps1
mbt build -p cf
cf deploy mta_archives\incoming-invoice-automation_0.1.0.mtar
```

Admin UI:

1. BTP route acilir.
2. Worker secret girilir.
3. `Ayarlar` sekmesinde mail ve SAP bilgileri doldurulur.
4. `Kaydet` ile runtime ayarlar kaydedilir.
5. `Isler > Inbox Isle` ile manuel test calistirilir.
6. `Loglar > Okunan Mailler` ile mailbox okuma sonucu izlenir.
7. `Loglar > SAP Kayitlari` ile fatura kayit denemeleri izlenir.
8. Eksik mapping varsa `Mapping` sekmesinde duzeltilir.
9. `Isler > Manual Tekrar` ile manuel klasordeki faturalar tekrar islenir.

## Kullanici Deneyimi

Son kullanici SAP Launchpad'de `Fatura Otomasyonu` tile'ini gorur. Uygulama Fiori benzeri bir arayuzle acilir.

Kullanicinin gorebildigi temel ekranlar:

- Ayarlar
- Loglar
- PDF Test
- Isler
- Mapping

Boylece surec sadece teknik bir entegrasyon olarak kalmaz; operasyon ekibi hangi faturanin neden manuel kontrole dustugunu gorebilir ve gerekli mapping duzeltmesini yapabilir.

## Clean-Core Yaklasimi

Bu tasarimda SAP standard objeleri modifiye edilmez. SAP Public Cloud ile iletisim released communication arrangement ve inbound API modeli uzerinden yapilir. Onay sureci gerekiyorsa SAP Flexible Workflow kullanilir.

## Sonuc

Bu calismayla mailden gelen fatura surecini:

- izlenebilir,
- kullanici tarafindan duzeltilebilir,
- SAP Launchpad'e entegre,
- BTP uzerinde dusuk maliyetli,
- clean-core uyumlu

hale getiren bir ilk urunlestirilebilir paket ortaya cikti.

Kaynak kod ve implementasyon questionnaire'i GitHub uzerinde paylasilabilir. Questionnaire sayesinde implementasyonu yapacak ekip, Microsoft 365 veya Google Workspace fark etmeksizin musteriden hangi bilgileri istemesi gerektigini bastan bilir.

## Kaynaklar

- SAP Custom Tiles: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0f69f8fb28ac4bf48d2b57b9637e81fa/16b1df7ce64b4bef98071fde8e716332.html
- SAP Spaces and Pages: https://help.sap.com/docs/SAP_S4HANA_CLOUD/4fc8d03390c342da8a60f8ee387bca1a/f78a65b96121447e8b276c6dec94d637.html
- Microsoft Graph permissions: https://learn.microsoft.com/en-us/graph/permissions-reference
- Exchange app RBAC: https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac
- Gmail API scopes: https://developers.google.com/workspace/gmail/api/auth/scopes
- Google Workspace domain-wide delegation: https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation
