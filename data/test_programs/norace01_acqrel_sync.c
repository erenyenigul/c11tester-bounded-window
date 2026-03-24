/*
 * norace01_acqrel_sync.c — NO race, proper acquire-release sync
 *
 * Thread 1 (producer): N release stores to `x`, final store signals
 *   "data is ready" by release-storing 1 to `ready`.
 * Thread 2 (consumer): spins with acquire load on `ready`; once it
 *   sees 1, all of thread 1's writes are hb-before thread 2's reads.
 *
 * No data race: thread 2's read of `data` is ordered after thread 1's
 * write via the release-acquire pair on `ready`.
 *
 * Prunable: x stores 1..N-1 after consumer syncs with producer
 */

#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>

#define N 30

atomic_int x     = 0;
atomic_int ready = 0;
int        data  = 0;   /* non-atomic — safe because of acq-rel on ready */

static void* producer(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    data = 123;
    atomic_store_explicit(&ready, 1, memory_order_release);
    return NULL;
}

static void* consumer(void* arg) {
    (void)arg;
    while (atomic_load_explicit(&ready, memory_order_acquire) == 0) {}
    /* hb from producer's write to data: safe read */
    printf("data = %d\n", data);
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, producer, NULL);
    pthread_create(&t2, NULL, consumer, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    (void)atomic_load_explicit(&x, memory_order_acquire);
    return 0;
}
