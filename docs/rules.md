# ChatCheckin Version 1 Rules

This document defines the Version 1 rules for message recognition, date resolution, weekly assignment, deduplication, reporting, and auditability.

The complete Chinese and English rule specification will be maintained here.

Version 1 principles:

- deterministic parsing;
- reproducible results;
- source-message traceability;
- no automatic counting of ambiguous records;
- separation between automatic recognition and manual correction.

Detailed rules include:

- `打卡` recognition;
- `补卡` recognition;
- explicit date parsing;
- relative day parsing (`昨天`, `昨日`, `前天`);
- weekday parsing (`周X`, `上周X`);
- makeup validation requiring `training_date < submission_date`;
- unresolved and ambiguous date handling;
- non-text message handling;
- member alias normalization;
- deduplication;
- Excel output requirements.

See README.md for usage examples.
