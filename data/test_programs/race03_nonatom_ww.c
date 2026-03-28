/*
 * race03_nonatom_ww.c — non-atomic write-write race
 *
 * Both threads build a long prunable history on atomic `x`, then write
 * to the plain (non-atomic) variable `shared`.  No happens-before
 * between the two plain writes → non-atomic write-write race.
 *
 * Race type: non-atomic-race (write-write)
 * Prunable:  all intermediate stores to `x` in both threads
 */

#include <stdatomic.h>
#include <pthread.h>

#define N 30

atomic_int x  = 0;
int        shared = 0;   /* non-atomic */

static void* thread1(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    shared = 1;          /* plain write */
    return NULL;
}

static void* thread2(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i + N, memory_order_release);
    shared = 2;          /* plain write — races with thread1 */
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
