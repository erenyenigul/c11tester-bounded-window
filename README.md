# CS4560 Parallel and Concurrent Programming - C11Tester
In this assignment, you will explore memory races from a practical
perspective through the use of the C11Tester tool made  by Weiyu Luo
and Brian Demsky at the University of California. Since getting it to
work is fairly tricky, we have made a Docker image with the necessary
tweaks for it to work.

## Using C11Tester
You can install and use the docker container by running the following
commands:
```bash
docker build . -t pcp
docker run --hostname PCP --cap-add=SYS_TRACE -it /usr/bin/fish
```

If the run command fails, try:
```bash
docker run --hostname PCP --cap-add=SYS_ADMIN -it pcp /usr/bin/fish
```

C11Tester is configured using a `config.h` file which defines C
options that can be set. The most relevant one for our purposes are
`#define PRINT_TRACE` and `#define `. Feel free to tweak and explore
this file. 

To run C11Tester, you need to compile the program using a special
compiler, the shared library and it's associated library headers. The
former two is done for by the docker container, so you just need to
run:
`clang -I/home/c11tester/c11tester/include -o [target] [target].c`

For example, to run C11tester on fences.c test program, run:
`clang -I/home/c11tester/c11tester/include -o prog2 c11tester-tests/test/fences.c`

Values to C11Tester can be passed using the `C11TESTER` environment
option to the program that you have compiled. You can see what is
available by running `C11TESTER="-h" ./[target]"`. To get a trace, you
can run `C11TESTER="--verbose=2" ./[target]`. Example programs from
an old version of C11Tester can be found in
`/home/c11tester/c11tester_tests`.



