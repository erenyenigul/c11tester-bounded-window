/*
 * race06_three_thread.c — three-thread relaxed race
 *
 * Thread 1 (producer): N release stores to `x` — creates prunable history.
 * Thread 2 (consumer): spins with acquire load until it sees x==N, then
 *   does a relaxed store to `result`.  Thread 2 syncs with thread 1 via
 *   rf+acquire, so x stores become prunable after the join.
 * Thread 3 (racer):  relaxed store to `result` with no synchronisation
 *   with thread 2 → write-write relaxed race on `result`.
 *
 * Race type: relaxed-race (write-write on `result`)
 * Prunable:  x stores 1..N-1 after consumer syncs with producer
 */

#include <stdatomic.h>
#include <pthread.h>

#define N 30

atomic_int x      = 0;
atomic_int result = 0;

static void* producer(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    return NULL;
}

static void* consumer(void* arg) {
    (void)arg;
    while (atomic_load_explicit(&x, memory_order_acquire) < N) {}
    atomic_store_explicit(&result, 1, memory_order_relaxed);
    return NULL;
}

static void* racer(void* arg) {
    (void)arg;
    atomic_store_explicit(&result, 2, memory_order_relaxed);  /* races with consumer */
    return NULL;
}

int main(void) {
    pthread_t t1, t2, t3;
    pthread_create(&t1, NULL, producer, NULL);
    pthread_create(&t2, NULL, consumer, NULL);
    pthread_create(&t3, NULL, racer,    NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    (void)atomic_load_explicit(&x, memory_order_acquire);
    return 0;
}
