#!/usr/bin/env python3
import json
import glob
import os
import argparse

# Keys to sanitize in the Prometheus exported metric labels
SENSITIVE_KEYS = {
    "hashed_api_key",
    "user",
    "user_email",
    "api_key_alias",
    "team_alias",
    "end_user",
    "team"
}

def sanitize_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {input_path} (not valid JSON): {e}")
        return

    # Typical PromQL export structure:
    # {"status": "success", "data": {"resultType": "matrix", "result": [{"metric": {"key": "value"}, "values": [...]}]}}
    
    modified = False
    if "data" in data and "result" in data["data"]:
        for item in data["data"]["result"]:
            if "metric" in item:
                metric_labels = item["metric"]
                for key in list(metric_labels.keys()):
                    if key in SENSITIVE_KEYS:
                        if metric_labels[key] != "None":
                            metric_labels[key] = "REDACTED"
                            modified = True
                        else:
                            # Already None, but let's be safe
                            metric_labels[key] = "REDACTED"
                            modified = True

    # We write it regardless so that the output dir gets a copy of all files.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))
        
    if modified:
        print(f"Sanitized: {input_path} -> {output_path}")
    else:
        print(f"Copied (no sensitive data found): {input_path} -> {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Sanitize Prometheus JSON exports")
    parser.add_argument("--input-dir", required=True, help="Directory containing raw JSON files")
    parser.add_argument("--output-dir", required=True, help="Directory to save sanitized JSON files")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_dir):
        print(f"Input directory does not exist: {args.input_dir}")
        return
        
    for filepath in glob.glob(os.path.join(args.input_dir, "*.json")):
        basename = os.path.basename(filepath)
        out_path = os.path.join(args.output_dir, basename)
        sanitize_file(filepath, out_path)

if __name__ == "__main__":
    main()
