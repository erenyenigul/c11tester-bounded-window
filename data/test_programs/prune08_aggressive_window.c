#include <pthread.h>
#include <stdatomic.h>

// Test: Aggressive window pruning scenario
// Long unsynced thread prevents conservative pruning
static atomic_int x, y;

void *busy_unsync_thread(void *arg) {
    (void)arg;
    // This thread never synchronizes, preventing conservative pruning
    // It continuously reads without proper sync
    volatile int dummy = 0;
    for (int i = 0; i < 100; i++) {
        int rx = atomic_load_explicit(&x, memory_order_relaxed);
        int ry = atomic_load_explicit(&y, memory_order_relaxed);
        dummy = rx + ry;
    }
    return NULL;
}

void *synced_writer(void *arg) {
    (void)arg;
    // Many writes that should trigger aggressive pruning
    for (int i = 0; i < 25; i++) {
        atomic_store_explicit(&x, i, memory_order_relaxed);
        atomic_store_explicit(&y, i + 1, memory_order_relaxed);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;
    atomic_init(&x, 0);
    atomic_init(&y, 0);

    pthread_create(&t1, NULL, busy_unsync_thread, NULL);
    pthread_create(&t2, NULL, synced_writer, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}
