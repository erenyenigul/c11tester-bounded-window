#!/bin/bash
set -e
sudo chown -R c11tester /c11tester
cd ~

#1. Copy over the tests
cp -r /c11tester/c11tester-tests .

# 2. Getting and compiling c11tester
echo "==============\nC11Tester\n============="
# git clone git://plrg.ics.uci.edu/c11tester.git
cp -r /c11tester/c11tester .
cd ~/c11tester
git checkout vagrant
sed -i -e 's/\/\/\#define\ PRINT\_TRACE/\#define\ PRINT\_TRACE/g' config.h
make clean
make

# Add symlink the model
sudo ln -s /home/c11tester/c11tester/libmodel.so /usr/lib/libmodel.so

cd ..


## This version of c11tester compiles volatiles into relaxed atomics
#git clone git://plrg.ics.uci.edu/c11tester.git c11tester-relaxed
echo "==============\nC11Tester Relaxed\n============="
cp -r /c11tester/c11tester c11tester-relaxed
cd ~/c11tester-relaxed
git checkout vagrant
sed -i 's/memory_order_acquire/memory_order_relaxed/g' config.h
sed -i 's/memory_order_release/memory_order_relaxed/g' config.h
sed -i -e 's/\/\/\#define\ PRINT\_TRACE/\#define\ PRINT\_TRACE/g' config.h
make clean
make

sudo ln -s /home/c11tester/c11tester-relaxed/libmodel.so /usr/lib/libmodel-relaxed.so
cd ..

# 3. Benchmarks
echo "==============\nC11Tester Benchmarks\n============="
#git clone git://plrg.ics.uci.edu/c11concurrency-benchmarks.git c11tester-benchmarks
cp -r /c11tester/c11tester-benchmarks .
cd c11tester-benchmarks
git checkout vagrant

# fix broken shebangs in the scripts and update the references to vagrance
sed -i -e 's/\#\/bin\/bash/\#\!\/usr\/bin\/env\ bash/g' g++ gcc clang clang++
find . -type f -exec sed -i -e 's/\/home\/vagrant/\/home\/c11tester/g' '{}' \;
sudo ln -s "$PWD/g++" /usr/local/bin/g++
sudo ln -s "$PWD/gcc" /usr/local/bin/gcc
sudo ln -s "$PWD/clang" /usr/local/bin/clang
sudo ln -s "$PWD/clang++" /usr/local/bin/clang++


cp /c11tester/scripts/build.sh .
cp /c11tester/scripts/do_test_all.sh .
cp /c11tester/scripts/app_assertion_test.sh .
cp /c11tester/scripts/app_test_all.sh .
cp /c11tester/scripts/run.sh .
cp /c11tester/scripts/calculator.py .
./build.sh
cd ..

## Firefox Javascript shell
#echo "==============\nJShell\n============="
#cp /c11tester/scripts/build_firefox_jsshell.sh .
#chmod +x build_firefox_jsshell.sh
#./build_firefox_jsshell.sh
echo >&2 "Setup is now complete. To run the benchmarks, please look at our READE.md"
