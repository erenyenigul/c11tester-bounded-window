#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int y;
static atomic_int r;

void *t0_fn(void *arg) {
    (void)arg;
    atomic_store_explicit(&x, 1, memory_order_relaxed);
    atomic_thread_fence(memory_order_seq_cst);
    atomic_store_explicit(&y, 1, memory_order_relaxed);
    return NULL;
}

void *t1_fn(void *arg) {
    (void)arg;
    int a = atomic_load_explicit(&y, memory_order_relaxed);
    atomic_thread_fence(memory_order_seq_cst);
    int b = atomic_load_explicit(&x, memory_order_relaxed);
    atomic_store_explicit(&r, a * 10 + b, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1;
    atomic_init(&x, 0);
    atomic_init(&y, 0);
    atomic_init(&r, 0);

    pthread_create(&t0, NULL, t0_fn, NULL);
    pthread_create(&t1, NULL, t1_fn, NULL);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    return atomic_load_explicit(&r, memory_order_relaxed);
}
