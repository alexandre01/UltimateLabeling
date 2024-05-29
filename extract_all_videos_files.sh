#!/usr/bin/env bash

for filename in data/*.MOV; do
	input_path=$filename
	output_path1=${input_path%.*}
	echo "$output_path1"
	mkdir $output_path1
	ffmpeg -i $input_path -vf "select=not(mod(n\,5))" -vsync vfr -qscale:v 2 -start_number 0 "$output_path1"/%05d.jpg
done
