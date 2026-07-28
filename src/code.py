# SPDX-FileCopyrightText: 2026 Stephen Merrony
# SPDX-License-Identifier: MIT


import time
import board
import neopixel
import supervisor
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
red = (0, 255, 0)
green = (255, 0, 0)
blue = (0, 0, 255)
black = (0, 0, 0)

midi = adafruit_midi.MIDI(
        midi_in=usb_midi.ports[0],
        in_channel = supervisor.get_setting("MIDI_CHANNEL")
        )


print("MidiOrgan ready...")

while True:
    msg = midi.receive()
    if isinstance(msg, NoteOn) and msg.velocity != 0:
        print("Note On:  ", msg.note, " velocity: ", msg.velocity)
        led.fill(green) # Order: GRB
    elif isinstance(msg, NoteOff) or (isinstance(msg, NoteOn) and msg.velocity == 0):
        print("Note Off: ", msg.note)
        led.fill(black)
    # not handling and CCs or other MIDI types at the moment
