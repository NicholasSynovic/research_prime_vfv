# Process-based Indicators of Vulnerability Re-Introducing Code Changes: An Exploratory Case Study

> Correlating software engineering process metrics to software vulnerability
> reintroduction

![arXiv](https://img.shields.io/badge/arXiv-10.48550%2FarXiv.2510.26676-red?link=https://arxiv.org/abs/2510.26676)

## Table of Contents

- [Process-based Indicators of Vulnerability Re-Introducing Code Changes: An Exploratory Case Study](#process-based-indicators-of-vulnerability-re-introducing-code-changes-an-exploratory-case-study)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
    - [Pre-Print Paper Abstract](#pre-print-paper-abstract)
  - [Running The Project](#running-the-project)
    - [Dependencies](#dependencies)
    - [Steps](#steps)

## About

This repository hosts the necessary code to replicate our study *Process-based
Indicators of Vulnerability Re-Introducing Code Changes: An Exploratory Case
Study*.

✨This work was accepted to the
[**Software Vulnerability Management (SVM) Workshop @ ICSE '26**](https://conf.researchr.org/home/icse-2026/svm-2026)✨

### Pre-Print Paper Abstract

> Taken from our paper's abstract. Read the arXiv preprint
> [here](https://arxiv.org/abs/2510.26676)

*Software vulnerabilities often persist or re-emerge even after being fixed,
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
security.*

## Running The Project

### Dependencies

Our work relies on:

- Python 3.13.9,
- OpenSSF Scorecard v5.3.0,
- [CWE Version 4.17](https://cwe.mitre.org/data/xml/cwec_v4.17.xml.zip),
- [CVEProject/cvelistV5 @ 0d9f00ef6f76fd013e7bcd2bc85580920f20a595](https://github.com/CVEProject/cvelistV5/tree/0d9f00ef6f76fd013e7bcd2bc85580920f20a595),
  and
- [anonSubmissionGithub/VulnerabilityReintroducingDataset @ ea86ca55363e905af504a0d6242681ae3f184f83](https://github.com/anonSubmissionGithub/VulnerabilityReintroducingDataset/tree/ea86ca55363e905af504a0d6242681ae3f184f83).

<!-- TODO: Add Zenodo release link -->

Datasets are availible for downloading from our [Zenodo] release.

### Steps

> Relies on downloading the latest Zenodo release

1. Clone the
   [`ImageMagick/ImageMagick`](https://github.com/ImageMagick/ImageMagick.git)
   `git` repository

```bash
git clone https://github.com/ImageMagick/ImageMagick.git
```

2. Create the virtual environment

```bash
make create-dev
```

3. Build the project

```bash
make build
```
