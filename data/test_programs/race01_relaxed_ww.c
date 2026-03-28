/*
 * race01_relaxed_ww.c — write-write relaxed race
 *
 * Both threads build a long history of release stores to `x` (prunable
 * after the join), then concurrently do a relaxed store to `flag`.
 * Neither store to `flag` is ordered after the other → write-write
 * relaxed race on `flag`.
 *
 * Race type: relaxed-race (write-write)
 * Prunable:  all intermediate stores to `x` in both threads
 */

#include <stdatomic.h>
#include <pthread.h>

#define N 30

atomic_int x = 0;
atomic_int flag = 0;

static void* thread1(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    atomic_store_explicit(&flag, 1, memory_order_relaxed);
    return NULL;
}

static void* thread2(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i + N, memory_order_release);
    atomic_store_explicit(&flag, 2, memory_order_relaxed);
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, thread1, NULL);
    pthread_create(&t2, NULL, thread2, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    /* acquire load gives main knowledge of both threads → pruning fires */
    (void)atomic_load_explicit(&x, memory_order_acquire);
    return 0;
}
