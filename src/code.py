# SPDX-FileCopyrightText: 2026 Stephen Merrony
# SPDX-License-Identifier: MIT

from   adafruit_display_shapes.rect import Rect
from   adafruit_display_text import label
from   adafruit_displayio_ssd1306 import SSD1306
from   adafruit_midi import MIDI
from   adafruit_midi.note_on import NoteOn
from   adafruit_midi.note_off import NoteOff
from   adafruit_midi.control_change import ControlChange
import array
import board
from   busio import I2C
from   digitalio import DigitalInOut, Direction
import displayio
import gc
from   i2cdisplaybus import I2CDisplayBus
import neopixel
import pwmio
import supervisor
from   terminalio import FONT
import time
from   usb_midi import ports

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
PWM_FREQ     = supervisor.get_setting("PWM_FREQ")
ATTACK_PWM_DUTY_CYCLE = supervisor.get_setting("ATTACK_PWM_DUTY_CYCLE")
ATTACK_DURATION_MS    = supervisor.get_setting("ATTACK_DURATION_MS")
HOLD_PWM_DUTY_CYCLE   = supervisor.get_setting("HOLD_PWM_DUTY_CYCLE")

# Derive some values
NUM_NOTES = (HIGHEST_NOTE - LOWEST_NOTE) + 1
VU_COL_WIDTH = (DISP_WIDTH - (2 * DISP_BORDER)) // NUM_NOTES
VU_COL_HEIGHT = DISP_HEIGHT - (2 * DISP_BORDER)

# Other constants
MCP23017_SCK = board.GP29 # pyright: ignore[reportAttributeAccessIssue]
MCP23017_SDA = board.GP28 # pyright: ignore[reportAttributeAccessIssue]
SSD1306_SCK  = board.GP27
SSD1306_SDA  = board.GP26

# BASE_MCP23017_I2C_ADDRESS = 0x20
# NUM_MCP23017s = (NUM_NOTES // 16) + 1

UNPLAYABLE = -1

RED = (0, 255, 0)
GREEN = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Globals...
pipe_pins: list[DigitalInOut] = []
pipe_pwms: list[pwmio.PWMOut] = []
bar_dict = {}
note_start_ticks = array.array("i", ())

# if DEBUG: print("Number of MCP23017s: ", NUM_MCP23017s)

# Functions

# We always setup the first 8 GPIOs as PWM outputs
def setup_onboard_pwm() -> None:
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP0, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP1, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP2, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP3, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP4, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP5, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP6, duty_cycle=0, frequency=PWM_FREQ))
    pipe_pwms.append(pwmio.PWMOut(pin=board.GP7, duty_cycle=0, frequency=PWM_FREQ))

def init_note_start_times() -> None:
    for t in range(LOWEST_NOTE, HIGHEST_NOTE + 1):
        note_start_ticks.append(-1)

_TICKS_PERIOD = 1<<29
_TICKS_MAX = _TICKS_PERIOD-1
_TICKS_HALFPERIOD =_TICKS_PERIOD//2

def ticks_diff(ticks1, ticks2):
    "Compute the signed difference between two ticks values, assuming that they are within 2**28 ticks"
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff

def setup_pipe_display() -> None:
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
    i2c = I2C(SSD1306_SCK, SSD1306_SDA)
    display_bus = I2CDisplayBus(i2c, device_address=DISP_ADDR)
    display = SSD1306(display_bus, width=DISP_WIDTH, height=DISP_HEIGHT)
    # Make the display context
    screen = displayio.Group()
    display.root_group = screen
    return screen

def setup_neopixel() -> neopixel.NeoPixel:
    led = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
    return led

def setup_midi(channel : int) -> MIDI:
    midi = MIDI(
        midi_in = ports[0], # type: ignore
        midi_out = None,
        in_channel = channel
        )
    return midi

def splash(scr : displayio.Group) -> None:
    app_label = label.Label(
        FONT,
        x=10, y = 12,
        text="Puffatron",
        color=0,
        scale=2,
        padding_left=1, padding_top=0,
        background_color=0xffffff
    )
    scr.append(app_label)
    version_label = label.Label(
        FONT,
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

def start_note(note_num : int) -> None:
    note_ix = note_num - LOWEST_NOTE
    if DEBUG: print("Pin index: ", note_ix)
    note_start_ticks[note_ix] = supervisor.ticks_ms()
    pipe_pwms[note_ix].duty_cycle = ATTACK_PWM_DUTY_CYCLE

def stop_note(note_num :int) -> None:
    note_ix = note_num - LOWEST_NOTE
    if DEBUG: print("Pin index: ", note_ix)
    note_start_ticks[note_ix] = -1
    pipe_pwms[note_ix].duty_cycle = 0

def stop_all_notes() -> None:
    n = LOWEST_NOTE
    while n <= HIGHEST_NOTE: 
        stop_note(n)
        n += 1

# **** Main code starts here **** #

screen = setup_ssd1306_display()
if DEBUG: print("Free memory: ", gc.mem_free())
splash(screen)
setup_pipe_display()

midi = setup_midi(MIDI_CHANNEL)
led  = setup_neopixel()
setup_onboard_pwm()
init_note_start_times()

if DEBUG: print("Free memory: ", gc.mem_free())
print("Puffatron ready...") 

while True:
    msg = midi.receive() # <--- This does not block
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
        if DEBUG: print("Free memory: ", gc.mem_free())
    elif isinstance(msg, ControlChange):
        if msg.control >= 120 and msg.control <= 123:
            if DEBUG: print("All notes off/panic")
            stop_all_notes()
    # check if any notes need to move from attack to hold phase...
    now = supervisor.ticks_ms()
    for t_ix in range(0, len(note_start_ticks)):
        if note_start_ticks[t_ix] != -1:
            if ticks_diff(now, note_start_ticks[t_ix]) > ATTACK_DURATION_MS:
                if pipe_pwms[t_ix].duty_cycle == ATTACK_PWM_DUTY_CYCLE:
                    pipe_pwms[t_ix].duty_cycle = HOLD_PWM_DUTY_CYCLE
                    if DEBUG: print("Moved pipe to HOLD phase: ", t_ix)