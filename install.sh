#!/bin/bash
# Create the virtualenv if there isn't already one
if [ ! -d "env" ]; then
    virtualenv -p python3 env
fi

# Activate and install dependencies
source ./env/bin/activate
pip install -r requirements.txt

# Load all the environment variables
source ./aws-account.private.sh
source ./facebook-access-token.private.sh
source ./mashape-key.private.sh

