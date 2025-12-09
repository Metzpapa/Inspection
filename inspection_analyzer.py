import base64
import json
import os
import re
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    print("Error: OPENROUTER_API_KEY not found in .env file")
    exit()

CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Directories to scan
INSPECTION_FOLDERS = [
    '8 Barnes Avenue Nov 3 Inspection',
    '8 Barnes Avenue Dec 1 Inspection',
    '8 Barnes Avenue Nov 3 Clean',
    '8 Barnes Avenue Nov 30 Clean'
]

# Output directory
OUTPUT_DIR = 'Analysis_Results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize_filename(filename):
    """
    Extract base name from filename by removing prefixes, numbers, and extensions.
    Examples:
        "- TVs remotes apple box eeros etc 1.jpg" -> "tvs remotes apple box eeros etc"
        "- Audio system brand speaker locations controller.jpg" -> "audio system brand speaker locations controller"
    """
    # Remove extension
    name = os.path.splitext(filename)[0]

    # Remove leading dash and spaces
    name = re.sub(r'^-\s*', '', name)

    # Remove trailing numbers (e.g., " 1", " 2", etc.)
    name = re.sub(r'\s+\d+$', '', name)

    # Remove parentheses with numbers (e.g., " (1)", " (2)")
    name = re.sub(r'\s*\(\d+\)$', '', name)

    # Lowercase and strip for consistent matching
    return name.lower().strip()

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_photo_group(group_name, photo_paths):
    """
    Send a group of photos to Gemini for analysis.
    Returns: dict with analysis results
    """
    print(f"\n{'='*80}")
    print(f"📤 Sending to Gemini: '{group_name}'")
    print(f"   Photos in group ({len(photo_paths)}):")
    for path in photo_paths:
        folder = os.path.basename(os.path.dirname(path))
        filename = os.path.basename(path)
        print(f"      - [{folder}] {filename}")
    print(f"{'='*80}\n")

    try:
        # Build message content
        if len(photo_paths) == 1:
            prompt_text = (
                "You are a property manager. Would a guest be unhappy seeing this?\n"
                "Flag anything that looks bad: damage, mess, poorly made beds, dirty areas, broken items, stains, etc.\n\n"
                "Return JSON: {\"has_issues\": true/false, \"description\": \"what's wrong\", "
                "\"severity\": \"none/minor/moderate/severe\"}"
            )
        else:
            prompt_text = (
                "You are a property manager. These photos show the same area across different dates.\n"
                "Flag anything a guest wouldn't want to see: damage, mess, poorly made beds, dirty areas, broken items, stains, etc.\n\n"
                "Return JSON: {\"has_issues\": true/false, \"description\": \"what's wrong\", "
                "\"severity\": \"none/minor/moderate/severe\", \"changes_over_time\": \"any changes or 'none'\"}"
            )

        content = [{"type": "text", "text": prompt_text}]

        # Add all images
        for path in photo_paths:
            base64_image = encode_image(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

        # Call Gemini
        response = CLIENT.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content

        # Clean up response
        if "```json" in result_text:
            result_text = result_text.replace("```json", "").replace("```", "")

        result = json.loads(result_text)

        # Print result
        has_issues = result.get("has_issues", False)
        severity = result.get("severity", "unknown")
        description = result.get("description", "No description")

        if has_issues:
            print(f"🔴 ISSUES FOUND ({severity.upper()}): {description}")
        else:
            print(f"🟢 NO ISSUES: {description}")

        if len(photo_paths) > 1:
            changes = result.get("changes_over_time", "none")
            if changes.lower() != "none":
                print(f"📊 Changes over time: {changes}")

        return {
            "group_name": group_name,
            "photo_paths": photo_paths,
            "result": result
        }

    except Exception as e:
        print(f"❌ Error analyzing group '{group_name}': {e}")
        return None

def save_result(result, output_file):
    """Append a single result to the JSON file."""
    # Load existing results
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            try:
                all_results = json.load(f)
            except json.JSONDecodeError:
                all_results = []
    else:
        all_results = []

    # Append new result
    all_results.append(result)

    # Write back
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

def main():
    print("🔍 Scanning inspection/clean folders...\n")

    # Step 1: Collect all photos and group by base name
    photo_groups = defaultdict(list)

    for folder in INSPECTION_FOLDERS:
        if not os.path.exists(folder):
            print(f"⚠️  Folder not found: {folder}")
            continue

        files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        print(f"📁 {folder}: {len(files)} photos")

        for filename in files:
            base_name = normalize_filename(filename)
            full_path = os.path.join(folder, filename)
            photo_groups[base_name].append(full_path)

    print(f"\n✅ Found {len(photo_groups)} unique photo groups")
    print(f"📊 Total photos: {sum(len(paths) for paths in photo_groups.values())}\n")

    # Step 2: Analyze each group and save as we go
    output_file = os.path.join(OUTPUT_DIR, 'analysis_results.json')
    issues_found = 0
    total_analyzed = 0

    for idx, (base_name, photo_paths) in enumerate(photo_groups.items(), 1):
        print(f"\n[{idx}/{len(photo_groups)}] Processing group...")

        result = analyze_photo_group(base_name, photo_paths)
        if result:
            save_result(result, output_file)
            total_analyzed += 1
            if result['result'].get('has_issues', False):
                issues_found += 1

    # Step 3: Summary
    print(f"\n{'='*80}")
    print(f"✅ Analysis complete! Results saved to: {output_file}")
    print(f"{'='*80}\n")

    print(f"📊 SUMMARY:")
    print(f"   Total groups analyzed: {total_analyzed}")
    print(f"   Groups with issues: {issues_found}")
    print(f"   Groups without issues: {total_analyzed - issues_found}")

if __name__ == "__main__":
    main()
