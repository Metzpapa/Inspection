import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory, Response

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "inspection_data.json"
BACKUP_DIR = BASE_DIR / "backups"
PRIMARY_ANALYSIS_FILE = BASE_DIR / "analysis_results.json"
FALLBACK_ANALYSIS_FILE = BASE_DIR / "Analysis_Results" / "analysis_results.json"

ALLOWED_STATUSES = {"pending", "approved", "rejected"}
ALLOWED_UPDATE_FIELDS = {"status", "task", "description", "importance"}

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def map_importance(severity: str) -> str:
    severity = (severity or "").lower()
    if severity in {"critical", "severe"}:
        return "high"
    if severity == "moderate":
        return "medium"
    return "low"


def ensure_analysis_source() -> Optional[Path]:
    """
    Make sure we have a root-level analysis_results.json available for read-only use.
    Returns the path that should be used as the source of truth.
    """
    if PRIMARY_ANALYSIS_FILE.exists():
        return PRIMARY_ANALYSIS_FILE

    if FALLBACK_ANALYSIS_FILE.exists():
        shutil.copy2(FALLBACK_ANALYSIS_FILE, PRIMARY_ANALYSIS_FILE)
        return PRIMARY_ANALYSIS_FILE

    return None


def transform_ai_results(raw: List[Dict]) -> List[Dict]:
    transformed = []
    for item in raw:
        folder = item.get("folder", "")
        filename = item.get("filename", "")
        analysis = item.get("analysis", {}) or {}
        severity = str(analysis.get("severity", "") or "").lower()
        transformed.append(
            {
                "id": f"{folder}/{filename}",
                "folder": folder,
                "filename": filename,
                "image_path": str(Path(folder) / filename),
                "description": analysis.get("description", ""),
                "severity": severity,
                "has_issues": bool(analysis.get("has_issues", False)),
                "task": item.get("task_derived", ""),
                "task_derived": item.get("task_derived", ""),
                "status": "pending",
                "importance": map_importance(severity),
            }
        )
    return transformed


def bootstrap_inspection_data() -> List[Dict]:
    source = ensure_analysis_source()
    if not source:
        return []

    raw = load_json(source)
    transformed = transform_ai_results(raw)
    write_json(DATA_FILE, transformed)
    return transformed


def ensure_inspection_data() -> List[Dict]:
    return load_inspection_data()


def load_inspection_data() -> List[Dict]:
    if DATA_FILE.exists():
        return load_json(DATA_FILE)
    return bootstrap_inspection_data()


def save_inspection_data(data: List[Dict], *, create_backup: bool = True) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if create_backup and DATA_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"inspection_data_{timestamp}.json"
        shutil.copy2(DATA_FILE, backup_path)
    write_json(DATA_FILE, data)


def build_report_html(records: List[Dict]) -> str:
    grouped: Dict[str, List[Dict]] = {}
    for item in records:
        grouped.setdefault(item.get("folder", "Uncategorized"), []).append(item)

    today_str = datetime.today().strftime("%B %d, %Y")

    head = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Rove Inspection Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0b0d10;
            --panel: #12151b;
            --ink: #e8ecf2;
            --muted: #95a1b5;
            --accent: #d6ff7f;
            --border: #1f2633;
            --high: #f05d6c;
            --medium: #f0c35d;
            --low: #53c7a1;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Space Grotesk', system-ui, sans-serif; background: var(--bg); color: var(--ink); line-height: 1.6; }}
        .navbar {{ display: flex; justify-content: space-between; align-items: center; padding: 24px 40px; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(11, 13, 16, 0.96); backdrop-filter: blur(8px); z-index: 10; }}
        .brand {{ letter-spacing: 6px; font-weight: 600; font-size: 1rem; }}
        .meta {{ color: var(--muted); border: 1px solid var(--border); padding: 8px 14px; border-radius: 30px; font-size: 0.9rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 60px 24px 120px; }}
        h1 {{ font-weight: 600; font-size: 2.8rem; margin-bottom: 14px; }}
        p.lede {{ color: var(--muted); margin-bottom: 40px; }}
        .section {{ margin-top: 60px; }}
        .section h2 {{ font-size: 1.4rem; font-weight: 600; margin-bottom: 18px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 26px; }}
        .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; min-height: 100%; }}
        .card img {{ width: 100%; aspect-ratio: 3/2; object-fit: cover; background: #0f1218; }}
        .card-body {{ padding: 18px; display: flex; flex-direction: column; gap: 12px; }}
        .pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; background: rgba(255,255,255,0.05); border: 1px solid var(--border); }}
        .pill.high {{ color: var(--high); border-color: rgba(240,93,108,0.5); }}
        .pill.medium {{ color: var(--medium); border-color: rgba(240,195,93,0.4); }}
        .pill.low {{ color: var(--low); border-color: rgba(83,199,161,0.4); }}
        .desc {{ color: var(--ink); opacity: 0.9; }}
        .task-box {{ background: rgba(255,255,255,0.04); border: 1px dashed var(--border); border-radius: 10px; padding: 12px; }}
        .task-label {{ font-size: 0.8rem; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; display: block; }}
        .task-text {{ font-weight: 600; }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="brand">ROVE</div>
        <div class="meta">{today_str}</div>
    </div>
    <div class="container">
        <h1>Inspection Report</h1>
        <p class="lede">Curated findings from the latest walkthrough. Items shown here reflect the current approved set in the dashboard.</p>
"""

    sections = []
    for folder, items in grouped.items():
        cards = []
        for item in items:
            importance = (item.get("importance") or "low").lower()
            description = item.get("description", "")
            task = item.get("task", "")
            img_path = f"/files/{item.get('image_path', '')}"
            cards.append(
                f"""
            <article class="card">
                <img src="{img_path}" alt="{item.get('filename', '')}">
                <div class="card-body">
                    <span class="pill {importance}">{importance.title()} importance</span>
                    <div class="desc">{description}</div>
                    {"<div class='task-box'><span class='task-label'>Recommended Action</span><div class='task-text'>" + task + "</div></div>" if task else ""}
                </div>
            </article>
            """
            )

        section_html = f"""
        <section class="section">
            <h2>{folder}</h2>
            <div class="grid">
                {''.join(cards)}
            </div>
        </section>
        """
        sections.append(section_html)

    body_end = """
    </div>
</body>
</html>
    """

    return head + "\n".join(sections) + body_end


@app.route("/")
def dashboard():
    ensure_inspection_data()
    return render_template("dashboard.html")


@app.route("/api/data")
def api_data():
    data = load_inspection_data()
    return jsonify(data)


@app.route("/api/update", methods=["POST"])
def api_update():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("id")
    if not item_id:
        return jsonify({"error": "Missing item id"}), 400

    updates = {k: v for k, v in payload.items() if k in ALLOWED_UPDATE_FIELDS}
    if not updates:
        return jsonify({"error": "No updates provided"}), 400

    if "status" in updates and updates["status"] not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status value"}), 400

    data = load_inspection_data()
    for item in data:
        if item.get("id") == item_id:
            item.update(updates)
            save_inspection_data(data)
            return jsonify({"status": "ok", "item": item})

    return jsonify({"error": "Item not found"}), 404


@app.route("/export")
def export_report():
    data = load_inspection_data()
    approved = [item for item in data if item.get("status") == "approved"]
    html = build_report_html(approved)
    response = Response(html, mimetype="text/html")
    if request.args.get("download"):
        response.headers["Content-Disposition"] = "attachment; filename=Rove_Final_Report.html"
    return response


@app.route("/files/<path:filename>")
def serve_files(filename: str):
    # Expose original image paths without relocating assets
    return send_from_directory(BASE_DIR, filename)


if __name__ == "__main__":
    ensure_inspection_data()
    port = int(os.getenv("PORT", "5050"))
    try:
        app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
    except OSError:
        # Commonly means the port is in use; try a fallback before exiting.
        fallback = port + 1
        print(f"Port {port} unavailable. Trying fallback port {fallback}...")
        app.run(host="0.0.0.0", port=fallback, debug=True, use_reloader=False)
