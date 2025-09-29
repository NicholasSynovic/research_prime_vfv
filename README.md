# PRIME + VFV Research

> Correlating risky-fix vulnerabilities to software engineering processes

## Table of Contents

- [PRIME + VFV Research](#prime--vfv-research)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Getting Started](#getting-started)

## About

asdf

## Getting Started

1. Create Python virtual environment: `make create-dev`
1. Sync submodules: `git submodule update --init --recursive`
1. Download data: `./scripts/download_cwe_list_4.17.bash`
1. Extract VulFixVul projects to JSON:
   `python scripts/extract_repos_from_vfv.py -i VulnerabilityReintroducingDataset/merged_dataset_with_CVE_CWE.csv -o vfv.json`
1. Clone repos: `./scripts/clone_vfv_repos.bash vfv.json`
