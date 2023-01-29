#!/usr/bin/env sh

top_dir="$(cd "$(dirname "$0")" > /dev/null 2>&1 && pwd)"
cd $top_dir

. ./config.bashrc

read_xml="${top_dir}/read_xml.py"
source_dir="${top_dir}/sources"

db()
{
	mkdir -p db
	cd db
	find ${source_dir}/${project}-${tar_ver}/sample/ -name "*.arxml" -print -exec python3 ${read_xml} -o v${tar_ver}.log -d v${tar_ver}.db {} \;
	find ${source_dir}/${project}-${ref_ver}/sample/ -name "*.arxml" -print -exec python3 ${read_xml} -o v${ref_ver}.log -d v${ref_ver}.db {} \;
	sqlite3 v${ref_ver}.db ".dump" > v${ref_ver}.sql
	sqlite3 v${tar_ver}.db ".dump" > v${tar_ver}.sql
	cd ${top_dir}
}

compare()
{
	python3 compare.py -o output.txt db/v${tar_ver}.db db/v${ref_ver}.db
}

yaml()
{
  python3 xml2yml.py -o output.yml sources/${project}-${ref_ver}/sample/sample1.${ext}
}

clean()
{
  rm -f database.db
  rm -f database.sql
  rm -f input.xml
  rm -f output.txt
  rm -f output.yml
  rm -f output.yml.ref
  rm -f sample1-ref.yml
}

all()
{
  db
  compare
  yaml
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

