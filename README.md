# docker-lirc-watcher
Listens to LIRC daemon and sends it to MQTT

## Environmental variables
| Variable | Description | Default value |
| --- | --- | :---:|
| `LONG_PRESS` | How many messages is received to be considered as long press | 12 |
| `READ_TIMEOUT` | How long to wait to process new data *in us* | 200000 | 
| `PAYLOAD_LONG_PRESS` | Payload on long press | "long" | 
| `PAYLOAD_SHORT_CLICK` | Payload on short press | "short" | 
| `MQTT_BROKER` | Broker address | localhost | 
| `MQTT_USER` | MQTT user | None | 
| `MQTT_PASSWORD` | MQTT password | None | 
| `MQTT_PORT` | MQTT broker port | 1883 | 
| `MQTT_ID` | MQTT client id | "lirc-watcher" | 
| `MQTT_PREFIX` | MQTT topic prefix | "lirc" | 

## Docker-compose
```yaml
version: "3.6"
services:
  lirc:
    container_name: lirc
    restart: always
    image: pilotak/lirc-watcher
    environment:
      - MQTT_HOST=192.168.0.10
      - MQTT_USER=admin
      - MQTT_PASSWORD=my-secret-pw
    volumes:
      - /var/run/lirc/lircd:/var/run/lirc/lircd
```
