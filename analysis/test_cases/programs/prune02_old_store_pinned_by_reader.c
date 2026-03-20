#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int gate;
static atomic_int keepalive;

void *old_writer(void *arg) {
    (void)arg;
    atomic_store_explicit(&x, 1, memory_order_relaxed);
    atomic_store_explicit(&gate, 1, memory_order_release);
    return NULL;
}

void *new_writer(void *arg) {
    (void)arg;
    while (atomic_load_explicit(&gate, memory_order_acquire) == 0) {
    }
    atomic_store_explicit(&x, 2, memory_order_relaxed);
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    int r1 = 0;
    int r2 = 0;

    while (atomic_load_explicit(&gate, memory_order_acquire) == 0) {
    }

    r1 = atomic_load_explicit(&x, memory_order_relaxed);
    r2 = atomic_load_explicit(&x, memory_order_relaxed);
    atomic_store_explicit(&keepalive, r1 + r2, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1, t2;
    atomic_init(&x, 0);
    atomic_init(&gate, 0);
    atomic_init(&keepalive, 0);

    pthread_create(&t0, NULL, old_writer, NULL);
    pthread_create(&t1, NULL, new_writer, NULL);
    pthread_create(&t2, NULL, reader, NULL);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return atomic_load_explicit(&keepalive, memory_order_relaxed);
}
