from bluepy import btle
from datetime import datetime
import logging
import re

_LOGGER = logging.getLogger(__name__)

BATTERY_INTERVAL = 3600

class XiomiHygroThermoDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.temperature = None
        self.humidity = None
        self.received = False

    def handleNotification(self, cHandle, data):
        if cHandle == 14:
            m = re.search('T=([\d\.]*)\s+?H=([\d\.]*)', ''.join(map(chr, data)))
            self.temperature = m.group(1)
            self.humidity = m.group(2)
            self.received = True

class MijiaHygrothermo(object):
    def __init__(self, address, iface = 0):
        self.address = address
        self.iface = iface

        self._name = None
        self._firmware = None

        self._battery = None
        self._temperature = None
        self._humidity = None

        self._last_battery = None

    def __repr__(self):
        return "<MijiaHygrothermo '%s'>" (self.address)

    def read_data(self, devinfo = False):
        try:
            p = btle.Peripheral(self.address, iface = self.iface)

            if devinfo:
                self._name = ''.join(map(chr, p.readCharacteristic(0x3)))
                self._firmware = ''.join(map(chr, p.readCharacteristic(0x24)))
            if self._last_battery is None or (datetime.utcnow() - self._last_battery).seconds >= BATTERY_INTERVAL:
                self._battery = p.readCharacteristic(0x18)[0]
                self._last_battery = datetime.utcnow()

            delegate = XiomiHygroThermoDelegate()
            p.withDelegate( delegate )
            p.writeCharacteristic(0x10, bytearray([1, 0]), True)
            while not delegate.received:
                p.waitForNotifications(1.0)

            self._temperature = delegate.temperature
            self._humidity = delegate.humidity
            return True
        except Exception as ex:
            if isinstance(ex, btle.BTLEException):
                """ TODO retry..."""
                _LOGGER.warning("BT connection error: {}".format(ex))
            else:
                _LOGGER.error("Unexpected error: {}".format(ex))
            return False

    @property
    def name(self):
        if self._name is None:
            self.read_data(True)
        return self._name

    @property
    def firmware(self):
        if self._firmware is None:
            self.read_data(True)
        return self._firmware

    @property
    def battery(self):
        if self._battery is None:
            self.read_data()
        return self._battery

    @property
    def temperature(self):
        if self._temperature is None:
            self.read_data()
        return self._temperature

    @property
    def humidity(self):
        if self._humidity is None:
            self.read_data()
        return self._humidity

    @staticmethod
    def discover(iface = 0, timeout = 2):
        try:
            return [
                MijiaHygrothermo(device.addr, iface = iface)
                for device in btle.Scanner(iface).scan(timeout)
                if device.addr.startswith('4c:65') and device.scanData[9] == b'MJ_HT_V1'
            ]
        except Exception as ex:
            _LOGGER.error("Unexpected error: {}".format(ex))
            return []
