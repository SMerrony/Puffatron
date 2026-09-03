# Puffatron

## Concept
A rank of 3D printed organ pipes, on a 3D printed wind-chest controlled via standard USB MIDI.
With 16 available MIDI channels, we could theoretically have 16 ranks/Puffatrons!

The goal is that all the 3D printed parts should be printable on a reasonably common domestic 3D printer eg. an Ender-3 KE.

## Microcontroller
The inexpensive WaveShare RP2020-PiZero has been chosen for the project.  Many similar "pico zero" type controllers should work equally well.

Each RP2040-Zero could potentially handle...

* 20 GPIOs using the pins only - not the pads*
* 48 GPIOs using 3 x MCP23017 16-way I2C GPIO expanders
* 66 GPIOs using 3 expanders and 18 pins
* 146 GPIOs using 8 expanders and 18 pins
* (290 GPIOs using 16 expanders (2 I2C channels) and 16 pins!)

\* But not on a standard breadboard - you can only use the 'side' pins, not the bottom ones.  The same applies to all the figures - subtract 5 local GPIOs from each count if using an off-the-shelf breadboard rather than the PCB

To handle the desired 49 - 56 notes per rank, best to use 3 expanders and some built-in GPIOs.

The 3D-printed windchest seems to max out at 33 pipes (on a 210x210mm print bed).  Maybe we could add a smaller extension to provide the full 49 - 56 pipes, i.e. an extra 16 - 23 pipes.

## Software/Firmware
As the required functionality is quite simple I have chosen to use CircuitPython which provides all the libraries needed (eg. USB MIDI, MCP23017).

## Configuration
See the README.md
  
## Wiring Conventions
By establishing the following conventions we eliminate the need for complex configuration files...

### Pipe Wiring (solenoids)
* It is assumed that all notes between HIGHEST_NOTE and LOWEST_NOTE exist.
* The LOWEST_NOTE should play via the first GPIO (GPA0) pin on the first I2C expander.
* The notes then play sequentially on that expander.
* If there are more than 16 notes playable, the 17th plays via the first GPIO pin of the second I2C expander.
* If there are more than 32 notes playable, the 33rd plays via the first GPIO pin of the third I2C expander.
* If there are more than 48 notes playable, the 47th plays via GPIO 0 on the microcontroller

### I2C Wiring
We use two I2C channels, one for the MCP23017 expanders, and one for the SSD1306 OLED display.
* The expanders connect to GPIO 28 and 29
* The display connects to GPIO 26 and 27
