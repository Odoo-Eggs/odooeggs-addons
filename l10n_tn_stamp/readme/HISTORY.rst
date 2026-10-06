20.0.1.0.0
~~~~~~~~~~

* Migration to Odoo 20, where a tax not linked to the fiscal position of the
  invoice is dropped: the stamp is kept under the VAT exemption position, and the
  domestic taxes (VAT) are kept under the public sector position.

19.0.1.0.0
~~~~~~~~~~

* Migration to Odoo 19: the export and public sector exemptions are stamps of 0
  that replace the 1 DT stamp, as fiscal positions now work with replacement
  taxes.

18.0.1.0.0
~~~~~~~~~~

* First release: the 1 DT stamp of ``l10n_tn`` once per invoice (customer invoices
  and vendor bills), sale stamp on account 4371 with a tax report line, export and
  public sector exemptions, optional legal mention, install on existing Tunisian
  companies.
