#!/bin/bash

source env.properties

# Environment variables
database=$1
database_dir="mnt/dumps/"

# Remote variables
remote_host="danae.zappos.net/dumps/"
remote_extension="_data.sql"
remote_packed_ext=".tgz"

schema_file="database_create.sql"

function init_check {
  # Check to see if a database has been passed in
  if [ -z $database ]; then
    echo "* Hey stupid, specific a database in the first parameter"
    exit
  fi

  # Create tmp in home directory
  echo "* Creating tmp in home directory"
  if [ ! -d $local_filepath ]; then
    mkdir $local_filepath
  fi
}

function fetch_dump {
  echo "* Fetching SQL Schema"
  local remote_schema=$database$schema_file
  curl -0 $remote_schema

  echo "* Fetching SQL Data"
  local file=$database$remote_extension$remote_packed_ext
  curl http://$remote_host$file > $local_filepath$file

  echo "* Extracting SQL Dump (this will take a while)"
  tar -zxf $local_filepath$file
}

function mysql_setup {
  local file=$database_dir$database$remote_extension
  local local_schema_file=$local_filepath$schema_file

  echo "file: $local_filepath$file"
  echo "schema_file: $local_schema_file"

  # Log into mysql and source that sucker
  echo "* Preparing mysql to source the SQL Dump"
  $mysql_path --max_allowed_packet=100M -u$db_user -p$db_password << eof
set global max_allowed_packet=1000000000;
set global net_buffer_length=1000000;
drop database if exists $database;
source $local_schema_file;
use $database;
source $local_filepath$file;
eof

  echo "* We all good?"
}

function main {
  init_check
  #fetch_dump
  mysql_setup
}

main
