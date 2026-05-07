from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import anndata as ad
import numpy as np
import pandas as pd

from medrix_flow.experiments import ExperimentRepository, ExperimentService
from medrix_flow.runtime.db import SQLiteRuntimeDB


def _make_paths(base_dir: Path):
    from medrix_flow.config.paths import Paths

    return Paths(base_dir=base_dir)


def _prepare_service(tmp_path: Path):
    async def _build():
        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        repo = ExperimentRepository(db)
        await repo.setup()
        return ExperimentService(repo), db

    return asyncio.run(_build())


def test_experiment_service_classification_bundle(tmp_path):
    paths = _make_paths(tmp_path)
    paths.ensure_thread_dirs("thread-exp-1")
    uploads = paths.sandbox_uploads_dir("thread-exp-1")
    outputs = paths.sandbox_outputs_dir("thread-exp-1")

    df = pd.DataFrame(
        {
            "feature_a": [0.1, 0.2, 0.3, 0.15, 0.18, 0.35, 0.8, 0.85, 0.9, 0.75, 0.88, 0.92] * 3,
            "feature_b": [1.0, 1.1, 0.95, 1.2, 1.05, 1.15, 2.2, 2.05, 2.3, 2.1, 2.25, 2.4] * 3,
            "label": ["control", "control", "control", "control", "control", "control", "treated", "treated", "treated", "treated", "treated", "treated"] * 3,
        }
    )
    csv_path = uploads / "classification.csv"
    df.to_csv(csv_path, index=False)

    service, db = _prepare_service(tmp_path)
    with patch("medrix_flow.experiments.service.get_paths", return_value=paths):
        result = asyncio.run(
            service.run_experiment(
                thread_id="thread-exp-1",
                agent_name="cs-ai-lab",
                topic="Run a logistic regression experiment on this dataset",
                dataset_ids=["/mnt/user-data/uploads/classification.csv"],
                output_dir=outputs,
                analysis_type="classification",
                target_column="label",
            )
        )

    assert result.run.status == "success"
    assert result.bundle.figure_count >= 2
    assert any(path.endswith("confusion_matrix.png") for path in result.bundle.export_files)
    assert any(path.endswith("metrics.json") for path in result.bundle.export_files)
    asyncio.run(db.close())


def test_experiment_service_bulk_bioinformatics_bundle(tmp_path):
    paths = _make_paths(tmp_path)
    paths.ensure_thread_dirs("thread-exp-2")
    uploads = paths.sandbox_uploads_dir("thread-exp-2")
    outputs = paths.sandbox_outputs_dir("thread-exp-2")

    expression = pd.DataFrame(
        {
            "gene": ["G1", "G2", "G3", "G4", "G5", "G6"],
            "S1": [120, 15, 20, 5, 8, 9],
            "S2": [130, 12, 18, 6, 9, 8],
            "S3": [8, 140, 22, 120, 10, 9],
            "S4": [10, 150, 24, 130, 12, 11],
        }
    )
    metadata = pd.DataFrame(
        {
            "sample": ["S1", "S2", "S3", "S4"],
            "group": ["A", "A", "B", "B"],
        }
    )
    expression_path = uploads / "expression.csv"
    metadata_path = uploads / "metadata.csv"
    expression.to_csv(expression_path, index=False)
    metadata.to_csv(metadata_path, index=False)

    service, db = _prepare_service(tmp_path)
    with patch("medrix_flow.experiments.service.get_paths", return_value=paths):
        result = asyncio.run(
            service.run_experiment(
                thread_id="thread-exp-2",
                agent_name="bioinformatics-lab",
                topic="Perform bulk RNA differential expression and figures",
                dataset_ids=[
                    "/mnt/user-data/uploads/expression.csv",
                    "/mnt/user-data/uploads/metadata.csv",
                ],
                output_dir=outputs,
                domain="bioinformatics",
                analysis_type="bulk_expression",
                metadata_path="/mnt/user-data/uploads/metadata.csv",
                sample_id_column="sample",
                group_column="group",
            )
        )

    assert result.run.status == "success"
    assert result.bundle.figure_count >= 3
    assert any(path.endswith("volcano_plot.png") for path in result.bundle.export_files)
    assert any(path.endswith("differential_expression.csv") for path in result.bundle.export_files)
    asyncio.run(db.close())


def test_experiment_service_single_cell_bundle(tmp_path):
    paths = _make_paths(tmp_path)
    paths.ensure_thread_dirs("thread-exp-3")
    uploads = paths.sandbox_uploads_dir("thread-exp-3")
    outputs = paths.sandbox_outputs_dir("thread-exp-3")

    matrix = np.array(
        [
            [10, 1, 0, 8, 0, 0],
            [9, 2, 0, 7, 0, 0],
            [0, 8, 9, 0, 7, 6],
            [0, 7, 8, 0, 8, 7],
            [6, 0, 0, 5, 1, 0],
            [0, 0, 7, 0, 6, 8],
        ],
        dtype=float,
    )
    adata = ad.AnnData(
        X=matrix,
        obs=pd.DataFrame(index=[f"cell_{idx}" for idx in range(matrix.shape[0])]),
        var=pd.DataFrame(index=[f"gene_{idx}" for idx in range(matrix.shape[1])]),
    )
    h5ad_path = uploads / "cells.h5ad"
    adata.write_h5ad(h5ad_path)

    service, db = _prepare_service(tmp_path)
    with patch("medrix_flow.experiments.service.get_paths", return_value=paths):
        result = asyncio.run(
            service.run_experiment(
                thread_id="thread-exp-3",
                agent_name="bioinformatics-lab",
                topic="Run a single-cell starter analysis",
                dataset_ids=["/mnt/user-data/uploads/cells.h5ad"],
                output_dir=outputs,
                domain="bioinformatics",
                analysis_type="single_cell",
            )
        )

    assert result.run.status == "success"
    assert result.bundle.figure_count >= 3
    assert any(path.endswith("cell_umap.png") for path in result.bundle.export_files)
    assert any(path.endswith("marker_genes.csv") for path in result.bundle.export_files)
    asyncio.run(db.close())
