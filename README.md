# LIRC watcher

Docker container that listens to LIRC daemon (running on the host) and sends received codes over MQTT with added benefit of short and long putton press.

LIRC must be install on the host system. Following example is for Raspberry Pi 4 but should work on other platforms with adjustments too.

## Install on Debian Buster
LIRC on Buster have to be patched in order to work, so the installation is more complex.

If you already tried to install `lirc`, remove it first
```sh
sudo apt remove lirc liblirc0 liblirc-client0
```

Install patched LIRC
```sh
sudo su -c "grep '^deb ' /etc/apt/sources.list | sed 's/^deb/deb-src/g' > /etc/apt/sources.list.d/deb-src.list"
sudo apt update
sudo apt install -y devscripts dh-exec doxygen expect libasound2-dev libftdi1-dev libsystemd-dev libudev-dev libusb-1.0-0-dev libusb-dev man2html-base portaudio19-dev socat xsltproc python3-yaml dh-python libx11-dev python3-dev python3-setuptools
mkdir build
cd build
apt source lirc
wget https://raw.githubusercontent.com/neuralassembly/raspi/master/lirc-gpio-ir-0.10.patch
patch -p0 -i lirc-gpio-ir-0.10.patch
cd lirc-0.10.1
debuild -uc -us -b
cd ..
sudo apt install -y --allow-downgrades ./liblirc0_0.10.1-5.2_armhf.deb ./liblircclient0_0.10.1-5.2_armhf.deb ./lirc_0.10.1-5.2_armhf.deb
```

The last command will fail, but it will create important files
```sh
sudo cp /etc/lirc/lirc_options.conf.dist /etc/lirc/lirc_options.conf
sudo cp /etc/lirc/lircd.conf.dist /etc/lirc/lircd.conf
```

Alter following file
```sh
sudo nano /etc/lirc/lirc_options.conf
```
```
driver = default
device = /dev/lirc0
```


Specify pin you have a IR receiver connected to
```sh
sudo echo dtoverlay=gpio-ir,gpio_pin=17 >> /boot/config.txt
```

Reboot to apply changes
```sh
sudo reboot
```


## Install on Debian Stretch
```sh
sudo apt install lirc
```

Enable LIRC & specify pins
```sh
# sudo echo "lirc_dev" >> /etc/modules
# sudo echo lirc_rpi gpio_in_pin=20 gpio_out_pin=16 >> /etc/modules
sudo echo dtoverlay=gpio-ir,gpio_pin=20,gpio_pull=up >> /boot/config.txt
```

Find and alter following lines in `/etc/lirc/lirc_options.conf`
```ApacheConf
driver = default
device = /dev/lirc0
```

Paste following code into file `/etc/lirc/hardware.conf`
```ApacheConf
########################################################
LIRCD_ARGS="--uinput --listen"
LOAD_MODULES=true
DRIVER="default"
DEVICE="/dev/lirc0"
MODULES="lirc_rpi"

LIRCD_CONF=""
LIRCMD_CONF=""
########################################################
```

Reboot to apply changes
```sh
sudo reboot
```

### Enable LIRC service
```sh
sudo systemctl enable lircd.service && sudo systemctl start lircd.service
sudo systemctl status lircd.service
```

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
version: "3.6"
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
| `READ_TIMEOUT` | How long to wait to process new data *in s* | 0.2 | 
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
