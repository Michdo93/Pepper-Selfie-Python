#!/bin/bash
sudo apt update

# Installiere die Schriftart "Arial Narrow"
sudo apt install -y ttf-mscorefonts-installer

# Installiere fontconfig zur Verwaltung von Schriftarten
sudo apt install -y fontconfig

# Aktualisiere den Schriftart-Cache
sudo fc-cache -f -v

# Überprüfe, ob die Schriftart erfolgreich installiert wurde
fc-match "Arial Narrow"
