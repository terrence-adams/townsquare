CREATE TRIGGER roots_opening_null_insert BEFORE INSERT ON roots WHEN NEW.opening_post_uid IS NOT NULL BEGIN SELECT RAISE(ABORT,'opening_post_uid must be NULL on root insert'); END;
