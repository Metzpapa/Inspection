import os
import re
import datetime

# Configuration
SOURCE_DIR = 'Reviewed_Inspection_Report'
OUTPUT_FILE = 'Rove_Final_Report.html'

def clean_filename(filename):
    """Converts filename to a readable title."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^-\s*', '', name) # Remove leading dash
    name = re.sub(r'\s+\d+$', '', name) # Remove trailing numbers
    name = re.sub(r'\s*\(\d+\)$', '', name) # Remove (1)
    return name.strip()

def generate_client_report():
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Error: Directory '{SOURCE_DIR}' not found.")
        return

    # 1. Scan the directory for approved images
    # Structure: { "Folder Name": [ "image1.jpg", "image2.jpg" ] }
    content_map = {}
    total_items = 0

    for root, dirs, files in os.walk(SOURCE_DIR):
        folder_name = os.path.basename(root)
        if folder_name == SOURCE_DIR: continue # Skip root folder
        
        images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if images:
            content_map[folder_name] = sorted(images)
            total_items += len(images)

    # 2. HTML Header & CSS (Rove Style)
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rove Property Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0a0a0a;
            --bg-card: #141414;
            --text-main: #ffffff;
            --text-muted: #888888;
            --accent: #ffffff;
            --border: #2a2a2a;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        /* Navbar */
        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 25px 50px;
            background: rgba(10, 10, 10, 0.9);
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid var(--border);
        }}

        .logo {{
            font-size: 1.2rem;
            font-weight: 400;
            letter-spacing: 3px;
            text-transform: uppercase;
        }}

        .report-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 50px;
        }}

        /* Hero */
        .hero {{
            text-align: center;
            padding: 100px 20px 60px;
            max-width: 800px;
            margin: 0 auto;
        }}

        .hero h1 {{
            font-size: 3.5rem;
            font-weight: 300;
            margin-bottom: 20px;
            letter-spacing: -1px;
        }}

        .hero p {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        /* Content */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 50px 100px;
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 300;
            margin: 60px 0 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
            color: var(--text-main);
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 40px;
        }}

        /* Card */
        .card {{
            background: transparent;
            display: flex;
            flex-direction: column;
            group: hover;
        }}

        .card-image-wrapper {{
            position: relative;
            width: 100%;
            padding-top: 66.66%; /* 3:2 Aspect Ratio */
            background: #1a1a1a;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 20px;
            cursor: pointer;
            transition: transform 0.3s ease;
        }}

        .card-image-wrapper:hover {{
            transform: scale(1.02);
        }}

        .card-image {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            object-fit: cover;
        }}

        .status-badge {{
            position: absolute;
            top: 15px; left: 15px;
            background: rgba(255, 255, 255, 0.95);
            color: black;
            padding: 6px 12px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            z-index: 2;
        }}

        .card-title {{
            font-size: 1.1rem;
            font-weight: 400;
            margin-bottom: 5px;
        }}

        .card-subtitle {{
            font-size: 0.9rem;
            color: var(--text-muted);
        }}

        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0; top: 0;
            width: 100%; height: 100%;
            background-color: rgba(0,0,0,0.95);
        }}
        .modal-content {{
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90vh;
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
        }}
        .close {{
            position: absolute;
            top: 30px; right: 50px;
            color: #fff;
            font-size: 40px;
            font-weight: 100;
            cursor: pointer;
        }}

        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2.5rem; }}
            .navbar {{ padding: 20px; }}
            .container {{ padding: 0 20px 80px; }}
        }}
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="logo">ROVE</div>
        <div class="report-meta">Generated: {datetime.date.today().strftime('%B %d, %Y')}</div>
    </nav>

    <div class="hero">
        <h1>Inspection Report</h1>
        <p>The following items have been flagged for attention based on recent property inspections.</p>
        <div style="margin-top: 30px;">
            <span style="border: 1px solid #333; padding: 10px 20px; border-radius: 4px; font-size: 0.9rem;">
                {total_items} Items Flagged
            </span>
        </div>
    </div>

    <div class="container">
    """

    # 3. Generate Content
    if not content_map:
        html += "<div style='text-align:center; color:#666;'>No items found in the reviewed folder.</div>"
    
    for folder, files in content_map.items():
        # Section Header (Folder Name)
        html += f'<div class="section-title">{folder}</div>'
        html += '<div class="grid">'
        
        for filename in files:
            title = clean_filename(filename)
            # Path relative to the HTML file
            img_path = f"{SOURCE_DIR}/{folder}/{filename}"
            
            html += f"""
            <div class="card">
                <div class="card-image-wrapper" onclick="openModal('{img_path}')">
                    <div class="status-badge">Action Required</div>
                    <img src="{img_path}" class="card-image" loading="lazy">
                </div>
                <div class="card-title">{title}</div>
                <div class="card-subtitle">Flagged Issue</div>
            </div>
            """
        
        html += '</div>' # End Grid

    # 4. Footer & Scripts
    html += """
    </div>

    <div id="imageModal" class="modal">
        <span class="close">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <script>
        const modal = document.getElementById('imageModal');
        const modalImg = document.getElementById('modalImage');
        const closeBtn = document.getElementsByClassName('close')[0];

        function openModal(src) {
            modal.style.display = "block";
            modalImg.src = src;
        }

        closeBtn.onclick = function() { modal.style.display = "none"; }
        modal.onclick = function(e) { if (e.target === modal) modal.style.display = "none"; }
        document.addEventListener('keydown', function(e) { if (e.key === "Escape") modal.style.display = "none"; });
    </script>
</body>
</html>
    """

    # 5. Write File
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Client Report Generated: {OUTPUT_FILE}")
    print(f"📊 Total Items: {total_items}")

if __name__ == "__main__":
    generate_client_report()