#!/bin/bash

VFV_JSON_FILE=$1

jq -r '.[].url' "$VFV_JSON_FILE" | sort -u | while read -r url; do
    author=$(basename "$(dirname "$url")")
    repo=$(basename "$url" .git)

    if [ -f ${author}_${repo}.json ]; then
        continue
    else
        scorecard \
            --format json \
            --output ${author}_${repo}.json \
            --repo $url
    fi;
done



for file in $(ls *.json); do
    score=$(jq .score $file)
    echo ${file},${score} >> openssf_scores.csv
done
