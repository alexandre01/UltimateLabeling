#!/usr/bin/env bash

input_path=$1
file_name=${input_path%%.*}

mkdir $file_name
ffmpeg -i $input_path -qscale:v 2 -start_number 0 $file_name/%05d.jpg
