==============
Invoice Number
==============

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! source digest: sha256:268beea04a506572b87d9291ad864ae2a22f5a32c01f67cb909e9327ab6e3ec5
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Mature-brightgreen.png
    :target: https://odoo-community.org/page/development-status
    :alt: Mature
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-dhongu%2Fdeltatech-lightgray.png?logo=github
    :target: https://github.com/dhongu/deltatech/tree/14.0/deltatech_invoice_number
    :alt: dhongu/deltatech

|badge1| |badge2| |badge3|

Functions:
 - At the validation, the invoice date must be greater than the last invoice validated (configurable in journal)
 - The number of the invoice can be modified
 - A number can be allocated to a invoice in the draft state. After the number is allocated, the date of the invoice cannot be changed
 - The user must be in the account.group_account_invoice group (Accounting & Finance / Billing)

Functionalitati:
 - Validare data factura sa fie mai mare decat data din ultima factura (configurabil in jurnal)
 - Posibilitatea de a modifica numarul unei facturi pentru un anumit grup de utilizatori
 - posibilitatea de a numerota o factura chiar daca aceasta nu este validata. Dupa numerotare nu se mai poate modifca data

**Table of contents**

.. contents::
   :local:

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/dhongu/deltatech/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/dhongu/deltatech/issues/new?body=module:%20deltatech_invoice_number%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Terrabit
* Dorin Hongu

Maintainers
~~~~~~~~~~~

.. |maintainer-dhongu| image:: https://github.com/dhongu.png?size=40px
    :target: https://github.com/dhongu
    :alt: dhongu

Current maintainer:

|maintainer-dhongu| 

This module is part of the `dhongu/deltatech <https://github.com/dhongu/deltatech/tree/14.0/deltatech_invoice_number>`_ project on GitHub.

You are welcome to contribute.
