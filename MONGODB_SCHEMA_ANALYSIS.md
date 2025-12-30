# MongoDB Schema Analysis & Recommendations for ClauseClear

## Executive Summary

The current ERD schema is **overly normalized for MongoDB** (designed for relational databases) and misses several critical entities. This document provides MongoDB-optimized recommendations with justifications for a production deployment.

---

## 1. Issues with Current Schema Design

### 1.1 Over-Normalization (Anti-Pattern for MongoDB)

**Problem**: The schema uses separate collections with foreign key relationships, which is inefficient for MongoDB:

- ❌ **Separate `clauses` collection**: Clauses are small, document-specific, and rarely queried independently
- ❌ **Separate `flags` collection**: Flags are tightly coupled to clauses and should be embedded
- ❌ **Separate `analytics` collection**: Analytics are tied to specific jobs and should be embedded or aggregated

**MongoDB Best Practice**: Embed data that is:
- Accessed together (clauses + flags + analytics per document)
- Not queried independently
- Small to medium size (<16MB document limit)

### 1.2 Missing Critical Collections

Based on the current implementation and production requirements, the following are **missing**:

1. **Sessions/Conversations Collection** - For managing multi-turn conversations
2. **Complete Chat Messages Collection** - Currently only stored as array in jobs (limited querying)
3. **Document Versions/History** - For tracking document re-uploads or updates
4. **User Preferences/Settings** - Language, notification preferences
5. **Audit Logs** - For compliance and debugging
6. **Index Metadata** - For TF-IDF index management and versioning

---

## 2. Recommended MongoDB Schema Design

### 2.1 `users` Collection ✅ (Keep, but enhance)

**Current**: Basic user info
**Recommended Structure**:
```javascript
{
  _id: ObjectId,
  uid: "user_alpha",  // String, indexed, unique
  email: "alice@example.com",  // String, indexed, unique
  role: "user" | "admin",
  profile: {
    firstName: "Alice",
    lastName: "Smith",
    phone: "9876543210",
    address: "123 Baker Street",
    dob: "1990-05-15"
  },
  preferences: {
    language: "en",
    notifications: true,
    defaultRiskThreshold: "YELLOW"
  },
  metadata: {
    createdAt: ISODate,
    lastLoginAt: ISODate,
    totalDocumentsProcessed: 5
  }
}
```

**Justification**:
- Embed `profile` and `preferences` (accessed together, rarely queried independently)
- Add `metadata` for analytics and user engagement tracking
- `uid` and `email` as indexed fields for fast lookups

---

### 2.2 `jobs` Collection ✅ (Restructure significantly)

**Current**: Minimal structure with embedded `chat_history`
**Recommended Structure**:
```javascript
{
  _id: ObjectId,
  job_id: "uuid-string",  // String, indexed, unique
  user_id: "user_alpha",  // Reference to users.uid, indexed
  document: {
    filename: "rental_agreement.pdf",
    gcs_uri: "gs://bucket/jobs/uuid/document.pdf",  // For production
    fileSize: 2048576,  // bytes
    mimeType: "application/pdf",
    status: "processed" | "processing" | "failed",
    createdAt: ISODate,
    expiresAt: ISODate  // TTL for auto-deletion
  },
  processing: {
    parsedAt: ISODate,
    indexedAt: ISODate,
    analyzedAt: ISODate,
    totalClauses: 150,
    totalPages: 12
  },
  analysis: {
    summary: {
      GREEN: 80,
      YELLOW: 50,
      RED: 20
    },
    clauses: [  // EMBED clauses (not separate collection)
      {
        id: "P01_C001",
        idx: 1,
        page: 1,
        section: "Terms",
        text: "The monthly rent shall be...",
        keyphrases: ["rent", "monthly"],
        risk: {
          level: "YELLOW",
          score: 0.45,
          reasons: ["deposit_above_standard"],
          flags: [  // EMBED flags (not separate collection)
            {
              rule_id: "deposit_4_months",
              severity: "YELLOW",
              reason: "Security deposit exceeds 3 months"
            }
          ]
        }
      }
    ],
    overallRiskLevel: "YELLOW",
    processedAt: ISODate
  },
  analytics: {  // EMBED analytics (not separate collection)
    latency_ms: 2340,
    tokens_used: 1250,
    processing_time_seconds: 2.34,
    indexed_at: ISODate
  },
  chat_history: [  // Keep but enhance
    {
      message_id: "msg_uuid",
      query: "What is the security deposit?",
      answer: "The security deposit is 4 months...",
      answer_llm: "You need to pay 4 months...",  // Optional LLM response
      evidence: [
        {
          clause_id: "P01_C001",
          page: 1,
          text: "...",
          risk_level: "YELLOW"
        }
      ],
      metadata: {
        top_k: 5,
        used_llm: true,
        response_time_ms: 450
      },
      timestamp: ISODate
    }
  ],
  metadata: {
    createdAt: ISODate,
    updatedAt: ISODate
  }
}
```

**Key Changes**:
1. ✅ **Embed clauses**: Clauses are document-specific and accessed together
2. ✅ **Embed flags**: Flags are tightly coupled to clauses
3. ✅ **Embed analytics**: Per-job analytics don't need separate collection
4. ✅ **Enhanced chat_history**: Add `evidence`, `metadata`, `message_id`
5. ✅ **Add `processing` status**: Track pipeline stages
6. ✅ **Add `expiresAt`**: For TTL index (auto-delete after 30 days)

**Indexes**:
```javascript
db.jobs.createIndex({ job_id: 1 }, { unique: true })
db.jobs.createIndex({ user_id: 1, "metadata.createdAt": -1 })
db.jobs.createIndex({ "document.expiresAt": 1 }, { expireAfterSeconds: 0 })
db.jobs.createIndex({ "document.status": 1 })
```

---

### 2.3 `sessions` Collection ✅ (NEW - Missing in ERD)

**Purpose**: Manage conversation sessions for multi-turn Q&A

```javascript
{
  _id: ObjectId,
  session_id: "session_uuid",  // String, indexed, unique
  job_id: "job_uuid",  // Reference to jobs.job_id, indexed
  user_id: "user_alpha",  // Reference to users.uid, indexed
  messages: [  // Full conversation history
    {
      message_id: "msg_uuid",
      role: "user" | "assistant",
      content: "What is the security deposit?",
      timestamp: ISODate,
      metadata: {
        query_params: { top_k: 5 },
        response_time_ms: 450,
        used_llm: true
      }
    }
  ],
  context: {
    current_focus: "deposit",  // User's current topic of interest
    previous_queries: ["deposit", "termination"]
  },
  metadata: {
    createdAt: ISODate,
    lastMessageAt: ISODate,
    messageCount: 12,
    isActive: true
  }
}
```

**Justification**:
- ✅ **Separate session management**: Better than embedding in jobs (sessions can span multiple jobs)
- ✅ **Full message history**: Complete conversation context for LLM context windows
- ✅ **Session analytics**: Track user engagement per session
- ✅ **Multi-turn conversations**: Support contextual follow-up questions

**Indexes**:
```javascript
db.sessions.createIndex({ session_id: 1 }, { unique: true })
db.sessions.createIndex({ job_id: 1, "metadata.lastMessageAt": -1 })
db.sessions.createIndex({ user_id: 1, "metadata.isActive": 1 })
```

---

### 2.4 `messages` Collection ✅ (NEW - Missing in ERD, but you're correct!)

**Purpose**: Dedicated collection for all messages (better for querying, analytics, search)

```javascript
{
  _id: ObjectId,
  message_id: "msg_uuid",  // String, indexed, unique
  session_id: "session_uuid",  // Reference to sessions.session_id, indexed
  job_id: "job_uuid",  // Reference to jobs.job_id, indexed
  user_id: "user_alpha",  // Reference to users.uid, indexed
  type: "query" | "response",
  content: {
    query: "What is the security deposit?",  // If type is "query"
    answer: "The security deposit is...",  // If type is "response"
    answer_llm: "You need to pay..."  // Optional LLM version
  },
  evidence: [  // Supporting clauses
    {
      clause_id: "P01_C001",
      page: 1,
      text: "...",
      risk_level: "YELLOW",
      similarity_score: 0.85
    }
  ],
  metadata: {
    top_k: 5,
    used_llm: true,
    response_time_ms: 450,
    tokens_used: 1250  // If LLM was used
  },
  timestamp: ISODate  // Indexed for time-range queries
}
```

**Justification**:
- ✅ **Dedicated storage**: Allows full-text search, analytics, and complex queries
- ✅ **Cross-session analysis**: Find common questions across all users
- ✅ **Performance**: Index `timestamp`, `user_id`, `job_id` separately
- ✅ **Audit trail**: Complete message history for compliance
- ✅ **Better than array**: MongoDB arrays are limited for complex queries (can't easily search within arrays across documents)

**Indexes**:
```javascript
db.messages.createIndex({ message_id: 1 }, { unique: true })
db.messages.createIndex({ session_id: 1, timestamp: -1 })
db.messages.createIndex({ job_id: 1, timestamp: -1 })
db.messages.createIndex({ user_id: 1, timestamp: -1 })
db.messages.createIndex({ timestamp: -1 })  // For time-range queries
db.messages.createIndex({ "content.query": "text", "content.answer": "text" })  // Full-text search
```

**Note**: Keep `chat_history` array in `jobs` for quick access, but also store in `messages` for advanced queries.

---

### 2.5 `analytics` Collection ⚠️ (Optional - for aggregation)

**Purpose**: Aggregated analytics across all jobs (if needed for dashboards)

```javascript
{
  _id: ObjectId,
  date: ISODate,  // Daily aggregation
  metrics: {
    totalJobs: 150,
    totalQueries: 1200,
    avgProcessingTime_ms: 2340,
    avgResponseTime_ms: 450,
    totalTokensUsed: 125000,
    riskDistribution: {
      GREEN: 8000,
      YELLOW: 4500,
      RED: 2000
    }
  }
}
```

**Justification**:
- ✅ **Pre-aggregated data**: Fast dashboard queries (no real-time aggregation needed)
- ✅ **Time-series data**: Daily/hourly snapshots for trends
- ✅ **Optional**: Only if you need cross-job analytics (per-job analytics embedded in `jobs`)

---

### 2.6 `audit_logs` Collection ✅ (NEW - Missing in ERD)

**Purpose**: Track all user actions for compliance and debugging

```javascript
{
  _id: ObjectId,
  user_id: "user_alpha",
  action: "upload" | "query" | "delete" | "export",
  resource_type: "document" | "message" | "session",
  resource_id: "job_uuid",
  details: {
    filename: "rental_agreement.pdf",
    query: "What is the security deposit?",
    ip_address: "192.168.1.1"
  },
  timestamp: ISODate,
  result: "success" | "failure",
  error_message: "..."  // If result is "failure"
}
```

**Justification**:
- ✅ **Compliance**: Required for legal/regulated industries
- ✅ **Debugging**: Track failures and user issues
- ✅ **Security**: Monitor suspicious activity
- ✅ **Analytics**: User behavior analysis

**Indexes**:
```javascript
db.audit_logs.createIndex({ user_id: 1, timestamp: -1 })
db.audit_logs.createIndex({ action: 1, timestamp: -1 })
db.audit_logs.createIndex({ timestamp: -1 })  // TTL index (delete after 90 days)
```

---

## 3. What Should Be Embedded vs. Referenced

### ✅ Embed (Keep in same document):

1. **Clauses in Jobs**: Document-specific, accessed together, <16MB total
2. **Flags in Clauses**: Tightly coupled, no independent queries
3. **Analytics in Jobs**: Per-job metrics, rarely queried across jobs
4. **Profile in Users**: User info accessed together
5. **Preferences in Users**: User settings accessed together

### ✅ Reference (Separate collections):

1. **Users**: Queried independently, shared across jobs
2. **Jobs**: Document/job entities, queried independently
3. **Sessions**: Conversation management, may span multiple queries
4. **Messages**: Advanced querying, full-text search, analytics
5. **Audit Logs**: Compliance, time-series data

---

## 4. Missing Features in Current Schema

### 4.1 Critical Missing Collections:

1. ✅ **`sessions`** - Multi-turn conversation management
2. ✅ **`messages`** - Dedicated message storage (you're absolutely right!)
3. ✅ **`audit_logs`** - Compliance and security
4. ⚠️ **`document_versions`** - If users can re-upload/update documents
5. ⚠️ **`index_metadata`** - Track TF-IDF index versions (if you rebuild indices)

### 4.2 Missing Fields:

1. **In `jobs`**:
   - ❌ `expiresAt` - For TTL index (auto-delete)
   - ❌ `processing.status` - Track pipeline stages
   - ❌ `document.fileSize`, `mimeType` - File metadata
   - ❌ `processing.parsedAt`, `indexedAt` - Timestamps for each stage

2. **In `users`**:
   - ❌ `preferences` - User settings
   - ❌ `metadata.lastLoginAt` - Engagement tracking
   - ❌ `metadata.totalDocumentsProcessed` - Usage stats

3. **In `messages`** (if added):
   - ❌ `evidence` - Supporting clauses (currently missing)
   - ❌ `metadata.tokens_used` - Cost tracking
   - ❌ `metadata.response_time_ms` - Performance tracking

---

## 5. Production Deployment Justifications

### 5.1 Why Embed Clauses, Flags, and Analytics?

**Performance**:
- ✅ **Single query**: Get job + clauses + flags + analytics in one read
- ✅ **No joins**: MongoDB doesn't support joins; embedding avoids multiple queries
- ✅ **Reduced latency**: 1 database call vs. 4+ calls

**Data Locality**:
- ✅ **Cache efficiency**: All related data fetched together
- ✅ **Atomic updates**: Update clauses and flags atomically
- ✅ **Document size**: Typical documents <5MB (well under 16MB limit)

**Query Patterns**:
- ✅ Users query by `job_id` → need all clauses/flags for that job
- ✅ Clauses rarely queried independently (no "find all clauses with X risk level across all jobs")
- ✅ Flags always accessed with clauses

**Trade-offs**:
- ⚠️ **Document size**: Monitor document size (MongoDB 16MB limit)
- ⚠️ **Update granularity**: Updating one clause requires updating entire document (but clauses are immutable after processing)

---

### 5.2 Why Separate `messages` Collection?

**Query Requirements**:
- ✅ **Full-text search**: Search across all user queries ("find all questions about security deposit")
- ✅ **Time-range queries**: "Show all messages in last 24 hours"
- ✅ **Cross-job analytics**: "What are the most common questions?"
- ✅ **User history**: "Show all my messages across all documents"

**Performance**:
- ✅ **Indexed queries**: Index `timestamp`, `user_id`, `job_id` separately
- ✅ **Array limitations**: MongoDB arrays can't be efficiently searched across documents
- ✅ **Sharding**: Can shard `messages` collection independently if needed

**Scalability**:
- ✅ **Growth**: Messages will grow faster than jobs (many messages per job)
- ✅ **Retention**: Can archive old messages without affecting jobs
- ✅ **Analytics**: Dedicated collection for message analytics

**Current Implementation Issue**:
- ❌ Chat history stored as array in `jobs.chat_history`
- ❌ Can't efficiently query: "Find all queries about security deposit"
- ❌ Can't efficiently query: "Show messages from user X in last week"
- ✅ **Solution**: Store in both places (array for quick access, collection for queries)

---

### 5.3 Why `sessions` Collection?

**Multi-Turn Conversations**:
- ✅ **Context preservation**: LLM context windows need conversation history
- ✅ **Session management**: Track active/inactive sessions
- ✅ **User experience**: Resume conversations, show conversation threads

**Analytics**:
- ✅ **Session metrics**: Average messages per session, session duration
- ✅ **Engagement**: Track user engagement per session

**Scalability**:
- ✅ **Separate lifecycle**: Sessions can be archived independently
- ✅ **Better indexing**: Index `session_id`, `job_id`, `user_id` separately

---

### 5.4 Why `audit_logs` Collection?

**Compliance**:
- ✅ **Legal requirements**: Document access, user actions (GDPR, data privacy)
- ✅ **Audit trail**: Who accessed what, when, and how

**Security**:
- ✅ **Anomaly detection**: Monitor suspicious activity
- ✅ **Debugging**: Track failures and errors

**Production Best Practice**:
- ✅ **TTL index**: Auto-delete logs after retention period (90 days)
- ✅ **Separate collection**: Doesn't impact main application performance

---

## 6. Migration Strategy (If Already Deployed)

### Phase 1: Enhance Existing Collections
1. Add missing fields to `jobs` (expiresAt, processing status)
2. Add missing fields to `users` (preferences, metadata)
3. Enhance `chat_history` structure (add evidence, metadata)

### Phase 2: Add New Collections
1. Create `sessions` collection
2. Create `messages` collection
3. Create `audit_logs` collection

### Phase 3: Data Migration
1. Migrate existing `chat_history` to `messages` collection
2. Create `sessions` for existing jobs
3. Backfill audit logs (if needed)

### Phase 4: Optimize
1. Add indexes
2. Set up TTL indexes
3. Monitor document sizes

---

## 7. Summary Recommendations

### ✅ Keep & Enhance:
- `users` collection (add preferences, metadata)
- `jobs` collection (embed clauses, flags, analytics)

### ✅ Add (Critical):
- `messages` collection - **You're absolutely right, this is missing!**
- `sessions` collection - For conversation management
- `audit_logs` collection - For compliance

### ❌ Remove (Over-normalized):
- Separate `clauses` collection → Embed in `jobs`
- Separate `flags` collection → Embed in `jobs.clauses[].risk.flags`
- Separate `analytics` collection → Embed in `jobs.analytics` (unless you need cross-job aggregation)

### ⚠️ Optional:
- `analytics` collection (only if you need aggregated dashboards)
- `document_versions` collection (only if users can update documents)

---

## 8. Final Schema Overview

```
clauseclear_db/
├── users/              ✅ Keep (enhanced)
├── jobs/               ✅ Keep (restructured, embed clauses/flags/analytics)
├── sessions/           ✅ NEW (missing in ERD)
├── messages/           ✅ NEW (you're right - critical missing!)
├── audit_logs/         ✅ NEW (missing in ERD)
└── analytics/          ⚠️ Optional (aggregated metrics)
```

---

## Conclusion

Your current ERD is **too relational for MongoDB**. The recommended schema:
1. ✅ **Embeds related data** (clauses, flags, analytics in jobs)
2. ✅ **Adds missing collections** (messages, sessions, audit_logs)
3. ✅ **Optimizes for query patterns** (indexes, document structure)
4. ✅ **Supports production requirements** (TTL, compliance, scalability)

**You're absolutely correct about messages** - they should have a dedicated collection for querying and analytics, in addition to the embedded array for quick access.

