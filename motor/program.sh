#!/bin/bash

. serial.sh

echo -ne "PS\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "E\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "CP\r" > $SERIAL_DEVICE
sleep 0.5
cat scan.mxt > $SERIAL_DEVICE
