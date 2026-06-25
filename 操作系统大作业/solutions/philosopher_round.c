#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define PHILOSOPHER_COUNT 5
#define MAX_ROUNDS 3

static sem_t forks[PHILOSOPHER_COUNT];
static pthread_mutex_t round_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t round_cond = PTHREAD_COND_INITIALIZER;
static int has_eaten[PHILOSOPHER_COUNT] = {0};
static int eaten_count = 0;
static int current_round = 1;

static void wait_for_turn_in_round(int philosopher_id, int *round_to_eat) {
    pthread_mutex_lock(&round_mutex);
    while (has_eaten[philosopher_id]) {
        pthread_cond_wait(&round_cond, &round_mutex);
    }
    *round_to_eat = current_round;
    pthread_mutex_unlock(&round_mutex);
}

static void finish_eating_in_round(int philosopher_id) {
    pthread_mutex_lock(&round_mutex);
    if (!has_eaten[philosopher_id]) {
        has_eaten[philosopher_id] = 1;
        eaten_count++;
    }

    if (eaten_count == PHILOSOPHER_COUNT) {
        printf("======== Round %d finished: every philosopher has eaten once ========\n",
               current_round);
        fflush(stdout);
        for (int i = 0; i < PHILOSOPHER_COUNT; i++) {
            has_eaten[i] = 0;
        }
        eaten_count = 0;
        current_round++;
        pthread_cond_broadcast(&round_cond);
    }
    pthread_mutex_unlock(&round_mutex);
}

static void take_forks(int philosopher_id) {
    int left = philosopher_id;
    int right = (philosopher_id + 1) % PHILOSOPHER_COUNT;
    int first = left < right ? left : right;
    int second = left < right ? right : left;

    sem_wait(&forks[first]);
    sem_wait(&forks[second]);
}

static void put_forks(int philosopher_id) {
    int left = philosopher_id;
    int right = (philosopher_id + 1) % PHILOSOPHER_COUNT;

    sem_post(&forks[left]);
    sem_post(&forks[right]);
}

static void *philosopher(void *arg) {
    int philosopher_id = *(int *)arg;

    while (1) {
        int round_to_eat;
        wait_for_turn_in_round(philosopher_id, &round_to_eat);
        if (round_to_eat > MAX_ROUNDS) {
            break;
        }

        usleep((useconds_t)(10000 * (philosopher_id + 1)));
        take_forks(philosopher_id);

        printf("Round %d: philosopher %d is eating.\n", round_to_eat, philosopher_id);
        fflush(stdout);
        usleep(30000);

        put_forks(philosopher_id);
        finish_eating_in_round(philosopher_id);
    }

    return NULL;
}

int main(void) {
    pthread_t threads[PHILOSOPHER_COUNT];
    int philosopher_ids[PHILOSOPHER_COUNT];

    for (int i = 0; i < PHILOSOPHER_COUNT; i++) {
        if (sem_init(&forks[i], 0, 1) != 0) {
            perror("sem_init");
            return EXIT_FAILURE;
        }
    }

    for (int i = 0; i < PHILOSOPHER_COUNT; i++) {
        philosopher_ids[i] = i;
        if (pthread_create(&threads[i], NULL, philosopher, &philosopher_ids[i]) != 0) {
            perror("pthread_create");
            return EXIT_FAILURE;
        }
    }

    for (int i = 0; i < PHILOSOPHER_COUNT; i++) {
        pthread_join(threads[i], NULL);
        sem_destroy(&forks[i]);
    }

    pthread_mutex_destroy(&round_mutex);
    pthread_cond_destroy(&round_cond);

    printf("All philosophers finish %d fair rounds.\n", MAX_ROUNDS);
    return EXIT_SUCCESS;
}
