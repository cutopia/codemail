
# Codemail Todo List

## Requirements
- [ ] Secure email monitoring with allowed sender/recipient configuration
- [ ] Subject format validation: codemail:[<projectnamehere>]
- [ ] Coding agent capable of making bash calls
- [ ] Mechanism to recover from hanging bash calls (timeouts)
- [ ] Local LLM integration (LM Studio)
- [ ] Email reporting via SMTP
- [ ] Task queue management (Celery/Redis)
- [ ] Status API for monitoring tasks (FastAPI)

## Implementation Phases
### Phase 1: Core Email Processing
- [ ] Configuration system (.env)
- [ ] IMAP listener for incoming emails
- [ ] Email parsing logic (extract project name and body)
- [ ] Basic LLM client implementation
- [ ] SMTP sender for reports
- [ ] Integration test: Email -> LLM -> Email

### Phase 2: Task Queue Foundation
- [ ] Redis installation/setup guide
- [ ] Celery task configuration
- [ ] Database schema for tasks (UUID, status, project)
- [ ] Sequential processing logic

### Phase 3: Agent Loop Enhancement
- [ ] Iterative agent loop implementation
- [ ] Bash execution tool with timeout/recovery
- [ ] Context management (history of bash calls)

### Phase 4: Concurrency & Status API
- [ ] FastAPI endpoint for queue status
- [ ] Endpoint to stop specific tasks
- [ ] Integration with Celery for real-time updates
