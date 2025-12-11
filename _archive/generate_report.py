import json
import os

# Configuration
INPUT_FILE = 'Analysis_Results/analysis_results.json'
OUTPUT_HTML = 'Analysis_Results/inspection_report.html'

def generate_html_report():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    # Filter Data (Only show issues)
    issues = [item for item in data if item['analysis'].get('has_issues', False)]
    
    total_issues = len(issues)
    severity_counts = {
        'severe': len([i for i in issues if i['analysis'].get('severity') == 'severe']),
        'moderate': len([i for i in issues if i['analysis'].get('severity') == 'moderate']),
        'minor': len([i for i in issues if i['analysis'].get('severity') == 'minor'])
    }

    html_head = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rove Inspection Review</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #121212;
            --bg-card: #1E1E1E;
            --text-main: #ffffff;
            --text-muted: #a0a0a0;
            --severe: #ff4d4d;
            --moderate: #ff9f43;
            --minor: #feca57;
            --success: #2ecc71;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding-bottom: 100px;
        }

        .navbar {
            padding: 20px 40px;
            background: rgba(18, 18, 18, 0.95);
            border-bottom: 1px solid #333;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo { font-size: 1.5rem; letter-spacing: 4px; text-transform: uppercase; }
        
        .status-bar {
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 40px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 30px;
        }

        .card {
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #333;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
        }

        .card.approved { border-color: var(--success); opacity: 0.5; pointer-events: none; }
        .card.rejected { opacity: 0.2; pointer-events: none; filter: grayscale(100%); }

        .card-image-wrapper {
            position: relative;
            width: 100%;
            padding-top: 66.66%;
            background: #000;
            cursor: pointer;
        }

        .card-image {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover;
        }

        .severity-badge {
            position: absolute;
            top: 15px; left: 15px;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            z-index: 2;
        }
        .severity-badge.severe { background: var(--severe); color: white; }
        .severity-badge.moderate { background: var(--moderate); color: white; }
        .severity-badge.minor { background: var(--minor); color: black; }

        .card-content { padding: 20px; flex-grow: 1; }
        .card-title { font-size: 1.1rem; font-weight: 500; margin-bottom: 8px; }
        .card-desc { font-size: 0.9rem; color: #ccc; margin-top: 10px; line-height: 1.5; }

        /* Action Buttons */
        .action-bar {
            display: flex;
            border-top: 1px solid #333;
        }

        .btn {
            flex: 1;
            padding: 15px;
            border: none;
            cursor: pointer;
            font-size: 1.2rem;
            transition: background 0.2s;
            color: white;
        }

        .btn-reject { background: #2a2a2a; color: #ff4d4d; }
        .btn-reject:hover { background: #3a1a1a; }

        .btn-approve { background: #2a2a2a; color: #2ecc71; border-left: 1px solid #333; }
        .btn-approve:hover { background: #1a3a2a; }

    </style>
</head>
<body>

    <nav class="navbar">
        <div class="logo">ROVE REVIEW</div>
        <div class="status-bar">Server Status: <span id="server-status">Checking...</span></div>
    </nav>

    <div class="container">
        <div class="grid">
    """

    html_cards = ""
    
    for i, item in enumerate(issues):
        folder = item['folder']
        filename = item['filename']
        task = item['task_derived']
        severity = item['analysis'].get('severity', 'unknown').lower()
        desc = item['analysis'].get('description', 'No description provided.')
        
        # Relative path for display
        image_rel_path = f"../{folder}/{filename}"
        # ID for JS manipulation
        card_id = f"card-{i}"

        html_cards += f"""
            <div class="card" id="{card_id}">
                <div class="card-image-wrapper">
                    <div class="severity-badge {severity}">{severity}</div>
                    <img src="{image_rel_path}" class="card-image">
                </div>
                <div class="card-content">
                    <div class="card-title">{task}</div>
                    <div class="card-desc">{desc}</div>
                </div>
                <div class="action-bar">
                    <button class="btn btn-reject" onclick="handleReview('{card_id}', 'reject', '{folder}', '{filename}')">✕ Discard</button>
                    <button class="btn btn-approve" onclick="handleReview('{card_id}', 'approve', '{folder}', '{filename}')">✓ Confirm</button>
                </div>
            </div>
        """

    html_footer = """
        </div>
    </div>

    <script>
        // Check if server is running
        fetch('/status')
            .then(r => {
                document.getElementById('server-status').innerText = "🟢 Connected";
                document.getElementById('server-status').style.color = "#2ecc71";
            })
            .catch(e => {
                document.getElementById('server-status').innerText = "🔴 Not Connected (Run review_server.py)";
                document.getElementById('server-status').style.color = "#ff4d4d";
            });

        function handleReview(cardId, action, folder, filename) {
            const card = document.getElementById(cardId);
            
            // Optimistic UI update
            if (action === 'approve') {
                card.classList.add('approved');
            } else {
                card.classList.add('rejected');
                setTimeout(() => card.style.display = 'none', 500); // Hide after animation
            }

            // Send to server
            fetch('/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: action,
                    folder: folder,
                    filename: filename
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Server response:', data);
                if(data.status === 'error') {
                    alert('Error saving file: ' + data.message);
                    card.classList.remove('approved'); // Revert on error
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Only alert if we expected a connection
                if(document.getElementById('server-status').innerText.includes("Connected")) {
                    alert("Failed to communicate with server.");
                }
            });
        }
    </script>
</body>
</html>
    """

    full_html = html_head + html_cards + html_footer
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"✅ Report generated: {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html_report()