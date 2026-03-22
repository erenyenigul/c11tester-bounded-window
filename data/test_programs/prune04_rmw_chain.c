#include <pthread.h>
#include <stdatomic.h>

// Test: RMW chain that generates many modification-ordered edges
// Tests pruning under heavy modification order constraints
static atomic_int counter;

void *increment_worker(void *arg) {
    (void)arg;
    // Each thread performs many increments
    for (int i = 0; i < 15; i++) {
        atomic_fetch_add_explicit(&counter, 1, memory_order_acq_rel);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2, t3, t4;
    atomic_init(&counter, 0);

    pthread_create(&t1, NULL, increment_worker, NULL);
    pthread_create(&t2, NULL, increment_worker, NULL);
    pthread_create(&t3, NULL, increment_worker, NULL);
    pthread_create(&t4, NULL, increment_worker, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    pthread_join(t4, NULL);
    return counter;
}
