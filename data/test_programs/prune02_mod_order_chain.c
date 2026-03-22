#include <pthread.h>
#include <stdatomic.h>

// Test: Modification order chain that requires pruning
// Multiple threads write to same location in sequence
static atomic_int value;
static atomic_int turn;

void *writer_thread(void *arg) {
    int id = (int)(intptr_t)arg;
    // Busy-wait for turn
    while (atomic_load_explicit(&turn, memory_order_acquire) != id) {
    }
    // Write to shared location
    atomic_store_explicit(&value, id * 100, memory_order_relaxed);
    // Pass turn to next thread
    atomic_store_explicit(&turn, (id + 1) % 3, memory_order_release);
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&value, 0);
    atomic_init(&turn, 0);

    pthread_create(&t1, NULL, writer_thread, (void*)(intptr_t)0);
    pthread_create(&t2, NULL, writer_thread, (void*)(intptr_t)1);
    pthread_create(&t3, NULL, writer_thread, (void*)(intptr_t)2);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return 0;
}
