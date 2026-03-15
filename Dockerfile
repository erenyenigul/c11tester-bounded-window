FROM ubuntu:20.04 AS base


ARG DEBIAN_FRONTEND=noninteractive TZ="Europe/Amsterdam"
WORKDIR /c11tester
COPY bootstrap.sh /c11tester
RUN sh /c11tester/bootstrap.sh

RUN useradd -u 1000 -ms /usr/bin/fish c11tester && echo "c11tester ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER c11tester

# Separate the LLVM compiling from the setup script so the result
# is cached
COPY data/llvm-8.0.0.src.tar.xz data/scripts/get-llvm.sh data/cfe-8.0.0.src.tar.xz .
COPY data/CDSPass CDSPass
RUN sh get-llvm.sh

COPY data .
RUN sh /c11tester/scripts/setup.sh

WORKDIR /home/c11tester
