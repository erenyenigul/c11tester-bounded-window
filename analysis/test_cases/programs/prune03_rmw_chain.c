#include <pthread.h>
#include <stdatomic.h>

static atomic_int x;
static atomic_int y;

void *rmw_worker(void *arg) {
    (void)arg;
    int old = atomic_fetch_add_explicit(&x, 1, memory_order_acq_rel);
    atomic_store_explicit(&y, old, memory_order_relaxed);
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    int r1 = atomic_load_explicit(&x, memory_order_acquire);
    int r2 = atomic_load_explicit(&y, memory_order_relaxed);
    if (r2 > r1) {
        atomic_store_explicit(&y, 100, memory_order_relaxed);
    }
    return NULL;
}

int main() {
    pthread_t t1, t2, t3;
    atomic_init(&x, 0);
    atomic_init(&y, 0);

    pthread_create(&t1, NULL, rmw_worker, NULL);
    pthread_create(&t2, NULL, rmw_worker, NULL);
    pthread_create(&t3, NULL, reader, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    pthread_join(t3, NULL);
    return atomic_load_explicit(&y, memory_order_relaxed);
}
