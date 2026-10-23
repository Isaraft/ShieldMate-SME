"""Local Compose check, using enrollment only: never queries DNS."""
import json
import secrets
import subprocess
import time
import uuid
from pathlib import Path

import httpx

base = 'http://127.0.0.1:5173'
with httpx.Client(base_url=base, headers={'Origin':base}) as client:
    def mutate(path,body=None):
        csrf=client.get('/api/v1/auth/csrf').json()['csrf_token']
        return client.post('/api/v1'+path,json=body,headers={'X-CSRF-Token':csrf})
    credentials={'email':f'qa-domain-{uuid.uuid4()}@example.com','password':secrets.token_urlsafe(32)}
    assert mutate('/auth/register',credentials).status_code==201
    assert mutate('/auth/login',credentials).status_code==200
    assert mutate('/organizations',{'name':'QA domain persistence'}).status_code==201
    response=mutate('/domains',{'fqdn':'qa-persistence.example.com','authorization_acknowledged':True})
    assert response.status_code==201, response.text
    before=response.json()
    subprocess.run(['docker','compose','restart','backend'],capture_output=True,check=True)
    for _ in range(30):
        try:
            response=client.get('/api/v1/domains/'+before['id'])
            if response.status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(1)
    assert response.status_code==200 and response.json()==before
    assert client.get('/api/v1/auth/me').status_code==200
    assert client.get('/api/v1/health').json()=={'status':'ok'}
    result={'domain_and_challenge_survive_container_restart':True,'session_preserved':True,'dns_queries_performed':False,'health':'ok'}
    Path('docs/evidence/phase-03/restart-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
