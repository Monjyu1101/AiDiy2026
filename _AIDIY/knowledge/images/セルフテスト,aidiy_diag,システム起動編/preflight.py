import json, socket
from pathlib import Path
from datetime import datetime
results = {}
for port in (8090, 8091, 8092, 8093, 8095, 8096, 8098):
    with socket.socket() as probe:
        probe.settimeout(.3)
        results[str(port)] = probe.connect_ex(('127.0.0.1', port)) == 0
result = {'time': datetime.now().astimezone().isoformat(), 'portsOpen': results}
Path(__file__).with_name('preflight.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
