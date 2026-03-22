#include <pthread.h>
#include <stdatomic.h>

// Test: Multiple stores to same location with longer trace
// This stresses the pruning of old stores that can no longer be read from
static atomic_int x;
static atomic_int done;

void *writer(void *arg) {
    (void)arg;
    // Long sequence of stores to same location
    for (int i = 1; i <= 20; i++) {
        atomic_store_explicit(&x, i, memory_order_relaxed);
    }
    atomic_store_explicit(&done, 1, memory_order_release);
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    // Keep reading until writer finishes
    int local_done = 0;
    while (!local_done) {
        int val = atomic_load_explicit(&x, memory_order_relaxed);
        local_done = atomic_load_explicit(&done, memory_order_acquire);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&x, 0);
    atomic_init(&done, 0);

    pthread_create(&t1, NULL, writer, NULL);
    pthread_create(&t2, NULL, reader, NULL);
    pthread_create(&t3, NULL, reader, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return 0;
}
