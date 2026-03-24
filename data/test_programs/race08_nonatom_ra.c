/*
 * race08_nonatom_ra.c — non-atomic race interleaved with RA sync
 *
 * Thread 1: N release stores to `x`, then plain write to `shared`.
 * Thread 2: acquire-loads until it sees x==N (syncs with thread 1),
 *   then plain read from `shared` — but thread 3 is still concurrent
 *   with thread 1 on `shared`.
 * Thread 3: plain write to `shared` with no synchronisation with t1.
 *
 * Thread 2 properly syncs with thread 1 via acquire-load (no race
 * between t1 write and t2 read on `shared`).  Thread 3, however, has
 * no ordering with thread 1 → non-atomic write-write race between
 * thread 1 and thread 3 on `shared`.
 *
 * Race type: non-atomic-race (write-write, t1 vs t3)
 * Prunable:  x stores 1..N-1 after t2 syncs with t1
 */

#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>

#define N 30

atomic_int x      = 0;
int        shared = 0;   /* non-atomic */

static void* thread1(void* arg) {
    (void)arg;
    for (int i = 1; i <= N; i++)
        atomic_store_explicit(&x, i, memory_order_release);
    shared = 42;
    return NULL;
}

static void* thread2(void* arg) {
    (void)arg;
    while (atomic_load_explicit(&x, memory_order_acquire) < N) {}
    /* hb from thread1's write to shared: no race here */
    printf("shared = %d\n", shared);
    return NULL;
}

static void* thread3(void* arg) {
    (void)arg;
    shared = 99;   /* concurrent with thread1 write → race */
    return NULL;
}

int main(void) {
    pthread_t t1, t2, t3;
    pthread_create(&t1, NULL, thread1, NULL);
    pthread_create(&t2, NULL, thread2, NULL);
    pthread_create(&t3, NULL, thread3, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    (void)atomic_load_explicit(&x, memory_order_acquire);
    return 0;
}
