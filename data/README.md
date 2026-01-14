# Downloading Data From Original Sources

## Table of Contents

- [Downloading Data From Original Sources](#downloading-data-from-original-sources)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Downloading Common Weakness Enumeration (CWE) Version 4.17 Data](#downloading-common-weakness-enumeration-cwe-version-417-data)
  - [Extracting Repository, CWE, and CVE Pairs From VFV](#extracting-repository-cwe-and-cve-pairs-from-vfv)

## About

The GitHub repository does not contain *all* data files to replicate our work.
If you download this project from Zenodo, then it has all of the necessary data
files. This file aims to help you download the original data files from their
sources. However, we encourage you to download the data and source code from the
Zenodo project for maximum compatibility.

Please note that unless otherwise specified, all data files are stored in this
`data` directory.

## Downloading Common Weakness Enumeration (CWE) Version 4.17 Data

```bash
wget -nc -O cwec.zip https://cwe.mitre.org/data/xml/cwec_v4.17.xml.zip
unzip cwec.zip
```

## Extracting Repository, CWE, and CVE Pairs From VFV

```bash
python scripts/vfv_repositories_cwe_cve.py \
  --input vfv/merged_dataset_with_CVE_CWE.csv \
  --output vfv_repositories_cwe_cve.json
```
