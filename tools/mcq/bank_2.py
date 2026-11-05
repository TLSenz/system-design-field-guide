# MCQ bank, part 2: Replication, Consistency, Message Queues, Rate Limiting.
# Format: see bank_1.py.

QUESTIONS = [
    # -------------------------------------------------------------- Replication
    {
        "topic": "Replication",
        "q": "A payments team switches their Postgres replica from asynchronous to synchronous replication in the same availability zone. What do they gain, and what do they now pay on every write?",
        "c": "No acknowledged write is lost if the primary dies, but each commit now waits for a replica round trip, and writes stall whenever the synchronous replica is slow or unavailable.",
        "w": [
            "Reads from the replica become guaranteed fresh, but the primary must now store twice as much WAL on disk, which roughly doubles storage costs without affecting commit latency.",
            "Failover becomes fully automatic, but the replica can no longer serve read queries, because a synchronous standby must keep all of its resources reserved for applying WAL.",
            "Backups can be taken from the replica instead of the primary, but each nightly backup now has to pause writes on the primary until the standby confirms the backup finished.",
        ],
        "x": "**{C} is correct.** Synchronous replication means the commit is acknowledged only after the replica has it. The gain is RPO ≈ 0 for that replica. The costs are an extra network round trip on every commit, and write availability now depends on the replica's health (mitigated with quorum-sync across several replicas).\n\n- **{W1}:** Replica *reads* can still lag behind replay unless you use `remote_apply`, and storage isn't doubled.\n- **{W2}:** Sync standbys can still serve reads, and failover automation is a separate concern.\n- **{W3}:** Backups don't depend on sync vs. async and don't pause the primary.\n\nRelated: Ch. 04 §3.",
    },
    {
        "topic": "Replication",
        "q": "A user edits their display name, the API returns 200, and the page reloads showing the old name. A refresh a second later shows the new one. Reads go to async replicas. What is this and what's a good fix?",
        "c": "A read-your-writes violation from replica lag. Send that user's reads to the primary for a short window after a write, or only use replicas that have caught up to that write.",
        "w": [
            "A lost update caused by two concurrent writes. Add optimistic concurrency with a version column so that the second write is rejected and the user is told to retry the edit.",
            "Clock skew between the app servers. Synchronize every host with NTP so that the update's timestamp is never earlier than the read, and the replica returns the new value.",
            "A failed cache invalidation on the CDN. Purge the profile page from every edge location after each edit so that the next request is forced to fetch the newest value.",
        ],
        "x": "**{C} is correct.** The write succeeded on the primary; the next read hit a replica that hadn't replayed it yet. Fixes: pin a user's reads to the primary after their writes (a cookie with a timestamp), or track the LSN/GTID of their write and only read from replicas that have reached it.\n\n- **{W1}:** Nothing was overwritten. The new value appears a second later.\n- **{W2}:** Replication lag isn't a clock problem.\n- **{W3}:** Plausible in general, but the setup says reads go to async replicas, and the self-healing after ~1 s matches replica lag.\n\nRelated: Ch. 04 §5.",
    },
    {
        "topic": "Replication",
        "q": "Your failover script promotes a replica whenever it cannot ping the primary for 5 seconds. During a network incident you end up with two primaries accepting writes. Why was the ping check insufficient?",
        "c": "Network failures can be partial: the primary may still be serving clients even though the replica can't reach it. Safe promotion needs a quorum and fencing of the old primary.",
        "w": [
            "Ping uses ICMP, which most cloud networks deprioritize under load, so the check should have used a TCP health endpoint, which would have correctly detected that the primary had failed.",
            "Five seconds is too short for a timeout. With a 60-second timeout the script would have waited for the network to recover and the second primary would never have been promoted.",
            "The replica should have pinged the primary from two network interfaces, because if both pings fail it proves that the primary is down rather than the replica's own network.",
        ],
        "x": "**{C} is correct.** From one node's point of view, \"dead\" and \"unreachable from here\" look identical. A single observer can't tell them apart. Safe failover uses a consensus/quorum system (etcd, ZooKeeper, Patroni with a DCS) to decide, and fences the old primary (STONITH, revoked leases, fencing tokens) so it can't keep accepting writes.\n\n- **{W1}:** A TCP check has exactly the same partial-partition blind spot.\n- **{W2}:** A longer timeout lowers the false-positive rate but doesn't remove split-brain. It just makes real failovers slower.\n- **{W3}:** Both interfaces still look from the same single observer.\n\nRelated: Ch. 04 §6, Ch. 08 §9.",
    },
    {
        "topic": "Replication",
        "q": "Worker A acquires a lock with a 10 s lease, then pauses for 15 s in a GC stop-the-world. The lease expires, worker B takes the lock and writes. A wakes up and writes too. What prevents A's write from corrupting the data?",
        "c": "A fencing token: the lock service issues a strictly increasing number per acquisition, and the storage rejects any write with a token lower than the highest it has seen.",
        "w": [
            "A longer lease: setting the lock TTL above the longest possible GC pause guarantees that the lease can never expire while its holder is still in the middle of doing its work.",
            "A heartbeat: worker A renews its lease every second from a background thread, so the lock service sees that it is alive and never hands the lock over to worker B at all.",
            "A unique lock value: each holder stores a random UUID in the lock, and checks before writing that the lock still holds its own UUID, which detects that the lease was lost.",
        ],
        "x": "**{C} is correct.** The check must happen at the **resource**, because the client can't know it was paused. With fencing, B's write carries token 34 and A's late write carries 33, so the storage rejects A.\n\n- **{W1}:** Pauses (GC, VM migration, swapping, network delay) have no upper bound you can rely on.\n- **{W2}:** The heartbeat thread is paused along with the rest of the process.\n- **{W3}:** Check-then-write is a race: A can check, pause, then write. The UUID only protects the *release* of the lock.\n\nRelated: Ch. 08 §5.3.",
    },
    {
        "topic": "Replication",
        "q": "A developer runs `DELETE FROM orders` without a `WHERE` clause on the primary. The team has three replicas in three zones. Why don't the replicas help, and what does?",
        "c": "Replicas apply the delete within milliseconds like any other change. Recovery needs point-in-time backups (snapshot plus WAL archive) restored to just before the bad delete.",
        "w": [
            "Replicas do help: promote the replica in the zone furthest from the primary, because cross-zone replication lag means it has not yet received the delete and still holds every row.",
            "Replicas do help: replicas ignore destructive statements without a `WHERE` clause by default, so you can copy the orders table back from any one of the replicas to the primary.",
            "Replicas don't help because they're in other zones; keeping a replica in the same zone as the primary would let you read the deleted rows from it before replication applies.",
        ],
        "x": "**{C} is correct.** Replication copies *changes*, good or bad: deletions, corruption, a buggy migration. Replicas protect against hardware failure, not against mistakes. PITR (or a deliberately delayed replica) is what lets you go back in time.\n\n- **{W1}:** Cross-zone lag is milliseconds. You won't win that race.\n- **{W2}:** No database replica filters statements like that.\n- **{W3}:** Location doesn't matter. Every replica applies the delete.\n\nRelated: Ch. 04 §1, Ch. 15 §6.",
    },
    # -------------------------------------------------------------- Consistency
    {
        "topic": "Consistency",
        "q": "A colleague says \"CAP means we pick two of consistency, availability and partition tolerance, so we chose CA.\" What's the more accurate framing?",
        "c": "Partitions happen whether you choose them or not, so the real choice is what a node does during one: refuse some requests to stay consistent (CP) or answer with possibly stale data (AP).",
        "w": [
            "CA is a valid choice for distributed systems running in a single region, because partitions only occur between regions, so inside one region the system can be fully consistent and available.",
            "CAP no longer applies to modern databases, because consensus protocols like Raft provide consistency, availability and partition tolerance at the same time without any trade-off.",
            "The framing is right, but CA is a poor choice; most systems should pick AP, because availability is always more valuable to the business than consistency under any partition.",
        ],
        "x": "**{C} is correct.** In a distributed system you don't get to opt out of network partitions. CAP says that *during* a partition you choose between consistency and availability. When there's no partition, PACELC adds the everyday trade-off: latency vs. consistency.\n\n- **{W1}:** Partitions happen inside a region too: switches, NICs, GC pauses, misconfigured security groups.\n- **{W2}:** Raft is CP. The minority side of a partition can't make progress.\n- **{W3}:** Which side to pick depends on the data. Payments and inventory often need CP; likes and feeds are fine as AP.\n\nRelated: Ch. 05 §2.",
    },
    {
        "topic": "Consistency",
        "q": "A Dynamo-style store has N=3 replicas. You configure W=2 and R=2. Assuming no sloppy quorum and no concurrent writes in flight, can a read return a value older than the last acknowledged write?",
        "c": "No. Any 2 replicas that are read must overlap with the 2 that acknowledged the write, because W + R = 4 > N = 3, so at least one of the two responses always holds the latest value.",
        "w": [
            "Yes. Two of the three replicas might both be stale, and the read can be served entirely by those two, because the quorum rule only constrains how many replicas each write waits for.",
            "Yes, but only during a network partition. Outside a partition all three replicas are always in sync, so any combination of W and R values will return the latest acknowledged write.",
            "No, but only because R=2 is a majority. Any read that consults a majority of replicas is linearizable regardless of how many replicas acknowledged each write before the response.",
        ],
        "x": "**{C} is correct.** The quorum condition W + R > N guarantees the read set and the write set overlap in at least one replica. The reader picks the newest version among its responses. (Edge cases such as sloppy quorums, hinted handoff and concurrent writes can still produce surprises, which is why the question excludes them.)\n\n- **{W1}:** Only one replica can have missed the write; the other two both have it.\n- **{W2}:** Replicas can lag at any time, not only during partitions. W and R are what bound the risk.\n- **{W3}:** With W=1, a majority read could miss the one replica that took the write. It's the *sum* that matters.\n\nRelated: Ch. 05 §4.",
    },
    {
        "topic": "Consistency",
        "q": "A billing worker consumes `ChargeCustomer` messages from a queue with at-least-once delivery. A customer was charged twice for one order. Which design prevents this?",
        "c": "Make the handler idempotent: record a unique charge key (e.g. the order ID) in the same transaction as the charge, and skip any message whose key has already been processed.",
        "w": [
            "Switch the queue to exactly-once delivery, because once the broker guarantees each message is delivered only once, the worker can safely charge as soon as a message arrives.",
            "Acknowledge each message before calling the payment provider, so the broker will never redeliver it, even if the worker crashes in the middle of processing the charge.",
            "Process messages with a single worker thread, because duplicate charges come from two threads handling the same message, and a single consumer cannot process anything twice.",
        ],
        "x": "**{C} is correct.** At-least-once delivery means duplicates *will* happen: redeliveries after timeouts, consumer crashes before the ack, producer retries. Idempotency makes the second delivery a no-op. Pass the same key to the payment provider as its idempotency key too.\n\n- **{W1}:** End-to-end exactly-once isn't something a broker can give you once side effects leave it (like calling a payment API).\n- **{W2}:** This turns duplicates into *lost* charges whenever the worker crashes after the ack: at-most-once.\n- **{W3}:** A single consumer still gets redeliveries after a crash or ack timeout.\n\nRelated: Ch. 05 §7, Ch. 07 §3.",
    },
    {
        "topic": "Consistency",
        "q": "A travel booking flow reserves a flight, a hotel and a car through three services, using a saga with compensating actions instead of a two-phase commit. What does the saga give up?",
        "c": "Isolation: other users can see intermediate states (flight booked, hotel not yet), and a failure is undone later by compensating actions instead of never being visible.",
        "w": [
            "Fault tolerance: if any one of the three services is down when the saga starts, the whole booking fails permanently and cannot be retried, whereas 2PC would wait for recovery.",
            "Durability: each step of the saga is held only in memory until the final step completes, so a crash midway loses every reservation that was made in the earlier steps.",
            "Retryability: because compensating actions are not idempotent, a saga step must never be retried, while 2PC can retry its prepare phase as many times as it needs to.",
        ],
        "x": "**{C} is correct.** A saga is a sequence of local transactions, each committed immediately. That's why there's no global lock or blocking coordinator, and also why intermediate states are visible and \"rollback\" is a new action (cancel the flight) that may itself fail or be noticeable (a refund email).\n\n- **{W1}:** Sagas are *more* tolerant of failure. Steps retry and the orchestrator resumes.\n- **{W2}:** Each step is durably committed in its own service.\n- **{W3}:** Saga steps and compensations *must* be idempotent precisely so they can be retried.\n\nRelated: Ch. 05 §8, Ch. 08 §7.",
    },
    {
        "topic": "Consistency",
        "q": "You're designing a social app. Which of these pieces of data most needs strong (linearizable) consistency?",
        "c": "The username registry, because two people must never claim the same handle, and a uniqueness check that reads stale data can let both registrations succeed.",
        "w": [
            "The follower count shown on profiles, because users frequently compare their counts with friends and will report a bug if the number differs between two page loads.",
            "The ranked home feed, because if two replicas order posts differently a user might see the same post twice or miss one when they scroll back up through the feed.",
            "The view counter on each video, because creators are paid by views, so every single view must be counted exactly once and be visible immediately on every replica.",
        ],
        "x": "**{C} is correct.** Uniqueness is a classic invariant that needs a single authoritative decision: a linearizable compare-and-set, a unique constraint on one primary, or consensus. Eventual consistency lets two claims both succeed.\n\n- **{W1}:** A few seconds of drift in a follower count is harmless.\n- **{W2}:** Feeds are derived, ranked and personalized. Eventual consistency is expected.\n- **{W3}:** Payouts need *accurate eventual* counts (dedupe and reconcile in batch), not linearizable reads on every view.\n\nRelated: Ch. 05 §1.",
    },
    # ----------------------------------------------------------- Message Queues
    {
        "topic": "Message Queues",
        "q": "An email-sending consumer occasionally sends the same welcome email twice after deploys. The broker is RabbitMQ with manual acks. What's the most robust fix?",
        "c": "Make the consumer idempotent: store a processed-message key (e.g. user ID plus email type) and check it before sending, because redelivery after a restart is expected.",
        "w": [
            "Acknowledge each message as soon as it is received, before sending the email, so that a consumer restarted during a deploy never sees the same message delivered a second time.",
            "Reduce the prefetch count to one, so that each consumer holds only a single unacknowledged message at a time and a deploy can never interrupt more than one email in flight.",
            "Disable consumer restarts during deploys by draining the queue first, so that no message is ever in flight when the consumers stop, which prevents duplicates from happening.",
        ],
        "x": "**{C} is correct.** A consumer that sends the email and is killed before acking will get the message redelivered. That is at-least-once working as designed. Idempotency handles every source of duplicates: deploys, crashes, network timeouts, producer retries.\n\n- **{W1}:** Early acks trade duplicates for *lost* emails whenever the consumer crashes mid-send.\n- **{W2}:** It shrinks the window but doesn't close it, and it hurts throughput.\n- **{W3}:** It's operationally fragile and only covers one source of duplicates.\n\nRelated: Ch. 07 §3.",
    },
    {
        "topic": "Message Queues",
        "q": "You need one alert that fires when an order-processing consumer is falling behind badly enough to hurt customers. Which metric is the best basis for that alert?",
        "c": "The age of the oldest unprocessed message, because it directly measures how long customers are waiting, whatever the current traffic volume or the number of consumers running.",
        "w": [
            "Queue depth, because the number of unprocessed messages is the most direct measure of backlog, and a fixed threshold like 10,000 messages works well at any time of the day.",
            "Messages processed per second, because a falling processing rate is the earliest sign that consumers are struggling, and it drops well before any backlog starts to build up.",
            "Consumer CPU utilization, because consumers that are falling behind are almost always CPU-bound, so CPU above 80% reliably predicts that a backlog is about to form in the queue.",
        ],
        "x": "**{C} is correct.** Oldest-message age is the user-facing symptom (\"orders wait 9 minutes\") and it is independent of volume. Alert when it exceeds what the business tolerates.\n\n- **{W1}:** 10,000 messages may be 2 seconds of work at peak or 3 hours at night. Depth needs context to mean anything.\n- **{W2}:** Throughput naturally drops when traffic drops. Low throughput isn't lag.\n- **{W3}:** Consumers are often IO-bound. Lag can grow at 20% CPU.\n\nRelated: Ch. 07 §6.",
    },
    {
        "topic": "Message Queues",
        "q": "Events for each bank account must be processed in order (deposit before withdrawal), but you need parallelism across accounts. How do you get this with Kafka?",
        "c": "Use the account ID as the message key so all of an account's events go to the same partition, and process each partition sequentially, with parallelism coming from the partitions.",
        "w": [
            "Use a single partition for the whole topic, and scale out by adding consumers to the group, which will then share the partition while preserving the order of every account's events.",
            "Use random partitioning to balance load evenly, and enable the idempotent producer, which makes Kafka deliver each account's events in order across all of the partitions.",
            "Use many partitions with round-robin assignment, and have consumers sort events by timestamp in a buffer before processing, which restores each account's order within a window.",
        ],
        "x": "**{C} is correct.** Kafka orders messages only *within* a partition. Keying by account sends each account's events to one partition. Partitions are processed in parallel, so you get per-key ordering plus horizontal scale. Watch out for repartitioning (adding partitions changes key placement) and for parallel processing inside one partition.\n\n- **{W1}:** Only one consumer per group can read a partition, so extra consumers sit idle.\n- **{W2}:** The idempotent producer prevents duplicates from retries; it doesn't order across partitions.\n- **{W3}:** Timestamp re-sorting is fragile (clock skew, late arrivals) and adds latency.\n\nRelated: Ch. 07 §4, §8.",
    },
    {
        "topic": "Message Queues",
        "q": "One malformed message makes the consumer throw an exception every time. It has been redelivered 4,000 times and is blocking the partition behind it. What should the system do?",
        "c": "After a bounded number of retries with backoff, move it to a dead-letter queue, alert someone, and keep consuming; replay it only once a fix for it is in place.",
        "w": [
            "Keep retrying with exponential backoff, capped at one hour, because the error might be caused by a transient dependency problem and the message will eventually succeed.",
            "Catch the exception, log it at debug level, and acknowledge the message so the partition can make progress, since a single message rarely matters to the overall system.",
            "Send the message back to the end of the main queue each time it fails, so that it stops blocking the messages behind it while still being retried indefinitely.",
        ],
        "x": "**{C} is correct.** A *poison message* will never succeed by retrying. Bounded retries separate transient failures from permanent ones. The DLQ preserves the message, the alert makes someone look, and the queue keeps flowing.\n\n- **{W1}:** It blocks the partition for hours and still never succeeds.\n- **{W2}:** Silent data loss: that message might be a payment.\n- **{W3}:** It still retries forever, burns capacity, and in ordered systems breaks ordering.\n\nRelated: Ch. 07 §5.",
    },
    {
        "topic": "Message Queues",
        "q": "A new fraud-detection team wants to process the last 7 days of `PaymentCompleted` events, which other services already consumed. Why is this easy with Kafka but hard with a classic queue like SQS?",
        "c": "Kafka keeps events for a retention period whether or not they've been read, and each consumer group has its own offset, so a new group can start reading from 7 days ago.",
        "w": [
            "Kafka is faster than SQS, so it can re-read a week of data in minutes, while SQS throttles reads so heavily that a backfill of that size would take several weeks to complete.",
            "Kafka stores events in a relational table that can be queried by date, while SQS stores messages in a binary format that cannot be filtered or searched after delivery.",
            "Kafka sends a copy of every event to each registered team by default, so the new team already has its own copy, while SQS only keeps a single copy for each queue.",
        ],
        "x": "**{C} is correct.** A queue deletes a message once it is acknowledged, so it's gone after consumption. A log is an append-only, retained stream; consumers just track their position. That makes replay, backfills and adding new consumers cheap.\n\n- **{W1}:** Raw speed isn't the difference. SQS simply no longer *has* the messages.\n- **{W2}:** Kafka stores segments in a log, not a queryable table. You seek by offset or timestamp.\n- **{W3}:** Kafka doesn't push copies. Consumers *pull* from a shared log.\n\nRelated: Ch. 07 §2, §8.",
    },
    # ------------------------------------------------------------ Rate Limiting
    {
        "topic": "Rate Limiting",
        "q": "A public API should allow clients an average of 10 requests/second but tolerate a page load that fires 30 requests at once. Which algorithm fits and why?",
        "c": "A token bucket with rate 10/s and capacity 30, because saved-up tokens allow a burst of up to 30 requests, while the refill rate holds the long-run average to 10 per second.",
        "w": [
            "A fixed one-second window with a limit of 10, because it is the simplest algorithm to reason about, and a burst of 30 will simply be served across the following three seconds.",
            "A leaky bucket that drains at 10/s with a queue of size 1, because it smooths traffic into a perfectly even stream, which is what downstream services need for stability.",
            "A sliding-window log storing every request timestamp, because it is the only algorithm that can tell a burst apart from sustained traffic, so it can allow bursts precisely.",
        ],
        "x": "**{C} is correct.** The token bucket separates two knobs: refill rate (the long-run average) and capacity (the allowed burst). That matches the requirement exactly.\n\n- **{W1}:** A fixed window *rejects* 20 of the 30 requests. It doesn't queue them. It also allows 2× bursts at window edges.\n- **{W2}:** A leaky bucket with a tiny queue rejects bursts; it smooths output rather than allowing bursts.\n- **{W3}:** A sliding log is precise but memory-hungry (one entry per request), and a token bucket expresses bursts just as well, more cheaply.\n\nRelated: Ch. 10 §3.4.",
    },
    {
        "topic": "Rate Limiting",
        "q": "Your API gateway rejects a client that exceeded its quota. Which response best helps well-behaved clients recover?",
        "c": "`429 Too Many Requests` with a `Retry-After` header (plus rate-limit headers for the remaining quota), so clients know they were throttled and exactly when to try again.",
        "w": [
            "`503 Service Unavailable` with a `Retry-After` header, because the service cannot currently accept the request, and every HTTP client library already retries 503 responses.",
            "`400 Bad Request` with an error body saying the quota is exceeded, because the client sent more requests than it was allowed to, which makes the request itself invalid.",
            "`403 Forbidden` with a message describing the quota, because the client is temporarily not permitted to make requests until its quota resets at the start of the next window.",
        ],
        "x": "**{C} is correct.** 429 says \"you, specifically, are sending too much\". `Retry-After` and `RateLimit-*` headers tell clients exactly when to come back, which prevents retry storms.\n\n- **{W1}:** 503 says the *server* is unhealthy, which misleads monitoring and triggers generic retries from every client.\n- **{W2}:** The request itself is fine. Repeating it later will work, so 400 is wrong.\n- **{W3}:** 403 means \"not permitted, don't retry\", and clients won't come back.\n\nRelated: Ch. 09 §7, Ch. 10 §6.",
    },
    {
        "topic": "Rate Limiting",
        "q": "A Redis-backed token bucket does `GET tokens`, computes the refill in the app, then `SET tokens`. Under load, clients get more requests through than the limit. What's wrong and how do you fix it?",
        "c": "The read-modify-write isn't atomic, so concurrent requests read the same count and each spend it. Run the refill-and-take step in one Lua script, which Redis runs atomically.",
        "w": [
            "Redis is eventually consistent between its read and write paths, so the `GET` returns a cached value; enabling `WAIT` after each write makes the next `GET` see the update.",
            "The token key's TTL expires between the `GET` and the `SET`, resetting the bucket to full; setting the TTL to a much larger value keeps the bucket from being reset early.",
            "The app servers' clocks disagree, so each server computes a different refill amount; moving the refill calculation to a single dedicated server makes all of them consistent.",
        ],
        "x": "**{C} is correct.** Two requests can both `GET` 1 token, both decide to allow, and both `SET` 0. A Lua script (or `MULTI` with `WATCH`, or a module like redis-cell) makes read, compute and write one atomic step. Using Redis server time inside the script also removes app-clock skew as a bonus.\n\n- **{W1}:** A single Redis primary is linearizable for single-key operations. The race is in your code.\n- **{W2}:** TTLs can cause surprises, but they don't explain systematic over-admission under concurrency.\n- **{W3}:** Clock skew is a real secondary issue, but a single server doesn't fix the race between two concurrent requests.\n\nRelated: Ch. 10 §4.4.",
    },
    {
        "topic": "Rate Limiting",
        "q": "The Redis cluster backing your API's rate limiter becomes unreachable. For a typical public API (not a login or payment endpoint), what should the limiter do?",
        "c": "Fail open to a conservative per-instance local limit and alert on the degraded mode, because the limiter itself must not turn a Redis outage into a full API outage.",
        "w": [
            "Fail closed and reject all requests with 429, because without accurate counts the API could be overwhelmed, and protecting the backend matters more than serving traffic.",
            "Retry the Redis call with exponential backoff until it succeeds, holding each request until a decision is available, so that every request is still counted accurately.",
            "Fail open with no limit at all until Redis recovers, because rate limiting is only an optimization, and any request served is better than a request that gets rejected.",
        ],
        "x": "**{C} is correct.** The limiter is a protective layer, so its own failure shouldn't take the product down. A local fallback limit still offers rough protection. For security-sensitive endpoints (login, OTP), failing closed may be the right call, which is why the question excludes them.\n\n- **{W1}:** A Redis blip becomes a total outage you caused yourself.\n- **{W2}:** Requests pile up behind the dead dependency, exhausting threads and memory: a cascading failure.\n- **{W3}:** No protection at all is risky. Abusers and retry storms get through exactly when the system is already degraded.\n\nRelated: Ch. 10 §4.3, §8.",
    },
    {
        "topic": "Rate Limiting",
        "q": "A reporting endpoint runs queries that take anywhere from 50 ms to 20 s. A limit of 50 requests/second still lets it exhaust the 100-connection database pool. What kind of limit works better?",
        "c": "A concurrency limit on in-flight queries (e.g. 40 at a time), because it bounds the resource that actually runs out, connections, however long each query happens to take.",
        "w": [
            "A lower rate limit, such as 5 requests/second, because fewer requests per second always means fewer connections in use, regardless of how long each query takes to finish.",
            "A per-user rate limit instead of a global one, because the pool is exhausted by a few heavy users, and limiting each user separately spreads the connections more fairly.",
            "A larger connection pool of 500 connections, because the rate limit is already correct, and the pool simply needs enough headroom for the slowest queries that are running.",
        ],
        "x": "**{C} is correct.** By Little's law, in-flight = rate × duration. At 50 rps × 20 s that's 1,000 concurrent queries. A rate limit can't bound that when the duration varies by 400×. A concurrency limit (a semaphore or bulkhead) caps exactly what's scarce.\n\n- **{W1}:** 5 rps × 20 s = 100 connections, and it also throttles cheap queries for no reason.\n- **{W2}:** It might help fairness, but the total can still exhaust the pool.\n- **{W3}:** More connections means more load on a database that's already struggling; Postgres degrades with too many connections.\n\nRelated: Ch. 10 §3.6, §10.",
    },
]
