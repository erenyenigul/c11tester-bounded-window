/*
 * race05_ra_race.c — RA-race (release store vs relaxed load)
 *
 * Thread 1 builds prunable history on `x`, then does a release store
 * to `y`.  Thread 2 builds its own prunable history on `x`, then does
 * a relaxed load from `y`.  The two accesses to `y` are concurrent
 * (no hb between them) — at least one is non-SC → RA-race.
 *
 * Race type: RA-race (write-read, both non-SC)
 * Prunable:  all intermediate stores to `x` in both threads
 */

#include <stdatomic.h>
#include <pthread.h>

#define N 30

atomic_int x = 0;
atomic_int y = 0;

static void* thread1(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    atomic_store_explicit(&y, 1, memory_order_release);
    return NULL;
}

static void* thread2(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i + N, memory_order_release);
    (void)atomic_load_explicit(&y, memory_order_relaxed);  /* RA-race */
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, thread1, NULL);
    pthread_create(&t2, NULL, thread2, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    (void)atomic_load_explicit(&x, memory_order_acquire);
    return 0;
}
