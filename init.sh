#!/bin/bash

# download E. Focht's UDMA library for Aurora
echo "Cloning VE UDMA library..."
mkdir -p .runtime/udma
git clone https://github.com/SX-Aurora/veo-udma.git .runtime/udma
/bin/bash -c "cd .runtime/udma && git checkout 84dd019"

# build UDMA library
echo "Bulding VE UDMA library..."
/bin/bash -c "cd .runtime/udma && make"

# download pycparser
echo "Cloning pycparser..."
mkdir -p .runtime/parser
git clone https://github.com/eliben/pycparser.git .runtime/parser
/bin/bash -c "cd .runtime/parser && git checkout 1166ea1"

echo "Applying custom changes to pycparser..."
patch -f -p1 < .runtime/patches/pycparser.patch

# adding a blind python package file
touch .runtime/parser/__init__.py
