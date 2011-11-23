#!/bin/bash

. serial.sh

echo -ne "DE=0\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "E\r" > $SERIAL_DEVICE
