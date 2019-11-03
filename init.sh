#!/bin/bash

# download E. Focht's UDMA library for Aurora
mkdir runtime/udma
git clone https://github.com/SX-Aurora/veo-udma.git runtime/udma

# build UDMA library
/bin/bash -c "cd runtime/udma && make"