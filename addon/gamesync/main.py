"""FastAPI application factory and lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gamesync.config import get_settings
from gamesync.engine.delay_buffer import DelayBuffer
from gamesync.engine.event_emitter import EventEmitter
from gamesync.engine.scheduler import PollScheduler
from gamesync.engine.session_manager import SessionManager
from gamesync.effects.composer import EffectComposer
from gamesync.effects.executor import EffectExecutor
from gamesync.ha_client.client import HAClient
from gamesync.ha_client.events import HAEventFirer
from gamesync.ha_client.lights import LightController
from gamesync.ha_client.media import MediaController
from gamesync.ha_client.tts import TTSController
from gamesync.sports.registry import ProviderRegistry
from gamesync.storage.db import Database
from gamesync.storage.sound_manager import SoundManager

logger = logging.getLogger(__name__)

# Global application state — set during lifespan
registry: ProviderRegistry | None = None
scheduler: PollScheduler | None = None
emitter: EventEmitter | None = None
delay_buffer: DelayBuffer | None = None
db: Database | None = None
ha_client: HAClient | None = None
light_controller: LightController | None = None
media_controller: MediaController | None = None
tts_controller: TTSController | None = None
ha_event_firer: HAEventFirer | None = None
effect_composer: EffectComposer | None = None
effect_executor: EffectExecutor | None = None
session_manager: SessionManager | None = None
sound_manager: SoundManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    global registry, scheduler, emitter, delay_buffer, db
    global ha_client, light_controller, media_controller, tts_controller
    global ha_event_firer, effect_composer, effect_executor
    global session_manager, sound_manager

    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger.info("GameSync starting up...")

    # Database
    db = Database(settings.db_path)
    await db.initialize()

    # Run seeders (idempotent — safe on every startup)
    from gamesync.storage.seeders import seed_leagues_and_event_types
    await seed_leagues_and_event_types(db)

    # Sound manager
    sound_manager = SoundManager(db, settings.data_path)
    await sound_manager.seed_builtin_sounds()

    # HA Client
    ha_client = HAClient(settings.supervisor_url, settings.supervisor_token)
    light_controller = LightController(ha_client)
    media_controller = MediaController(ha_client)
    tts_controller = TTSController(ha_client)
    ha_event_firer = HAEventFirer(ha_client)

    # Effect engine (with DB for 3-tier resolution)
    effect_composer = EffectComposer(db=db)
    effect_executor = EffectExecutor(light_controller, media_controller)

    # Apply mute state from config
    app_config = await db.get_app_config()
    effect_executor.muted = app_config.global_mute

    # Session manager
    session_manager = SessionManager(db)

    # Event pipeline
    emitter = EventEmitter()
    delay_buffer = DelayBuffer()

    # Subscribe: event emitter -> HA event firer + SSE broadcast + db logging
    async def on_event(event):
        await ha_event_firer.fire(event)
        await emitter._broadcast_to_sse(event)
        # Log to database
        await db.log_event(
            event_id=event.id,
            game_id=event.game_id,
            event_type=event.event_type.value,
            team_id=event.team_id,
            league=event.league.value,
            timestamp=event.timestamp.isoformat(),
            data=event.details,
        )

    emitter.subscribe(on_event)

    # Start delay buffer (publishes to emitter)
    await delay_buffer.start(emitter.publish)

    # Load followed teams and delays from DB
    followed_teams = await db.get_followed_teams()
    delays = {t.team_id: t.delay_seconds for t in followed_teams}
    delay_buffer.load_delays(delays)

    # Sport providers
    registry = ProviderRegistry()
    await registry.initialize()

    # Scheduler
    scheduler = PollScheduler(
        registry=registry,
        emitter=emitter,
        delay_buffer=delay_buffer,
        poll_interval_live=app_config.poll_interval_live,
        poll_interval_gameday=app_config.poll_interval_gameday,
        poll_interval_idle=app_config.poll_interval_idle,
    )

    # Set followed teams on scheduler (convert str league back to LeagueId)
    from gamesync.sports.models import LeagueId
    team_leagues = {}
    for t in followed_teams:
        try:
            team_leagues[t.team_id] = LeagueId(t.league)
        except ValueError:
            logger.warning("Unknown league %s for team %s, skipping", t.league, t.team_id)
    scheduler.set_followed_teams(team_leagues)

    if followed_teams:
        await scheduler.start()
        logger.info("Scheduler started with %d followed teams", len(followed_teams))
    else:
        logger.info("No followed teams — scheduler idle")

    logger.info("GameSync ready")
    yield

    # Shutdown
    logger.info("GameSync shutting down...")
    if scheduler:
        await scheduler.stop()
    if delay_buffer:
        await delay_buffer.stop()
    if registry:
        await registry.shutdown()
    if ha_client:
        await ha_client.close()
    if db:
        await db.close()
    logger.info("GameSync stopped")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="GameSync",
        version="0.2.0",
        description="Live sports score tracking with smart light effects",
        lifespan=lifespan,
    )

    # CORS for ingress
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers — existing
    from gamesync.api.health import router as health_router
    from gamesync.api.games import router as games_router
    from gamesync.api.teams import router as teams_router
    from gamesync.api.effects import router as effects_router
    from gamesync.api.lights import router as lights_router
    from gamesync.api.config import router as config_router
    from gamesync.api.events import router as events_router

    # API routers — new (Mowgli v7)
    from gamesync.api.sounds import router as sounds_router
    from gamesync.api.event_types import router as event_types_router
    from gamesync.api.sessions import router as sessions_router
    from gamesync.api.game_overrides import router as game_overrides_router
    from gamesync.api.ha_entities import router as ha_entities_router
    from gamesync.api.global_controls import router as global_controls_router

    app.include_router(health_router, prefix="/api")
    app.include_router(games_router, prefix="/api")
    app.include_router(teams_router, prefix="/api")
    app.include_router(effects_router, prefix="/api")
    app.include_router(lights_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    app.include_router(events_router, prefix="/api")
    app.include_router(sounds_router, prefix="/api")
    app.include_router(event_types_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")
    app.include_router(game_overrides_router, prefix="/api")
    app.include_router(ha_entities_router, prefix="/api")
    app.include_router(global_controls_router, prefix="/api")

    # Mount static files for web UI — serve React build if available, else old web UI
    import os
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    web_dir = os.path.join(os.path.dirname(__file__), "web")

    if os.path.isdir(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    elif os.path.isdir(web_dir):
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")

    return app


# Application instance
app = create_app()
