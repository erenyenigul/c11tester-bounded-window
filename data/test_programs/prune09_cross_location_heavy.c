#include <pthread.h>
#include <stdatomic.h>

// Test: Cross-location activity with heavy stores
// Tests per-location pruning independence
static atomic_int loc1[10], loc2[10], sync;

void *writer_loc1(void *arg) {
    (void)arg;
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            atomic_store_explicit(&loc1[j], i * 10 + j, memory_order_relaxed);
        }
    }
    atomic_store_explicit(&sync, 1, memory_order_release);
    return NULL;
}

void *writer_loc2(void *arg) {
    (void)arg;
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            atomic_store_explicit(&loc2[j], i * 100 + j, memory_order_relaxed);
        }
    }
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    while (atomic_load_explicit(&sync, memory_order_acquire) == 0) {
    }
    for (int i = 0; i < 10; i++) {
        int val1 = atomic_load_explicit(&loc1[i], memory_order_relaxed);
        int val2 = atomic_load_explicit(&loc2[i], memory_order_relaxed);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    for (int i = 0; i < 10; i++) {
        atomic_init(&loc1[i], 0);
        atomic_init(&loc2[i], 0);
    }
    atomic_init(&sync, 0);

    pthread_create(&t1, NULL, writer_loc1, NULL);
    pthread_create(&t2, NULL, writer_loc2, NULL);
    pthread_create(&t3, NULL, reader, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return 0;
}
