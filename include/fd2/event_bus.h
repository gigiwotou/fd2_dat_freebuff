#ifndef FD2_EVENT_BUS_H
#define FD2_EVENT_BUS_H

#include "fd2/types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Event Bus ---- */

#define FD2_MAX_EVENT_SUBSCRIBERS 64

typedef struct {
    fd2_event_type_t   type;
    fd2_event_handler_t handler;
    void*              user_data;
    bool               active;
} fd2_event_subscription_t;

typedef struct {
    fd2_event_subscription_t subscribers[FD2_MAX_EVENT_SUBSCRIBERS];
    int                      subscriber_count;
    fd2_event_t              pending[FD2_MAX_EVENT_SUBSCRIBERS];
    int                      pending_count;
    u32                      tick;
} fd2_event_bus_t;

/* Initialize the event bus */
void fd2_event_bus_init(fd2_event_bus_t* bus);

/* Shutdown the event bus */
void fd2_event_bus_shutdown(fd2_event_bus_t* bus);

/* Subscribe to an event type */
int fd2_event_bus_subscribe(fd2_event_bus_t* bus,
                            fd2_event_type_t type,
                            fd2_event_handler_t handler,
                            void* user_data);

/* Unsubscribe from all events for a given handler */
void fd2_event_bus_unsubscribe(fd2_event_bus_t* bus,
                               fd2_event_handler_t handler);

/* Publish an event to the bus (queued for processing) */
void fd2_event_bus_publish(fd2_event_bus_t* bus,
                           fd2_event_type_t type,
                           const void* data,
                           size_t data_size);

/* Process all pending events (call in main loop) */
void fd2_event_bus_process(fd2_event_bus_t* bus);

/* Get current event bus tick */
u32 fd2_event_bus_get_tick(const fd2_event_bus_t* bus);

/* Advance the event bus tick (call once per game tick) */
void fd2_event_bus_advance_tick(fd2_event_bus_t* bus);

#ifdef __cplusplus
}
#endif

#endif /* FD2_EVENT_BUS_H */
