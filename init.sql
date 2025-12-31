-- Tasker Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_name VARCHAR(100) NOT NULL,
    task_parameters JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    task_output JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_task_name ON tasks(task_name);

-- Add constraint for valid status values
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS chk_tasks_status;
ALTER TABLE tasks ADD CONSTRAINT chk_tasks_status
    CHECK (status IN ('pending', 'running', 'completed', 'failed'));

COMMENT ON TABLE tasks IS 'Stores async task submissions and their results';
COMMENT ON COLUMN tasks.id IS 'Unique task identifier (UUID)';
COMMENT ON COLUMN tasks.task_name IS 'Type of task: sum, query_llm, file_hash';
COMMENT ON COLUMN tasks.task_parameters IS 'JSON input parameters for the task';
COMMENT ON COLUMN tasks.status IS 'Current state: pending, running, completed, failed';
COMMENT ON COLUMN tasks.task_output IS 'JSON result after task completion';
COMMENT ON COLUMN tasks.error IS 'Error message if task failed';
