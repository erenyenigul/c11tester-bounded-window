#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int observed;

void *reader_then_writer(void *arg) {
    (void)arg;
    int r = atomic_load_explicit(&x, memory_order_relaxed);
    atomic_store_explicit(&x, r + 10, memory_order_relaxed);
    atomic_store_explicit(&observed, r, memory_order_relaxed);
    return NULL;
}

void *writer(void *arg) {
    (void)arg;
    atomic_store_explicit(&x, 1, memory_order_relaxed);
    atomic_store_explicit(&x, 2, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1;
    atomic_init(&x, 0);
    atomic_init(&observed, 0);

    pthread_create(&t0, NULL, reader_then_writer, NULL);
    pthread_create(&t1, NULL, writer, NULL);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    return atomic_load_explicit(&observed, memory_order_relaxed);
}
