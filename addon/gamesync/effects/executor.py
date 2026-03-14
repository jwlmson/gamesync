"""Effect executor — walks effect sequences and issues HA calls."""

from __future__ import annotations

import asyncio
import logging

from gamesync.effects.models import EffectPrimitive, EffectSequence, EffectStep
from gamesync.effects import primitives as prim
from gamesync.ha_client.lights import LightController
from gamesync.ha_client.media import MediaController

logger = logging.getLogger(__name__)


class EffectExecutor:
    """Execute effect sequences on lights and speakers."""

    def __init__(
        self,
        lights: LightController,
        media: MediaController,
    ) -> None:
        self._lights = lights
        self._media = media
        self._active_tasks: dict[str, asyncio.Task] = {}  # group_key -> task
        self._semaphore = asyncio.Semaphore(5)  # max concurrent HA calls
        self._muted: bool = False

    @property
    def muted(self) -> bool:
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        self._muted = value

    async def emergency_stop(self) -> int:
        """Cancel ALL active effects immediately and restore lights. Returns count stopped."""
        count = 0
        for group_key, task in list(self._active_tasks.items()):
            if not task.done():
                task.cancel()
                count += 1
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._active_tasks.clear()
        logger.info("Emergency stop: cancelled %d active effects", count)
        return count

    async def execute(self, sequence: EffectSequence, group_key: str = "default") -> None:
        """Execute an effect sequence.

        If muted, skips execution entirely.
        If an effect is already running for the same group_key, cancel it first.
        """
        if self._muted:
            logger.debug("Effect suppressed (muted) for group %s", group_key)
            return

        # Cancel existing effect for this group
        existing = self._active_tasks.get(group_key)
        if existing and not existing.done():
            existing.cancel()
            try:
                await existing
            except asyncio.CancelledError:
                pass

        # Launch as task
        task = asyncio.create_task(
            self._run_sequence(sequence), name=f"effect-{group_key}"
        )
        self._active_tasks[group_key] = task

        try:
            await task
        except asyncio.CancelledError:
            logger.debug("Effect cancelled for group %s", group_key)
        except Exception:
            logger.exception("Effect execution failed for group %s", group_key)

    async def _run_sequence(self, sequence: EffectSequence) -> None:
        """Internal: walk steps and execute."""
        # Gather all entity IDs for state capture
        all_entities = set()
        for step in sequence.steps:
            for target in step.targets:
                all_entities.update(target.entity_ids)

        # Capture pre-effect state
        saved_states = {}
        if sequence.restore_after:
            saved_states = await self._lights.capture_states(list(all_entities))

        try:
            # Play audio if configured
            if sequence.audio and sequence.audio.media_url:
                try:
                    await self._media.play_media(
                        sequence.audio.entity_id,
                        sequence.audio.media_url,
                    )
                except Exception:
                    logger.warning("Failed to play audio for effect %s", sequence.name)

            # Execute each step
            for step in sequence.steps:
                if step.primitive == EffectPrimitive.RESTORE:
                    if saved_states:
                        await self._lights.restore_states(saved_states)
                    continue

                entity_ids = []
                for target in step.targets:
                    entity_ids.extend(target.entity_ids)

                if not entity_ids:
                    continue

                await self._execute_step(step, entity_ids)

                if step.delay_after_ms > 0:
                    await asyncio.sleep(step.delay_after_ms / 1000)

        except asyncio.CancelledError:
            # Restore lights on cancellation
            if sequence.restore_after and saved_states:
                await self._lights.restore_states(saved_states)
            raise

    async def _execute_step(self, step: EffectStep, entity_ids: list[str]) -> None:
        """Execute a single effect step."""
        p = step.params

        async with self._semaphore:
            if step.primitive == EffectPrimitive.FLASH:
                await prim.flash(
                    self._lights,
                    entity_ids,
                    color_hex=p.get("color_hex", "#FFFFFF"),
                    on_ms=p.get("on_ms", 200),
                    off_ms=p.get("off_ms", 100),
                    count=p.get("count", 5),
                    brightness=p.get("brightness", 255),
                )
            elif step.primitive == EffectPrimitive.COLOR_CYCLE:
                await prim.color_cycle(
                    self._lights,
                    entity_ids,
                    colors=p.get("colors", ["#FFFFFF"]),
                    step_ms=p.get("step_ms", 500),
                    cycles=p.get("cycles", 4),
                    brightness=p.get("brightness", 255),
                )
            elif step.primitive == EffectPrimitive.FADE:
                await prim.fade(
                    self._lights,
                    entity_ids,
                    from_color=p.get("from_color", "#FFFFFF"),
                    to_color=p.get("to_color", "#000000"),
                    duration_ms=p.get("duration_ms", 2000),
                    brightness=p.get("brightness", 255),
                )
            elif step.primitive == EffectPrimitive.SOLID:
                await prim.solid(
                    self._lights,
                    entity_ids,
                    color_hex=p.get("color_hex", "#FFFFFF"),
                    duration_ms=p.get("duration_ms", 3000),
                    brightness=p.get("brightness", 255),
                )
            elif step.primitive == EffectPrimitive.PULSE:
                await prim.pulse(
                    self._lights,
                    entity_ids,
                    color_hex=p.get("color_hex", "#FFFFFF"),
                    min_brightness=p.get("min_brightness", 50),
                    max_brightness=p.get("max_brightness", 255),
                    period_ms=p.get("period_ms", 400),
                    count=p.get("count", 3),
                )
