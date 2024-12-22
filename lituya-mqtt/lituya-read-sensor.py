import time
import json
import paho.mqtt.client as mqtt

def read_sensor(self, gpio=None, identifier=None):
    #self._log.debug("Reading from: {}".format(identifier))
    print("Reading from: {}".format(identifier))
    counter = 0
    # while identifier not in _sensor_vals and counter < 10:
    #     counter = counter+1
    #     time.sleep(1)

    if identifier in _sensor_vals:
        value = _sensor_vals[identifier]
    else:
        value = None
        print("Value not found for: " + identifier)
    return([value])

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")
    #client.subscribe("N/c0619ab56440/vebus/276/Dc/0/Temperature")
    client.subscribe("N/c0619ab56440/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    payload = json.loads(msg.payload)
    _sensor_vals[msg.topic] = payload["value"]

# Callback if the MQTT connection is broken
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    if reason_code != 0:
        try:
            print("Unexpected disconnection with rc: " + str(reason_code) + "! Datetime: " + str(time.localtime()))
            print("Reconnecting, please wait...")
            time.sleep(3)
        except Exception as e:
            print("General exception in MQTT with rc: " + str(reason_code))
            print(e)
    else:
        print("Normal disconnect with rc: " + str(reason_code) + "! Datetime: " + str(time.localtime()))

def main():
    _mqttc = None
    _mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _mqttc.on_connect = on_connect
    _mqttc.on_disconnect = on_disconnect
    _mqttc.on_message = on_message
    _mqttc.connect("venus.local", 1883, 60)
    _mqttc.loop_start()
    while True:
        #_mqttc.publish('R/c0619ab56440/keepalive', retain=False)
        _mqttc.publish('R/c0619ab56440/vebus/276/Ac', retain=False)
        _mqttc.publish('R/c0619ab56440/vebus/276/Dc', retain=False)
        _mqttc.publish('R/c0619ab56440/system/0/Ac', retain=False)
        _mqttc.publish('R/c0619ab56440/system/0/Dc/Battery', retain=False)

        #val = read_sensor(None, identifier='N/c0619ab56440/vebus/276/Dc/0/Temperature')
        val = read_sensor(None, identifier='N/c0619ab56440/system/0/Ac/ActiveIn/L1/Power')
        print("Got value: " + str(val))
        time.sleep(2)
    _mqttc.loop_stop()
    _mqttc.disconnect()

    # try:
    #     _mqttc.loop_forever()
    # except KeyboardInterrupt:
    #     pass


if __name__ == "__main__":
    _sensor_vals = {}
    main()

