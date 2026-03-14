"""Atomic light effect operations."""

from __future__ import annotations

import asyncio
import logging

from gamesync.ha_client.lights import LightController

logger = logging.getLogger(__name__)


async def flash(
    lights: LightController,
    entity_ids: list[str],
    color_hex: str,
    on_ms: int = 200,
    off_ms: int = 100,
    count: int = 5,
    brightness: int = 255,
) -> None:
    """Flash lights on and off at a specified color."""
    for i in range(count):
        for eid in entity_ids:
            await lights.turn_on(eid, color_hex=color_hex, brightness=brightness)
        await asyncio.sleep(on_ms / 1000)

        for eid in entity_ids:
            await lights.turn_off(eid)
        await asyncio.sleep(off_ms / 1000)


async def color_cycle(
    lights: LightController,
    entity_ids: list[str],
    colors: list[str],
    step_ms: int = 500,
    cycles: int = 4,
    brightness: int = 255,
) -> None:
    """Cycle through a list of colors."""
    for _ in range(cycles):
        for color in colors:
            for eid in entity_ids:
                await lights.turn_on(eid, color_hex=color, brightness=brightness)
            await asyncio.sleep(step_ms / 1000)


async def fade(
    lights: LightController,
    entity_ids: list[str],
    from_color: str,
    to_color: str,
    duration_ms: int = 2000,
    brightness: int = 255,
) -> None:
    """Fade from one color to another using HA transition."""
    # Set initial color
    for eid in entity_ids:
        await lights.turn_on(eid, color_hex=from_color, brightness=brightness)
    await asyncio.sleep(0.1)

    # Transition to target color
    for eid in entity_ids:
        await lights.turn_on(
            eid,
            color_hex=to_color,
            brightness=brightness,
            transition=duration_ms / 1000,
        )
    await asyncio.sleep(duration_ms / 1000)


async def solid(
    lights: LightController,
    entity_ids: list[str],
    color_hex: str,
    duration_ms: int = 3000,
    brightness: int = 255,
) -> None:
    """Hold a solid color for a duration."""
    for eid in entity_ids:
        await lights.turn_on(eid, color_hex=color_hex, brightness=brightness)
    await asyncio.sleep(duration_ms / 1000)


async def pulse(
    lights: LightController,
    entity_ids: list[str],
    color_hex: str,
    min_brightness: int = 50,
    max_brightness: int = 255,
    period_ms: int = 400,
    count: int = 3,
) -> None:
    """Pulse brightness up and down."""
    half_period = period_ms / 2000  # seconds for half cycle

    for _ in range(count):
        # Ramp up
        for eid in entity_ids:
            await lights.turn_on(
                eid,
                color_hex=color_hex,
                brightness=max_brightness,
                transition=half_period,
            )
        await asyncio.sleep(half_period)

        # Ramp down
        for eid in entity_ids:
            await lights.turn_on(
                eid,
                color_hex=color_hex,
                brightness=min_brightness,
                transition=half_period,
            )
        await asyncio.sleep(half_period)
