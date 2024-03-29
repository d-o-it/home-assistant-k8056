"""Support for Velleman K8056 switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_COUNT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .k8056 import K8056
from .const import DOMAIN, HUB

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


def create_switch_entity(
    config_entry: ConfigEntry, hub: K8056, card: int, relay: int
) -> K8056Relay:
    """Set up an entity for this domain."""
    _LOGGER.debug("Adding K8056 switch card %i relay %i", card, relay)
    return K8056Relay(config_entry.entry_id, hub, card, relay)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velleman K8056 switch entities from a config entry."""

    entities = []

    hub: K8056 = hass.data[DOMAIN][config_entry.entry_id][HUB]
    for card in range(1, int(config_entry.data[CONF_COUNT]) + 1):
        for relay in range(1, 9):
            entities.append(create_switch_entity(config_entry, hub, card, relay))

    async_add_entities(entities)


class K8056Relay(SwitchEntity):
    """Representation of a Velleman K8056 switch for relay ports."""

    def __init__(self, entry_id: str, hub: K8056, card: int, relay: int) -> None:
        """Initialize the Velleman K8056 switch."""
        self.entry_id = entry_id
        self.hub = hub
        self.card = card
        self.relay = relay
        self.card_name = f"K{self.card}"
        self._attr_name = f"K{card}R{relay}"
        self._attr_unique_id = f"{card}.{relay}"
        self._is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.card_name)
            },
            name=self.card_name,
            manufacturer="Velleman",
            model="K8056",
        )

    @property
    def icon(self) -> str:
        """Return a representative icon of the switch."""
        if self._is_on:
            return "mdi:toggle-switch-variant"
        return "mdi:toggle-switch-variant-off"

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        try:
            await self.hub.set(self.card, self.relay)
        except ConnectionRefusedError as ex:
            _LOGGER.error(ex.strerror)
        else:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        try:
            await self.hub.clear(self.card, self.relay)
        except ConnectionRefusedError as ex:
            _LOGGER.error(ex.strerror)
        else:
            self._is_on = False
            self.async_write_ha_state()
