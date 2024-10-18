CREATE SCHEMA monitoring;
CREATE TABLE monitoring.service_log (
  id serial PRIMARY KEY,
  service_name text NOT NULL,
  start_date timestamptz NOT NULL DEFAULT now(),
  end_date timestamptz,
  status text,
  error_message text,
  ack_date timestamptz
);

CREATE VIEW monitoring.v_service_log AS
SELECT id,
       service_name,
       start_date,
       end_date,
       round(extract(epoch from (end_date - start_date))::numeric, 2) AS duration_s,
       date_trunc('second', end_date - start_date + interval '0.5 seconds') AS duration,
       status,
       substring(error_message, 1, 30) AS error,
       ack_date
  FROM monitoring.service_log;

CREATE VIEW monitoring.v_failed_log AS
SELECT id,
       service_name,
       start_date,
       end_date,
       duration_s,
       duration,
       status,
       error
  FROM monitoring.v_service_log
 WHERE status = 'error'
   AND ack_date IS NULL;
