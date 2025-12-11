import os
import shutil
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Configuration
ROOT_DIR = os.getcwd()
REPORT_DIR = os.path.join(ROOT_DIR, 'Analysis_Results')
REVIEWED_DIR = os.path.join(ROOT_DIR, 'Reviewed_Inspection_Report')

# Create output directory if it doesn't exist
os.makedirs(REVIEWED_DIR, exist_ok=True)

print(f"📂 Root Directory: {ROOT_DIR}")
print(f"📂 Reviewed Images will be saved to: {REVIEWED_DIR}")

@app.route('/')
def serve_report():
    """Serves the HTML report."""
    return send_from_directory(REPORT_DIR, 'inspection_report.html')

@app.route('/<path:filename>')
def serve_files(filename):
    """Serves images and other static files relative to root."""
    # This allows the HTML to load images like "../Folder/image.jpg"
    return send_from_directory(ROOT_DIR, filename)

@app.route('/status')
def status():
    """Simple health check for the UI."""
    return jsonify({"status": "running"})

@app.route('/review', methods=['POST'])
def review_action():
    """Handles the Approve/Reject logic."""
    data = request.json
    action = data.get('action')
    folder = data.get('folder')
    filename = data.get('filename')

    if action == 'approve':
        # Construct source path
        source_path = os.path.join(ROOT_DIR, folder, filename)
        
        # Construct destination path
        # We keep the folder structure inside the reviewed dir to avoid name collisions
        dest_folder = os.path.join(REVIEWED_DIR, folder)
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, filename)

        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                print(f"✅ Approved & Copied: {filename}")
                return jsonify({"status": "success", "message": "File copied"})
            else:
                print(f"❌ File not found: {source_path}")
                return jsonify({"status": "error", "message": "Source file not found"}), 404
        except Exception as e:
            print(f"❌ Error copying: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    elif action == 'reject':
        print(f"🗑️ Rejected: {filename}")
        return jsonify({"status": "success", "message": "Item rejected"})

    return jsonify({"status": "error", "message": "Invalid action"}), 400

if __name__ == '__main__':
    print("\n🚀 STARTING REVIEW SERVER...")
    print(f"👉 Open your browser to: http://localhost:5000")
    print("   (Press CTRL+C to stop)\n")
    app.run(port=5000, debug=True)