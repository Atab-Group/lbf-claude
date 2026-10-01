---
name: tasks
description: Use when the person asks about LBF tasks: what they or someone else has on, what is overdue or unassigned, or wants to create, edit, assign, move or delete a task.
---

# The task board

Read `lbf-platform` first if you have not this session.

## Reading

- `list_tasks` answers anything across clients or about a person: `assignee` (a name, a user id, or
  `unassigned`), `createdBy`, `statuses`, `overdueOnly`, `dueBefore`/`dueAfter`, `dueInMonth`, `noClient`
  and `search`. They combine.
- `get_tasks` is one client's board.
- "Overdue" means the due date is before today in South African time, whatever the status. Pass
  `statuses: ["todo","doing"]` with `overdueOnly` for what is actually late.
- `list_users` turns a name into a user id when a name is ambiguous.

## Changing

Each change is a job: poll `get_job` until `done`.

- `create_task`: `clientRef`, `title`, optional `description`, `assigneeId` (from `list_users`) and
  `dueDate` (`YYYY-MM-DD`).
- `update_task`: title, description or due date. `set_task_status`: `todo`, `doing` or `done` (there is
  no blocked column). `assign_task`: a user id, or leave it out to unassign.
- `delete_task` cannot be undone. Only delete when the person clearly asked, and name the task back to
  them first.
- Agency tasks with no client cannot be changed from here.

When listing tasks, group by client or person, show the due date, and put overdue ones first.
