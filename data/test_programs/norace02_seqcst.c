/*
 * norace02_seqcst.c — NO race, all seq_cst operations
 *
 * Three threads each do N seq_cst increments on a shared counter via
 * fetch_add (seq_cst).  All accesses are totally ordered by the SC
 * axiom → no data race.
 *
 * The long chain of RMWs creates substantial history; after all threads
 * sync through the seq_cst total order the intermediate stores are
 * prunable.
 *
 * Prunable: early RMW stores once all threads have observed later ones
 */

#include <stdatomic.h>
#include <pthread.h>
#include <stdio.h>

#define N 20

atomic_int counter = 0;

static void* worker(void* arg) {
    (void)arg;
    for (int i = 0; i < N; i++)
        atomic_fetch_add_explicit(&counter, 1, memory_order_seq_cst);
    return NULL;
}

int main(void) {
    pthread_t t1, t2, t3;
    pthread_create(&t1, NULL, worker, NULL);
    pthread_create(&t2, NULL, worker, NULL);
    pthread_create(&t3, NULL, worker, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    printf("counter = %d (expected %d)\n",
           atomic_load_explicit(&counter, memory_order_seq_cst), 3 * N);
    return 0;
}
