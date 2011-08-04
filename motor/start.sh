#!/bin/bash

SERIAL_DEVICE=/dev/cu.usbserial-FTC8534M

echo -ne "DE=1\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "EX SU\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "RS\r" > $SERIAL_DEVICE
