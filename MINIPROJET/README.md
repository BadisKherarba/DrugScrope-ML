# DrugScope AI - Kinase Inhibitor Data & Discovery Platform

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31011/)
[![Data Source: ChEMBL](https://img.shields.io/badge/Data%20Source-ChEMBL-darkgreen.svg)](https://www.ebi.ac.uk/chembl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An exploratory and machine-learning-ready data curation pipeline targeting human **protein kinase inhibitors**. This project audits, inspects, and analyzes bioactivity, chemical descriptors, mechanism of action, and clinical indications retrieved from the ChEMBL database.

---

## 📌 Project Overview

Protein kinases are critical enzymes in cellular signaling and major therapeutic targets in oncology, immunology, and cardiovascular medicine. 

**DrugScope AI** provides a structured raw-to-processed pipeline that:
- Collects candidate kinase inhibitors with clinical progression ($\text{Max Phase} \ge 1$).
- Standardizes bioactivities across binding assays ($\text{IC}_{50}$, $K_i$, $K_d$, $\text{pChEMBL}$).
- Computes physicochemical properties (Lipinski's Rule of 5 parameters, polar surface area, rotatable bonds).
- Audits correlations and screens for domain/statistical outliers across all features.

---

## 🗂️ Data Architecture

The project tracks 5 interconnected raw data streams stored in `data/raw/`:

| Dataset | Records | Features | Description |
| :--- | :---: | :---: | :--- |
| **`targets_raw.csv`** | 548 | 4 | Human single-protein targets classified with kinase activity. |
| **`molecules_raw.csv`** | 407 | 15 | Candidate molecules (89 approved, 318 clinical Phase 1–3), SMILES, and 2D descriptors. |
| **`mechanisms_raw.csv`** | 610 | 5 | Molecule-target mechanism mappings (Inhibitors, Antagonists, Blockers, Allosteric modulators). |
| **`activities_raw.csv`** | 15,655 | 11 | Bioactivity measurements ($\text{IC}_{50}, K_i, K_d$) with standardized concentrations and $\text{pChEMBL}$ scores. |
| **`indications_raw.csv`** | 2,864 | 4 | Clinical indications with EFO ontology terms and MeSH headings. |

Detailed selection parameters are documented in [DATA_SOURCES.md](data/DATA_SOURCES.md).

---

## 🔬 Data Audit & Outlier Analysis Findings

All raw datasets were audited for **domain-specific validity** and **statistical variance** (using 1.5× and 3.0× IQR thresholds):

1. **Zero Out-of-Range Errors**:
   - No negative molecular weights, PSA, or atom counts.
   - All clinical phases strictly conform to $[0.5, 4.0]$.
   - No negative or non-physiological activity concentrations ($\text{pChEMBL} \in [4.00, 10.80]$).
2. **Real Pharmacological Outliers**:
   - **Macromolecules**: 2 molecules have $\text{MW} > 1500\text{ Da}$ (max: $3823.5\text{ Da}$, $\text{PSA} = 355.2\text{ \AA}^2$). These correspond to legitimate modern bivalent degraders (PROTACs) and peptide-conjugates rather than erroneous small molecules.
   - **Bioactivity Skew**: Raw concentrations span 7 orders of magnitude ($0.02\text{ nM}$ to $100,000\text{ nM}$), which normalizes into a Gaussian bell curve under logarithmic $\text{pChEMBL}$ transformation ($\text{mean} = 6.86$).

Inspection logs and summary notes are maintained in [notes.txt](data/raw/notes.txt).

---

## 📁 Repository Structure

```
MINIPROJET/
├── data/
│   ├── DATA_SOURCES.md             # Collection methodology & ChEMBL criteria
│   └── raw/
│       ├── targets_raw.csv         # 548 kinase targets
│       ├── molecules_raw.csv       # 407 molecules with chemical descriptors
│       ├── mechanisms_raw.csv      # 610 mechanism of action entries
│       ├── activities_raw.csv      # 15,655 bioactivity data points
│       ├── indications_raw.csv     # 2,864 clinical indications
│       ├── notes.txt               # Data quality audit log
│       ├── check_data.py           # Self-bootstrapping data inspection script
│       ├── graph.py                # Correlation heatmaps & IQR outlier boxplots
│       └── *.png                   # Generated figures & plots
├── requirements.txt                # Python package dependencies
├── setup_env.bat                   # 1-click Windows environment setup script
├── push_to_github.bat              # Automated GitHub publishing script
└── README.md                       # Project documentation
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+ (The setup script will automatically install it via `winget` if missing).
- Git.

### 2. Quick Setup (Windows)
Double-click or run:
```cmd
.\setup_env.bat
```
*This installs dependencies and creates a local `.venv`.*

### 3. Manual Installation
```bash
# Clone the repository
git clone https://github.com/BadisKherarba/DrugScrope-ML.git
cd DrugScrope-ML

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate       # On Windows
# source .venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 4. Running the Analysis & Graphs
```bash
# Run comprehensive audit & data inspection
python data\raw\check_data.py

# Generate correlation heatmaps and outlier boxplots
python data\raw\graph.py
```

---

## 👤 Author

**Badis Kherarba**  
GitHub: [@BadisKherarba](https://github.com/BadisKherarba)

