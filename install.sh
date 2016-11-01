#!/bin/bash
if [ ! -d "env" ]; then
    virtualenv -p python3 env
fi

source ./env/bin/activate
pip install -r requirements.txt

# Load all the environment variables
source ./aws-account.private.sh
source ./facebook-access-token.private.sh
source ./mashape-key.private.sh

