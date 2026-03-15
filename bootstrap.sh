#!/usr/bin/env bash
apt-get update
apt-get -y install cmake g++ autoconf autoconf2.13 libreadline-dev libssl-dev libncurses-dev
apt-get -y install libnuma-dev libdb++-dev libz-dev libboost-dev libboost-system-dev libaio-dev
apt-get -y install python3 python3-pip sudo nano clang-format 
pip install statistics

apt-get -y install mg neovim fish gdb cgdb valgrind git ninja-build

#su -c /vagrant/data/scripts/setup.sh vagrant
