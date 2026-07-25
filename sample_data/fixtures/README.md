# Intake fixtures

`vision_khaata.json` and `vision_invoice.json` are **PLACEHOLDER** fixtures aligned
to `../GROUND_TRUTH.md` on 2026-07-26. The repository now has generated sample images,
but the locally configured `OPENAI_API_KEY` was the invalid documented placeholder and
the real recording attempt returned HTTP 401. They match the §7.1 intake JSON schema
and are regression-tested against the generated ground truth; they were not recorded
from a live model call. Replace them by recording the corresponding prompt once a
usable `OPENAI_API_KEY` is available, then compare every field to `GROUND_TRUTH.md`.
