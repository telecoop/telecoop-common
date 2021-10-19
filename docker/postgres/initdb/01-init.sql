CREATE TABLE subscription (
  id serial PRIMARY KEY,
  create_date timestamptz NOT NULL DEFAULT now(),
  sellsy_opportunity_id int UNIQUE NOT NULL,
  sellsy_ticket_id int,
  bazile_result_date timestamptz,
  bazile_order_num int,
  bazile_account_id text,
  bazile_return_code int,
  bazile_return_label text,
  bazile_errors text
);
