import sys
import os
import subprocess
import shutil
import urllib.request
from pathlib import Path

# ==============================================================================
# 1. PYTHON VERSION & COMPATIBILITY MANAGEMENT
# ==============================================================================
TARGET_MAJOR = 3
TARGET_MINOR = 10
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VENV_DIR = PROJECT_ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"

def find_python_310():
    """Search for an existing Python 3.10 installation on the system."""
    # Check py launcher
    try:
        res = subprocess.run(
            ["py", f"-{TARGET_MAJOR}.{TARGET_MINOR}", "-c", "import sys; print(sys.executable)"],
            capture_output=True, text=True, check=True
        )
        path = res.stdout.strip()
        if os.path.exists(path):
            return path
    except Exception:
        pass

    # Check common Windows install paths
    candidate_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / f"Python{TARGET_MAJOR}{TARGET_MINOR}" / "python.exe",
        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Python" / f"Python{TARGET_MAJOR}{TARGET_MINOR}" / "python.exe",
        Path("C:\\") / f"Python{TARGET_MAJOR}{TARGET_MINOR}" / "python.exe",
    ]
    for p in candidate_paths:
        if p.is_file():
            return str(p)

    return None

def install_python_310():
    """Install Python 3.10 using winget or direct official installer."""
    print(f"\n[INFO] Python {TARGET_MAJOR}.{TARGET_MINOR} not found. Attempting automatic installation...")
    
    # Method 1: Try winget (Windows Package Manager)
    try:
        print("[INFO] Trying Windows Package Manager (winget)...")
        result = subprocess.run(
            ["winget", "install", "-e", "--id", f"Python.Python.{TARGET_MAJOR}.{TARGET_MINOR}",
             "--accept-source-agreements", "--accept-package-agreements"],
            check=True
        )
        if result.returncode == 0:
            print("[OK] Python 3.10 installed successfully via winget.")
            return find_python_310()
    except Exception as e:
        print(f"[!] winget method failed ({e}). Trying direct download...")

    # Method 2: Direct download from python.org
    installer_url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
    installer_path = PROJECT_ROOT / "python-3.10.11-amd64.exe"
    try:
        print(f"[INFO] Downloading official Python 3.10 installer from {installer_url} ...")
        urllib.request.urlretrieve(installer_url, installer_path)
        print("[INFO] Running silent installer (adding Python to PATH)...")
        subprocess.run(
            [str(installer_path), "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0"],
            check=True
        )
        if installer_path.exists():
            installer_path.unlink()  # Clean up installer
        print("[OK] Python 3.10 installed successfully.")
        return find_python_310()
    except Exception as e:
        print(f"[ERROR] Could not install Python 3.10 automatically: {e}")
        print("\nPlease manually download and install Python 3.10 from:")
        print("https://www.python.org/downloads/release/python-31011/")
        print("Make sure to check 'Add Python to PATH' during installation.")
        sys.exit(1)

def ensure_environment():
    """Ensure we are running in a Python 3.10 virtual environment with required packages."""
    is_target_version = (sys.version_info.major == TARGET_MAJOR and sys.version_info.minor == TARGET_MINOR)
    
    # Check if already inside the project's .venv
    in_venv = (sys.prefix == str(VENV_DIR)) or (Path(sys.executable) == VENV_PYTHON)

    if not (is_target_version and in_venv):
        print("==========================================================")
        print(f" Environment Check: Current is Python {sys.version.split()[0]}")
        print(f" Target environment: Python {TARGET_MAJOR}.{TARGET_MINOR} (.venv)")
        print("==========================================================")

        # 1. Locate or install Python 3.10
        py310_bin = find_python_310()
        if not py310_bin:
            py310_bin = install_python_310()

        if not py310_bin:
            print("[ERROR] Failed to locate Python 3.10 binary.")
            sys.exit(1)

        # 2. Create virtual environment if missing
        if not VENV_PYTHON.exists():
            print(f"[INFO] Creating virtual environment at {VENV_DIR} using {py310_bin} ...")
            subprocess.run([py310_bin, "-m", "venv", str(VENV_DIR)], check=True)

        # 3. Ensure required packages are installed
        print("[INFO] Checking/installing required packages (numpy, pandas, matplotlib)...")
        subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )
        subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "install", "numpy", "pandas", "matplotlib", "seaborn", "openpyxl"],
            check=True
        )

        # 4. Relaunch script using the Python 3.10 virtual environment
        print("\n[OK] Relaunching script under Python 3.10 virtual environment...\n")
        result = subprocess.run([str(VENV_PYTHON), __file__] + sys.argv[1:])
        sys.exit(result.returncode)

# Run environment verification before importing heavier data libraries
ensure_environment()

# ==============================================================================
# 2. OUTPUT LOGGER (SAVES CONSOLE OUTPUT TO notes.txt)
# ==============================================================================
class DualLogger:
    """Tee print statements to both terminal and notes.txt."""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.filepath = filepath
        self.logfile = open(filepath, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.logfile.write(message)

    def flush(self):
        self.terminal.flush()
        self.logfile.flush()

notes_file = Path(__file__).resolve().parent / "notes.txt"
sys.stdout = DualLogger(notes_file)

# ==============================================================================
# 3. DATA INSPECTION & VISUALIZATION (NUMPY, PANDAS, MATPLOTLIB, SEABORN)
# ==============================================================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import seaborn as sns
except ImportError:
    sns = None

def plot_correlation_heatmap(df, dataset_name, output_dir):
    """Generate and display correlation heatmap for all numeric features."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        print(f"\n[Correlation] '{dataset_name}' has fewer than 2 numeric columns ({numeric_df.shape[1]}). Skipping correlation.")
        return

    print(f"\n--------------------------------------------------")
    print(f" [Correlation Analysis] {dataset_name}")
    print(f"--------------------------------------------------")
    corr = numeric_df.corr(method='pearson')
    print("Pearson Correlation Matrix:")
    print(corr.round(3))

    # Identify strong correlations (|r| >= 0.7, excluding self-correlation)
    strong_corrs = []
    cols = corr.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.iloc[i, j]
            if abs(r) >= 0.7:
                strong_corrs.append((cols[i], cols[j], r))
    
    if strong_corrs:
        print("\nStrong feature correlations (|r| >= 0.70):")
        for col1, col2, r in strong_corrs:
            print(f"  • {col1} <---> {col2} : r = {r:+.3f}")
    else:
        print("\nNo strong correlations (|r| >= 0.70) detected.")

    # Plot Heatmap
    fig_size = max(7, min(14, len(numeric_df.columns) * 1.2))
    plt.figure(figsize=(fig_size, fig_size * 0.85))
    if sns is not None:
        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            cbar=True,
            square=True,
            linewidths=0.5,
            annot_kws={"size": 9}
        )
    else:
        # Fallback to pure matplotlib
        im = plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
        plt.colorbar(im)
        plt.xticks(range(len(cols)), cols, rotation=45, ha='right')
        plt.yticks(range(len(cols)), cols)
        for i in range(len(cols)):
            for j in range(len(cols)):
                plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color="black", fontsize=8)

    plt.title(f"Feature Correlation Heatmap: {dataset_name}", fontsize=13, pad=12)
    plt.tight_layout()
    
    save_path = output_dir / f"correlation_{dataset_name.replace('.csv', '')}.png"
    plt.savefig(save_path, dpi=300)
    print(f"Saved correlation plot to: {save_path.name}")
    plt.show()

def analyze_and_plot_outliers(df, dataset_name, output_dir):
    """Detect mild/extreme outliers using IQR and plot boxplots."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return

    print(f"\n--------------------------------------------------")
    print(f" [Outlier Analysis (IQR Method)] {dataset_name}")
    print(f"--------------------------------------------------")

    outlier_report = []
    valid_cols = []

    for col in numeric_df.columns:
        s = df[col].dropna()
        if len(s) == 0 or s.nunique() <= 1:
            continue
        valid_cols.append(col)

        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower_1_5 = q1 - 1.5 * iqr
        upper_1_5 = q3 + 1.5 * iqr
        lower_3_0 = q1 - 3.0 * iqr
        upper_3_0 = q3 + 3.0 * iqr

        mild_outliers = s[(s < lower_1_5) | (s > upper_1_5)]
        extreme_outliers = s[(s < lower_3_0) | (s > upper_3_0)]

        # Check for physically / domain out-of-range suspects
        suspects = []
        if col in ['mol_weight', 'psa', 'rtb', 'hbd', 'hba', 'value', 'standard_value', 'pchembl_value']:
            negatives = s[s < 0]
            if not negatives.empty:
                suspects.append(f"{len(negatives)} negative value(s)")

        if col == 'max_phase':
            out_phase = s[(s < 0) | (s > 4)]
            if not out_phase.empty:
                suspects.append(f"{len(out_phase)} invalid phases")

        if col == 'pchembl_value':
            out_pchembl = s[(s < 0) | (s > 15)]
            if not out_pchembl.empty:
                suspects.append(f"{len(out_pchembl)} unusual pChEMBL values")

        if col == 'mol_weight':
            heavy = s[s > 1500]
            if not heavy.empty:
                suspects.append(f"{len(heavy)} very high MW (>1500 Da)")

        flag_str = "; ".join(suspects) if suspects else "None detected"

        outlier_report.append({
            'Feature': col,
            'Total': len(s),
            'Min': s.min(),
            'Max': s.max(),
            'Q1': round(q1, 2),
            'Q3': round(q3, 2),
            'IQR': round(iqr, 2),
            '1.5x IQR Bounds': f"[{lower_1_5:.2f}, {upper_1_5:.2f}]",
            'Mild Outliers (1.5x)': f"{len(mild_outliers)} ({len(mild_outliers)/len(s)*100:.1f}%)",
            'Extreme Outliers (3.0x)': f"{len(extreme_outliers)} ({len(extreme_outliers)/len(s)*100:.1f}%)",
            'Out-Of-Range Suspects': flag_str
        })

    if outlier_report:
        report_df = pd.DataFrame(outlier_report)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(report_df.to_string(index=False))

    # Boxplots Grid
    if valid_cols:
        n_cols = min(3, len(valid_cols))
        n_rows = (len(valid_cols) + n_cols - 1) // n_cols
        plt.figure(figsize=(5 * n_cols, 4 * n_rows))

        for idx, col in enumerate(valid_cols, 1):
            ax = plt.subplot(n_rows, n_cols, idx)
            vals = df[col].dropna()
            
            if sns is not None:
                sns.boxplot(y=vals, ax=ax, color='lightskyblue', flierprops=dict(marker='o', markersize=4, markerfacecolor='crimson', alpha=0.6))
            else:
                ax.boxplot(vals, flierprops=dict(marker='o', markersize=4, markerfacecolor='crimson', alpha=0.6))

            ax.set_title(f"{col}", fontsize=11, fontweight='bold')
            ax.set_ylabel("Value")
            ax.grid(True, linestyle='--', alpha=0.5)

        plt.suptitle(f"Outlier Boxplots: {dataset_name}", fontsize=14, y=1.00)
        plt.tight_layout()
        save_path = output_dir / f"outliers_boxplots_{dataset_name.replace('.csv', '')}.png"
        plt.savefig(save_path, dpi=300)
        print(f"Saved outlier boxplots to: {save_path.name}")
        plt.show()

def inspect_tabular(file_path):
    print(f"\n==================================================")
    print(f" [Tabular Data] {file_path.name}")
    print(f"==================================================")
    
    ext = file_path.suffix.lower()
    try:
        if ext in ['.csv', '.txt']:
            df = pd.read_csv(file_path, sep=None, engine='python')
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif ext == '.parquet':
            df = pd.read_parquet(file_path)
        elif ext == '.json':
            df = pd.read_json(file_path)
        else:
            return
    except Exception as e:
        print(f"Error loading file {file_path.name}: {e}")
        return

    print(f"\n-> Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    
    print("\n-> First 5 Rows:")
    print(df.head())

    print("\n-> Column Info & Missing Count:")
    summary_df = pd.DataFrame({
        'Dtype': df.dtypes,
        'Non-Null Count': df.notnull().sum(),
        'Missing Values': df.isnull().sum(),
        '% Missing': (df.isnull().sum() / len(df) * 100).round(2)
    })
    print(summary_df)

    print("\n-> Statistical Summary (Numeric):")
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        print(numeric_df.describe().T[['mean', 'std', 'min', '50%', 'max']])
        
        # 1. Plot histograms
        cols_to_plot = numeric_df.columns.tolist()[:6]
        plt.figure(figsize=(12, 6))
        for idx, col in enumerate(cols_to_plot, 1):
            plt.subplot(2, 3, idx)
            df[col].dropna().hist(bins=25, color='steelblue', edgecolor='black', alpha=0.7)
            plt.title(f"{col}")
            plt.grid(True, linestyle='--', alpha=0.5)
        plt.suptitle(f"Distributions for {file_path.name}", fontsize=14)
        plt.tight_layout()
        plt.show()

        # 2. Correlation Heatmap between all numeric features
        plot_correlation_heatmap(df, file_path.name, file_path.parent)

        # 3. Outlier Analysis & Boxplots
        analyze_and_plot_outliers(df, file_path.name, file_path.parent)
    else:
        print("No numerical columns found to analyze correlations or outliers.")

def inspect_numpy(file_path):
    print(f"\n==================================================")
    print(f" [NumPy File] {file_path.name}")
    print(f"==================================================")
    
    try:
        if file_path.suffix.lower() == '.npy':
            arr = np.load(file_path, allow_pickle=True)
            print(f"-> Array Shape : {arr.shape}")
            print(f"-> Data Type   : {arr.dtype}")
            print(f"-> Dimensions  : {arr.ndim}")
            
            if np.issubdtype(arr.dtype, np.number):
                print(f"-> Min / Max   : {np.nanmin(arr)} / {np.nanmax(arr)}")
                print(f"-> Mean / Std  : {np.nanmean(arr):.4f} / {np.nanstd(arr):.4f}")
            
            print("\n-> Sample Values:")
            print(arr[:5] if arr.ndim > 0 else arr)

            # Visualization based on dimensions
            if arr.ndim == 1 and np.issubdtype(arr.dtype, np.number):
                plt.figure(figsize=(9, 4))
                plt.plot(arr[:500], color='teal', linewidth=1.5)
                plt.title(f"1D Signal (First 500 points): {file_path.name}")
                plt.xlabel("Index")
                plt.ylabel("Value")
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.show()

            elif arr.ndim == 2 and np.issubdtype(arr.dtype, np.number):
                plt.figure(figsize=(7, 5))
                plt.imshow(arr, cmap='viridis', aspect='auto')
                plt.colorbar(label='Intensity')
                plt.title(f"2D Array Heatmap: {file_path.name}")
                plt.show()

            elif arr.ndim == 3 and arr.shape[2] in [1, 3, 4]:
                # Looks like an image array (H, W, C)
                plt.figure(figsize=(6, 6))
                plt.imshow(arr.squeeze(), cmap='gray' if arr.shape[2] == 1 else None)
                plt.title(f"3D Image Tensor: {file_path.name}")
                plt.axis('off')
                plt.show()

        elif file_path.suffix.lower() == '.npz':
            data = np.load(file_path, allow_pickle=True)
            print(f"-> Keys in .npz archive: {list(data.keys())}")
            for key in data.files:
                val = data[key]
                print(f"   • '{key}': shape={val.shape}, dtype={val.dtype}")
    except Exception as e:
        print(f"Error loading NumPy file: {e}")

def inspect_image(file_path):
    print(f"\n==================================================")
    print(f" [Image File] {file_path.name}")
    print(f"==================================================")
    try:
        img = plt.imread(file_path)
        print(f"-> Image Dimensions: {img.shape}")
        print(f"-> Data Type       : {img.dtype}")
        plt.figure(figsize=(6, 6))
        plt.imshow(img)
        plt.title(file_path.name)
        plt.axis('off')
        plt.show()
    except Exception as e:
        print(f"Error reading image: {e}")

def main():
    current_dir = Path(__file__).resolve().parent
    print(f"\n[SCAN] Searching for datasets in: {current_dir}")

    patterns = {
        'tabular': ['*.csv', '*.tsv', '*.xlsx', '*.xls', '*.parquet', '*.json'],
        'numpy': ['*.npy', '*.npz'],
        'image': ['*.png', '*.jpg', '*.jpeg', '*.bmp']
    }

    found = False

    # 1. Inspect Tabular Files
    for pat in patterns['tabular']:
        for f in current_dir.glob(pat):
            found = True
            inspect_tabular(f)

    # 2. Inspect NumPy Files
    for pat in patterns['numpy']:
        for f in current_dir.glob(pat):
            found = True
            inspect_numpy(f)

    # 3. Inspect Image Files (preview up to 3)
    img_count = 0
    for pat in patterns['image']:
        for f in current_dir.glob(pat):
            if img_count < 3:
                found = True
                inspect_image(f)
                img_count += 1

    if not found:
        print("\n[!] No dataset files found inside this folder.")
        print(f"    Put your data files (CSV, Excel, NPY, NPZ, Images) in:")
        print(f"    {current_dir}")
        print(f"    and run this script again!")

if __name__ == "__main__":
    main()
