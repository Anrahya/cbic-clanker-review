# GST Rule Review Report

## Confirmed issues
- **XREF-DUPE-CGST-R19(1) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(1)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `Where there is any change in any of the particulars furnished in the application for registration in FORM GST REG-01 or FORM GST REG-07 or FORM GST REG-09 or FORM GST REG-10 or in the intimation furnished by the composition taxpayer in FORM GST CMP-02 or for Unique Identity Number in FORM GST-REG-13, either at the time of obtaining registration or Unique Identity Number or as amended from time to time, the registered person shall, within a period of fifteen days of such change, submit an application, duly signed or verified through electronic verification code, electronically in FORM GST REG-14, along with the documents relating to such change at the common portal, either directly or through a Facilitation Centre notified by the Commissioner:`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(1)-P1(a) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(1)-P1(a)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `which does not warrant cancellation of registration under section 29, the proper officer shall, after due verification, approve the amendment within a period of fifteen working days from the date of the receipt of the application in FORM GST REG-14 and issue an order in FORM GST REG-15 electronically and such amendment shall take effect from the date of the occurrence of the event warranting such amendment;`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(1)-P1(b) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(1)-P1(b)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `the change relating to sub-clause ( i ) and sub-clause (iii) of clause (a) in any State or Union territory shall be applicable for all registrations of the registered person obtained under the provisions of this Chapter on the same Permanent Account Number;`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(1)-P1(c) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(1)-P1(c)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `where the change relates to any particulars other than those specified in clause (a), the certificate of registration shall stand amended upon submission of the application in FORM GST REG- 14 on the common portal;`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(1)-P2 | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(1)-P2`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `Provided further that any change in the mobile number or e-mail address of the authorised signatory submitted under this rule, as amended from time to time, shall be carried out only after online verification through the common portal in the manner provided under sub-rule (2) of rule 8.`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(1A) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(1A)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `Notwithstanding anything contained in sub-rule (1), any particular of the application for registration shall not stand amended with effect from a date earlier than the date of submission of the application in FORM GST REG-14 on the common portal except with the order of the Commissioner for reasons to be recorded in writing and subject to such conditions as the Commissioner may, in the said order, specify.`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(2) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(2)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `Where the proper officer is of the opinion that the amendment sought under sub-rule (1) is either not warranted or the documents furnished therewith are incomplete or incorrect, he may, within a period of fifteen working days from the date of the receipt of the application in FORM GST REG-14, serve a notice in FORM GST REG-03, requiring the registered person to show cause, within a period of seven working days of the service of the said notice, as to why the application submitted under sub-rule (1) shall not be rejected.`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(3) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(3)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `The registered person shall furnish a reply to the notice to show cause, issued under sub rule (2), in FORM GST REG-04, within a period of seven working days from the date of the service of the said notice.`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **XREF-DUPE-CGST-R19(4) | moderate | cross_refs**: Duplicate cross-reference emitted for one source mention (node `CGST-R19(4)`)
  Problem: The same cross-reference target has been emitted multiple times from the same textual mention.
  Source: `Where the reply furnished under sub-rule (3) is found to be not satisfactory or where no reply is furnished in response to the notice issued under sub-rule (2) within the period prescribed in sub-rule (3), the proper officer shall reject the application submitted under sub-rule (1) and pass an order in FORM GST REG-05.`
  Why real defect: Duplicate graph edges add noise and can distort downstream relationship counts.
  Fix: Deduplicate cross_refs by mention and target within a node.
- **CHRON-DATE-AMBIGUOUS-CGST-R19(1)-3 | moderate | chronology**: Amendment has enacted_date but no clear effective date (node `CGST-R19(1)`)
  Problem: The hint amendment for marker 3 was enacted on '2025-01-23' but the source footnote does not specify a w.e.f. date. The node has no effective_from.
  Source: `3. Inserted (w.e.f. yet to be notified) vide Notification No. 7/2025 -CT., dated 23.01.2025.`
  Why real defect: When a notification does not specify 'w.e.f.', the effective date may default to the notification date or to a separately notified enforcement date. This ambiguity requires manual legal review.
  Fix: Verify whether the amendment took effect on the enacted date or awaits a separate enforcement notification. Set effective_from accordingly.
- **CHRON-DATE-AMBIGUOUS-CGST-R19(1A)-2 | moderate | chronology**: Amendment has enacted_date but no clear effective date (node `CGST-R19(1A)`)
  Problem: The hint amendment for marker 2 was enacted on '2017-12-29' but the source footnote does not specify a w.e.f. date. The node has no effective_from.
  Source: `2. Inserted vide Notification No.75/2017 -CT., dated 29.12.2017.`
  Why real defect: When a notification does not specify 'w.e.f.', the effective date may default to the notification date or to a separately notified enforcement date. This ambiguity requires manual legal review.
  Fix: Verify whether the amendment took effect on the enacted date or awaits a separate enforcement notification. Set effective_from accordingly.

## Likely false positives / acceptable source-faithful artifacts
- **Textless structural container allowed by config/schema**: The node has children and no operative text. The reviewer is configured to treat textless containers as acceptable unless source evidence shows otherwise.
- **Textless structural container allowed by config/schema**: The node has children and no operative text. The reviewer is configured to treat textless containers as acceptable unless source evidence shows otherwise.

## Overall verdict
- **close_but_not_ready**: Only moderate/minor confirmed issues were found, but the extraction still needs correction before production use.
