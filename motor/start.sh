#!/bin/bash

. serial.sh

echo -ne "DE=1\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "EX SU\r" > $SERIAL_DEVICE
sleep 0.1
echo -ne "RS\r" > $SERIAL_DEVICE
