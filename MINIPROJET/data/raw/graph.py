import sys
import os
import subprocess
from pathlib import Path

# ==============================================================================
# AUTO-INSTALL DEPENDENCIES IF MISSING
# ==============================================================================
required_pkgs = ["numpy", "pandas", "matplotlib", "seaborn", "openpyxl"]
missing_pkgs = []
for pkg in required_pkgs:
    try:
        __import__(pkg)
    except ImportError:
        missing_pkgs.append(pkg)

if missing_pkgs:
    print(f"[INFO] Installing missing packages: {missing_pkgs} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_pkgs)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

# ==============================================================================
# LOGGER: TEE TERMINAL OUTPUT DIRECTLY TO notes.txt
# ==============================================================================
DATA_DIR = Path(__file__).resolve().parent
NOTES_FILE = DATA_DIR / "notes.txt"

class DualOutputLogger:
    def __init__(self, log_path):
        self.terminal = sys.stdout
        self.log_file = open(log_path, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

sys.stdout = DualOutputLogger(NOTES_FILE)

# ==============================================================================
# DOMAIN VALIDITY RULES (TO IDENTIFY IMPOSSIBLE / OUT-OF-RANGE OUTLIERS)
# ==============================================================================
def check_domain_rules(col_name, series):
    """Flags values that are physically or biologically impossible/out-of-range."""
    issues = []
    s = series.dropna()
    if s.empty:
        return "No data"

    # 1. Non-negative physical/chemical properties
    non_negative_cols = [
        'mol_weight', 'psa', 'hbd', 'hba', 'rtb', 'aromatic_rings',
        'ro5_violations', 'value', 'standard_value', 'pchembl_value'
    ]
    if col_name in non_negative_cols:
        negatives = s[s < 0]
        if not negatives.empty:
            issues.append(f"OUT-OF-RANGE: {len(negatives)} negative value(s) (min: {negatives.min()})")

    # 2. Clinical Phases: strictly in [0, 4]
    if 'max_phase' in col_name:
        invalid_phase = s[(s < 0) | (s > 4)]
        if not invalid_phase.empty:
            issues.append(f"OUT-OF-RANGE: {len(invalid_phase)} phase value(s) not in [0, 4]")

    # 3. pChEMBL value (-log10 molar affinity, standard range: 2 to 14)
    if col_name == 'pchembl_value':
        abnormal = s[(s < 2) | (s > 14)]
        if not abnormal.empty:
            issues.append(f"SUSPECT: {len(abnormal)} pChEMBL value(s) outside realistic window [2, 14]")

    # 4. Molecular weight (small molecules usually 100 - 1500 Da)
    if col_name == 'mol_weight':
        heavy = s[s > 1500]
        if not heavy.empty:
            issues.append(f"INFO: {len(heavy)} macromolecule(s) with MW > 1500 Da (max: {heavy.max()})")

    # 5. Activity standard values (standard_value <= 0 is invalid for IC50/Ki/Kd)
    if col_name in ['standard_value', 'value']:
        zero_or_neg = s[s <= 0]
        if not zero_or_neg.empty:
            issues.append(f"OUT-OF-RANGE: {len(zero_or_neg)} non-positive activity measurement(s) (<= 0)")

    return "; ".join(issues) if issues else "VALID (No domain violations)"

# ==============================================================================
# 1. CORRELATION HEATMAP
# ==============================================================================
def generate_correlation_heatmap(df, filename):
    """Calculates and displays Pearson correlation matrix and heatmap."""
    num_df = df.select_dtypes(include=[np.number])
    num_df = num_df.loc[:, num_df.nunique() > 1]
    
    if num_df.shape[1] < 2:
        print(f"\n[Correlation] '{filename}' has fewer than 2 numeric features with variance. Skipping heatmap.")
        return

    print(f"\n" + "="*70)
    print(f" 1. CORRELATION HEATMAP: {filename}")
    print("="*70)
    
    corr = num_df.corr(method='pearson')
    print("Correlation Matrix:")
    print(corr.round(2))

    # Detect notable correlations (|r| >= 0.70)
    strong = []
    cols = corr.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.iloc[i, j]
            if abs(r) >= 0.70:
                strong.append((cols[i], cols[j], r))

    if strong:
        print("\nStrong Feature Correlations (|r| >= 0.70):")
        for c1, c2, r in strong:
            print(f"  • {c1:20} <---> {c2:20} : r = {r:+.3f}")
    else:
        print("\nNo strong multi-collinearity (|r| >= 0.70) found.")

    # Plot
    fig_dim = max(7, min(14, len(cols) * 1.15))
    plt.figure(figsize=(fig_dim, fig_dim * 0.85))
    
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        annot_kws={"size": 9}
    )

    plt.title(f"Correlation Heatmap: {filename}", fontsize=13, pad=12, fontweight='bold')
    plt.tight_layout()
    
    out_img = DATA_DIR / f"correlation_{Path(filename).stem}.png"
    plt.savefig(out_img, dpi=300)
    print(f"[OK] Saved plot: {out_img.name}")
    plt.show()

# ==============================================================================
# 2. OUTLIER DETECTION (IQR METHOD) & BOXPLOTS
# ==============================================================================
def generate_outliers_report_and_plots(df, filename):
    """Computes IQR bounds, detects statistical & domain outliers, and plots boxplots."""
    num_df = df.select_dtypes(include=[np.number])
    valid_cols = [c for c in num_df.columns if df[c].dropna().nunique() > 1]
    
    if not valid_cols:
        return

    print(f"\n" + "="*70)
    print(f" 2. OUTLIER AUDIT (IQR & DOMAIN RULES): {filename}")
    print("="*70)

    records = []
    for col in valid_cols:
        s = df[col].dropna()
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        
        # Mild outliers (1.5x IQR)
        lower_1_5 = q1 - 1.5 * iqr
        upper_1_5 = q3 + 1.5 * iqr
        mild = s[(s < lower_1_5) | (s > upper_1_5)]
        
        # Extreme outliers (3.0x IQR)
        lower_3_0 = q1 - 3.0 * iqr
        upper_3_0 = q3 + 3.0 * iqr
        extreme = s[(s < lower_3_0) | (s > upper_3_0)]

        domain_verdict = check_domain_rules(col, s)

        records.append({
            'Feature': col,
            'Total': len(s),
            'Min': round(s.min(), 2),
            'Max': round(s.max(), 2),
            'Mean': round(s.mean(), 2),
            'IQR': round(iqr, 2),
            '1.5x IQR Bounds': f"[{lower_1_5:.1f}, {upper_1_5:.1f}]",
            'Mild Outliers (1.5x)': f"{len(mild)} ({len(mild)/len(s)*100:.1f}%)",
            'Extreme Outliers (3.0x)': f"{len(extreme)} ({len(extreme)/len(s)*100:.1f}%)",
            'Domain Out-of-Range Verdict': domain_verdict
        })

    report_df = pd.DataFrame(records)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(report_df.to_string(index=False))

    # Boxplots Grid
    n_cols = min(3, len(valid_cols))
    n_rows = (len(valid_cols) + n_cols - 1) // n_cols
    plt.figure(figsize=(5 * n_cols, 4 * n_rows))

    for idx, col in enumerate(valid_cols, 1):
        ax = plt.subplot(n_rows, n_cols, idx)
        s = df[col].dropna()

        sns.boxplot(
            y=s,
            ax=ax,
            color="#85C1E9",
            flierprops=dict(marker='o', markersize=5, markerfacecolor='#E74C3C', markeredgecolor='darkred', alpha=0.7)
        )

        ax.set_title(f"{col}", fontsize=11, fontweight='bold')
        ax.set_ylabel("Value")
        ax.grid(True, linestyle='--', alpha=0.5)

    plt.suptitle(f"Outlier Boxplots: {filename}", fontsize=14, y=1.01, fontweight='bold')
    plt.tight_layout()

    out_img = DATA_DIR / f"outliers_{Path(filename).stem}.png"
    plt.savefig(out_img, dpi=300)
    print(f"[OK] Saved plot: {out_img.name}")
    plt.show()

# ==============================================================================
# MAIN PIPELINE
# ==============================================================================
def main():
    print("\n" + "#"*75)
    print(" DRUGSCOPE AI - FULL DATASET CORRELATION & OUTLIER AUDIT (graph.py)")
    print(f" Working Directory: {DATA_DIR}")
    print("#"*75)

    csv_files = sorted(list(DATA_DIR.glob("*.csv")))
    if not csv_files:
        print("[!] No CSV files found in data/raw/.")
        return

    for f in csv_files:
        print(f"\n==================================================================")
        print(f" DATASET: {f.name}")
        print(f"==================================================================")
        try:
            df = pd.read_csv(f, sep=None, engine='python')
        except Exception as e:
            print(f"[!] Could not load {f.name}: {e}")
            continue

        # 1. Correlation Heatmap
        generate_correlation_heatmap(df, f.name)

        # 2. Outliers Report & Boxplots
        generate_outliers_report_and_plots(df, f.name)

    print("\n" + "#"*75)
    print(" SUMMARY CONCLUSION:")
    print("  - Statistical Outliers (data points beyond 1.5x or 3.0x IQR) are normal in")
    print("    biomedical datasets (e.g. high molecular weight drugs, highly potent IC50).")
    print("  - Domain Out-of-Range Outliers (physically impossible values like negative MW,")
    print("    negative activity, or invalid phases) are flagged above under 'Domain Verdict'.")
    print("  - All results and tables have been recorded in data/raw/notes.txt")
    print("#"*75 + "\n")

if __name__ == "__main__":
    main()
