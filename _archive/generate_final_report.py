import json
import os
import datetime

# Configuration
INPUT_FILE = 'draft_data.json'
OUTPUT_FILE = 'Rove_Final_Report.html'

def generate_final_report():
    if not os.path.exists(INPUT_FILE):
        print("❌ Error: draft_data.json not found. Run the editor first.")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    # Group by folder
    grouped = {}
    for item in data:
        if item['folder'] not in grouped:
            grouped[item['folder']] = []
        grouped[item['folder']].append(item)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rove Property Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #0a0a0a; --card: #141414; --text: #fff; --muted: #888; --border: #2a2a2a; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; }}
        
        .navbar {{ padding: 25px 50px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.2rem; letter-spacing: 3px; text-transform: uppercase; }}
        .date {{ color: var(--muted); font-size: 0.9rem; border: 1px solid var(--border); padding: 5px 15px; border-radius: 20px; }}

        .container {{ max-width: 1200px; margin: 0 auto; padding: 60px 20px; }}
        
        .hero {{ text-align: center; margin-bottom: 80px; }}
        .hero h1 {{ font-size: 3rem; font-weight: 300; margin-bottom: 15px; }}
        .hero p {{ color: var(--muted); font-size: 1.1rem; }}

        .section-title {{ font-size: 1.4rem; font-weight: 400; margin: 60px 0 30px; padding-bottom: 15px; border-bottom: 1px solid var(--border); }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 40px; }}
        
        .card {{ background: transparent; display: flex; flex-direction: column; }}
        .card-img {{ width: 100%; aspect-ratio: 3/2; object-fit: cover; border-radius: 4px; margin-bottom: 20px; background: #222; cursor: pointer; }}
        
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }}
        .badge.critical {{ background: #ff4d4d; color: white; }}
        .badge.high {{ background: #ff9f43; color: white; }}
        .badge.medium {{ background: #feca57; color: black; }}
        .badge.low {{ background: #2a2a2a; color: #ccc; border: 1px solid #444; }}

        .desc {{ font-size: 1rem; margin-bottom: 15px; color: #eee; }}
        
        .task-box {{ background: #1a1a1a; padding: 15px; border-radius: 4px; border-left: 2px solid #fff; }}
        .task-label {{ font-size: 0.7rem; text-transform: uppercase; color: var(--muted); letter-spacing: 1px; margin-bottom: 5px; }}
        .task-text {{ font-size: 0.9rem; color: #fff; }}

        /* Modal */
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); }}
        .modal-content {{ max-width: 90%; max-height: 90vh; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }}
        .close {{ position: absolute; top: 30px; right: 50px; color: #fff; font-size: 40px; cursor: pointer; }}
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">ROVE</div>
        <div class="date">{datetime.date.today().strftime('%B %d, %Y')}</div>
    </nav>

    <div class="container">
        <div class="hero">
            <h1>Inspection Report</h1>
            <p>Action items and observations from recent property inspection.</p>
        </div>
    """

    for folder, items in grouped.items():
        html += f'<div class="section-title">{folder}</div>'
        html += '<div class="grid">'
        
        for item in items:
            imp = item.get('importance', 'low').lower()
            task = item.get('task', '')
            desc = item.get('description', '')
            
            # If task is empty, show a default message or hide the box? 
            # Let's show "No specific task assigned" if empty, or just hide it.
            # User said "Generate a task", so let's assume they filled it in.
            
            task_html = ""
            if task:
                task_html = f"""
                <div class="task-box">
                    <div class="task-label">Recommended Task</div>
                    <div class="task-text">{task}</div>
                </div>
                """

            html += f"""
            <div class="card">
                <img src="{item['image_path']}" class="card-img" onclick="openModal(this.src)">
                <div>
                    <span class="badge {imp}">{imp} Importance</span>
                </div>
                <div class="desc">{desc}</div>
                {task_html}
            </div>
            """
        html += '</div>'

    html += """
    </div>
    <div id="imageModal" class="modal"><span class="close" onclick="document.getElementById('imageModal').style.display='none'">&times;</span><img class="modal-content" id="modalImage"></div>
    <script>
        function openModal(src) { document.getElementById('imageModal').style.display='block'; document.getElementById('modalImage').src=src; }
        window.onclick = function(e) { if(e.target == document.getElementById('imageModal')) document.getElementById('imageModal').style.display='none'; }
    </script>
</body>
</html>
    """

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Final Report Generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_final_report()