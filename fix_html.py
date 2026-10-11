import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacement = '''<!-- Action Buttons -->
                <div class="action-buttons">
                    <button id="btnStartScan" class="btn-scan">
                        <span class="btn-icon">▶</span> Run Full Scanner
                    </button>
                    <button id="btnStopScan" class="btn-stop" disabled>
                        <span>🛑</span> Stop
                    </button>
                    <button id="btnExportCsv" class="btn-action" onclick="window.open('/api/export/scan?universe=' + document.getElementById('universeSelect').value, '_blank')" style="background-color: #3b82f6; border-color: #3b82f6;">
                        <span>📥</span> Export CSV
                    </button>
                </div>'''

html = re.sub(
    r'<!-- Action Buttons -->\s*<div class="action-buttons">\s*<button id="btnStartScan".*?</button>\s*</div>',
    replacement,
    html,
    flags=re.DOTALL
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Done")
