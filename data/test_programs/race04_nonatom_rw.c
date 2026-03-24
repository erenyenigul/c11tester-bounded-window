/*
 * race04_nonatom_rw.c — non-atomic read-write race
 *
 * Thread 1 builds a long prunable atomic history then does a plain
 * write to `buf`.  Thread 2 builds its own prunable history then does
 * a plain read from `buf`.  No ordering between the accesses →
 * non-atomic read-write race.
 *
 * Race type: non-atomic-race (read-write)
 * Prunable:  all intermediate stores to `x` in both threads
 */

#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>

#define N 30

atomic_int x   = 0;
int        buf = 0;    /* non-atomic */

static void* writer(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    buf = 99;           /* plain write */
    return NULL;
}

static void* reader(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i + N, memory_order_release);
    printf("buf = %d\n", buf);   /* plain read — races with writer */
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, writer, NULL);
    pthread_create(&t2, NULL, reader, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    (void)atomic_load_explicit(&x, memory_order_acquire);
    return 0;
}
