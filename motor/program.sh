#!/bin/bash

if [ `uname` = "Linux" ]; then
  SERIAL_DEVICE=/dev/ttyUSB0
  stty -F $SERIAL_DEVICE 9600
else
  SERIAL_DEVICE=/dev/cu.usbserial-FTC8534M
fi

echo -ne "PS\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "E\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "CP\r" > $SERIAL_DEVICE
sleep 0.5
cat sensors.mxt > $SERIAL_DEVICE
