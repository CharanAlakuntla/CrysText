# Dataset

Place your `.cif` files in the `cif_files/` directory.

## Getting 1000+ CIF files

### Option 1 – Materials Project (recommended)
1. Get a free API key at https://materialsproject.org
2. Run the download script:
   ```bash
   pip install mp-api
   python scripts/download_mp.py --api-key YOUR_KEY --count 1000
   ```

### Option 2 – COD (Crystallography Open Database)
- Free, no API key required
- Download bulk from https://www.crystallography.net/cod/

### Option 3 – Copy from existing project
If you already have CIF files in `../data/cifs/`, copy them here:
```bash
copy ..\data\cifs\*.cif cif_files\
```

## After adding CIF files
Run the ingest script from the `backend/` directory:
```bash
cd backend
python ingest.py
```
