from mijiahygrothermo import MijiaHygrothermo

for device in MijiaHygrothermo.discover():
    data = device.get_latest_properties()
    print("- {}".format(data['macAddress']))
    print("  name: {}".format(data['name']))
    print("  firmware: {}".format(data['firmwareVersion']))
    print("  battery level: {}%".format(data['batteryPercentage']))
    print("  temperature: {}*C".format(data['temperature']))
    print("  humidity: {}%".format(data['humidity']))
    print("  last data read: {}%".format(data['lastDataRead']))
    print()
