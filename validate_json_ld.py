import json
import os
import glob

def validate_json_ld(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find JSON-LD script
        start = content.find('<script type="application/ld+json">')
        if start == -1:
            return False, "No JSON-LD script found"

        start += len('<script type="application/ld+json">')
        end = content.find('</script>', start)
        if end == -1:
            return False, "No closing script tag found"

        json_str = content[start:end].strip()
        json_obj = json.loads(json_str)
        return True, "Valid"
    except json.JSONDecodeError as e:
        return False, f"JSON decode error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    html_files = glob.glob('*.html') + glob.glob('areas/*.html')
    total = len(html_files)
    valid = 0
    invalid = 0

    for file_path in html_files:
        is_valid, message = validate_json_ld(file_path)
        if is_valid:
            valid += 1
            print(f"✓ {file_path}: {message}")
        else:
            invalid += 1
            print(f"✗ {file_path}: {message}")

    print(f"\nSummary: {valid}/{total} files have valid JSON-LD")

if __name__ == "__main__":
    main()