#!/bin/sh
mkdir /etc/mksite
install -b -c -o root -g wheel -m 0755 mksite.py           /usr/bin/mksite
install -b -c -o root -g wheel -m 0755 mksite.conf.example /etc/mksite/mksite.conf
cp -R templates /etc/mksite
chmod -R 755 /etc/mksite