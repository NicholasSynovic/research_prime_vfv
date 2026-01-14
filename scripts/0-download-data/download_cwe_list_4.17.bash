#!/bin/bash

# Downloads latest CWE infomration in XML format

ZIP_FILENAME="../cwe/cwe.zip"

wget -nc -O $ZIP_FILENAME https://cwe.mitre.org/data/xml/cwec_v4.17.xml.zip
unzip $ZIP_FILENAME -d "../cwe"
