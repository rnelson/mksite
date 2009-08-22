#!/bin/sh

install -b -c -o root -g wheel -m 0755 mksite.py   /usr/bin/mksite
install -b -c -o root -g wheel -m 0755 mksite.conf /etc/mksite.conf