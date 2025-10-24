#!/bin/bash

# Downloads latest CWE infomration in XML format

ZIP_FILENAME="../cwe/cwe.zip"

wget -nc -O $ZIP_FILENAME https://cwe.mitre.org/data/xml/cwec_latest.xml.zip
unzip $ZIP_FILENAME -d "../cwe"
