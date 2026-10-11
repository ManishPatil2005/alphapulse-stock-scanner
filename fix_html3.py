import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacement = '''
                        <div class="diag-card" id="contextCard">
                            <div class="diag-header">
                                <div class="diag-title">
                                    <span class="diag-icon">🎓</span>
                                    <h3>Institutional Context</h3>
                                </div>
                            </div>
                            <div class="diag-body">
                                <p id="institutionalContextText" style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.5; padding: 12px; background: rgba(30, 41, 59, 0.5); border-radius: 6px; border: 1px solid rgba(148, 163, 184, 0.2);">Loading Context...</p>
                            </div>
                        </div>

                        <div class="diag-card">
                            <div class="diag-header">
                                <div class="diag-title">
                                    <span class="diag-icon">🧠</span>
                                    <h3>Trade Psychology / Risk</h3>
'''

html = re.sub(
    r'<div class="diag-card">\s*<div class="diag-header">\s*<div class="diag-title">\s*<span class="diag-icon">🧠</span>\s*<h3>Trade Psychology / Risk</h3>',
    replacement,
    html
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Done")
