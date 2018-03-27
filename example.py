from mijiahygrothermo import MijiaHygrothermo

for device in MijiaHygrothermo.discover():
    print("- {}".format(device.address))
    print("  name: {}".format(device.name))
    print("  firmware: {}".format(device.firmware))
    print("  battery level: {}%".format(device.battery))
    print("  temperature: {}*C".format(device.temperature))
    print("  humidity: {}%".format(device.humidity))
    print()
