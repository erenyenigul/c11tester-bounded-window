#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int flag;
static atomic_int out;

void *t0_fn(void *arg) {
    (void)arg;
    atomic_store_explicit(&x, 1, memory_order_relaxed);
    atomic_store_explicit(&flag, 1, memory_order_release);
    return NULL;
}

void *t1_fn(void *arg) {
    (void)arg;
    int expected = 1;
    while (!atomic_compare_exchange_weak_explicit(&flag, &expected, 2,
                                                  memory_order_acq_rel,
                                                  memory_order_acquire)) {
        expected = 1;
    }
    return NULL;
}

void *t2_fn(void *arg) {
    (void)arg;
    while (atomic_load_explicit(&flag, memory_order_acquire) < 2) {
    }
    atomic_store_explicit(&out, atomic_load_explicit(&x, memory_order_relaxed), memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t0, t1, t2;
    atomic_init(&x, 0);
    atomic_init(&flag, 0);
    atomic_init(&out, 0);

    pthread_create(&t0, NULL, t0_fn, NULL);
    pthread_create(&t1, NULL, t1_fn, NULL);
    pthread_create(&t2, NULL, t2_fn, NULL);

    pthread_join(t0, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return atomic_load_explicit(&out, memory_order_relaxed);
}
