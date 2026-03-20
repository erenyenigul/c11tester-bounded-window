#include <pthread.h>
#include <stdatomic.h>

// Test: Very long execution window with mixed operations
// Combines multiple pruning challenge scenarios
static atomic_int value;
static atomic_int ready;
static int data;

void *producer_a(void *arg) {
    (void)arg;
    // Many stores to drive modification order chain
    for (int i = 1; i <= 12; i++) {
        data = i * 100;  // Non-atomic write: potential race
        atomic_store_explicit(&value, i, memory_order_release);
    }
    return NULL;
}

void *producer_b(void *arg) {
    (void)arg;
    // Another producer with non-atomic data corruption possibility
    for (int i = 100; i <= 112; i++) {
        data = i;  // Non-atomic write: races with producer_a
        atomic_store_explicit(&value, i, memory_order_release);
    }
    return NULL;
}

void *consumer(void *arg) {
    (void)arg;
    // Consumer waits then reads repeatedly
    while (atomic_load_explicit(&ready, memory_order_acquire) == 0) {
    }
    for (int i = 0; i < 30; i++) {
        int val = atomic_load_explicit(&value, memory_order_acquire);
        int non_atomic_val = data;  // May race with producers
    }
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&value, 0);
    atomic_init(&ready, 0);
    data = 0;

    pthread_create(&t1, NULL, producer_a, NULL);
    pthread_create(&t2, NULL, producer_b, NULL);
    pthread_create(&t3, NULL, consumer, NULL);

    // Signal consumer to start
    atomic_store_explicit(&ready, 1, memory_order_release);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return 0;
}
