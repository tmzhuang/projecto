#!/bin/bash

echo "Running server side tests..."
python -m unittest discover
if [ $? -ne 0 ]; then
  exit 1;
fi

echo "Running client side tests..."
karma start scripts/travis/travis.karma.config.js
if [ $? -ne 0 ]; then
  exit 1;
fi

echo "\o/ Everything works!"
