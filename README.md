# PRIME + VFV Research

> Correlating risky-fix vulnerabilities to software engineering processes

## Table of Contents

- [PRIME + VFV Research](#prime--vfv-research)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Getting Started](#getting-started)

## About

> From our paper's abstract. Read the arXiv preprint
> [here](https://arxiv.org/abs/2510.26676)

Software vulnerabilities often persist or re-emerge even after being fixed,
revealing the complex interplay between code evolution and socio-technical
factors. While source code metrics provide useful indicators of vulnerabilities,
software engineering process metrics can uncover patterns that lead to their
introduction. Yet few studies have explored whether process metrics can reveal
risky development activities over time -- insights that are essential for
anticipating and mitigating software vulnerabilities. This work highlights the
critical role of process metrics along with code changes in understanding and
mitigating vulnerability reintroduction. We move beyond file-level prediction
and instead analyze security fixes at the commit level, focusing not only on
whether a single fix introduces a vulnerability but also on the longer sequences
of changes through which vulnerabilities evolve and re-emerge. Our approach
emphasizes that reintroduction is rarely the result of one isolated action, but
emerges from cumulative development activities and socio-technical conditions.
To support this analysis, we conducted a case study on the ImageMagick project
by correlating longitudinal process metrics such as bus factor, issue density,
and issue spoilage with vulnerability reintroduction activities, encompassing 76
instances of reintroduced vulnerabilities. Our findings show that
reintroductions often align with increased issue spoilage and fluctuating issue
density, reflecting short-term inefficiencies in issue management and team
responsiveness. These observations provide a foundation for broader studies that
combine process and code metrics to predict risky fixes and strengthen software
security.

## Getting Started

1. Create Python virtual environment: `make create-dev`
1. Sync submodules: `git submodule update --init --recursive`
1. Download data: `./scripts/download_cwe_list_4.17.bash`
1. Extract VulFixVul projects to JSON:
   `python scripts/extract_repos_from_vfv.py -i VulnerabilityReintroducingDataset/merged_dataset_with_CVE_CWE.csv -o vfv.json`
1. Clone repos: `./scripts/clone_vfv_repos.bash vfv.json`
