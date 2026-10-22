import { useMemo, useState } from 'react'
import type { EventView } from '../../api/types'
import './EventLog.css'
import './runs.css'

export type EventLogProps = { events: EventView[] }

function EventLog({ events }: EventLogProps) {
  const [eventTypeFilter, setEventTypeFilter] = useState('')
  const [taskFilter, setTaskFilter] = useState('')
  const eventTypes = useMemo(() => Array.from(new Set(events.map((event) => event.event_type))), [events])
  const normalizedTaskFilter = taskFilter.trim().toLowerCase()
  const visibleEvents = events.filter((event) => {
    if (eventTypeFilter && event.event_type !== eventTypeFilter) return false
    if (!normalizedTaskFilter) return true
    return [event.task_run_id, event.attempt_id]
      .filter((value): value is string => value !== null)
      .some((value) => value.toLowerCase().includes(normalizedTaskFilter))
  })
  const clearFilters = () => {
    setEventTypeFilter('')
    setTaskFilter('')
  }

  return (
    <section aria-labelledby="event-log-heading" className="event-log">
      <h2 id="event-log-heading">Event log</h2>
      <div className="event-log__filters" aria-label="Event log filters">
        <label htmlFor="event-type-filter">Event type</label>
        <select id="event-type-filter" value={eventTypeFilter} onChange={(event) => setEventTypeFilter(event.target.value)}>
          <option value="">All event types</option>
          {eventTypes.map((eventType) => <option key={eventType} value={eventType}>{eventType}</option>)}
        </select>
        <label htmlFor="event-task-filter">Task text</label>
        <input
          id="event-task-filter"
          type="search"
          value={taskFilter}
          onChange={(event) => setTaskFilter(event.target.value)}
          placeholder="Search task or attempt"
        />
        <button type="button" onClick={clearFilters} disabled={!eventTypeFilter && !taskFilter}>Clear filters</button>
      </div>
      {events.length === 0
        ? <p>No events recorded.</p>
        : visibleEvents.length === 0
          ? <p>No events match the current filters.</p>
          : <ol className="event-log__items">
          {visibleEvents.map((event) => (
            <li key={event.id}>
              <div className="event-log__summary">
                <time dateTime={event.created_at}>{event.created_at}</time>
                <strong>{event.event_type}</strong>
                {event.task_run_id && <span>Task: {event.task_run_id}</span>}
                {event.attempt_id && <span>Attempt: {event.attempt_id}</span>}
              </div>
              <details>
                <summary>Payload</summary>
                <pre>{JSON.stringify(event.payload, null, 2)}</pre>
              </details>
            </li>
          ))}
        </ol>}
    </section>
  )
}

export default EventLog
