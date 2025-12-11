import json
import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
DRAFT_FILE = 'draft_data.json'

@app.route('/')
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Report Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #121212; --card: #1e1e1e; --text: #fff; --border: #333; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { font-weight: 300; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
        
        .editor-card {
            display: flex; gap: 20px; background: var(--card); padding: 20px;
            border-radius: 8px; margin-bottom: 20px; border: 1px solid var(--border);
        }
        .img-col { flex: 0 0 300px; }
        .img-col img { width: 100%; border-radius: 4px; }
        .data-col { flex: 1; display: flex; flex-direction: column; gap: 15px; }
        
        label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 5px; }
        input, textarea, select {
            width: 100%; background: #2a2a2a; border: 1px solid #333; color: white;
            padding: 10px; border-radius: 4px; font-family: inherit;
        }
        textarea { min-height: 80px; resize: vertical; }
        
        .row { display: flex; gap: 20px; }
        .col { flex: 1; }

        .save-indicator { position: fixed; bottom: 20px; right: 20px; background: #2ecc71; color: white; padding: 10px 20px; border-radius: 50px; opacity: 0; transition: opacity 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Report Editor</h1>
        <div id="cards-container"></div>
    </div>
    <div id="save-indicator" class="save-indicator">Saved</div>

    <script>
        let data = [];

        async function loadData() {
            const res = await fetch('/data');
            data = await res.json();
            render();
        }

        function render() {
            const container = document.getElementById('cards-container');
            container.innerHTML = data.map((item, index) => `
                <div class="editor-card">
                    <div class="img-col">
                        <img src="${item.image_path}" loading="lazy">
                        <div style="margin-top:10px; font-size:0.8rem; color:#666;">${item.filename}</div>
                    </div>
                    <div class="data-col">
                        <div>
                            <label>Description</label>
                            <textarea onchange="update(${index}, 'description', this.value)">${item.description}</textarea>
                        </div>
                        <div>
                            <label>Recommended Task</label>
                            <input type="text" placeholder="e.g. Replace batteries, Schedule deep clean..." 
                                   value="${item.task}" onchange="update(${index}, 'task', this.value)">
                        </div>
                        <div class="row">
                            <div class="col">
                                <label>Importance</label>
                                <select onchange="update(${index}, 'importance', this.value)">
                                    <option value="low" ${item.importance === 'low' ? 'selected' : ''}>Low</option>
                                    <option value="medium" ${item.importance === 'medium' ? 'selected' : ''}>Medium</option>
                                    <option value="high" ${item.importance === 'high' ? 'selected' : ''}>High</option>
                                    <option value="critical" ${item.importance === 'critical' ? 'selected' : ''}>Critical</option>
                                </select>
                            </div>
                            <div class="col">
                                <label>Severity (AI)</label>
                                <input type="text" value="${item.severity}" disabled style="opacity: 0.5; cursor: not-allowed;">
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        async function update(index, field, value) {
            data[index][field] = value;
            
            // Show save indicator
            const ind = document.getElementById('save-indicator');
            ind.style.opacity = '1';
            setTimeout(() => ind.style.opacity = '0', 1000);

            await fetch('/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        }

        loadData();
    </script>
</body>
</html>
    """

@app.route('/data')
def get_data():
    if os.path.exists(DRAFT_FILE):
        with open(DRAFT_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/save', methods=['POST'])
def save_data():
    with open(DRAFT_FILE, 'w') as f:
        json.dump(request.json, f, indent=2)
    return jsonify({"status": "saved"})

@app.route('/<path:filename>')
def serve_files(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    print("🚀 Editor running at http://localhost:5001")
    app.run(port=5001, debug=True)