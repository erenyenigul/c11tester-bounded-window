/*
 * race02_relaxed_rw.c — read-write relaxed race
 *
 * Thread 1 builds prunable release-store history on `x`, then does a
 * relaxed store to `data`.  Thread 2 does the same history then a
 * relaxed load from `data`.  No synchronisation between the two on
 * `data` → read-write relaxed race.
 *
 * Race type: relaxed-race (read-write)
 * Prunable:  all intermediate stores to `x` in both threads
 */

#include <stdatomic.h>
#include <pthread.h>

#define N 30

atomic_int x    = 0;
atomic_int data = 0;

static void* writer(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    atomic_store_explicit(&data, 42, memory_order_relaxed);
    return NULL;
}

static void* reader(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i + N, memory_order_release);
    (void)atomic_load_explicit(&data, memory_order_relaxed);
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
