#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int start_flag;
static atomic_int sink;

static void spin_start(void) {
    // busy-wait
    while (atomic_load_explicit(&start_flag, memory_order_acquire) == 0) {
    }
}

void *writer_a(void *arg) {
    (void)arg;
    spin_start();
    atomic_store_explicit(&x, 1, memory_order_relaxed);
    return NULL;
}

void *writer_b(void *arg) {
    (void)arg;
    spin_start();
    atomic_store_explicit(&x, 2, memory_order_relaxed);
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    int r1, r2;
    spin_start();
    r1 = atomic_load_explicit(&x, memory_order_relaxed);
    r2 = atomic_load_explicit(&x, memory_order_relaxed);
    atomic_store_explicit(&sink, r1 * 10 + r2, memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&x, 0);
    atomic_init(&start_flag, 0);
    atomic_init(&sink, 0);

    pthread_create(&t1, NULL, writer_a, NULL);
    pthread_create(&t2, NULL, writer_b, NULL);
    pthread_create(&t3, NULL, reader, NULL);

    atomic_store_explicit(&start_flag, 1, memory_order_release);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return atomic_load_explicit(&sink, memory_order_relaxed);
}
