#!/bin/bash
if [ ! -d "env" ]; then
    virtualenv -p python3 env
fi

source ./env/bin/activate
pip install -r requirements.txt

source ./aws-account.private.sh

