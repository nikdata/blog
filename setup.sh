#!/usr/bin/env bash

# Detect CPU architecture
if [[ $(uname -m) == "aarch64" ]] || [[ $(uname -m) == "arm64" ]]; then
    CPU="arm64"
else
    CPU="amd64"
fi

echo "Detected CPU: $CPU"

# Install uv
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Install Quarto
echo "Installing Quarto..."
QUARTO_VERSION="1.7.32"
wget -q -O /tmp/quarto.deb https://github.com/quarto-dev/quarto-cli/releases/download/v$QUARTO_VERSION/quarto-$QUARTO_VERSION-linux-$CPU.deb
sudo dpkg -i /tmp/quarto.deb
rm /tmp/quarto.deb

# Initialize uv project and install core packages
echo "Setting up Python environment..."
uv init
uv add numpy scipy polars matplotlib jupyterlab seaborn wheel

echo "Setup complete!"