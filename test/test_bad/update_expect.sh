#!/bin/bash

# run this script after a failing test run to update the expect files

for f in *.diff
do
  fileName=`basename "$f" ".diff"`
  expectFileName="expect/${fileName}.out"
  output="${fileName}.out"

  if [ "$1" != "-f" ]; then
      less $f
      echo "Replace $expectFileName [y]nq: "  | tr -d '\012'
      read -n 1 answer
      echo
  fi

  if [ "${answer}" = "y" -o "${answer}" = "" ]
  then
    mv -f "$output" "$expectFileName"
    rm $f
  elif [ "${answer}" = "q" ]
  then
    exit 0
  fi
done

