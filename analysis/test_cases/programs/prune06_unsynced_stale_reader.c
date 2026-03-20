#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int done;
static atomic_int sink;

void *writer(void *arg) {
    (void)arg;
    for (int i = 1; i <= 4; i++) {
        atomic_store_explicit(&x, i, memory_order_relaxed);
    }
    atomic_store_explicit(&done, 1, memory_order_release);
    return NULL;
}

void *stale_reader(void *arg) {
    (void)arg;
    int acc = 0;
    while (atomic_load_explicit(&done, memory_order_relaxed) == 0) {
        acc ^= atomic_load_explicit(&x, memory_order_relaxed);
    }
    atomic_store_explicit(&sink, acc, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1;
    atomic_init(&x, 0);
    atomic_init(&done, 0);
    atomic_init(&sink, 0);

    pthread_create(&t0, NULL, writer, NULL);
    pthread_create(&t1, NULL, stale_reader, NULL);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    return atomic_load_explicit(&sink, memory_order_relaxed);
}
