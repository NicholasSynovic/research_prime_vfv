#!/usr/bin/env bash

VFV_JSON_FILE=$1

jq -r '.[].url' "$VFV_JSON_FILE" | sort -u | while read -r url; do
    author=$(basename "$(dirname "$url")")
    repo=$(basename "$url" .git)
    echo "$url ${author}_${repo}" >> urls.txt
done
