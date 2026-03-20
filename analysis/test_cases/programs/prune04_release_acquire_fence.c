#include <pthread.h>
#include <stdatomic.h>

static atomic_int data;
static atomic_int flag;
static atomic_int out;

void *producer(void *arg) {
    (void)arg;
    atomic_store_explicit(&data, 7, memory_order_relaxed);
    atomic_thread_fence(memory_order_release);
    atomic_store_explicit(&flag, 1, memory_order_relaxed);
    return NULL;
}

void *consumer(void *arg) {
    (void)arg;
    while (atomic_load_explicit(&flag, memory_order_relaxed) == 0) {
    }
    atomic_thread_fence(memory_order_acquire);
    atomic_store_explicit(&out, atomic_load_explicit(&data, memory_order_relaxed), memory_order_relaxed);
    return NULL;
}

int main() {
    pthread_t t1, t2;
    atomic_init(&data, 0);
    atomic_init(&flag, 0);
    atomic_init(&out, 0);

    pthread_create(&t1, NULL, producer, NULL);
    pthread_create(&t2, NULL, consumer, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return atomic_load_explicit(&out, memory_order_relaxed);
}
