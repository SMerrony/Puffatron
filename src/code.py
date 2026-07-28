# SPDX-FileCopyrightText: 2026 Stephen Merrony
# SPDX-License-Identifier: MIT

import board
import neopixel
import supervisor
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# Grab some settings 
DEBUG = supervisor.get_setting("DEBUG")
LOWEST_NOTE = supervisor.get_setting("LOWEST_NOTE")
HIGHEST_NOTE = supervisor.get_setting("HIGHEST_NOTE")

led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
red = (0, 255, 0)
green = (255, 0, 0)
blue = (0, 0, 255)
black = (0, 0, 0)

unplayable = 99

# translate a MIDI note number into a GPIO address.
# This conforms to the wiring conventions described in DevNotes.md
def note_to_gpio(note_num):
    i2c_addr = 0 
    pin = 0
    if note_num < LOWEST_NOTE or note_num > HIGHEST_NOTE:
        pin = unplayable
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

midi = adafruit_midi.MIDI(
        midi_in=usb_midi.ports[0],
        in_channel = supervisor.get_setting("MIDI_CHANNEL")
        )

print("Puffatron ready...")

while True:
    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:
        if DEBUG: print("Note On:  ", msg.note, " velocity: ", msg.velocity)
        start_note(msg.note)
        led.fill(green) # Order: GRB
    elif isinstance(msg, NoteOff) or (isinstance(msg, NoteOn) and msg.velocity == 0):
        if DEBUG: print("Note Off: ", msg.note)
        stop_note(msg.note)
        led.fill(black)
    elif isinstance(msg, ControlChange):
        if msg.control >= 120 and msg.control <= 123:
            if DEBUG: print("All notes off/panic")
            stop_all_notes()
