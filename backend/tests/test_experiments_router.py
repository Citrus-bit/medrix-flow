from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import experiments
from medrix_flow.experiments import ExperimentRepository, ExperimentService
from medrix_flow.runtime.db import SQLiteRuntimeDB


def _make_paths(base_dir: Path):
    from medrix_flow.config.paths import Paths

    return Paths(base_dir=base_dir)


def test_experiments_router_end_to_end(tmp_path):
    paths = _make_paths(tmp_path)
    paths.ensure_thread_dirs("thread-router-1")
    uploads = paths.sandbox_uploads_dir("thread-router-1")
    df = pd.DataFrame(
        {
            "x1": [0.1, 0.2, 0.3, 0.8, 0.9, 1.0] * 4,
            "x2": [1.0, 0.9, 1.1, 2.0, 2.2, 2.1] * 4,
            "label": ["A", "A", "A", "B", "B", "B"] * 4,
        }
    )
    (uploads / "router.csv").parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(uploads / "router.csv", index=False)

    async def make_service():
        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        repo = ExperimentRepository(db)
        await repo.setup()
        return ExperimentService(repo), db

    service, db = asyncio.run(make_service())
    app = FastAPI()
    app.state.experiment_service = service
    app.include_router(experiments.router)

    with patch("medrix_flow.experiments.service.get_paths", return_value=paths):
        with TestClient(app) as client:
            created = client.post(
                "/api/experiments/projects",
                json={
                    "thread_id": "thread-router-1",
                    "agent_name": "cs-ai-lab",
                    "domain": "cs_ai",
                    "topic": "Router classification experiment",
                    "dataset_ids": ["/mnt/user-data/uploads/router.csv"],
                },
            )
            assert created.status_code == 200
            project_id = created.json()["project"]["project_id"]

            executed = client.post(
                f"/api/experiments/projects/{project_id}/execute",
                json={"analysis_type": "classification", "target_column": "label"},
            )
            assert executed.status_code == 200
            assert executed.json()["run"]["status"] == "success"

            summary = client.get(f"/api/experiments/projects/{project_id}")
            assert summary.status_code == 200
            assert summary.json()["figure_count"] >= 2

            artifacts = client.get(f"/api/experiments/projects/{project_id}/artifacts")
            assert artifacts.status_code == 200
            assert len(artifacts.json()["data"]) >= 1

            exported = client.post(f"/api/experiments/projects/{project_id}/export", json={})
            assert exported.status_code == 200
            assert exported.json()["figure_count"] >= 2

    asyncio.run(db.close())
