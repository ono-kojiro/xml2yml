#!/usr/bin/env sh

top_dir="$(cd "$(dirname "$0")" > /dev/null 2>&1 && pwd)"
cd $top_dir

. ./config.bashrc

source_dir="${top_dir}/sources"

help()
{
  echo "usage : $0 [target]"
  cat - << EOS

target :
  extract         extract source from archives
  yaml            extract data from xml and save yaml
  db              create database from yaml

  clean           remove generated files
EOS
}

extract()
{
  cd ${source_dir}
  sh extract.sh
  cd ${top_dir}
}

compare()
{
  python3 compare.py -o output.txt db/v${tar_ver}.db db/v${ref_ver}.db
}

yaml()
{
  echo "INFO : yaml"
  cmd="python3 xml2yml.py -o ref.yml"
  cmd="$cmd --long-definition-ref"
  cmd="$cmd sources/${project}-${ref_ver}/sample/sample1.${ext}"

  echo $cmd
  $cmd
}

db()
{
  echo "INFO : db"
  cmd="python3 yml2db.py -o ref.db ref.yml"
  echo $cmd
  $cmd

  sqlite3 ref.db ".dump" > ref.sql
}


clean()
{
  rm -f ref.db ref.yml ref.log ref.sql
}

all()
{
  extract
  yaml
  db
}

args=""
while [ $# -ne 0 ]; do
  case $1 in
    -h )
      usage
      exit 1
      ;;
    -v )
      verbose=1
      ;;
    * )
      args="$args $1"
      ;;
  esac
  
  shift
done

if [ -z "$args" ]; then
  all
fi

for arg in $args; do
  num=`LANG=C type $arg | grep 'function' | wc -l`

  if [ $num -ne 0 ]; then
    $arg
  else
    echo "ERROR : $arg is not shell function in this script"
    exit 1
  fi
done

