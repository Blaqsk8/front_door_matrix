import board
import displayio
import busio
from digitalio import DigitalInOut
from analogio import AnalogIn
import neopixel
import adafruit_adt7410
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_button import Button
from digitalio import DigitalInOut, Direction, Pull
import adafruit_touchscreen
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_si7021
 
# ------------- WiFi ------------- #
 
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
 
# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
 
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# ------------- Sensor Setup ------------- #
temp_sensor = adafruit_si7021.SI7021(board.I2C())

door_sensor = DigitalInOut(board.A0)
door_sensor.direction = Direction.INPUT
door_sensor.pull = Pull.UP

# ------------- MQTT Topic Setup ------------- #
 
PUBLISH_DELAY = 60
mqtt_topic = "test/topic"
mqtt_temperature = "door/temperature"
mqtt_humidity = "pyportal/humidity"
mqtt_PIR = "pyportal/pir"
mqtt_switch = "door/switch1"

# ------------- MQTT Functions ------------- #
 
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to MQTT Broker!")
    print("Flags: {0}\n RC: {1}".format(flags, rc))
 
 
def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from MQTT Broker!")
 
 
def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))
 
 
def publish(client, userdata, topic, pid):
    # This method is called when the client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))
 
 
def message(client, topic, message):
    """Method callled when a client's subscribed feed has a new
    value.
    :param str topic: The topic of the feed with a new value.
    :param str message: The new value
    """
    print("New message on topic {0}: {1}".format(topic, message))
    if topic == "pyportal/feed1":
        feed1_label.text = "Next Bus: {}".format(message)
    if topic == "pyportal/feed2":
        feed2_label.text = "Weather: \n    {}".format(message)
    if topic == "pyportal/button1":
        if message == "1":
            buttons[0].label = "ON"
            buttons[0].selected = False
            print("Button 1 ON")
        else:
            buttons[0].label = "OFF"
            buttons[0].selected = True
            print("Button 1 OFF")

# ------------- Network Connection ------------- #
 
# Connect to WiFi
print("Connecting to WiFi...")
wifi.connect()
print("Connected to WiFi!")
 
# Initialize MQTT interface with the esp interface
MQTT.set_socket(socket, esp)
 
# Set up a MiniMQTT Client
client = MQTT(
    broker=secrets["broker"],
    port=1883,
    username=secrets["user"],
    password=secrets["pass"],
)
 
# Connect callback handlers to client
client.on_connect = connect
client.on_disconnect = disconnected
client.on_subscribe = subscribe
client.on_publish = publish
client.on_message = message
 
print("Attempting to connect to %s" % client.broker)
client.connect()
 
print(
    "Subscribing to %s, %s, %s, and %s"
    % (mqtt_feed1, mqtt_feed2, mqtt_button1, mqtt_button2)
)
client.subscribe(mqtt_feed1)
client.subscribe(mqtt_feed2)
client.subscribe(mqtt_button1)
client.subscribe(mqtt_button2)

# ------------- Program Loop ------------- #
while True:
    temp_f = (temp_sensor.temperature * 1.8) + 32
    humidity = temp_sensor.relative_humidty)
    print(temp_f)
    print(door_sensor)
    
    output = {
        "temperature": temp_f,
        "humidity": humidity,
        "deep": door_sensor,
    }
    print("Publishing to %s" % MQTT_TOPIC)
    mqtt_client.publish(MQTT_TOPIC, json.dumps(output))
    
    last_update = time.monotonic()
    while time.monotonic() < last_update + PUBLISH_DELAY:
        mqtt_client.loop()
