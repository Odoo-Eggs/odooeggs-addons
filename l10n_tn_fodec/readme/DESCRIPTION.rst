Invoice the Tunisian **FODEC tax (1%)** with the right VAT: the VAT is computed on
the price **plus** the FODEC, as the Tunisian VAT code requires. The official
Tunisian localization of Odoo (``l10n_tn``) has no FODEC tax: this module adds it,
ready to use, for new and existing companies.

The FODEC (*taxe professionnelle au profit du fonds de développement de la
compétitivité*) is due by the **manufacturers** of the products listed by decree,
at 1% of their turnover excluding VAT. On an invoice of 1,000.000 TND with 19% VAT:
FODEC 10.000, VAT 19% of 1,010.000 = 191.900, total 1,201.900.

What the module adds to the Tunisian chart of accounts:

* a **FODEC 1%** sales tax, computed before the VAT and included in the VAT base,
  posted on account 43678 (other taxes on turnover, 436780 in the chart);
* a **FODEC 1% (cost)** purchase tax, for the bills of manufacturers who invoice
  the FODEC: it is a cost, added to the expense or stock account, and the
  deductible VAT is computed on the right base;
* the **Export** fiscal position replaces the FODEC by a **FODEC 0%** tax (exported
  products are exempt);
* a **FODEC** line in the Tunisian tax report (base and FODEC due).

Legal basis: Finance Law for 2000 (Law no. 99-101 of 31 December 1999, art. 36
and 37), amended by the Finance Law for 2011 (Law no. 2010-58 of 17 December 2010,
art. 15); list of products: Decree no. 2000-634 of 13 March 2000, completed by
Decree no. 2008-4111 of 30 December 2008; VAT base including the other taxes:
VAT code (Law no. 88-61 of 2 June 1988), art. 6. Checked in the French version of
the Official Journal (JORT) on 5 October 2026; only the Arabic version is
authentic. Ask your accountant to confirm how it applies to your business.
