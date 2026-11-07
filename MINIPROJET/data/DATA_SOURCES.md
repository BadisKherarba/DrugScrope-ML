# DrugScope AI - Data Sources Documentation

- Collection date: 2026-11-06
- Source: ChEMBL (https://www.ebi.ac.uk/chembl/)
- ChEMBL version: unknown - write it from https://www.ebi.ac.uk/chembl/
- Access method: chembl_webresource_client (official ChEMBL Python client)
- PubChem: not used (add a note here if used later)

## Selection criteria
- Targets: human, SINGLE PROTEIN, name contains 'kinase'
- Molecules: mechanism action type in ['INHIBITOR', 'ANTAGONIST', 'BLOCKER', 'NEGATIVE ALLOSTERIC MODULATOR'] against those targets
- Activities/indications collected for molecules with max_phase >= 1 (4 = approved, 1-3 = clinical/exploratory)
- Activity types: ['IC50', 'Ki', 'Kd'], relation '=', pChEMBL value present

## Raw files and record counts
- targets_raw.csv: 548 rows
- mechanisms_raw.csv: 610 rows
- molecules_raw.csv: 407 rows
- activities_raw.csv: 15655 rows
- indications_raw.csv: 2864 rows

- Distinct candidate molecules: 407
- Selected molecules (max_phase >= 1): 407
- Approved drugs (max_phase = 4): 89

## Known limitations
- Kinase targets selected by name keyword, not by protein classification.
- Not every molecule has activity or indication data.
- Data is raw: duplicates, invalid SMILES and missing values are NOT handled (cleaning is a separate task).