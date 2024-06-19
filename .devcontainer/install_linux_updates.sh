#!/usr/bin/env bash

# install base linux dependecies
 apt-get update && apt-get install -y --no-install-recommends \
    python3-launchpadlib \
    nano \
    curl \
    wget \
    gdebi \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*