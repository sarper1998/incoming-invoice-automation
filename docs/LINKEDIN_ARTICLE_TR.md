# SAP S/4HANA Cloud'da Mailden Gelen Fatura Otomasyonu

SAP S/4HANA Cloud Public Edition projelerinde gelen fatura sureci hala cok kez mail kutusu, PDF kontrolu ve manuel SAP islemleri arasinda ilerliyor.

Bu calismada bu sureci BTP uzerinde calisan kucuk ama genisletilebilir bir uygulamayla daha otomatik ve izlenebilir hale getirdik.

Senaryo su: tedarikci e-fatura PDF'ini belirlenen mailbox'a gonderiyor. Uygulama maili okuyor, PDF attachment'i indiriyor, fatura bilgilerini parse ediyor ve SAP icin gerekli mapping kontrollerini yapiyor.

Tedarikci/BP, company code, tax code veya GL account gibi alanlarda eksik mapping varsa sistem yanlis fatura yaratmak yerine kaydi manuel kontrole dusuruyor. Kullanici mapping'i duzelttikten sonra manuel klasordeki faturayi tekrar isleyebiliyor.

Uygulama SAP BTP Cloud Foundry uzerinde calisiyor. Backend tarafinda Python/Flask, arayuz tarafinda React kullandik. Arayuzu Fiori'ye yakin bir deneyimle tasarladik ve SAP Launchpad'e tile olarak bagladik.

SAP Public Cloud tarafinda kullandigimiz yapi standart: Communication User, Communication System, Communication Arrangement, Custom Tile, Launchpad Space/Page, Business Role ve Business User.

Buradaki kritik nokta su: Custom Tile olusturmak tek basina yeterli degil. Uygulamanin kullanicida gorunmesi icin tile'in Launchpad Page ve Space yapisina eklenmesi, sonra ilgili Business Role uzerinden Business User'a atanmasi gerekiyor. Bir kere kurulduktan sonra yeni kullanici icin sadece role assignment yeterli.

Mail entegrasyonunda mevcut calisan versiyon Microsoft 365 icin Microsoft Graph kullaniyor. Musteriden Tenant ID, Client ID, secret/certificate, okunacak mailbox, Mail.ReadWrite application permission ve admin consent gerekiyor. Guvenlik icin app erisiminin sadece ilgili mailbox ile sinirlanmasi oneriliyor.

Ayni mimari Google Workspace icin de uygulanabilir. Google tarafinda Gmail API, service account, domain-wide delegation ve ilgili Gmail scope'lari gerekir. Mail islendikten sonra label/tasima yapilacaksa pratikte gmail.modify scope'una ihtiyac olur.

Uygulama su an guvenli fazda dry-run modda calisiyor. Yani PDF okunuyor, mapping kontrol ediliyor, SAP payload'i hazirlaniyor ve loglaniyor; gercek supplier invoice create cagrisi payload onayindan sonra aciliyor. Onay sureci gerekiyorsa SAP Flexible Workflow devreye giriyor.

Bu yaklasimla gelen fatura sureci:

- manuel mailbox takibinden cikiyor,
- eksik mapping'i gorunur hale getiriyor,
- yanlis SAP kaydi riskini azaltiyor,
- SAP Launchpad icinde tek uygulama gibi calisiyor,
- clean-core sinirlarinda kaliyor,
- Microsoft 365 ve Google Workspace senaryolarina uyarlanabiliyor.

Kod, kurulum adimlari ve musteri questionnaire'i GitHub'da:

https://github.com/sarper1998/incoming-invoice-automation

Questionnaire implementasyon ekipleri icin hazirlandi: Microsoft ise hangi bilgiler istenecek, Google ise hangi bilgiler istenecek, SAP Public Cloud tarafinda hangi Fiori app'leri kullanilacak, hepsi ayri ayri listeleniyor.

#SAP #SAPBTP #S4HANACloud #Fiori #MicrosoftGraph #GoogleWorkspace #CleanCore #AccountsPayable #Automation
