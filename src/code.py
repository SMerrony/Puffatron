# SPDX-FileCopyrightText: 2026 Stephen Merrony
# SPDX-License-Identifier: MIT

from   adafruit_display_shapes.rect import Rect
from   adafruit_display_text import label
import adafruit_displayio_ssd1306
from   adafruit_mcp230xx.mcp23017 import MCP23017
import adafruit_midi
from   adafruit_midi.note_on import NoteOn
from   adafruit_midi.note_off import NoteOff
from   adafruit_midi.control_change import ControlChange
import board
import busio
from   digitalio import DigitalInOut, Direction
import displayio
from   i2cdisplaybus import I2CDisplayBus
import neopixel
import supervisor
import terminalio
import time
import usb_midi

# Grab some settings 
VERSION      = supervisor.get_setting("VERSION")
DEBUG        = supervisor.get_setting("DEBUG")
MIDI_CHANNEL = supervisor.get_setting("MIDI_CHANNEL")
LOWEST_NOTE  = supervisor.get_setting("LOWEST_NOTE")
HIGHEST_NOTE = supervisor.get_setting("HIGHEST_NOTE")
DISP_ADDR    = supervisor.get_setting("DISP_ADDR")
DISP_HEIGHT  = supervisor.get_setting("DISP_HEIGHT")
DISP_WIDTH   = supervisor.get_setting("DISP_WIDTH")
DISP_BORDER  = supervisor.get_setting("DISP_BORDER")

# Derive some values
NUM_NOTES = (HIGHEST_NOTE - LOWEST_NOTE) + 1
VU_COL_WIDTH = (DISP_WIDTH - (2 * DISP_BORDER)) // NUM_NOTES
VU_COL_HEIGHT = DISP_HEIGHT - (2 * DISP_BORDER)

# Other constants
BASE_MCP23017_I2C_ADDRESS = 0x20
NUM_MCP23017s = (NUM_NOTES // 16) + 1

UNPLAYABLE = -1

RED = (0, 255, 0)
GREEN = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Globals...
mcps: list[MCP23017] = []
pipe_pins: list[DigitalInOut] = []
bar_dict = {}

if DEBUG: print("Number of MCP23017s: ", NUM_MCP23017s)

# Functions

def setup_mcp23017s():
    i2c = busio.I2C(board.GP1, board.GP0)
    for mcp in range(1, NUM_MCP23017s + 1):
        if DEBUG: print("Setting up MCP")
        mcps.append(MCP23017(i2c, address = BASE_MCP23017_I2C_ADDRESS + mcp - 1))
        for pin in range(0,16):
            if DEBUG: print("Adding MCP pin")
            pipe_pins.append(mcps[mcp - 1].get_pin(pin)) # type: ignore
    if DEBUG: print("Total pins: ", len(pipe_pins))
    # set all the pins to output - even if we're not using them
    for pin in pipe_pins:
        if DEBUG: print("Setting pin to output")
        pin.direction = Direction.OUTPUT
        pin.value = False

def setup_pipe_display():
    # build a dict of all possible bars for the "VU meter"
    # this stores the images in the bar_dict
    for bar in range(LOWEST_NOTE, HIGHEST_NOTE + 1):
        adjusted_note = bar - LOWEST_NOTE
        x_left = adjusted_note * VU_COL_WIDTH
        if NUM_NOTES < (VU_COL_HEIGHT / 2):
            adjusted_note *= 2
        bar_dict[bar] = Rect(
            x_left, 
            DISP_BORDER + adjusted_note, 
            VU_COL_WIDTH, 
            VU_COL_HEIGHT - adjusted_note, 
            fill=0xffffff)

def setup_ssd1306_display() -> displayio.Group:
    displayio.release_displays()
    i2c = busio.I2C(board.GP3, board.GP2)
    display_bus = I2CDisplayBus(i2c, device_address=DISP_ADDR)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=DISP_WIDTH, height=DISP_HEIGHT)
    # Make the display context
    screen = displayio.Group()
    display.root_group = screen
    return screen

def setup_neopixel() -> neopixel.NeoPixel:
    led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
    return led

def setup_midi(channel : int) -> adafruit_midi.MIDI:
    midi = adafruit_midi.MIDI(
        midi_in = usb_midi.ports[0], # type: ignore
        midi_out = None,
        in_channel = channel
        )
    return midi

def splash(scr : displayio.Group):
    app_label = label.Label(
        terminalio.FONT,
        x=10, y = 12,
        text="Puffatron",
        color=0,
        scale=2,
        padding_left=1, padding_top=0,
        background_color=0xffffff
    )
    scr.append(app_label)
    version_label = label.Label(
        terminalio.FONT,
        x=30, y = 40,
        text=VERSION,
        scale=2,
        padding_left=1, padding_top=0,
    )
    scr.append(version_label)
    time.sleep(2)
    scr.remove(version_label)
    scr.remove(app_label)

def playable(note_num : int) -> bool:
    if note_num < LOWEST_NOTE or note_num > HIGHEST_NOTE:
        return False
    else:
        return True

def start_note(note_num):
    # i2c_addr, pin = note_to_gpio(note_num)
    if DEBUG: print("Pin index: ", note_num - LOWEST_NOTE)
    pipe_pins[note_num - LOWEST_NOTE].value = True

def stop_note(note_num):
    # i2c_addr, pin = note_to_gpio(note_num)
    if DEBUG: print("Pin index: ", note_num - LOWEST_NOTE)
    pipe_pins[note_num - LOWEST_NOTE].value = False

def stop_all_notes():
    n = LOWEST_NOTE
    while n <= HIGHEST_NOTE: 
        stop_note(n)
        n += 1

# **** Main code starts here **** #

screen = setup_ssd1306_display()
splash(screen)
setup_pipe_display()

midi = setup_midi(MIDI_CHANNEL)
led  = setup_neopixel()
mcps = setup_mcp23017s()

print("Puffatron ready...")

while True:
    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:
        if DEBUG: print("Note On:  ", msg.note, " velocity: ", msg.velocity)
        if playable(msg.note):
            start_note(msg.note) 
            # The error handling below is for the rare case when we get two Note Ons for the same note
            try:
                screen.append(bar_dict[msg.note])
            except:
                if DEBUG: print("Error drawing a VU bar which was already there")    
            if DEBUG: led.fill(GREEN) # Order: GRB
    elif isinstance(msg, NoteOff) or (isinstance(msg, NoteOn) and msg.velocity == 0):
        if DEBUG: print("Note Off: ", msg.note)
        if playable(msg.note):
            stop_note(msg.note)
            # The error handling below deals with the rare case where we might get a Note Off without
            # having received a corresponding Note On.
            try:
                screen.remove(bar_dict[msg.note])
            except:
                if DEBUG: print("Error removing VU bar which didn't exist")
            if DEBUG:led.fill(BLACK)
    elif isinstance(msg, ControlChange):
        if msg.control >= 120 and msg.control <= 123:
            if DEBUG: print("All notes off/panic")
            stop_all_notes()
