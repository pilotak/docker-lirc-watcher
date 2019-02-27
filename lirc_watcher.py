#!/usr/bin/env python3

import socket
import os
import paho.mqtt.client as paho
from datetime import datetime
import sys
import socket
import fcntl
import errno

sock = None
prev_data = None
priority_data = None
last_data_timestamp = 0

LONG_PRESS = os.getenv('LONG_PRESS', 12)
READ_TIMEOUT = os.getenv('READ_TIMEOUT', 200000)
PAYLOAD_LONG_PRESS = os.getenv('PAYLOAD_LONG_PRESS', 'long')
PAYLOAD_SHORT_CLICK = os.getenv('PAYLOAD_SHORT_CLICK', 'short')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_USER = os.getenv('MQTT_USER', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_ID = os.getenv('MQTT_ID', 'lirc-watcher')
MQTT_PREFIX = os.getenv('MQTT_PREFIX', 'lirc')


def on_message(client, userdata, message):
    print("Message received: %s on topic: %s " %
          (str(message.payload.decode("utf-8")), message.topic))


def init_mqtt():
    global mqtt
    mqtt = paho.Client(MQTT_ID)
    mqtt.on_message = on_message  # attach function to callback
    mqtt.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt.connect(MQTT_BROKER, MQTT_PORT)
    mqtt.loop_start()


def init_lirc():
    global sock
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect("/var/run/lirc/lircd")
    fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)


if __name__ == '__main__':
    print("LIRC watcher started")

    init_mqtt()
    init_lirc()

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
            Check for "real" error, exclude empty data
            """
            if err != errno.EAGAIN or err != errno.EWOULDBLOCK:
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
                    priority_data = prev_data

                prev_data = new_data
                last_data_timestamp = datetime.now().microsecond
                # print("start time: ", last_data_timestamp)

        if priority_data is not None or \
           (last_data_timestamp > 0 and prev_data is not None and
                ((datetime.now().microsecond - last_data_timestamp) >=
                 READ_TIMEOUT)):
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
            mqtt.publish(topic, payload)

            if priority_data is not None:
                priority_data = None
            else:
                prev_data = None
                last_data_timestamp = 0
