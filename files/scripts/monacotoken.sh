#!/bin/bash

VAR_NAME="dttoken"
VAR_VALUE="TOKEN_TOREPLACE"

# Append only if not already present
if ! grep -q "^${VAR_NAME}=" /etc/environment; then
    echo "${VAR_NAME}=\"${VAR_VALUE}\"" | sudo tee -a /etc/environment
fi