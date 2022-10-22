#!/usr/bin/env zsh

cd "$(dirname "$0")"
path=('/opt/homebrew/bin' $path)
export PATH

pip3 install -r ./requirements.txt
python3 -u ./main.py
