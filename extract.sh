#!/bin/bash

file="frames.zip"
directory="badapple"

if [ -f "$file" ]; then
    if [ -d "$directory" ]; then
        rm -r "$directory"
    fi
    7z x "$file"
else
    echo "$file nedostaje."
fi
