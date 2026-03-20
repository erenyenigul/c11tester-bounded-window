#include <pthread.h>
#include <stdatomic.h>

// Test: Long trace with fences and multiple locations
// Tests fence pruning and per-location pruning
static atomic_int x, y, z;
static atomic_int sync;

void *producer(void *arg) {
    (void)arg;
    for (int i = 0; i < 10; i++) {
        atomic_store_explicit(&x, i, memory_order_relaxed);
        atomic_store_explicit(&y, i * 2, memory_order_relaxed);
        atomic_store_explicit(&z, i * 3, memory_order_relaxed);
    }
    atomic_thread_fence(memory_order_release);
    atomic_store_explicit(&sync, 1, memory_order_relaxed);
    return NULL;
}

void *consumer(void *arg) {
    (void)arg;
    while (atomic_load_explicit(&sync, memory_order_relaxed) == 0) {
    }
    atomic_thread_fence(memory_order_acquire);
    int rx = atomic_load_explicit(&x, memory_order_relaxed);
    int ry = atomic_load_explicit(&y, memory_order_relaxed);
    int rz = atomic_load_explicit(&z, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t1, t2;
    atomic_init(&x, 0);
    atomic_init(&y, 0);
    atomic_init(&z, 0);
    atomic_init(&sync, 0);

    pthread_create(&t1, NULL, producer, NULL);
    pthread_create(&t2, NULL, consumer, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}
