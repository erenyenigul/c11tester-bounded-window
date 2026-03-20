#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int y;
static atomic_int start;
static atomic_int sink;

static void wait_start(void) {
    while (atomic_load_explicit(&start, memory_order_acquire) == 0) {
    }
}

void *writer_x(void *arg) {
    (void)arg;
    wait_start();
    for (int i = 0; i < 40; i++) {
        atomic_store_explicit(&x, i, memory_order_relaxed);
    }
    return NULL;
}

void *writer_y(void *arg) {
    (void)arg;
    wait_start();
    for (int i = 0; i < 40; i++) {
        atomic_store_explicit(&y, i, memory_order_relaxed);
    }
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    int acc = 0;
    wait_start();
    for (int i = 0; i < 40; i++) {
        int a = atomic_load_explicit(&x, memory_order_relaxed);
        int b = atomic_load_explicit(&y, memory_order_relaxed);
        acc ^= (a + b);
    }
    atomic_store_explicit(&sink, acc, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1, t2;
    atomic_init(&x, 0);
    atomic_init(&y, 0);
    atomic_init(&start, 0);
    atomic_init(&sink, 0);

    pthread_create(&t0, NULL, writer_x, NULL);
    pthread_create(&t1, NULL, writer_y, NULL);
    pthread_create(&t2, NULL, reader, NULL);

    atomic_store_explicit(&start, 1, memory_order_release);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return atomic_load_explicit(&sink, memory_order_relaxed);
}
