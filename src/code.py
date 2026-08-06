# SPDX-FileCopyrightText: 2026 Stephen Merrony
# SPDX-License-Identifier: MIT

from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import board
import busio
import displayio
import neopixel
import supervisor
import terminalio
import time
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from i2cdisplaybus import I2CDisplayBus

# Grab some settings 
VERSION      = supervisor.get_setting("VERSION")
DEBUG        = supervisor.get_setting("DEBUG")
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

# build a dict of all possible bars for the "VU meter"
bar_dict = {}
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

displayio.release_displays()
i2c = busio.I2C(board.GP3, board.GP2)
display_bus = I2CDisplayBus(i2c, device_address=DISP_ADDR)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=DISP_WIDTH, height=DISP_HEIGHT)
# Make the display context
screen = displayio.Group()
display.root_group = screen

def splash(scr):
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

led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
red = (0, 255, 0)
green = (255, 0, 0)
blue = (0, 0, 255)
black = (0, 0, 0)

UNPLAYABLE = 0

def playable(note_num):
    if note_num < LOWEST_NOTE or note_num > HIGHEST_NOTE:
        return False
    else:
        return True

# translate a MIDI note number into a GPIO address.
# This conforms to the wiring conventions described in DevNotes.md
def note_to_gpio(note_num):
    i2c_addr = 0 
    pin = 0
    if note_num < LOWEST_NOTE or note_num > HIGHEST_NOTE:
        pin = UNPLAYABLE
    elif note_num < LOWEST_NOTE + 16:
        i2c_addr = 0x20     # 1st i2c expander
        pin = note_num - LOWEST_NOTE
    elif note_num < LOWEST_NOTE + 32:
        i2c_addr = 0x21     # 2nd expander
        pin = note_num - LOWEST_NOTE - 16
    else:
        i2c_addr = 0x22     # 3rd expander
        pin = note_num - 32
    # TODO handle valid notes beyond third I2C expander
    if DEBUG: print("note_to_gpio returning: ", i2c_addr, pin)
    return i2c_addr, note_num

def start_note(note_num):
    i2c_addr, pin = note_to_gpio(note_num)

def stop_note(note_num):
    i2c_addr, pin = note_to_gpio(note_num)

def stop_all_notes():
    n = LOWEST_NOTE
    while n <= HIGHEST_NOTE:
        stop_note(n)
        n += 1

splash(screen)

midi = adafruit_midi.MIDI(
        midi_in=usb_midi.ports[0],
        in_channel = supervisor.get_setting("MIDI_CHANNEL")
        )

print("Puffatron ready...")

while True:
    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:
        if DEBUG: print("Note On:  ", msg.note, " velocity: ", msg.velocity)
        if playable(msg.note):
            start_note(msg.note) 
            screen.append(bar_dict[msg.note])
            if DEBUG: led.fill(green) # Order: GRB
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
            if DEBUG:led.fill(black)
    elif isinstance(msg, ControlChange):
        if msg.control >= 120 and msg.control <= 123:
            if DEBUG: print("All notes off/panic")
            stop_all_notes()
