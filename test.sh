#!/bin/sh

convert() {
img=$1
dir=$2
col=$3
brd=$4

cp ${img}.svg ${dir}/${img}.svg
sed -i '' "s/#333/#${col}/g" ${dir}/${img}.svg
sed -i '' "s/#000/#${col}/g" ${dir}/${img}.svg
sed -i '' "s/#b2b2b2/#${col}/g" ${dir}/${img}.svg
sed -i '' "s/#e5e5e5/#${col}/g" ${dir}/${img}.svg
sed -i '' "s/#ccc/#${col}/g" ${dir}/${img}.svg
sed -i '' "s/#5e5e5e/#${col}/g" ${dir}/${img}.svg

sed -i '' 's/\(class="lucid-layer"\)/\1 fill="#XXX"/g' ${dir}/${img}.svg
sed -i '' 's/\(class="lucid-layer lucid-layer"\)/\1 fill="#XXX"/g' ${dir}/${img}.svg
sed -i '' 's/\(fill="[^"]*"[^>]*\)fill="[^"]*"/\1/g' ${dir}/${img}.svg
sed -i '' "s/#XXX/#${col}/g" ${dir}/${img}.svg
sed -i '' "s/stroke=\(.\)#fff./stroke=\1#${brd}\1/g" ${dir}/${img}.svg
sed -i '' "s/fill=\(.\)#fff./fill=\1#${brd}\1/g" ${dir}/${img}.svg


}

BASE=$(pwd)

cd ${BASE}/www/venetian
mkdir active inactive
for file in 10 20 30 40 50 60 70 80 90 up mid move
do
convert $file inactive 44739e fff
convert $file active FDD835 727272
done

cd $BASE/www/vertical
mkdir active inactive
for file in 00 25 50 75 99 move mid open
do
convert $file inactive 44739e fff
convert $file active FDD835 aaa
done

cd $BASE/www/roller
mkdir active inactive
for file in 00 50 99 move
do
convert $file inactive 44739e 000
convert $file active FDD835 aaa
done
