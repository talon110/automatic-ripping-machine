#!/usr/bin/env bash

# This script is inspired by the script posted on the forums.
# Given that it hasn't been taken down I'm going to assume they
# don't have a problem with users programmatically scraping the
# beta key.
# Link: https://forum.makemkv.com/forum/viewtopic.php?p=119221#p119221

# Define variables
makemkv_serial_url="https://forum.makemkv.com/forum/viewtopic.php?f=5&t=1053"
MAKEMKV_KEY=
MAKEMKV_DIR="/root/.MakeMKV"
SETTINGS_FILE="$MAKEMKV_DIR/settings.conf"

# save MAKEMKV_KEY passed as argument, or scrape this month's beta key
if [ -n "$1" ]; then
    echo "MAKEMKV_KEY passed as argument"
    MAKEMKV_KEY=$1
else
    MAKEMKV_KEY=$(curl -fsSL "$makemkv_serial_url" | grep -oP 'T-[\w\d@]{66}')
    echo "MakeMKV beta key for this month: $MAKEMKV_KEY"
fi

# create .MakeMKV dir if it doesn't already exist
if [ ! -d "$MAKEMKV_DIR" ]; then
    mkdir -p "$MAKEMKV_DIR"
fi

# if file doesn't exist OR grep doesn't find app_Key entry in settings
if [[ ! -f "$SETTINGS_FILE" ]] || ! grep -q "app_Key" "$SETTINGS_FILE"; then
    echo "Either $SETTINGS_FILE doesn't exist, or app_Key is not inside it"
    echo "Appending app_Key: $MAKEMKV_KEY to settings file."
    echo "app_Key = \"$MAKEMKV_KEY\"" >> "$SETTINGS_FILE"
fi

CURRENT_KEY=$(grep -oh \"T-.*\" $SETTINGS_FILE)
if [[ CURRENT_KEY != MAKEMKV_KEY ]]; then
    echo "$SETTINGS_FILE exists and app_Key is currently: $CURRENT_KEY. Updating app_Key value."
    echo "Replacing beta key in settings file: $CURRENT_KEY with: $MAKEMKV_KEY"
    # avoid using sed -i to avoid filesystem issues when running inside a container
    sed "s|app_Key = \"T-.*\"|app_Key = \"$MAKEMKV_KEY\"|" "$SETTINGS_FILE" > /tmp/settings.conf && cat /tmp/settings.conf > $SETTINGS_FILE
else
    echo "app_Key already set. Ending script."
fi
