Add a fixed tax **once per invoice**, not once per line: fiscal stamp (timbre fiscal),
stamp duty, or any fixed fee required by law on each invoice or vendor bill.

In standard Odoo, a tax of type *Fixed* is multiplied by the quantity of every
invoice line: an invoice with 3 lines of 5 units gets 15 stamps instead of one.
This module adds the tax a single time, on the whole document, and lets the
standard Odoo tax engine do the rest: tax journal item, tax group in the totals,
tax report, payment terms.

Typical use: the Tunisian **1 DT fiscal stamp** (``l10n_tn``, tax "1DT Tax stamp").
