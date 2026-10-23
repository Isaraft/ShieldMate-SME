"""Actual container crash/restart check on the isolated Phase04 fixture stack only."""
import json
import secrets
import subprocess
import time
import uuid
from pathlib import Path

import httpx

COMPOSE = ["docker", "compose", "-p", "shieldmate-phase04-qa", "-f",
           "scripts/qa/phase04.compose.yaml"]
BASE = "http://127.0.0.1:15273"


def compose(*args):
    subprocess.run([*COMPOSE, *args], check=True, capture_output=True)


with httpx.Client(base_url=BASE, headers={"Origin": BASE}, timeout=10) as client:
    def mutate(path, body=None):
        token = client.get("/api/v1/auth/csrf").json()["csrf_token"]
        return client.post("/api/v1" + path, json=body, headers={"X-CSRF-Token": token})

    credentials = {"email": f"qa-restart-{uuid.uuid4()}@example.com",
                   "password": secrets.token_urlsafe(32)}
    assert mutate("/auth/register", credentials).status_code == 201
    assert mutate("/auth/login", credentials).status_code == 200
    assert mutate("/organizations", {"name": "LOCAL QA — container restart fixtures"}).status_code == 201
    asset = mutate("/domains", {"fqdn": "qacomplete.example.com",
                               "authorization_acknowledged": True}).json()["id"]
    assert mutate(f"/domains/{asset}/verification/check").json()["code"] == "verified"
    scope = f"/domains/{asset}/scans"
    compose("stop", "worker")
    job = mutate(scope).json()["id"]
    compose("restart", "backend")
    time.sleep(1)
    def detail(identifier):
        return client.get("/api/v1" + scope + "/" + identifier)
    for _ in range(30):
        try:
            response = detail(job)
            if response.status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(1)
    assert response.json()["status"] == "queued"
    assert client.get("/api/v1/auth/me").status_code == 200
    compose("start", "worker")
    for _ in range(50):
        record = detail(job).json()
        if record["status"] == "completed":
            break
        time.sleep(0.2)
    assert record["status"] == "completed" and len(record["observations"]) == 13
    previous = record
    interrupted = mutate(scope).json()["id"]
    for _ in range(100):
        record = detail(interrupted).json()
        if record["status"] == "running":
            break
        time.sleep(0.02)
    assert record["status"] == "running"
    compose("kill", "-s", "SIGKILL", "worker")
    compose("restart", "backend", "worker")
    # The production lease is 90s; do not modify timestamps to manufacture crash recovery.
    start = time.monotonic()
    for _ in range(110):
        try:
            record = detail(interrupted).json()
            if record.get("status") == "interrupted":
                break
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(1)
    assert record["status"] == "interrupted" and record["error_code"] == "worker_interrupted"
    assert detail(job).json() == previous
    result = {"isolated_fixture_stack": True, "external_network_probes": False,
              "queued_job_and_session_survive_backend_restart": True,
              "completed_observations_survive_backend_and_worker_restart": True,
              "sigkill_running_worker_recovers_to_interrupted": True,
              "actual_recovery_wait_seconds": round(time.monotonic() - start, 1)}
    Path("docs/evidence/phase-04/restart-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
