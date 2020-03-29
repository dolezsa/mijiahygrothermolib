from bluepy import btle
from functools import wraps
import logging
import re
import time
import datetime

_LOGGER = logging.getLogger(__name__)

BATTERY_INTERVAL = 3600
DATA_TIMEOUT = 3600

def retry(method):
    @wraps(method)
    def wrapper_retry(self, p):
        initial = time.monotonic()
        while True:
            if time.monotonic() - initial >= 10:
                return None
            try:
                #print("try...")
                return method(self, p)
            except (AttributeError, btle.BTLEException):
                _LOGGER.warning("Connection error for device {}."
                                " Reconnecting...".format(self.address))
                p.connect(self.address, iface = self.iface)
    return wrapper_retry

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

        self._read_timestamp = None

        self.__last_battery = None
        self.__last_data = None

        self.__errorcnt = 0

    def __repr__(self):
        return "<MijiaHygrothermo '%s'>" (self.address)

    @retry
    def __name(self, p):
        return ''.join(map(chr, p.readCharacteristic(0x3)))

    @retry
    def __firmware(self, p):
        return ''.join(map(chr, p.readCharacteristic(0x24)))

    @retry
    def __battery(self, p):
        return p.readCharacteristic(0x18)[0]

    @retry
    def __ht_data(self, p):
        delegate = XiomiHygroThermoDelegate()
        p.withDelegate(delegate)
        p.writeCharacteristic(0x10, bytearray([1, 0]), True)
        while not delegate.received:
            p.waitForNotifications(1.0)
        return delegate.temperature, delegate.humidity

    def read_data(self, devinfo = False):
        try:
            p = btle.Peripheral(self.address, iface = self.iface)
            self.__errorcnt = 0

            if devinfo:
                self._name = self.__name(p)
                self._firmware = self.__firmware(p)

            if self.__last_battery is None or time.monotonic() - self.__last_battery >= BATTERY_INTERVAL:
                self._battery = self.__battery(p)
                self.__last_battery = time.monotonic()

            data = self.__ht_data(p)
            if data is not None:
                self._temperature, self._humidity = data
            else:
                self._temperature = None
                self._humidity = None

            self._read_timestamp = datetime.datetime.now()

            self.__last_data = time.monotonic()

            return True
        except Exception as ex:
            if isinstance(ex, btle.BTLEException):
                _LOGGER.warning("BT connection error: {}".format(ex))
            else:
                _LOGGER.error("Unexpected error: {}".format(ex))

            self.__errorcnt += 1
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
        if self._temperature is None or time.monotonic() - self.__last_data >= DATA_TIMEOUT:
            self.read_data()
        return self._temperature

    @property
    def humidity(self):
        if self._humidity is None or time.monotonic() - self.__last_data >= DATA_TIMEOUT:
            self.read_data()
        return self._humidity

    @property
    def last_data_read(self):
        if self._read_timestamp is None:
            return "N/A"
        return self._read_timestamp

    @property
    def errorcnt(self):
        return self.__errorcnt

    def get_latest_properties(self):
        return {'macAddress' : self.address,
                'firmwareVersion': self.firmware,
                'batteryPercentage': self.battery,
                'name': self.name,
                'temperature': self.temperature,
                'humidity': self.humidity,
                'lastDataRead': self.last_data_read}

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
