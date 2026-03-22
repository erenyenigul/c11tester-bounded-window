#include <pthread.h>
#include <stdatomic.h>

// Test: SC fence with long trace and multiple threads
// Sequentially consistent fences interact with many stores/loads
static atomic_int a, b, c;

void *thread_a(void *arg) {
    (void)arg;
    for (int i = 1; i <= 5; i++) {
        atomic_store_explicit(&a, i, memory_order_seq_cst);
        atomic_thread_fence(memory_order_seq_cst);
    }
    return NULL;
}

void *thread_b(void *arg) {
    (void)arg;
    for (int i = 1; i <= 5; i++) {
        atomic_store_explicit(&b, i, memory_order_seq_cst);
        atomic_thread_fence(memory_order_seq_cst);
    }
    return NULL;
}

void *thread_c(void *arg) {
    (void)arg;
    for (int i = 0; i < 5; i++) {
        int ra = atomic_load_explicit(&a, memory_order_seq_cst);
        int rb = atomic_load_explicit(&b, memory_order_seq_cst);
        atomic_thread_fence(memory_order_seq_cst);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&a, 0);
    atomic_init(&b, 0);
    atomic_init(&c, 0);

    pthread_create(&t1, NULL, thread_a, NULL);
    pthread_create(&t2, NULL, thread_b, NULL);
    pthread_create(&t3, NULL, thread_c, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return 0;
}
