# SAP S/4HANA Cloud'da Mailden Gelen Fatura Otomasyonu

SAP S/4HANA Cloud Public Edition projelerinde gelen fatura sureci hala cok kez mail kutusu, PDF, manuel kontrol ve SAP ekrani arasinda ilerliyor.

Bu calismada amacimiz bu sureci clean-core yaklasimiyla daha otomatik, izlenebilir ve kullanici tarafindan duzeltilebilir hale getirmekti.

Senaryo basit:

Bir tedarikci e-fatura PDF'ini belirlenen mailbox'a gonderiyor. Uygulama maili okuyor, PDF attachment'i indiriyor, fatura bilgilerini cikariyor ve SAP icin gerekli mapping kontrollerini yapiyor.

Mapping tamamsa supplier invoice create sureci tetiklenmeye hazir hale geliyor. Eksik mapping varsa sistem yanlis kayit olusturmak yerine faturayi manuel kontrole dusuruyor.

## Neden BTP?

Bu cozum SAP BTP Cloud Foundry uzerinde calisiyor.

Backend tarafinda Python ve Flask, arayuz tarafinda React kullandik. Arayuzu Fiori'ye yakin bir deneyimle tasarladik ve SAP Launchpad'e tile olarak bagladik.

Kullanici Launchpad'de "Fatura Otomasyonu" uygulamasini acip:

- hangi mailbox'in okunacagini,
- hangi klasorlerin kullanilacagini,
- SAP mapping bilgilerini,
- okunan mailleri,
- SAP kayit denemelerini

tek yerden gorebiliyor.

## Mail Entegrasyonu

Mevcut calisan versiyon Microsoft 365 icin Microsoft Graph kullaniyor.

Musteriden gereken temel bilgiler:

- Tenant ID
- Client ID
- Client Secret veya certificate
- Okunacak mailbox
- Mail.ReadWrite application permission
- Admin consent
- Tercihen sadece ilgili mailbox'a sinirlanmis app erisimi

Ayni mimari Google Workspace icin de uygulanabilir. Google tarafinda Gmail API, service account ve domain-wide delegation gerekir. Mail okunduktan sonra label/tasima yapilacaksa pratikte gmail.modify scope'una ihtiyac olur.

## SAP Public Cloud Tarafi

SAP tarafinda standart Public Cloud yapisi kullaniliyor:

- Maintain Communication Users
- Communication Systems
- Communication Arrangements
- Custom Tiles
- Manage Launchpad Spaces
- Manage Launchpad Pages
- Maintain Business Roles
- Maintain Business Users

Burada onemli nokta su: Tile'i sadece olusturmak yetmiyor. Uygulamayi gercekten kullaniciya gostermek icin tile'in Launchpad Page ve Space yapisina eklenmesi, sonra Business Role uzerinden Business User'a atanmasi gerekiyor.

Bir kere kurulduktan sonra yeni kullanici icin tek yapilacak is ilgili business role'u atamak.

## Akis

1. Mailbox kontrol edilir.
2. PDF attachment okunur.
3. Fatura bilgileri parse edilir.
4. Tedarikci, sirket kodu, vergi kodu ve GL mapping kontrol edilir.
5. Eksik bilgi varsa fatura manuel kontrole duser.
6. Mapping tamamlaninca manuel klasorden tekrar islenebilir.
7. Okunan mailler ve SAP kayit denemeleri ayri ayri loglanir.
8. SAP tarafinda onay ihtiyaci varsa Flexible Workflow devreye girer.

Su anki guvenli faz dry-run modda calisiyor. Yani sistem PDF'i okuyor, mapping kontrolunu yapiyor ve SAP payload'ini hazirliyor; gercek supplier invoice create cagrisi payload onayindan sonra aciliyor.

## Neden Onemli?

Bu yaklasimla surec:

- manuel mailbox takibinden cikiyor,
- yanlis SAP kaydi riskini azaltiyor,
- eksik mapping'i kullaniciya gorunur hale getiriyor,
- SAP Launchpad icinde tek uygulama gibi calisiyor,
- clean-core sinirlarinda kaliyor,
- Microsoft 365 veya Google Workspace senaryolarina uyarlanabiliyor.

Kod, teknik kurulum adimlari ve musteri questionnaire'i GitHub'da:

https://github.com/sarper1998/incoming-invoice-automation

Questionnaire ozellikle implementasyon ekipleri icin hazirlandi. Microsoft ise hangi bilgiler istenecek, Google ise hangi bilgiler istenecek, SAP Public Cloud tarafinda hangi Fiori app'leri kullanilacak, hepsi ayri ayri listeleniyor.

#SAP #SAPBTP #S4HANACloud #Fiori #MicrosoftGraph #GoogleWorkspace #CleanCore #AccountsPayable #Automation
