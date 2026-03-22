#include <pthread.h>
#include <stdatomic.h>

// Test: Release sequence with long chain
// Multiple RMW operations forming a release sequence
static atomic_int x;
static atomic_int flag;

void *rmw_worker(void *arg) {
    (void)arg;
    // Perform several RMW operations
    for (int i = 0; i < 8; i++) {
        int old = atomic_fetch_add_explicit(&x, 1, memory_order_release);
    }
    return NULL;
}

void *observer(void *arg) {
    (void)arg;
    // Acquire observations
    while (atomic_load_explicit(&flag, memory_order_acquire) == 0) {
    }
    int val = atomic_load_explicit(&x, memory_order_acquire);
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&x, 0);
    atomic_init(&flag, 0);

    pthread_create(&t1, NULL, rmw_worker, NULL);
    pthread_create(&t2, NULL, rmw_worker, NULL);
    
    // Let RMW workers do some work before observer starts
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    
    atomic_store_explicit(&flag, 1, memory_order_release);
    pthread_create(&t3, NULL, observer, NULL);
    pthread_join(t3, NULL);

    return 0;
}
