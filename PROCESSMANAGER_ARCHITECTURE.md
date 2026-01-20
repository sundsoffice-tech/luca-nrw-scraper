# ProcessManager Architecture

## Before Refactoring (Monolithic)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                   ProcessManager                        │
│                    (942 lines)                          │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │ • Script finding & command building            │   │
│  │ • Process start/stop                           │   │
│  │ • Output reading & logging                     │   │
│  │ • Error tracking & retry logic                 │   │
│  │ • Circuit breaker management                   │   │
│  │ • Configuration loading                        │   │
│  │ • Status aggregation                           │   │
│  └────────────────────────────────────────────────┘   │
│                                                         │
│  ❌ Tight coupling                                      │
│  ❌ Hard to test                                        │
│  ❌ Difficult to maintain                               │
│  ❌ Single responsibility violation                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## After Refactoring (Composition Pattern)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                      ProcessManager                                 │
│                       (~600 lines)                                  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Orchestration Layer                                       │   │
│  │  • Coordinates all components                              │   │
│  │  • Manages overall process lifecycle                       │   │
│  │  • Aggregates status from components                       │   │
│  │  • Maintains backward compatibility                        │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ ProcessLauncher  OutputMonitor │  RetryController │            │
│  │   (224 lines)│  │  (219 lines) │  │  (248 lines) │            │
│  │              │  │              │  │              │            │
│  │ • Find script│  │ • Read output│  │ • Track errors│            │
│  │ • Build cmd  │  │ • Store logs │  │ • Calc backoff│            │
│  │ • Start proc │  │ • Detect err │  │ • Schedule    │            │
│  │ • Stop proc  │  │ • Persist DB │  │   retries     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │               CircuitBreaker                             │     │
│  │                (205 lines)                               │     │
│  │                                                          │     │
│  │  • Manage states (CLOSED/OPEN/HALF_OPEN)                │     │
│  │  • Track failures                                        │     │
│  │  • Auto transitions                                      │     │
│  │  • Penalty management                                    │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ✅ Loose coupling via composition                                 │
│  ✅ Each component independently testable                          │
│  ✅ Easy to maintain and extend                                    │
│  ✅ Follows single responsibility principle                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Interactions

```
┌──────────────┐
│   External   │
│    Caller    │
└───────┬──────┘
        │ start(params, user)
        ▼
┌────────────────────────────┐
│    ProcessManager          │
│  (Orchestration Layer)     │
└─┬──────────┬───────┬───────┘
  │          │       │
  │ 1. Check circuit breaker
  │          │       │
  ▼          │       │
┌────────────────┐  │
│ CircuitBreaker │  │
│ • check_and_   │  │
│   update()     │  │
└────────────────┘  │
  │                 │
  │ 2. Find & build command
  │                 │
  ▼                 │
┌─────────────────┐ │
│ ProcessLauncher │ │
│ • find_script() │ │
│ • build_cmd()   │ │
│ • start_proc()  │ │
└─────────────────┘ │
  │                 │
  │ 3. Start monitoring
  │                 │
  ▼                 │
┌─────────────────┐ │
│ OutputMonitor   │ │
│ • start_        │ │
│   monitoring()  │ │
│ • error_callback│ │
│ • completion_   │ │
│   callback      │ │
└────────┬────────┘ │
         │          │
         │ 4a. On error detected
         ▼          │
    ┌────────────────────┐
    │ ProcessManager     │
    │ _handle_error()    │
    └─┬──────────────┬───┘
      │              │
      ▼              ▼
┌──────────────┐ ┌────────────────┐
│RetryController│ │ CircuitBreaker │
│• track_error()│ │ • record_      │
│              │ │   failure()    │
└──────────────┘ └────────────────┘
      │
      │ 4b. Schedule retry if needed
      ▼
┌──────────────────┐
│ RetryController  │
│ • should_retry() │
│ • schedule_retry()│
└──────────────────┘
      │
      │ After backoff delay
      └──────┐
             │
             ▼
       ┌────────────────┐
       │ ProcessManager │
       │ start() again  │
       └────────────────┘
```

## Data Flow: Error Handling & Recovery

```
┌─────────────────────────────────────────────────────────────┐
│                    Process Running                          │
│                                                             │
│  ┌──────────────┐                                          │
│  │ OutputMonitor│                                          │
│  │  reads output│                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         │ Detects error in log                             │
│         ▼                                                   │
│  ┌─────────────────────┐                                   │
│  │ Error callback:     │                                   │
│  │ _handle_error(type) │                                   │
│  └─────────┬───────────┘                                   │
│            │                                                │
│      ┌─────┴─────┐                                         │
│      │           │                                         │
│      ▼           ▼                                         │
│  ┌────────┐  ┌─────────┐                                  │
│  │ Retry  │  │ Circuit │                                  │
│  │Control │  │ Breaker │                                  │
│  └────┬───┘  └────┬────┘                                  │
│       │           │                                        │
│       │ track_    │ record_                                │
│       │ error()   │ failure()                              │
│       │           │                                        │
│       ▼           ▼                                        │
│  Error count   Failure count                               │
│  increases     increases                                   │
│       │           │                                        │
│       │           │ Threshold?                             │
│       │           ├─ No ──► Continue                       │
│       │           │                                        │
│       │           └─ Yes ─► Open Circuit                   │
│       │                     Breaker                        │
│       │                                                    │
│       │ Should retry?                                      │
│       ├─ No ──► Stop                                       │
│       │                                                    │
│       └─ Yes ─► Schedule Retry                             │
│                 (with backoff)                             │
│                      │                                     │
│                      │ Wait...                             │
│                      │                                     │
│                      ▼                                     │
│                 Retry Start                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## State Diagram: Circuit Breaker

```
                    ┌─────────────┐
                    │   CLOSED    │
                    │  (Normal)   │
                    └──────┬──────┘
                           │
                           │ failures >= threshold
                           ▼
                    ┌─────────────┐
                    │    OPEN     │◄───────┐
                    │  (Blocking) │        │
                    └──────┬──────┘        │
                           │               │
                           │ penalty       │ More
                           │ timeout       │ failures
                           ▼               │
                    ┌─────────────┐        │
                    │  HALF_OPEN  │────────┘
                    │  (Testing)  │
                    └──────┬──────┘
                           │
                           │ success
                           ▼
                    ┌─────────────┐
                    │   CLOSED    │
                    │  (Normal)   │
                    └─────────────┘
```

## Component Responsibilities

### ProcessLauncher
- **Input**: Parameters, environment
- **Output**: Running process
- **Responsibilities**:
  - Locate scraper script
  - Build command with parameters
  - Manage subprocess lifecycle
  - Handle environment variables

### OutputMonitor
- **Input**: Process stdout
- **Output**: Logs, error notifications
- **Responsibilities**:
  - Read process output in background thread
  - Buffer logs in memory
  - Persist logs to database
  - Detect and classify errors
  - Notify on errors and completion

### RetryController
- **Input**: Error events
- **Output**: Retry decisions, adjusted parameters
- **Responsibilities**:
  - Track errors by type
  - Calculate error rates
  - Determine retry eligibility
  - Calculate exponential backoff
  - Adjust parameters (e.g., QPI reduction)
  - Schedule automatic retries

### CircuitBreaker
- **Input**: Failure/success events
- **Output**: Allow/block decisions
- **Responsibilities**:
  - Track failure count
  - Manage state transitions
  - Enforce penalty periods
  - Allow test operations in HALF_OPEN
  - Reset on success

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Lines per component** | 942 | 205-248 avg |
| **Cohesion** | Low | High |
| **Coupling** | High | Low |
| **Testability** | Difficult | Easy |
| **Maintainability** | Hard | Easy |
| **Reusability** | None | High |
| **Clarity** | Mixed concerns | Clear responsibilities |
| **Breaking changes** | N/A | None (backward compatible) |
