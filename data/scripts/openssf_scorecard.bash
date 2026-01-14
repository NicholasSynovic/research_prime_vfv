#!/bin/bash

# Given a VulFixVul JSON file containing an array of objects that have a "url"
# key whose value is a clone-able `git` repository, run OpenSSF Scorecard on
# each repo and output the results to JSON files. Then take all of the JSON
# files and extract the scores into a CSV file.

VFV_JSON_FILE=$1

jq -r '.[].url' "$VFV_JSON_FILE" | sort -u | while read -r url; do
    author=$(basename "$(dirname "$url")")
    repo=$(basename "$url" .git)

    if [ -f ${author}_${repo}.json ]; then
        continue
    else
        scorecard \
            --format json \
            --output ../openssf_scorecard/${author}_${repo}.json \
            --repo $url
    fi;
done

for file in $(ls *.json); do
    score=$(jq .score $file)
    echo ${file},${score} >> ../openssf_scorecard.csv
done
