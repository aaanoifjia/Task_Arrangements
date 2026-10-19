import type { EventView } from '../../api/types'
import './EventLog.css'

export type EventLogProps = { events: EventView[] }

function EventLog({ events }: EventLogProps) {
  return (
    <section aria-labelledby="event-log-heading" className="event-log">
      <h2 id="event-log-heading">Event log</h2>
      {events.length === 0
        ? <p>No events recorded.</p>
        : <ol className="event-log__items">
          {events.map((event) => (
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
