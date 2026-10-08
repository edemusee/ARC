#!/bin/sh
# Rebuild every Hindu work from the source clones (see common.py for the HINDUISM_SOURCES path).
set -e
cd "$(dirname "$0")"
for s in convert_gita convert_rigveda convert_upanishads convert_ramayana convert_ramcharitmanas convert_yoga_sutras convert_devotional; do
  python3 -I "$s.py"
done
cd ../..
node build.js --validate-work=bhagavad-gita,rig-veda,isha,kena,katha,prashna,mundaka,mandukya,aitareya,ramayana,ramcharitmanas,yoga-sutras,hanuman-chalisa,vishnu-sahasranama
