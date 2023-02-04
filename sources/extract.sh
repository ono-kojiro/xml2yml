#!/bin/sh

. ../config.bashrc

archives=$(find ../archives/ -name "${project}*.tar.gz")

for archive in $archives; do
  basename=$(basename $archive .tar.gz)
  if [ ! -e $basename ]; then
    echo "extract $archive ..."
    tar xf $archive
    mv ${project} $basename
  else
    echo "skip extracting $archive"
  fi
done

