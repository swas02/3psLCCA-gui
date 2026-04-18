# 3psLCCA - Bridge Life Cycle Cost Analysis

3psLCCA is a desktop application for performing Life Cycle Cost Analysis (LCCA) on bridge infrastructure projects. It evaluates the economic performance of steel design options over their entire life cycle.

---

## ⚙️ Installation (via Conda)

This is the recommended method as it automatically handles all dependencies, including a **portable LaTeX environment** for PDF reports. Using `conda-forge` avoids any Anaconda Terms of Service (ToS) requirements.

### 1. Prerequisites
- **Install Miniconda**: [Download and install Miniconda](https://docs.conda.io/en/latest/miniconda.html).

### 2. Clean Conda Configuration (Run Once)
Run these commands to ensure your Conda setup is clean and uses reliable open-source channels:

```bash
# Remove problematic default channels
conda config --remove channels defaults

# Add required channels
conda config --add channels conda-forge
conda config --add channels osdag
conda config --add channels zehen-249

# Set channel priority to prevent conflicts
conda config --set channel_priority strict
```

### 3. Setup and Run
```bash
# Create the environment using the provided file
conda create -n 3pslcca

# Activate the environment
conda activate 3pslcca

# Install application
conda install three-ps-lcca-gui 

# Run the application
threePSLCCA
```

---

## 🔄 Keeping Up to Date

To get the latest features and bug fixes for both the interface and the calculation engine:

1. **Update the source code**:
   ```bash
   git pull origin main
   ```

2. **Update the environment**:
   ```bash
   # Ensure your environment is active
   conda activate 3pslcca

   # Update libraries and prune old ones
   conda env update -f environment.yml --prune

   # Force update the internal Core engine from GitHub
   pip install --upgrade git+https://github.com/swas02/3psLCCA-core.git@main

   # Re-sync local package entry points
   pip install -e .

   # Launch the application
   three-ps-lcca-gui
   ```

---

## 🗑️ Uninstallation & Cleanup

To completely remove the application and its environment from your system:

```bash
# Deactivate the environment (if active)
conda deactivate

# Remove the conda environment
conda env remove -n 3pslcca
```

---

## 🛠️ Development Setup

If you are contributing to the source code, please **first follow the [Installation (via Conda)](#⚙️-installation-via-conda) steps above**, then complete these additional steps:

1. **Clone the Project**:
   ```bash
   git clone https://github.com/swas02/3psLCCA-gui.git
   cd 3psLCCA-gui
   ```

2. **Install in Editable Mode**:
   This allows you to see your code changes immediately without reinstalling the package:
   ```bash
   # Ensure your environment is active
   conda activate 3pslcca
   
   # Install the project locally for development
   conda env create -f environment.yml -n 3pslcca
   ```

---

## 📄 PDF Report Generation
- **Conda Environment**: Uses a built-in portable LaTeX engine (no extra setup required).
- **Manual Installation**: Requires a system-wide LaTeX distribution (e.g., [MiKTeX](https://miktex.org/)) added to your system PATH.

---

## ❓ Troubleshooting

### SSL Errors (CondaSSLError)
If you encounter an SSL error on Windows (`record layer failure`):
1. Disable SSL verification temporarily: `conda config --set ssl_verify false`.
2. Try the installation again: `conda env create -f environment.yml`.
3. If you use a VPN, try disconnecting it before running the setup.

---

## 🔧 Maintenance & Tools
To access internal database management and debugging tools:
```bash
python devtools/launcher.py
```
Available tools:
- **WPI Database**: Manage Wholesale Price Index data.
- **Catalog Builder**: Rebuild material and section catalogs.
- **Project Inspector**: Repair and inspect `.3psLCCA` project files.
