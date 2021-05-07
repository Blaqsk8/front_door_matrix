import board
import displayio
import busio
import terminalio
import adafruit_display_text.label
import framebufferio
import rgbmatrix
from digitalio import DigitalInOut
from analogio import AnalogIn
import neopixel
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from digitalio import DigitalInOut, Direction, Pull
import adafruit_touchscreen
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_si7021
import adafruit_matrixportal.matrixportal import MatrixPortal

# ------------- Display ------------- #

SCROLL_DELAY = 0.02

matrixportal = Matrixportal(status_neopixel=board.NEOPIXEL, debug=True)

# Create a new label with the color and text selected
# First Text Line
matrixportal.add_text(
    text_font=terminalio.FONT,
    text_position=(0, 3), 
    scrolling=True,
)

# Second Text Line
matrixportal.add_text(
    text_font=terminalio.FONT, 
    text_position=(0, 19),
    scrolling=True
)

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

door_sensor = DigitalInOut(board.A1)
door_sensor.direction = Direction.INPUT
door_sensor.pull = Pull.UP

pir_sensor = DigitalInOut(board.A0)
pir_sensor.direction = Direction.INPUT
pir_sensor.pull = Pull.UP

# ------------- MQTT Topic Setup ------------- #
# Group Feed is set to Door group
PUBLISH_DELAY = 60
mqtt_topic = "test/topic"
mqtt_temperature = "door/temperature"
mqtt_humidity = "door/humidity"
mqtt_PIR = "door/pir"
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

# ------------- Network Connection Function ------------- #
def update_data():
    # Connect to WiFi
    print("Connecting to WiFi...")
    wifi.connect()
    print("Connected to WiFi!")
    matrixportal.set_text("Connecting", 1)
 
    # Initialize MQTT interface with the esp interface
    MQTT.set_socket(socket, esp)
 
    # Set up a MiniMQTT Client
    client = MQTT(
        broker=secrets["mqtt_broker"],
        port=1883,
        username=secrets["mqtt_username"],
        password=secrets["mqtt_password"],
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
        % (mqtt_temperature, mqtt_humidity, mqtt_switch, mqtt_PIR)
    )
    client.subscribe(mqtt_temperature)
    client.subscribe(mqtt_humidity)
    client.subscribe(mqtt_switch)
    client.subscribe(mqtt_PIR)
    
    temp_f = (temp_sensor.temperature * 1.8) + 32
    humidity = temp_sensor.relative_humidty)
    print(temp_f)
    client.publish(mqtt_temperature, temp_f)
    print(humidity)
    client.publish(mqtt_humidity, humidity)
    print(door_sensor.value)
    client.publish(mqtt_witch1, door_sensor.value)
    print(pir_sensor.value)
    client.publish(mqtt_PIR, pir_sensor.value)
    if door_sensor.value == True:
        text_door = str(door_sensor.value)
        matrixportal.set_text(text_door)
    if door_sensor.value == False:
        text_door = str(door_sensor.value)
        matrixportal.set_text(text_door)
    if door_sensor.value == True:
        text_pir = str(pir_sensor.value)
        matrixportal.set_text(text_pir, 1)
    if door_sensor.value == False:
        text_pir = str(pir_sensor.value)
        matrixportal.set_text(text_pir, 1)
    matrixportal.scroll_text(SCROLL_DELAY)

# ------------- Initialize Services ------------- #

update_data()
matrixportal.set_text(" ", 1)
last_update = time.monotonic()

# ------------- Program Loop ------------- #
while True:
    while time.monotonic() < last_update + PUBLISH_DELAY:
        update_data()
        last_update = time.monotonic()
