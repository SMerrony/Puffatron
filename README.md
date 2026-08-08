# The Puffatron
<img src="logo.jpg" alt= "Puffatron Logo" width = "200" align="right">

The Puffatron is a mostly 3D printed USB MIDI-controlled pipe organ rank.

It can be used as a standalone USB-MIDI player, connected to MIDI keyboards to create a hybrid electronic/physical pipe organ, or added to an existing instrument as an extension.

## Features
* Easy to configure
* Active pipe display - a bit like a VU meter
* Relatively low-cost
* All the 3D printed parts are printable on a reasonably common domestic 3D printer eg. an Ender-3 KE
* All the off-the-shelf parts are easily obtainable
* Use either off-the-shelf breadboards, or a custom PCB

## Configuration
The configuration is stored in the `settings.toml` file.  All of the following settings are required...

* __MIDI_CHANNEL__ - which MIDI channel should this Puffatron play
* __LOWEST_NOTE__ - MIDI note number of lowest note playable on this Puffatron
* __HIGHEST_NOTE__ - MIDI note number of highest note playable on this Puffatron
* __DEBUG__ - set to `false` for production, `true` for development - controls debug messages, slows responsiveness of Puffatron

Do not change the settings below unless you are developing Puffatron
* DISP_ADDR 
* DISP_HEIGHT 
* DISP_WIDTH 
* DISP_BORDER 
* VERSION 

## Off-the-shelf Parts
* 5V mini-solenoids (one per pipe)
* WaveShare RP2040-Zero (or close equivalent)
* MCP23017 GPIO expander (one for each 16 pipes)
* ULN2803A Darlington array (two for each 16 pipes)
* SSD1306 OLED display
* Blower...
* PSU...
* Breadboards/PCB

## 3D Printed Parts
* Windchest
* Blower box
* Pipe feet (whistles)
* Tuning slides (or corks?)
  
## Miscellaneous Parts
* Neoprene sheet
* Medium-sized metal-cored paperclips (one per pipe)
* Hook-up wire for breadboard and solenoids

