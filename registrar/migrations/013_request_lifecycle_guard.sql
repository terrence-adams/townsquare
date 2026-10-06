-- The controlled Request lifecycle has exactly six states. Existing immutable
-- rows are not rewritten; the service parks any obsolete current state, and
-- this guard prevents new out-of-contract Request rows at the storage seam.
CREATE TRIGGER ledger_events_request_state_guard
BEFORE INSERT ON ledger_events
WHEN NEW.kind = 'REQUEST'
 AND NEW.state NOT IN ('OPEN','WORKING','BLOCKED','RESOLVED','CLOSED','CANCELLED')
BEGIN
  SELECT RAISE(ABORT,'unsupported Request lifecycle state');
END;
