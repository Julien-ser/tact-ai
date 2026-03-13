-- Tact AI Database Initialization Script
-- This script runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create additional indexes for better performance (beyond Alembic migrations)
-- These are production optimizations

-- Tasks table indexes for common query patterns
-- Note: Single-column indexes are created by Alembic migrations
-- These composite indexes optimize common query patterns
CREATE INDEX IF NOT EXISTS idx_tasks_user_completed ON tasks(user_id, completed);
CREATE INDEX IF NOT EXISTS idx_tasks_user_priority ON tasks(user_id, priority);
CREATE INDEX IF NOT EXISTS idx_tasks_user_quadrant ON tasks(user_id, quadrant);
CREATE INDEX IF NOT EXISTS idx_tasks_user_due_date ON tasks(user_id, due_date);

-- Task chains indexes (using actual column names from schema)
CREATE INDEX IF NOT EXISTS idx_task_chains_task_id ON task_chains(task_id);
CREATE INDEX IF NOT EXISTS idx_task_chains_prerequisite_task_id ON task_chains(prerequisite_task_id);

-- Timelines indexes
CREATE INDEX IF NOT EXISTS idx_timelines_user_generated ON timelines(user_id, generated_at DESC);

-- Time blocks indexes (using actual column names: day_of_week, start_time, end_time)
CREATE INDEX IF NOT EXISTS idx_time_blocks_user_day ON time_blocks(user_id, day_of_week);

-- Auth-related indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Comments for documentation
COMMENT ON EXTENSION "uuid-ossp" IS 'Provides UUID generation functions';
COMMENT ON EXTENSION "pg_stat_statements" IS 'Tracks execution statistics of all SQL statements';
