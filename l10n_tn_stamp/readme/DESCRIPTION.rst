Charge the Tunisian **fiscal stamp** (*droit de timbre*, 1.000 TND) **once per
invoice**, on the right account and in the tax report. In the official Tunisian
localization of Odoo (``l10n_tn``), the stamp is a fixed tax applied per invoice
line and per unit: an invoice of 3 lines of 5 units gets 15 stamps. This module
fixes it for new and existing companies, with no configuration.

What the module changes in the Tunisian chart of accounts:

* the **1 DT stamp** of ``l10n_tn`` is added **once per invoice**, on customer
  invoices and on vendor bills (through *Fiscal Stamp per Invoice*), and no longer
  on credit notes;
* the sale stamp is posted on account **4371** (stamp duty collected) instead of
  437, and tagged for a **stamp duty line** in the Tunisian tax report; the
  purchase stamp stays an expense (6654);
* the **Export** fiscal position removes the stamp: export invoices are exempt,
  and a foreign supplier does not charge it;
* a new **Public sector (stamp exempt)** fiscal position, for the invoices paid by
  the State, local authorities and public bodies, which are exempt;
* an optional legal mention, *« Droit de timbre payé sur déclaration »*.

Legal basis: stamp duty code (Law no. 93-53 of 17 May 1993), art. 117 I no. 6
(1.000 TND per invoice since the Finance Law for 2023, Decree-law no. 2022-79,
art. 69), art. 118 no. 19 and no. 29 (exemptions), art. 127 (mention). Checked in
the French version of the Official Journal (JORT) on 6 October 2026; only the
Arabic version is authentic. Ask your accountant to confirm how it applies to
your business.
