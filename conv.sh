#!/bin/bash

BASE=$(pwd)

convert() {
img=$1
dir=$2
col=$3

magick convert -background none ${img}.svg -fuzz "90%" -fill "${col}" -opaque black $dir/${img}-1.png
magick convert ${dir}/${img}-1.png -fuzz "40%" -background none -transparent white ${dir}/${img}-2.png
magick convert ${dir}/${img}-2.png -resize 40x40 ${dir}/${img}.png
magick convert -channel RGB -resize 160x160 -antialias +contrast +contrast +contrast +contrast ${dir}/${img}-2.png ${dir}/${img}.png

rm ${dir}/${img}-1.png ${dir}/${img}-2.png
}


cd $BASE/www/venetian
mkdir active inactive
for x in 10 20 30 40 50 60 70 80 90 mid move up
do
convert $x inactive "#44739e"
convert $x active "#FDD835"
#  magick convert -background white $x.svg +level-colors "#44739e", -resize 40x40 -tint 40 -transparent white inactive/$x.png
#  magick convert -background white $x.svg +level-colors "#FDD835", -resize 40x40 -tint 40 -transparent white active/$x.png
done

cd $BASE/www/vertical
mkdir active inactive
for x in 00 25 50 75 99 move mid open
do
convert $x inactive "#44739e"
convert $x active "#FDD835"
#  magick convert -background white $x.svg +level-colors "#44739e", -resize 40x40 -tint 40 -transparent white inactive/$x.png
#  magick convert -background white $x.svg +level-colors "#FDD835", -resize 40x40 -tint 40 -transparent white active/$x.png
done

cd $BASE/www/roller
mkdir active inactive
for x in 00 50 99 move
do
convert $x inactive "#44739e"
convert $x active "#FDD835"
#  magick convert -background white $x.svg +level-colors "#44739e", -resize 40x40 -tint 40 -transparent white inactive/$x.png
#  magick convert -background white $x.svg +level-colors "#FDD835", -resize 40x40 -tint 40 -transparent white active/$x.png
done
