import base64
import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
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

# Directories
SOURCE_FOLDERS = ['New_Photos', 'Old_Photos']
DIR_DAMAGED = 'Sorted_Images/Damaged'
DIR_CLEAN = 'Sorted_Images/No_Damage'

# Create output directories
os.makedirs(DIR_DAMAGED, exist_ok=True)
os.makedirs(DIR_CLEAN, exist_ok=True)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(file_path):
    filename = os.path.basename(file_path)
    
    # --- SKIP LOGIC ---
    # Check if this file is already in Damaged or Clean folders
    if os.path.exists(os.path.join(DIR_DAMAGED, filename)):
        print(f"⏭️  Skipping {filename} (Already in Damaged)")
        return None
    if os.path.exists(os.path.join(DIR_CLEAN, filename)):
        print(f"⏭️  Skipping {filename} (Already in Clean)")
        return None
    # ------------------

    print(f"Analyzing: {filename}...")

    try:
        base64_image = encode_image(file_path)

        response = CLIENT.chat.completions.create(
            model="google/gemini-3-pro-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": (
                                "You are a property inspector. Analyze this image for PROPERTY DAMAGE.\n"
                                "Look for: Stains on carpet/walls, holes, cracks, broken glass, water damage, mold, or broken fixtures.\n"
                                "Ignore: Clutter, messy beds, or old furniture styles. Only flag actual damage or filth.\n"
                                "Return a JSON object with this exact format:\n"
                                "{\"has_damage\": true, \"reason\": \"brief description of damage\"}\n"
                                "If no damage, set has_damage to false."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"} 
        )

        result_text = response.choices[0].message.content
        if "```json" in result_text:
            result_text = result_text.replace("```json", "").replace("```", "")
            
        result_json = json.loads(result_text)
        
        return {
            "file_path": file_path,
            "filename": filename,
            "has_damage": result_json.get("has_damage", False),
            "reason": result_json.get("reason", "No reason provided")
        }

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return None

def process_and_move(file_path):
    result = analyze_image(file_path)
    
    if result:
        if result['has_damage']:
            destination = os.path.join(DIR_DAMAGED, result['filename'])
            print(f"🔴 DAMAGE DETECTED: {result['filename']} ({result['reason']})")
        else:
            destination = os.path.join(DIR_CLEAN, result['filename'])
            print(f"🟢 CLEAN: {result['filename']}")
        
        shutil.copy2(result['file_path'], destination)

def main():
    all_images = []
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')

    print(f"Scanning folders...")
    for folder in SOURCE_FOLDERS:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(valid_extensions):
                        all_images.append(os.path.join(root, file))

    print(f"Found {len(all_images)} total images. Checking which ones need processing...")
    
    # Process in Parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_and_move, all_images)

    print("\nProcessing Complete!")

if __name__ == "__main__":
    main()