# Puffatron

## Concept
A rank of 3D printed organ pipes, on a 3D printed wind-chest controlled via standard USB MIDI.
With 16 available MIDI channels, we could theoretically have 16 ranks/Puffatrons!

The goal is that all the 3D printed parts should be printable on a reasonably common domestic 3D printer eg. an Ender-3 KE.

## Microcontrollers

The inexpensive WaveShare RP2020-PiZero has been chosen for the project.  Many similar "pico zero" type controllers should work equally well.

Each RP2040-Zero can handle...

* 20 GPIOs using the pins only - not the pads
* 48 GPIOs using 3 x MCP23017 16-way I2C GPIO expanders
* 66 GPIOs using 3 expanders and 18 pins
* 146 GPIOs using 8 expanders and 18 pins

To handle the desired 49 notes per rank, best to use 3 expanders and one built-in GPIO.

Using two I2C devices, one device could therefore handle 2 ranks, but it's probably not worth it.

The 3D-printed windchest seems to max out at 33 pipes (on a 210x210mm print bed).  Maybe we could add a smaller extension to provide the full 49 pipes, i.e. an extra 16 pipes.

## Software/Firmware

As the required functionality is quite simple I have chosen to use CircuitPython which provides all the libraries needed (eg. USB MIDI, MCP23017).

## Configuration
See the README.md
  
## Wiring Conventions
By establishing the following conventions we eliminate the need for complex configuration files...
* It is assumed that all notes between HIGHEST_NOTE and LOWEST_NOTE exist.
* The LOWEST_NOTE should play the first GPIO pin on the first I2C expander.
* The notes then play sequentially on that expander.
* If there are more than 16 notes playable, the 17th plays the first GPIO pin of the second I2C expander.
* If there are more than 32 notes playable, the 33rd plays the first GPIO pin of the third I2C expander.

