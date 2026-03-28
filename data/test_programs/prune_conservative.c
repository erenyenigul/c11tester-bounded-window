/*
 * prune_conservative.c
 *
 * Designed to exercise conservative pruning.
 *
 * Scenario
 * --------
 *   Thread 1 (producer): writes x = 1, 2, …, N  (release stores)
 *   Thread 2 (consumer): spins until x == N      (acquire load)
 *   Main: pthread_join on both threads
 *
 * Why pruning fires
 * -----------------
 * After the consumer's acquire-load reads the final release-store of the
 * producer, the consumer's clock vector includes the producer's entire
 * history.  The subsequent pthread_join in main creates a happens-before
 * edge from both threads to main, giving main a clock vector that covers
 * all events in both threads.
 *
 * At that point CVmin[producer_thread] >= last_store_of_producer, so all
 * stores x=1 … x=N-1 are mo-before the last globally-synced store and
 * are safely prunable (no future load can read them).
 *
 * N=20 is intentionally small so C11Tester explores it in a few executions,
 * but large enough that multiple stores get pruned.
 */

#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>

#define N 20

atomic_int x = 0;

static void* producer(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++) {
        atomic_store_explicit(&x, i, memory_order_release);
    }
    printf("producer: done (wrote 1..%d)\n", N);
    return NULL;
}

static void* consumer(void* arg) {
    (void)arg;
    int val;
    /* Spin until we observe the final store from the producer. */
    do {
        val = atomic_load_explicit(&x, memory_order_acquire);
    } while (val < N);
    printf("consumer: saw x == %d\n", val);
    return NULL;
}

int main(void) {
    pthread_t t1, t2;

    pthread_create(&t1, NULL, producer, NULL);
    pthread_create(&t2, NULL, consumer, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    printf("main: both threads done, x = %d\n",
           atomic_load_explicit(&x, memory_order_acquire));
    return 0;
}
