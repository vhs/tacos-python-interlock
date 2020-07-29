import os
import requests
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import json
from time import sleep
import time
import sched
import datetime
import traceback

BLINK_DELAY = 250

if (os.environ.get("TACOS_ENV") or "").strip() == "mock":
    print("Loading mock GPIO")
    from GPIOEmulator.EmulatorGUI import GPIO
    from GPIOEmulator.EmulatorGUI import app
else:
    print("Loading native GPIO")
    try:
        import RPi.GPIO as GPIO
    except:
        print("Error trying to import RPi.GPIO")


def loadConfig():
    config_file_handler = open("config.yml", "r")
    config_content = config_file_handler.read()
    config_file_handler.close()
    config = yaml.load(config_content, Loader=Loader)

    return config


def blinkLED(PIN):
    global leds

    for step in range(0, 5):
        GPIO.output(leds[PIN], GPIO.HIGH)
        sleep(BLINK_DELAY / 1000.0)
        GPIO.output(leds[PIN], GPIO.LOW)
        sleep(BLINK_DELAY / 1000.0)


def getButtonState(PIN):
    return GPIO.input(PIN)


def latchButtonState(PIN):
    sleep(0.05)
    return getButtonState(PIN)


def getDevicePowerState():
    global config
    r = requests.get(
        config["tacos"]["server"]["api"]
        + "/api/devices/state/"
        + config["tacos"]["server"]["device_id"]
    )

    return json.loads(r.text)["state"]["powered"]


def setToolOn():
    global leds, outputs

    clearToolError()

    GPIO.output(leds["status"], GPIO.HIGH)

    for output in outputs.items():
        GPIO.output(output[1], GPIO.HIGH)

    print("NOTICE: Tool enabled")


def setToolOff():
    global leds, outputs, tool_armed

    for output in outputs.items():
        GPIO.output(output[1], GPIO.LOW)

    tool_armed = 0

    GPIO.output(leds["error"], GPIO.LOW)
    GPIO.output(leds["status"], GPIO.LOW)

    print("NOTICE: Tool disabled")


def setToolError():
    global block_retry

    blinkLED("error")
    block_retry = 1
    print("NOTICE: Error set")
    GPIO.output(leds["error"], GPIO.HIGH)


def clearToolError():
    global block_retry

    GPIO.output(leds["error"], GPIO.LOW)
    blinkLED("status")
    block_retry = 0
    print("NOTICE: Error cleared")


config = loadConfig()

inputs = {}
leds = {}
outputs = {}

tool_armed = 0
block_retry = 1

print("Setting up...")
try:
    GPIO.setmode(GPIO.BCM)

    GPIO.setwarnings(False)

    ## inputs
    for input in config["tacos"]["input"].items():
        inputs[input[0]] = input[1]["pin"]
        GPIO.setup(input[1]["pin"], GPIO.IN)

    ## LEDs
    for led in config["tacos"]["leds"].items():
        leds[led[0]] = led[1]["pin"]
        GPIO.setup(led[1]["pin"], GPIO.OUT, initial=GPIO.LOW)

    ## Outputs
    for output in config["tacos"]["outputs"].items():
        outputs[output[0]] = output[1]["pin"]
        GPIO.setup(output[1]["pin"], GPIO.OUT, initial=GPIO.LOW)

    print("ONLINE")

    while True:
        button_status = getButtonState(inputs["arm"])

        if button_status == True and tool_armed == 0 and block_retry == 0:
            if latchButtonState(inputs["arm"]) == True:
                tool_armed = getDevicePowerState()

                if tool_armed == 1:
                    setToolOn()
                else:
                    setToolError()

        if button_status == False and tool_armed == 1:
            if latchButtonState(inputs["arm"]) == False:
                setToolOff()

        if button_status == False and tool_armed == 0 and block_retry == 1:
            if latchButtonState(inputs["arm"]) == False:
                clearToolError()

        if button_status == True and tool_armed == 0 and block_retry == 1:
            if latchButtonState(inputs["arm"]) == True:
                setToolError()


except Exception as ex:
    traceback.print_exc()
finally:
    GPIO.cleanup()  # this ensures a clean exit

