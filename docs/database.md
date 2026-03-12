# Database Schema

## Overview

The Tact AI database uses PostgreSQL with SQLAlchemy ORM. The schema consists of 6 main tables that support task management, scheduling, and AI-driven organization based on the Eisenhower Matrix.

## Entity Relationship Diagram

```
┌─────────────────┐          1 ┌─────────────────────────────────────────┐
│    users       │◄───────────┤│              tasks                      │
├─────────────────┤           └─────────────────────────────────────────┘
│ id (PK)        │               │ id (PK)                               │
│ email          │               │ user_id (FK → users.id)               │
│ hashed_password│               │ title                                 │
│ is_active      │               │ description                           │
│ created_at     │               │ quadrant (ENUM: Q1,Q2,Q3,Q4)          │
│ updated_at     │               │ priority (ENUM: low,med,high,crit)    │
└─────────────────┘               │ estimated_duration (minutes)          │
       │ 1                        │ due_date                              │
       │                         │ completed (bool)                      │
       │                         │ created_at                            │
       │                         │ updated_at                            │
       │ N                       └─────────────────────────────────────┘
       │                               │ 1
       │ N                              │ N
┌─────────────────┐           ┌─────────┴────────────────────────────┐
│   time_blocks   │           │                                      │
├─────────────────┤           │      task_chains                     │
│ id (PK)        │           │      (junction/relationship)        │
│ user_id (FK)   │◄──────────┤                                      │
│ day_of_week    │           ├──────────────────────────────────────┤
│ start_time     │           │ id (PK)                              │
│ end_time       │           │ task_id (FK → tasks.id)              │
└─────────────────┘           │ prerequisite_task_id (FK → tasks.id) │
                              │ relationship_type (ENUM)             │
                              └──────────────────────────────────────┘
                                         ▲
                                         │ N
┌─────────────────┐           ┌─────────┴────────────────────────────┐
│   timelines     │           │                                      │
├─────────────────┤           │      timeline_tasks                 │
│ id (PK)        │           │      (junction with scheduling)     │
│ user_id (FK)   │◄──────────┤                                      │
│ name           │           ├──────────────────────────────────────┤
│ start_date     │           │ id (PK)                              │
│ end_date       │           │ timeline_id (FK → timelines.id)     │
│ generated_at   │           │ task_id (FK → tasks.id)             │
│ schedule_data  │           │ scheduled_start (datetime)          │
└─────────────────┘           │ scheduled_end (datetime)            │
                              │ created_at                           │
                              └──────────────────────────────────────┘
```

## Legend
- **PK**: Primary Key
- **FK**: Foreign Key
- **ENUM**: Enumerated Type
- **1**: One
- **N**: Many
- **◄───**: CASCADE on delete

## Table Details

### 1. users

Stores user account information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email (login) |
| hashed_password | VARCHAR | NOT NULL | Bcrypt hashed password |
| is_active | BOOLEAN | DEFAULT true | Account status |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | ON UPDATE NOW() | Last update timestamp |

**Indexes:** `users.id` (PK), `users.email` (unique)
**Relationships:**
- 1:N with `tasks`
- 1:N with `timelines`
- 1:N with `time_blocks`

---

### 2. tasks

Core task entity with Eisenhower Matrix classification.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique task identifier |
| user_id | INTEGER | FK → users.id (CASCADE), NOT NULL | Task owner |
| title | VARCHAR(255) | NOT NULL | Task title |
| description | TEXT | NULL | Detailed description |
| quadrant | quadrant_enum (ENUM) | NOT NULL | Eisenhower quadrant: Q1 (urgent+important), Q2 (not urgent+important), Q3 (urgent+not important), Q4 (not urgent+not important) |
| priority | priority_enum (ENUM) | DEFAULT 'medium' | Priority level: low, medium, high, critical |
| estimated_duration | INTEGER | NULL | Estimated duration in minutes |
| due_date | TIMESTAMPTZ | NULL | Task deadline |
| completed | BOOLEAN | DEFAULT false | Completion status |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | ON UPDATE NOW() | Last update timestamp |

**Indexes:** PK on `id`, `tasks.user_id`, `tasks.due_date`, `tasks.completed`, `tasks.quadrant`, `tasks.priority`
**Relationships:**
- N:1 with `users`
- N:1 as `task_id` in `task_chains`
- N:1 as `prerequisite_task_id` in `task_chains`
- 1:N as `task_id` in `timeline_tasks`

---

### 3. task_chains

Junction table defining task dependencies and relationships.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique chain identifier |
| task_id | INTEGER | FK → tasks.id (CASCADE), NOT NULL | Dependent task |
| prerequisite_task_id | INTEGER | FK → tasks.id (CASCADE), NOT NULL | Prerequisite task |
| relationship_type | relationship_type_enum (ENUM) | DEFAULT 'depends_on' | Type: depends_on, blocks, relates_to |

**Indexes:** PK on `id`, `task_chains.task_id`, `task_chains.prerequisite_task_id`
**Composite Index:** (`task_id`, `prerequisite_task_id`) - implicit via PK but also has separate indexes
**Relationships:**
- N:1 `task` via `task_id`
- N:1 `prerequisite_task` via `prerequisite_task_id`

**Business Rules:**
- A task can have multiple prerequisites (incoming edges in dependency graph)
- A task can be a prerequisite for multiple tasks (outgoing edges)
- Circular dependencies must be detected by application logic

---

### 4. timelines

Generated schedule snapshots containing a set of scheduled tasks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique timeline identifier |
| user_id | INTEGER | FK → users.id (CASCADE), NOT NULL | Timeline owner |
| name | VARCHAR(255) | NULL | Timeline name (e.g., "Week of March 10") |
| start_date | TIMESTAMPTZ | NOT NULL | Timeline start (inclusive) |
| end_date | TIMESTAMPTZ | NOT NULL | Timeline end (exclusive or inclusive) |
| generated_at | TIMESTAMPTZ | DEFAULT NOW() | When timeline was generated |
| schedule_data | TEXT | NULL | Full schedule as JSON blob (optimization for quick retrieval) |

**Indexes:** PK on `id`, `timelines.user_id`, `timelines.start_date`, `timelines.end_date`
**Relationships:**
- N:1 with `users`
- 1:N with `timeline_tasks`

---

### 5. timeline_tasks

Junction table storing the actual scheduled times for tasks within a timeline. This is the output of the AI scheduler.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique timeline task identifier |
| timeline_id | INTEGER | FK → timelines.id (CASCADE), NOT NULL | Parent timeline |
| task_id | INTEGER | FK → tasks.id (CASCADE), NOT NULL | Scheduled task |
| scheduled_start | TIMESTAMPTZ | NOT NULL | When task starts |
| scheduled_end | TIMESTAMPTZ | NOT NULL | When task ends |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |

**Indexes:** PK on `id`, `timeline_tasks.timeline_id`, `timeline_tasks.task_id`, `timeline_tasks.scheduled_start`
**Unique Constraint:** `(timeline_id, task_id)` - prevents duplicate task assignments in same timeline
**Relationships:**
- N:1 with `timelines`
- N:1 with `tasks`

---

### 6. time_blocks

User-defined working hours and availability blocks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Unique time block identifier |
| user_id | INTEGER | FK → users.id (CASCADE), NOT NULL | Block owner |
| day_of_week | day_of_week_enum (ENUM) | NOT NULL | Day: 0=Monday, 6=Sunday |
| start_time | TIME | NOT NULL | Block start time (e.g., 09:00:00) |
| end_time | TIME | NOT NULL | Block end time (e.g., 17:00:00) |

**Indexes:** PK on `id`, `time_blocks.user_id`, `time_blocks.day_of_week`
**Relationships:**
- N:1 with `users`
- One user can have multiple blocks per day (range partitioning supported)

**Business Rules:**
- Blocks define when the AI scheduler can assign tasks
- Multiple blocks per day allow for split workdays (e.g., 9-12 and 13-17)
- Blocks are recurring weekly

---

## Enumerated Types

All enums are PostgreSQL ENUM types for type safety and storage efficiency:

1. **quadrant_enum**: `Q1`, `Q2`, `Q3`, `Q4`
2. **priority_enum**: `low`, `medium`, `high`, `critical`
3. **relationship_type_enum**: `depends_on`, `blocks`, `relates_to`
4. **day_of_week_enum**: `0`, `1`, `2`, `3`, `4`, `5`, `6` (ISO Monday=0)

---

## Database Constraints & Rules

### Referential Integrity
All foreign keys use `ON DELETE CASCADE` to ensure automatic cleanup:
- When a user is deleted, all their tasks, timelines, and time_blocks are removed
- When a task is deleted, all `task_chains` entries referencing it are removed
- When a timeline is deleted, all `timeline_tasks` entries are removed
- When a task is deleted, all `timeline_tasks` references become invalid (CASCADE)

### Business Logic Constraints (Application-Level)
- **Task Dependencies**: Circular dependency detection must be implemented in `backend/scheduler/dependency.py`
- **Timeline Overlap**: Tasks in `timeline_tasks` may not overlap for the same user (checked by scheduler)
- **Due Dates**: Tasks with `due_date` must be scheduled to complete before the deadline
- **Time Block Respect**: Scheduler must only schedule tasks within user's defined `time_blocks`

---

## Migration Strategy

Alembic is configured in the `backend/` directory. The initial migration (`20260312_000001_initial_schema.py`) creates all tables, indexes, constraints, and enum types.

### Applying Migrations

```bash
cd backend
alembic upgrade head
```

### Generating New Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Rolling Back

```bash
cd backend
alembic downgrade -1  # one step
alembic downgrade base  # all migrations
```

---

## Performance Considerations

### Indexes
The following indexes are included in the initial schema:
- Foreign key indexes (most are auto-created by PostgreSQL but explicitly added for clarity)
- `tasks.user_id` - fast lookup of user's tasks
- `tasks.due_date` - deadline-based queries
- `tasks.completed` - filter for incomplete tasks
- `tasks.quadrant` & `tasks.priority` - Eisenhower matrix filtering
- `timeline_tasks.scheduled_start` - timeline query optimization
- `time_blocks.day_of_week` - weekly schedule queries

### Future Optimizations
- Consider partitioning large tables (e.g., `timeline_tasks`) by `scheduled_start` date
- Add composite index on `tasks(user_id, completed, due_date)` for common task list queries
- Consider full-text search on `tasks.title` and `tasks.description` if search requirements grow
- Add covering indexes for frequent query patterns after profiling

---

## Data Retention & Archiving

No automatic archiving is implemented. Application logic should consider:
- Moving completed tasks older than 90 days to an `archived_tasks` table if needed
- Purging or exporting timelines older than N months for compliance
- Implementing soft delete (`is_deleted` flag) if reversibility is required

---

## Connection Pooling

Uses SQLAlchemy's default pooling. For production, configure appropriate pool size in `backend/database/__init__.py`:
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```
