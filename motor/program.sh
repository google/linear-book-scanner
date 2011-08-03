#!/bin/bash

SERIAL_DEVICE=/dev/cu.usbserial-FTC8534M

echo -ne "E\r" > $SERIAL_DEVICE
sleep 1
echo -ne "CP\r" > $SERIAL_DEVICE
sleep 1
cat scan.mxt > $SERIAL_DEVICE
