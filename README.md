# LIRC watcher

Docker container that listens to LIRC daemon (running on the host) and sends received codes over MQTT with added benefit of short and long putton press.

**LIRC must be install on the host system**. Following examples have been tested below but should work on other platforms with adjustments too.

## Debian Buster
Please follow steps in wiki [Install-on-Debian-Buster](https://github.com/pilotak/docker-lirc-watcher/wiki/Install-on-Debian-Buster)

## Debian Stretch
Please follow steps in wiki [Install-on-Debian-Stretch](https://github.com/pilotak/docker-lirc-watcher/wiki/Install-on-Debian-Stretch)

## Ubuntu 18.04
Please follow steps in wiki [Install-on-Ubuntu-18.04](https://github.com/pilotak/docker-lirc-watcher/wiki/Install-on-Ubuntu-18.04)

## Recording codes
Test receiver
```sh
sudo systemctl stop lircd.service
mode2 --driver default --device /dev/lirc0
```
Output should look similar to this:
```
space 4195
pulse 551
space 1621
pulse 501
space 529
pulse 572
space 1553
pulse 547
space 524
pulse 551
space 525
pulse 549
```

If everything is ok, execute following and follow the commands in the script. Adjust name of the file should you wish.
```sh
sudo irrecord --driver default --device /dev/lirc0 ~/pioneer.lircd.conf
```

You will end it up with file `~/pioneer.lircd.conf`.

```
begin remote

  name  pioneer
  bits           32
  flags SPACE_ENC|CONST_LENGTH
  eps            30
  aeps          100

  header       8544  4180
  one           578  1545
  zero          578   497
  ptrail        575
  gap          91166
  min_repeat      3
  toggle_bit_mask 0xF0F08080
  frequency    38000

      begin codes
          KEY_POWER                0xA55A38C7
          KEY_MUTE                 0xA55A48B7
          KEY_VOLUMEUP             0xA55A50AF
          KEY_VOLUMEDOWN           0xA55AD02F
      end codes

end remote
```

Let's move this config over to LIRC daemon.
```sh
sudo mv ~/pioneer.lircd.conf /etc/lirc/lircd.conf.d/
sudo systemctl start lircd.service
```

Test receiver again, if you see the names of your keys when button pressed, that's a win-win.
```sh
irw
```

## Docker-compose
Now just start the docker container, alter the config to your needs and you ready to rock.
```yaml
version: "3"
services:
  lirc:
    container_name: lirc
    restart: always
    image: pilotak/lirc-watcher
    environment:
      - MQTT_BROKER=192.168.0.10
      - MQTT_USER=admin
      - MQTT_PASSWORD=my-secret-pw
    volumes:
      - /var/run/lirc/lircd:/var/run/lirc/lircd
```

### Environmental variables
Bellow are all available variables

| Variable | Description | Default value |
| --- | --- | :---:|
| `LONG_PRESS` | How many messages is received to be considered as long press | 12 |
| `READ_TIMEOUT` | How long to wait to process new data *seconds* | 0.2 | 
| `PAYLOAD_LONG_PRESS` | Payload on long press | "long" | 
| `PAYLOAD_SHORT_CLICK` | Payload on short press | "short" | 
| `MQTT_BROKER` | Broker address | localhost | 
| `MQTT_USER` | MQTT user | None | 
| `MQTT_PASSWORD` | MQTT password | None | 
| `MQTT_PORT` | MQTT broker port | 1883 | 
| `MQTT_ID` | MQTT client id | "lirc-watcher" | 
| `MQTT_PREFIX` | MQTT topic prefix | "lirc" |

### MQTT topics
When button is pressed you will receive message in format
`MQTT_PREFIX/REMOTE_NAME/KEY_NAME` with payload `short` / `long` ie. `lirc/pioneer/KEY_POWER`
