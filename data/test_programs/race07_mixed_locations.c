/*
 * race07_mixed_locations.c — races at two independent locations
 *
 * Both threads build a shared prunable history on `counter` via
 * release stores.  They then concurrently access two other variables:
 *   - `flag` (relaxed write-write race)
 *   - `buf`  (non-atomic write-write race)
 *
 * Race type: relaxed-race on `flag`, non-atomic-race on `buf`
 * Prunable:  all intermediate stores to `counter` in both threads
 */

#include <stdatomic.h>
#include <pthread.h>

#define N 30

atomic_int counter = 0;
atomic_int flag    = 0;
int        buf     = 0;   /* non-atomic */

static void* thread1(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&counter, i, memory_order_release);
    atomic_store_explicit(&flag, 1, memory_order_relaxed);
    buf = 10;
    return NULL;
}

static void* thread2(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&counter, i + N, memory_order_release);
    atomic_store_explicit(&flag, 2, memory_order_relaxed);
    buf = 20;
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, thread1, NULL);
    pthread_create(&t2, NULL, thread2, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    (void)atomic_load_explicit(&counter, memory_order_acquire);
    return 0;
}
