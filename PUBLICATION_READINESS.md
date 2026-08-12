# Publication readiness

## Current release class

`PARTIAL_FROZEN_CODE_MATERIALIZED`

The repository contains the original 2025 zoonoses ingestion script, the original frozen 2025 prospective evaluator, the prespecified follow-up protocol, source/provenance documentation, and public-release safety tooling.

## Reproducibility boundary

The executed project notebook records a successful call to `scripts/pipeline.py --permutations 250 --bootstraps 1000`, including 99 modeled transitions and 7 emergence events. The exact primary `scripts/pipeline.py` source was not recoverable from the connected project materials during this publication pass. It has not been recreated and labeled as original code.

The executed notebook itself is not mirrored here because it contains embedded figure outputs; this repository follows a no-image-binary publication policy until redistribution rights are independently confirmed. The code and aggregate results needed for the current public deposit are text-based.

## Publication safeguards

- Missing species-specific reporting is preserved as missing rather than zero.
- The ingestion path fails closed and prohibits OCR/map digitization.
- `code/evaluate_frozen_2025.py` evaluates the frozen 2025 predictions without refitting.
- `tools/public_release_audit.py` and GitHub Actions enforce the public-tree safety policy.
- `CITATION.cff` does not claim a release version or DOI before an immutable release exists.

## Remaining blockers to a complete code archive

1. Recover the exact original `scripts/pipeline.py` and any required companion modules/configuration.
2. Select an explicit software license after ownership/upstream-license review.
3. After the frozen source tree is complete, create an immutable release and preservation DOI and add it to repository/manuscript citation metadata.

Until item 1 is resolved, describe this repository as a partial frozen-code deposit with exact ingestion and prospective-evaluation artifacts.
