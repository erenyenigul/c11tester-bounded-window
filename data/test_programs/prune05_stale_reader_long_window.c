#include <pthread.h>
#include <stdatomic.h>

// Test: Stale reader scenario with long trace window
// Unsynchronized reader continuously loads while writer advances values
static int data[20];  // Non-atomic array
static atomic_int writer_idx;
static atomic_int reader_spinning;

void *writer(void *arg) {
    (void)arg;
    // Write to array locations sequentially
    for (int i = 0; i < 20; i++) {
        data[i] = i * 10;  // Non-atomic write -- potential race with reader
        atomic_store_explicit(&writer_idx, i, memory_order_relaxed);
    }
    return NULL;
}

void *reader(void *arg) {
    (void)arg;
    // Keep reading while writer is writing
    for (int r = 0; r < 50; r++) {
        int idx = atomic_load_explicit(&writer_idx, memory_order_relaxed);
        if (idx >= 0 && idx < 20) {
            int val = data[idx];  // May race with concurrent write
        }
    }
    return NULL;
}

int main() {
    pthread_t t1, t2;
    atomic_init(&writer_idx, -1);

    for (int i = 0; i < 20; i++) {
        data[i] = 0;
    }

    pthread_create(&t1, NULL, writer, NULL);
    pthread_create(&t2, NULL, reader, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}
