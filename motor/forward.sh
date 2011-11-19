#!/bin/bash

if [ `uname` = "Linux" ]; then
  SERIAL_DEVICE=/dev/ttyUSB0
  stty -F $SERIAL_DEVICE 9600
else
  SERIAL_DEVICE=/dev/cu.usbserial-FTC8534M
fi

function send {
  echo -ne "$*\r" > $SERIAL_DEVICE
}

send A=1000000
send VM=70000
send E  # end any running program
send DE=1  # enable drive

while true; do
  send MR 10000
  sleep 0.1
done
