-- Tact AI Database Initialization Script
-- This script runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create additional indexes for better performance (beyond Alembic migrations)
-- These are production optimizations

-- Tasks table indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_user_due_date ON tasks(user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_user_quadrant ON tasks(user_id, quadrant);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- Task chains indexes
CREATE INDEX IF NOT EXISTS idx_task_chains_from_task ON task_chains(from_task_id);
CREATE INDEX IF NOT EXISTS idx_task_chains_to_task ON task_chains(to_task_id);

-- Timelines indexes
CREATE INDEX IF NOT EXISTS idx_timelines_user_date ON timelines(user_id, generated_at DESC);

-- Time blocks indexes
CREATE INDEX IF NOT EXISTS idx_time_blocks_user_date ON time_blocks(user_id, start_date, end_date);

-- Auth-related indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Comments for documentation
COMMENT ON EXTENSION "uuid-ossp" IS 'Provides UUID generation functions';
COMMENT ON EXTENSION "pg_stat_statements" IS 'Tracks execution statistics of all SQL statements';
