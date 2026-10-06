Does Odoo not have the stamp already?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The official ``l10n_tn`` has a 1 DT stamp tax, but as a fixed tax on the invoice
lines: it is multiplied by the lines and the quantities, it is posted on account
437 and it has no tax grid. This module uses the same tax, once per invoice.

Is the stamp added to credit notes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
No: no text provides for it. You can still turn it on, on the stamp tax
(*Also on credit notes*).

Is the stamp part of the VAT base?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
No, as in common practice and in ``l10n_tn``: the stamp is a fixed amount added
after the VAT.

What about the large retail stores (1.500 and 2.000 TND)?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since 2026, the invoices of large retail stores carry a 1.500 TND stamp from 50
to 100 TND, and 2.000 TND above. This version applies 1.000 TND to all invoices:
the brackets are planned.

Does it work with the FODEC?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Yes, with *Tunisia - FODEC Tax*: total = price + FODEC + VAT on price and FODEC
+ 1.000 TND.

What happens if I uninstall it?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The stamp taxes stay as they are (they belong to ``l10n_tn``) and are still added
once per invoice by *Fiscal Stamp per Invoice*. The Public sector fiscal position
stays.

Does it work on Odoo Online?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Odoo Online only installs the modules of Odoo S.A. Use Odoo.sh or your own server.
