/**
 * Event Bus Implementation
 * Publish/Subscribe system for decoupled game system communication.
 */

#define _GNU_SOURCE
#include "fd2/event_bus.h"
#include <string.h>
#include <stdio.h>

void fd2_event_bus_init(fd2_event_bus_t* bus) {
    memset(bus, 0, sizeof(*bus));
}

void fd2_event_bus_shutdown(fd2_event_bus_t* bus) {
    memset(bus, 0, sizeof(*bus));
}

int fd2_event_bus_subscribe(fd2_event_bus_t* bus,
                            fd2_event_type_t type,
                            fd2_event_handler_t handler,
                            void* user_data) {
    if (!bus || !handler) return -1;
    if (bus->subscriber_count >= FD2_MAX_EVENT_SUBSCRIBERS) return -1;

    fd2_event_subscription_t* sub = &bus->subscribers[bus->subscriber_count];
    sub->type       = type;
    sub->handler    = handler;
    sub->user_data  = user_data;
    sub->active     = true;

    int id = bus->subscriber_count;
    bus->subscriber_count++;
    return id;
}

void fd2_event_bus_unsubscribe(fd2_event_bus_t* bus,
                               fd2_event_handler_t handler) {
    if (!bus || !handler) return;

    for (int i = 0; i < bus->subscriber_count; i++) {
        if (bus->subscribers[i].handler == handler) {
            bus->subscribers[i].active = false;
        }
    }
}

void fd2_event_bus_publish(fd2_event_bus_t* bus,
                           fd2_event_type_t type,
                           const void* data,
                           size_t data_size) {
    if (!bus) return;
    if (bus->pending_count >= FD2_MAX_EVENT_SUBSCRIBERS) {
        fprintf(stderr, "event_bus: event queue full, dropping event %d\n", type);
        return;
    }

    fd2_event_t* event = &bus->pending[bus->pending_count];
    event->type      = type;
    event->timestamp = bus->tick;

    if (data && data_size > 0) {
        size_t copy_size = data_size < EVENT_DATA_SIZE ? data_size : EVENT_DATA_SIZE;
        memcpy(event->data, data, copy_size);
        if (copy_size < EVENT_DATA_SIZE) {
            memset(event->data + copy_size, 0, EVENT_DATA_SIZE - copy_size);
        }
    } else {
        memset(event->data, 0, EVENT_DATA_SIZE);
    }

    bus->pending_count++;
}

void fd2_event_bus_process(fd2_event_bus_t* bus) {
    if (!bus || bus->pending_count == 0) return;

    int pending = bus->pending_count;
    bus->pending_count = 0;

    for (int i = 0; i < pending; i++) {
        fd2_event_t* event = &bus->pending[i];

        for (int j = 0; j < bus->subscriber_count; j++) {
            fd2_event_subscription_t* sub = &bus->subscribers[j];
            if (!sub->active) continue;

            if (sub->type == event->type || sub->type == EVENT_NONE) {
                sub->handler(event, sub->user_data);
            }
        }
    }
}

u32 fd2_event_bus_get_tick(const fd2_event_bus_t* bus) {
    return bus ? bus->tick : 0;
}

void fd2_event_bus_advance_tick(fd2_event_bus_t* bus) {
    if (bus) bus->tick++;
}
