#!/usr/bin/bash

function send {
  echo -ne "$*\r" > /dev/cu.usbserial-FTC8534M
}

send A=1000000
send VM=70000

while true; do
  send MR 10000
  sleep 0.1
done
