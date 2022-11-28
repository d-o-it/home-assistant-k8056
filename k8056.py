"""The Velleman K8056 implementation."""

import logging
import asyncio
import asyncio.tasks
import serialio

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = 3.0


class K8056:
    def __init__(self, serial: serialio, repeat=0, wait=0) -> None:
        self.serial = serial
        self.serial_lock = asyncio.Lock()
        self.repeat = repeat
        self.wait = wait

    async def __worker(self, cmd, card, relay):
        try:
            await self.serial.open()

            cksum = (243 - cmd - relay - card) & 255
            for i in range(self.repeat + 1):
                data = bytearray([13, card, cmd, relay, cksum])
                _LOGGER.debug("Sending %s", data.hex())
                await self.serial.write(data)
                await asyncio.sleep(self.wait)
        finally:
            await self.serial.close()

    async def __process(self, cmd, card, relay):
        await self.serial_lock.acquire()
        try:
            await asyncio.wait_for(self.__worker(cmd, card, relay), _TIMEOUT)
        finally:
            self.serial_lock.release()

    async def set(self, card, relay):
        """Set `relay` (9 for all) of `card`."""
        _LOGGER.info("Switch on card %i relay %i", card, relay)
        if not 0 < relay < 10:
            raise Exception("invalid relay number")

        await self.__process(83, card & 255, relay + 48)

    async def clear(self, card, relay):
        """Clear `relay` (9 for all) of `card`."""
        _LOGGER.info("Switch off card %i relay %i", card, relay)
        if not 0 < relay < 10:
            raise Exception("invalid relay number")

        await self.__process(67, card & 255, relay + 48)

    async def emergency_stop(self):
        """Clear all relays on all cards. emergency purpose."""
        await self.__process(69, 1, 1)
