# European Zoonotic-TB Surveillance

**Repository status:** `PARTIAL_FROZEN_CODE_MATERIALIZED`

Vintage-correct One Health analysis of next-year human M. bovis/M. caprae reporting.

## Public-release policy

This repository is code/provenance-forward: raw patient-level surveillance data are excluded, third-party datasets are linked rather than mirrored, and image binaries are intentionally excluded. Source sites for visuals and data are recorded in `FIGURE_AND_IMAGE_PROVENANCE.md` and `DATA_SOURCES.md`.

Run before publishing:

```bash
python tools/public_release_audit.py
```

## Layout

- `code/` or `software/`: materialized analysis code
- `results/`: publication-safe aggregate results/receipts
- `manifests/`: identities and hashes without restricted raw data
- `docs/`: protocols/methods
- `REPOSITORY_STATUS.md`: completeness status

## Archival DOI

After the GitHub tree is complete, tag `v1.0.0`, create a GitHub Release, archive that release with Zenodo or an equivalent preservation service, and add the DOI to this README, `CITATION.cff`, and the manuscript.
