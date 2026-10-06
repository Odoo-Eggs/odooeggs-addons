#. Install the module on a database using the Tunisian chart of accounts
   (``l10n_tn``). The stamp is configured for every Tunisian company, existing or
   new: nothing else to set up.
#. At install, the stamp is removed from the taxes of the products where it had
   been added by hand. If you add a "fiscal stamp" product as an invoice line, stop
   doing so: the stamp is now added to the invoice by itself.
#. For a customer of the public sector paid by payment order, set the
   **Public sector (stamp exempt)** fiscal position on the contact.
#. To print *« Droit de timbre payé sur déclaration »* on the invoices, check
   **Stamp duty mention** in *Invoicing > Configuration > Settings > Taxes*.
