#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdatomic.h> // C11 Atomics

#define NUM_THREADS 4
#define ITERATIONS 100

atomic_int shared_counter = 0;

void* thread_func(void* arg) {
    int thread_id = *((int*)arg);
    
    for (int i = 0; i < ITERATIONS; i++) {
        atomic_fetch_add_explicit(&shared_counter, 1, memory_order_relaxed);
    }
    
    printf("Thread %d finished its work.\n", thread_id);
    return NULL;
}

int main() {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];

    printf("Starting %d threads, each incrementing the counter %d times...\n", 
           NUM_THREADS, ITERATIONS);

    // 1. Create the threads
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i; // Pass a unique ID to each thread
        
        if (pthread_create(&threads[i], NULL, thread_func, &thread_ids[i]) != 0) {
            perror("Failed to create thread");
            return EXIT_FAILURE;
        }
    }

    // 2. Wait for all threads to finish executing
    for (int i = 0; i < NUM_THREADS; i++) {
        if (pthread_join(threads[i], NULL) != 0) {
            perror("Failed to join thread");
            return EXIT_FAILURE;
        }
    }

    return EXIT_SUCCESS;
}