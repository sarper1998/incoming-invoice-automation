# Automating Incoming Supplier Invoices in SAP S/4HANA Cloud with SAP BTP

In many SAP S/4HANA Cloud Public Edition projects, incoming supplier invoices still move through a mailbox, PDF checks, mapping validations, and manual SAP steps.

I built a small SAP BTP application to make this flow more automatic, traceable, and clean-core friendly.

**The scenario**

A supplier sends an e-invoice PDF to a dedicated mailbox. The application reads the mailbox, downloads the PDF attachment, extracts the invoice data, and checks the SAP mappings required for supplier invoice creation.

If a mapping is missing, such as supplier/BP, company code, tax code, or GL account, the system does not create a wrong invoice. Instead, it moves the item to manual review. After the user corrects the mapping, the same invoice can be reprocessed from the manual folder.

**The BTP application**

The backend runs on SAP BTP Cloud Foundry with Python and Flask. The frontend is built with React and designed to feel close to a Fiori-style operational app.

From the application, users can switch between English and Turkish, manage the mailbox settings, SAP connection placeholders, mapping data, processed mail logs, and SAP posting attempt logs.

The app is also exposed in SAP S/4HANA Cloud Launchpad as a tile.

**SAP S/4HANA Cloud activation**

The SAP side uses standard Public Cloud configuration:

- Maintain Communication Users
- Communication Systems
- Communication Arrangements
- Custom Tiles
- Manage Launchpad Spaces
- Manage Launchpad Pages
- Maintain Business Roles
- Maintain Business Users

One important detail: creating a Custom Tile is not enough. The tile must be assigned to a Launchpad Page and Space, then exposed through a Business Role and assigned to the relevant Business Users.

Once this is set up, onboarding a new user is just a role assignment.

**Mail provider options**

The current implementation works with Microsoft 365 through Microsoft Graph. The customer needs to provide the tenant ID, client ID, secret or certificate, target mailbox, Mail.ReadWrite application permission, and admin consent.

For production, the Graph application should be restricted to the invoice mailbox instead of having broad mailbox access.

The same architecture can also be extended to Google Workspace. In that case, the implementation would use Gmail API, a service account, domain-wide delegation, and the required Gmail scopes. If processed emails need to be moved or labeled, gmail.modify is usually required.

**Current status**

The safe version currently runs in dry-run mode. It reads the mailbox, parses the PDF, validates the mapping, prepares the SAP payload, and logs the result.

The actual Supplier Invoice create call can be enabled after the payload and mapping contract are approved. If an approval process is needed afterwards, SAP Flexible Workflow can handle it.

**Why this matters**

This approach removes manual mailbox tracking, makes missing mappings visible, reduces the risk of wrong SAP postings, and keeps the solution clean-core aligned.

It also gives implementation teams a reusable pattern for both Microsoft 365 and Google Workspace scenarios.

Code, setup steps, and customer questionnaire:

https://github.com/sarper1998/incoming-invoice-automation

#SAP #SAPBTP #S4HANACloud #Fiori #MicrosoftGraph #GoogleWorkspace #CleanCore #AccountsPayable #Automation
