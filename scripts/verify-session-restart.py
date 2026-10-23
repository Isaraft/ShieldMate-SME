"""Local Compose persistence check; credentials/tokens remain only in process memory."""
import json
import secrets
import subprocess
import time
import uuid
from pathlib import Path

import httpx

base = 'http://127.0.0.1:5173'
email = f'qa-restart-{uuid.uuid4()}@example.com'
password = secrets.token_urlsafe(32)
with httpx.Client(base_url=base, headers={'Origin': base}) as client:
    def mutate(path, body):
        csrf = client.get('/api/v1/auth/csrf').json()['csrf_token']
        return client.post('/api/v1'+path, json=body, headers={'X-CSRF-Token':csrf})
    assert mutate('/auth/register', {'email':email,'password':password}).status_code == 201
    assert mutate('/auth/login', {'email':email,'password':password}).status_code == 200
    assert mutate('/organizations', {'name':'QA restart verification'}).status_code == 201
    before = client.get('/api/v1/auth/me').json()
    subprocess.run(['docker','compose','restart','backend'],check=True,capture_output=True)
    for _ in range(30):
        try:
            after = client.get('/api/v1/auth/me')
            if after.status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(1)
    assert after.status_code == 200 and after.json() == before
    assert mutate('/auth/logout', None).status_code == 200
    result = {'container_restart':'PASS','same_account_and_company':'PASS','session_survives':'PASS','logout_after_restart':'PASS'}
    Path('docs/evidence/phase-02/restart-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
