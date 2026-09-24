#!/bin/bash

# Comando da eseguire ogni ora
/home/rmadaudo/.virtualenvs/preactivate
cd /home/rmadaudo/ryanair_price_agen

while true; do
    python -m scripts.run_collect
    sleep 100
done
