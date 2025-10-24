#!/usr/bin/env bash

# Downloads all VulFixVUl files into a directory.
# Expects a JSON file of the VulFixVul repos as an array of objects with each
# object have a "url" key whose value is a clone-able `git` repository as input

VFV_JSON_FILE=$1

jq -r '.[].url' "$VFV_JSON_FILE" | sort -u | while read -r url; do
    author=$(basename "$(dirname "$url")")
    repo=$(basename "$url" .git)
    git clone $url ${author}_${repo}
done
