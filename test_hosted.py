import subprocess
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [edge_path, "--headless", "--disable-gpu", "--virtual-time-budget=6000", "--dump-dom", "https://alphapulse-stock-scanner.vercel.app"]

print("Loading https://alphapulse-stock-scanner.vercel.app in headless Edge...")
proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
dom = proc.stdout

print("DOM length from hosted Vercel:", len(dom))
print("tv-lightweight-charts in DOM:", "tv-lightweight-charts" in dom)
print("canvas in DOM:", "<canvas" in dom)
prices = re.findall(r'id=["\']activePrice["\'][^>]*>(.*?)</span>', dom)
print("activePrice in DOM:", prices)
sectors = re.findall(r'id=["\']activeSectorBadge["\'][^>]*>(.*?)</span>', dom)
print("activeSectorBadge in DOM:", sectors)
