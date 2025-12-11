import json
import os

# Configuration
APPROVED_DIR = 'Reviewed_Inspection_Report'
AI_RESULTS_FILE = 'Analysis_Results/analysis_results.json'
DRAFT_FILE = 'draft_data.json'

def prepare_draft():
    # 1. Load original AI results
    if os.path.exists(AI_RESULTS_FILE):
        with open(AI_RESULTS_FILE, 'r') as f:
            raw_data = json.load(f)
    else:
        raw_data = []

    # Create a lookup dictionary for fast access
    # Key: "folder/filename", Value: Analysis Data
    ai_lookup = {}
    for item in raw_data:
        key = f"{item['folder']}/{item['filename']}"
        ai_lookup[key] = item

    # 2. Scan Approved Directory
    draft_items = []
    
    for root, dirs, files in os.walk(APPROVED_DIR):
        folder_name = os.path.basename(root)
        if folder_name == APPROVED_DIR: continue

        for filename in files:
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue

            # Try to find original AI data
            key = f"{folder_name}/{filename}"
            original = ai_lookup.get(key)

            # Default values
            description = ""
            severity = "minor"
            
            if original:
                description = original['analysis'].get('description', '')
                severity = original['analysis'].get('severity', 'minor')

            # Create the draft entry
            draft_items.append({
                "id": key, # Unique ID
                "folder": folder_name,
                "filename": filename,
                "image_path": os.path.join(APPROVED_DIR, folder_name, filename),
                "description": description,
                "severity": severity,
                "importance": severity, # Default importance to severity
                "task": "" # Blank for you to fill in
            })

    # 3. Save Draft JSON
    with open(DRAFT_FILE, 'w') as f:
        json.dump(draft_items, f, indent=2)

    print(f"✅ Draft prepared with {len(draft_items)} items.")
    print(f"📄 Saved to: {DRAFT_FILE}")

if __name__ == "__main__":
    prepare_draft()