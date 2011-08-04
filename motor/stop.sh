#!/bin/bash

SERIAL_DEVICE=/dev/cu.usbserial-FTC8534M

echo -ne "DE=0\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "E\r" > $SERIAL_DEVICE
