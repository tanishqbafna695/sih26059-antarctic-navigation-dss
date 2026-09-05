# Account Setup — Real Data Downloads

Phase 4's pipeline is verified on synthetic data. To exercise the **real-data path**
(close the gap), two free Copernicus accounts are required. Both take ~2 minutes
to create and are free for any use including commercial.

---

## 1. Copernicus Climate Data Store (CDS) — ERA5 atmospheric forcing + waves

**Used for:** ERA5 single-levels (10 m wind, 2 m temperature, MSLP, SST, wave parameters)
**Product:** `reanalysis-era5-single-levels` (0.25°, hourly/6-hourly, 1940–present)
**License:** Copernicus licence (free incl. commercial use, attribution required)

### Steps

1. Go to **https://cds.climate.copernicus.eu**
2. Click **Register** and create a free account (email + password)
3. After email verification, log in
4. Click your **username** (top-right) → **Profile**
5. Under **API Key**, click **Show Key**
6. Copy both values:
   - **URL** (e.g. `https://cds.climate.copernicus.eu/api`)
   - **Key** (e.g. `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)

### Accept the ERA5 licence

Before the first download, you **must** accept the ERA5 licence:
1. Go to https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
2. Scroll down and click **"Accept licence"**

### Environment variables

```
CDSAPI_URL=https://cds.climate.copernicus.eu/api
CDSAPI_KEY=your-key-here
```

### Python client

The pipeline uses `cdsapi` (free, `pip install cdsapi`). On first use CDS may
ask you to accept a licence agreement for ERA5 — log into the CDS web interface
and accept it before the first download.

---

## 2. Copernicus Marine Environment Monitoring Service (CMEMS) — ocean + sea ice

**Used for:** GLORYS12 ocean reanalysis (currents, SST), OSI SAF sea-ice concentration
and drift
**Products:** `cmems_mod_glo_phy_my_0.083deg_P1D-m` (GLORYS12),
`osisaf_obs-si_glo_phy_sic-south_my_amsr_cdr_P1D-m` (SIC),
`cmems_obs-si_glo_phy-drift-south_my_l4_P1D-m` (drift)
**License:** Copernicus licence (attribution required)

### Steps

1. Go to **https://data.marine.copernicus.eu**
2. Click **Register** and create a free account (email + password)
3. After email verification, log in — your **email is your username**
4. No separate API key is needed; the pipeline authenticates with email + password directly
5. Accept any licence agreements for the products you need (click "Accept" on the product page)

### Environment variables

```
CMEMS_USERNAME=your-email@example.com
CMEMS_PASSWORD=your-password
```

### Python client

The pipeline uses `copernicusmarine` (free, `pip install copernicusmarine`). On
first use you may need to accept a licence in the CMEMS web interface.

---

## 3. Set credentials locally (one-time)

### PowerShell (current session only)

```powershell
$env:CDSAPI_URL      = "https://cds.climate.copernicus.eu/api"
$env:CDSAPI_KEY       = "your-cds-key-here"
$env:CMEMS_USERNAME   = "your-cmems-email@example.com"
$env:CMEMS_PASSWORD   = "your-cmems-password"
```

### Or: .env file (loaded before each run)

Create a `.env` file at the project root (already in `.gitignore`):

```
CDSAPI_URL=https://cds.climate.copernicus.eu/api
CDSAPI_KEY=your-cds-key-here
CMEMS_USERNAME=your-cmems-email@example.com
CMEMS_PASSWORD=your-cmems-password
```

Then load it before running the pipeline:

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^#][^=]+)=(.*)') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim()) } }
```

---

## 4. Verify and download

```bash
# Activate the project venv
.venv\Scripts\Activate

# Verify credentials (downloads nothing)
python scripts/data_fetch/fetch_all.py --dry-run

# Run the real fetch (~2-4 GB, depends on network)
python scripts/data_fetch/fetch_all.py
```

The `--dry-run` output shows which products are ready and which credentials
are missing. Once both say **OK**, the real fetch runs all four products:

- OSI SAF sea-ice concentration (daily, 25 km)
- OSI SAF sea-ice drift (daily, 62.5 km)
- ERA5 atmospheric forcing + waves (6-hourly, 0.25°)
- GLORYS12 ocean currents (daily, 1/12°)

Processed feature store + provenance manifests land in `data/processed/` and
`data/manifests/` respectively. Heavy raw data stays in `data/raw/` (gitignored).

---

## 5. Troubleshooting

| Problem | Cause | Fix |
| ------- | ----- | --- |
| `CredentialsMissing: CDS credentials missing` | env vars not set | Check `echo $env:CDSAPI_KEY` |
| `401 Unauthorized` (CDS) | wrong API key | Re-copy from CDS Profile |
| `401 Unauthorized` (CMEMS) | wrong email/password | Re-login at data.marine.copernicus.eu |
| CDS download hangs | large file; first-time queue | CDS may take minutes for large ERA5 requests — be patient |
| CMEMS product not found | product ID changed | Check `data.marine.copernicus.eu` → search the product → update `configs/data_sources.yaml` |
| `403 Forbidden` (CDS) | licence not accepted | Accept ERA5 licence at the product page |
| `cdsapi not installed` | missing dependency | `.venv/Scripts/pip install cdsapi` |
| `copernicusmarine not installed` | missing dependency | `.venv/Scripts/pip install copernicusmarine` |

---

## Zero-cost confirmation

Both accounts are free. Both datasets are free for any use. No paid tiers are
required for anything in this pipeline (§7.4 of `docs/project-definition.md`).