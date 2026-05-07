"""Gateway-scoped runtime dependency bootstrap and accessors."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import TypeVar, cast

from fastapi import FastAPI, HTTPException, Request
from langgraph.types import Checkpointer

from medrix_flow.agents.checkpointer.async_provider import make_checkpointer
from medrix_flow.academic import AcademicRepository, AcademicResearchService
from medrix_flow.config.paths import get_paths
from medrix_flow.experiments import ExperimentRepository, ExperimentService
from medrix_flow.runtime import MemoryStreamBridge, SQLiteFeedbackRepo, SQLiteRunEventStore, SQLiteRunStore
from medrix_flow.runtime.db import SQLiteRuntimeDB
from medrix_flow.runtime.runs import RunManager

from .services import GatewayRunService

T = TypeVar("T")


@asynccontextmanager
async def runtime_dependencies(app: FastAPI) -> AsyncGenerator[None, None]:
    async with AsyncExitStack() as stack:
        db = SQLiteRuntimeDB(get_paths().runtime_db_file)
        await db.connect()
        academic_db = SQLiteRuntimeDB(get_paths().academic_db_file)
        await academic_db.connect()
        experiment_db = SQLiteRuntimeDB(get_paths().experiment_db_file)
        await experiment_db.connect()

        app.state.runtime_db = db
        app.state.academic_db = academic_db
        app.state.experiment_db = experiment_db
        app.state.checkpointer = await stack.enter_async_context(make_checkpointer())
        app.state.stream_bridge = MemoryStreamBridge()
        app.state.run_store = SQLiteRunStore(db)
        app.state.run_event_store = SQLiteRunEventStore(db)
        app.state.feedback_repo = SQLiteFeedbackRepo(db)
        app.state.academic_repo = AcademicRepository(academic_db)
        app.state.experiment_repo = ExperimentRepository(experiment_db)

        await app.state.run_store.setup()
        await app.state.run_event_store.setup()
        await app.state.feedback_repo.setup()
        await app.state.academic_repo.setup()
        await app.state.experiment_repo.setup()

        app.state.run_manager = RunManager(store=app.state.run_store)
        app.state.run_service = GatewayRunService(
            checkpointer=app.state.checkpointer,
            stream_bridge=app.state.stream_bridge,
            run_manager=app.state.run_manager,
            run_store=app.state.run_store,
            event_store=app.state.run_event_store,
            feedback_repo=app.state.feedback_repo,
        )
        app.state.academic_service = AcademicResearchService(app.state.academic_repo)
        app.state.experiment_service = ExperimentService(app.state.experiment_repo)
        try:
            yield
        finally:
            await experiment_db.close()
            await academic_db.close()
            await db.close()


def _require(attr: str, label: str) -> Callable[[Request], T]:
    def dep(request: Request) -> T:
        value = getattr(request.app.state, attr, None)
        if value is None:
            raise HTTPException(status_code=503, detail=f"{label} not available")
        return cast(T, value)

    dep.__name__ = dep.__qualname__ = f"get_{attr}"
    return dep


get_checkpointer: Callable[[Request], Checkpointer] = _require("checkpointer", "Checkpointer")
get_run_manager: Callable[[Request], RunManager] = _require("run_manager", "Run manager")
get_run_service: Callable[[Request], GatewayRunService] = _require("run_service", "Run service")
get_academic_service: Callable[[Request], AcademicResearchService] = _require("academic_service", "Academic service")
get_experiment_service: Callable[[Request], ExperimentService] = _require("experiment_service", "Experiment service")
