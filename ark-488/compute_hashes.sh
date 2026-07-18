#!/bin/bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.md" -o -name "*.sh" \) \
  ! -path "./node_modules/*" ! -path "./.git/*" ! -name "MANIFEST.txt" \
  -exec sha256sum {} \; | sort -k 2 > MANIFEST.txt
