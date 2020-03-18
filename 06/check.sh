#!/bin/bash
set -e
asmfiles=`find . -name *.asm`
for f in $asmfiles; do
  ref=`echo $f | cut -d . -f2 -`
  echo ".$ref.hack"
  python hackasm.py $f
  diff out.hack .$ref.hack
done