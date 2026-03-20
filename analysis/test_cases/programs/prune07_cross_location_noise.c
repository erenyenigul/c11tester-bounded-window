#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int y;
static atomic_int z;

void *x_writer(void *arg) {
    (void)arg;
    atomic_store_explicit(&x, 1, memory_order_relaxed);
    atomic_store_explicit(&x, 2, memory_order_relaxed);
    return NULL;
}

void *y_writer(void *arg) {
    (void)arg;
    for (int i = 0; i < 8; i++) {
        atomic_store_explicit(&y, i, memory_order_relaxed);
    }
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    int a = atomic_load_explicit(&x, memory_order_relaxed);
    int b = atomic_load_explicit(&y, memory_order_relaxed);
    atomic_store_explicit(&z, a + b, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1, t2;
    atomic_init(&x, 0);
    atomic_init(&y, 0);
    atomic_init(&z, 0);

    pthread_create(&t0, NULL, x_writer, NULL);
    pthread_create(&t1, NULL, y_writer, NULL);
    pthread_create(&t2, NULL, reader, NULL);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return atomic_load_explicit(&z, memory_order_relaxed);
}
