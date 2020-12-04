#!/usr/bin/env python3

import os
import paho.mqtt.client as paho
from threading import Timer
import sys
import socket
import fcntl
import errno
from time import sleep

LONG_PRESS = os.getenv('LONG_PRESS', 12)
READ_TIMEOUT = os.getenv('READ_TIMEOUT', 0.2)
PAYLOAD_LONG_PRESS = os.getenv('PAYLOAD_LONG_PRESS', 'long')
PAYLOAD_SHORT_CLICK = os.getenv('PAYLOAD_SHORT_CLICK', 'short')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_USER = os.getenv('MQTT_USER', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
MQTT_QOS = os.getenv('MQTT_QOS', 1)
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_ID = os.getenv('MQTT_ID', 'lirc-watcher')
MQTT_PREFIX = os.getenv('MQTT_PREFIX', 'lirc')

MQTT_STATUS_TOPIC = '%s/alive' % MQTT_PREFIX
MQTT_PAYLOAD_ONLINE = '1'
MQTT_PAYLOAD_OFFLINE = '0'

print("LIRC watcher started")


def on_mqtt_connect(mqtt, userdata, flags, rc):
    if rc == 0:
        print('MQTT connected')

        mqtt.publish(MQTT_STATUS_TOPIC, payload=MQTT_PAYLOAD_ONLINE,
                     qos=MQTT_QOS, retain=True)
    else:
        print('MQTT connect failed:', rc)


prev_data = None
t = None

mqtt = paho.Client(MQTT_ID)
mqtt.on_connect = on_mqtt_connect
mqtt.will_set(MQTT_STATUS_TOPIC, payload=MQTT_PAYLOAD_OFFLINE,
              qos=MQTT_QOS, retain=True)
mqtt.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt.connect(MQTT_BROKER, MQTT_PORT)
mqtt.loop_start()

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/var/run/lirc/lircd")
fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)


def send_code(priority_data=None):
    global prev_data, mqtt

    if priority_data is not None or prev_data is not None:
        to_send = priority_data if priority_data is not None else prev_data
        to_send = to_send.split()
        key_name = to_send[2]
        remote = to_send[3]
        counter = int(to_send[1], 16)

        if(counter >= LONG_PRESS):
            payload = PAYLOAD_LONG_PRESS
        else:
            payload = PAYLOAD_SHORT_CLICK

        topic = "%s/%s/%s" % (MQTT_PREFIX, remote, key_name)
        print("Sending message: '%s' to topic: '%s'" %
              (payload, topic))
        mqtt.publish(topic, payload=payload, qos=MQTT_QOS)

        if priority_data is None:
            prev_data = None


try:
    while True:
        """
        Check for new data
        """
        try:
            new_data = sock.recv(128)
            new_data = new_data.strip()

        except socket.error as e:
            err = e.args[0]

            """
            Check for "real" error
            """
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                sleep(0.01)
                continue
            else:
                print(e)
                mqtt.disconnect()
                mqtt.loop_stop()
                sys.exit(1)
        else:
            if new_data:
                new_data = new_data.decode("utf-8")
                # print("new_data: ", new_data)
                counter_str = new_data.split()

                """
                If we received new_data and prev_data was not sent
                """
                if prev_data is not None and int(counter_str[1], 16) == 0:
                    send_code(prev_data)

                prev_data = new_data

                if t is not None and t.is_alive():
                    t.cancel()

                t = Timer(READ_TIMEOUT, send_code)
                t.start()


except KeyboardInterrupt:
    mqtt.disconnect()
    mqtt.loop_stop()
