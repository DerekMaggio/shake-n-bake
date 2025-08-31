#!/bin/bash

STARTS_WITH=""
OUTPUT_FORMAT="hcl"
POSITIONAL=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --starts-with)
            STARTS_WITH="$2"
            shift 2
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

JSON_FILES=("${POSITIONAL[@]}")
if [ ${#JSON_FILES[@]} -eq 0 ]; then
    echo "Usage: $0 [--starts-with <prefix>] [--output-format json|hcl] <json_file1> <json_file2> ..."
    exit 1
fi
if ! command -v jq &> /dev/null; then
    echo "jq is required but not installed. Please install jq and try again."
    exit 1
fi

if [ ${#JSON_FILES[@]} -eq 1 ]; then
    input=$(<"${JSON_FILES[0]}")
else
    input=$(jq -s '.[0] * .[1]' "${JSON_FILES[@]}")
    if [ $? -ne 0 ]; then
        echo "Error merging JSON files."
        exit 1
    fi
fi

if [ -n "$STARTS_WITH" ]; then
    filter="with_entries(select(.key | startswith(\"$STARTS_WITH\")))"
else
    filter="."
fi

if [ "$OUTPUT_FORMAT" = "json" ]; then
    echo "${input}" | jq "$filter"
elif [ "$OUTPUT_FORMAT" = "hcl" ]; then
    echo "${input}" | jq -r "
        $filter
        | to_entries 
        | ([\"variable \\\"_images\\\" {\\n  default = {\"] 
            + (map(\"    \\\"\" + .key + \"\\\" = [\\n\" 
                + ( .value | map(\"      \\\"\" + . + \"\\\"\") | join(\",\\n\") ) 
                + \"\\n    ]\") ) 
            + [\"  }\\n}\"]
        ) 
        | join(\"\\n\")
        "
else
    echo "Unknown output format: $OUTPUT_FORMAT"
    exit 1
fi