#!/bin/sh

. ../config.bashrc

archives=$(find ../archives/ -name "${project}*.tar.gz")

for archive in $archives; do
  basename=$(basename $archive .tar.gz)
  tar xvf $archive
  mv ${project} $basename
done

