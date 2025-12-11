import base64
import json
import os
import re
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

def get_task_from_filename(filename):
    """
    Converts a filename into a readable task description.
    Example: "- Audio system brand speaker locations... 1.jpg" -> "Audio system brand speaker locations"
    """
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Remove leading dash and spaces
    name = re.sub(r'^-\s*', '', name)
    # Remove trailing numbers (e.g., " 1", " 2", etc.)
    name = re.sub(r'\s+\d+$', '', name)
    # Remove parentheses with numbers (e.g., " (1)", " (2)")
    name = re.sub(r'\s*\(\d+\)$', '', name)
    
    return name.strip()

def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_single_image(image_path):
    """
    Send a single photo to Gemini to verify the task based on filename.
    """
    filename = os.path.basename(image_path)
    folder_name = os.path.basename(os.path.dirname(image_path))
    task_name = get_task_from_filename(filename)

    print(f"Processing: [{folder_name}] {filename}")
    print(f"   ↳ Task: {task_name}")

    try:
        # Prompt construction
        prompt_text = (
            f"Examine this photo for physical damages only. The item being inspected is: '{task_name}'.\n\n"
            f"STRICT REQUIREMENTS:\n"
            f"- ONLY flag 'has_issues' as true if there is visible physical damage (cracks, breaks, dents, scratches, "
            f"tears, stains that indicate damage, missing parts, structural issues, etc.).\n"
            f"- Do NOT flag normal wear, minor cosmetic imperfections, or general condition issues.\n"
            f"- Do NOT flag cleanliness, messes, or task completion status.\n"
            f"- Be very strict: only clear, obvious physical damage should be flagged.\n"
            f"- If there is any doubt or the damage is minimal/normal wear, mark 'has_issues' as false.\n\n"
            f"Return JSON: {{\"has_issues\": true/false, \"description\": \"short explanation\", "
            f"\"severity\": \"none/minor/moderate/severe\"}}"
        )

        base64_image = encode_image(image_path)
        
        content = [
            {"type": "text", "text": prompt_text},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
        ]

        # Call Gemini
        response = CLIENT.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content

        # Clean up response if markdown is present
        if "```json" in result_text:
            result_text = result_text.replace("```json", "").replace("```", "")

        result = json.loads(result_text)

        # Print result to console
        has_issues = result.get("has_issues", False)
        severity = result.get("severity", "unknown")
        description = result.get("description", "No description")

        if has_issues:
            print(f"   🔴 ISSUE FOUND ({severity.upper()}): {description}")
        else:
            print(f"   🟢 OK")

        return {
            "folder": folder_name,
            "filename": filename,
            "task_derived": task_name,
            "analysis": result
        }

    except Exception as e:
        print(f"   ❌ Error analyzing image: {e}")
        return None

def save_result(result, output_file):
    """Append a single result to the JSON file."""
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            try:
                all_results = json.load(f)
            except json.JSONDecodeError:
                all_results = []
    else:
        all_results = []

    all_results.append(result)

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

def main():
    print("🔍 Starting Individual Image Analysis...\n")
    
    output_file = os.path.join(OUTPUT_DIR, 'analysis_results.json')
    
    # Clear previous results file if you want a fresh start, otherwise it appends
    if os.path.exists(output_file):
        os.remove(output_file)

    total_images = 0
    issues_found = 0

    for folder in INSPECTION_FOLDERS:
        if not os.path.exists(folder):
            print(f"⚠️  Folder not found: {folder}")
            continue

        # Get all images in folder
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        files.sort() # Sort alphabetically

        print(f"\n📂 Entering Folder: {folder} ({len(files)} images)")

        for filename in files:
            full_path = os.path.join(folder, filename)
            
            # Analyze
            result = analyze_single_image(full_path)
            
            if result:
                save_result(result, output_file)
                total_images += 1
                if result['analysis'].get('has_issues', False):
                    issues_found += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"✅ Analysis complete! Results saved to: {output_file}")
    print(f"{'='*80}")
    print(f"📊 SUMMARY:")
    print(f"   Total images analyzed: {total_images}")
    print(f"   Images with issues:    {issues_found}")
    print(f"   Images passed:         {total_images - issues_found}")

if __name__ == "__main__":
    main()