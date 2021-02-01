#!/bin/bash

file="frames.zip"
directory="badapple"

if [ -f "$file" ]; then
    mv "$file" "$file.bak"
fi

if [ -d "$directory" ]; then
    7z a "$file" "$directory"
else
    echo "direktorij $directory ne postoji"
fi
