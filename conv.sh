#!/bin/bash

BASE=$(pwd)

cd $BASE/www/venetian
mkdir active inactive
for x in 10 20 30 40 50 60 70 80 90 mid move up
do
  magick convert $x.svg -background transparent +level-colors "#44739e", -resize 40x40 -tint 40 inactive/$x.png
  magick convert $x.svg -background transparent +level-colors "#FDD835", -resize 40x40 -tint 40 active/$x.png
done

cd $BASE/www/vertical
mkdir active inactive
for x in 00 25 75 99 move
do
  magick convert $x.svg +level-colors "#44739e", -resize 40x40 -tint 40 inactive/$x.png
  magick convert $x.svg +level-colors "#FDD835", -resize 40x40 -tint 40 active/$x.png
done

# cd $BASE/www/roller
# mkdir active inactive
# for x in 00 50 99 move
# do
#   magick convert $x.svg +level-colors "#44739e", -resize 40x40 -tint 40 inactive/$x.png
#   magick convert $x.svg +level-colors "#FDD835", -resize 40x40 -tint 40 active/$x.png
# done
