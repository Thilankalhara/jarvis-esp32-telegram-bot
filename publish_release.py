import json
import subprocess
import urllib.request
import urllib.error
import pathlib

repo = 'Thilankalhara/jarvis-esp32-telegram-bot'
tag = 'v2.2'

creds = subprocess.check_output(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n', text=True)
token = None
for line in creds.splitlines():
    if line.startswith('password='):
        token = line.split('=', 1)[1].strip()
        break

if not token:
    raise SystemExit('No token found')

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
}

body = {
    'tag_name': tag,
    'target_commitish': 'main',
    'name': 'J.A.R.V.I.S. v2.2',
    'body': '## J.A.R.V.I.S. v2.2\n\n### New in this release\n- Added voice feedback mute/unmute support in the desktop control center\n- Added Windows volume control support for master and app-level audio\n- Updated documentation and build packaging\n\n### Assets\n- JARVIS_Control_Center.exe\n- START_JARVIS.bat\n- JARVIS_Setup_v2.1.exe',
    'draft': False,
    'prerelease': False,
}

req = urllib.request.Request(
    f'https://api.github.com/repos/{repo}/releases/tags/{tag}',
    headers=headers,
    method='GET',
)
try:
    with urllib.request.urlopen(req) as resp:
        release = json.load(resp)
    method = 'PATCH'
    url = f'https://api.github.com/repos/{repo}/releases/{release["id"]}'
except urllib.error.HTTPError as e:
    if e.code != 404:
        raise
    method = 'POST'
    url = f'https://api.github.com/repos/{repo}/releases'

req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**headers, 'Content-Type': 'application/json'}, method=method)
with urllib.request.urlopen(req) as resp:
    release = json.load(resp)

print(release['html_url'])

assets = [
    ('dist/JARVIS_Control_Center/JARVIS_Control_Center.exe', 'JARVIS_Control_Center.exe'),
    ('dist/JARVIS_Control_Center/START_JARVIS.bat', 'START_JARVIS.bat'),
    ('dist/JARVIS_Setup_v2.1.exe', 'JARVIS_Setup_v2.1.exe'),
]

for path, name in assets:
    p = pathlib.Path(path)
    if not p.exists():
        print(f'Skip missing {path}')
        continue
    upload_url = release['upload_url'].split('{')[0] + '?name=' + name
    data = p.read_bytes()
    upload_req = urllib.request.Request(upload_url, data=data, headers={**headers, 'Content-Type': 'application/octet-stream'}, method='POST')
    with urllib.request.urlopen(upload_req) as resp:
        print(f'Uploaded {name}')
