# MCQ bank, part 1: Caching, Load Balancing, Databases, Sharding.
#
# Authoring format (see tools/build_mcq.py):
#   "c"  = the correct option, "w" = three distractors.
#   In "x" (explanation) write {C}, {W1}, {W2}, {W3}; the generator replaces them
#   with the final letters after options are placed.
#   Keep every option a full, plausible sentence of similar length — the correct
#   one must not stand out by being longer or more detailed.

QUESTIONS = [
    # ------------------------------------------------------------------ Caching
    {
        "topic": "Caching",
        "q": "A product catalog API serves 40k reads/s. Prices are edited by a back-office tool a few hundred times a day, and the business says a price may be up to 60 seconds stale on product pages (checkout re-reads the database). Which caching approach fits best?",
        "c": "Cache-aside with a 60-second TTL, plus a best-effort delete of the key when the back-office tool saves an edit, so the TTL is only the safety net for missed invalidations.",
        "w": [
            "Write-through with no TTL, because every edit already passes through the application and updates the cache synchronously, so entries can never be stale and never need to expire.",
            "Write-behind caching, because buffering price edits in the cache and flushing them to the database asynchronously gives the lowest write latency for the back-office tool.",
            "A read-through cache with a 24-hour TTL and a nightly full flush, because prices change rarely and long TTLs maximize the hit rate, which is what matters at 40k reads/s.",
        ],
        "x": "**{C} is correct.** The staleness budget (60 s) maps directly to a TTL, and the explicit delete on edit makes most updates visible immediately. The TTL catches the cases where the delete is lost (crash, network blip, a code path that forgot to invalidate).\n\n- **{W1}:** \"No TTL\" means one missed invalidation leaves a wrong price forever. Not every write path goes through the app (migrations, manual SQL fixes, bulk imports).\n- **{W2}:** Write-behind optimizes write latency, which is irrelevant at a few hundred edits per day, and it can lose acknowledged edits if the cache dies.\n- **{W3}:** A 24-hour TTL breaks the 60-second staleness requirement outright. Hit rate does not matter if the data is wrong.\n\nRelated: Ch. 06 §3, §5.",
    },
    {
        "topic": "Caching",
        "q": "Every night at 00:00 your batch job warms 2 million cache keys, all with a 24-hour TTL. Each night at exactly midnight the database CPU spikes to 100% for several minutes. What is the most direct fix?",
        "c": "Add random jitter to each TTL (for example 24h ± 30 min) so expirations are spread out, and serve stale values while one request refreshes each key.",
        "w": [
            "Wrap the database read in single-flight request coalescing, so that when a key expires only one caller recomputes it while the other callers wait for that result.",
            "Add a Bloom filter in front of the cache so that lookups for keys that are known not to exist are rejected before they ever reach the database.",
            "Double the size of the cache cluster, so that more of the 2 million keys fit in memory at once and fewer of them are evicted before midnight.",
        ],
        "x": "**{C} is correct.** This is a *cache avalanche*: many different keys expire at the same instant because they were written at the same instant with the same TTL. Jitter removes the synchronized expiry, and stale-while-revalidate smooths out the refills that remain.\n\n- **{W1}:** Single-flight fixes a *stampede* on **one** hot key. Here two million distinct keys expire together. Coalescing per key still sends up to two million queries at midnight.\n- **{W2}:** A Bloom filter fixes *cache penetration* (lookups for keys that don't exist). These keys exist; they just all expired.\n- **{W3}:** The keys aren't being evicted for lack of memory. They expire on schedule, so a bigger cluster changes nothing.\n\nRelated: Ch. 06 §6.",
    },
    {
        "topic": "Caching",
        "q": "The homepage config is a single cache key read by every request (~20k rps). It is expensive to build (800 ms query). When it expires, p99 latency explodes and the database briefly saturates. What is the best fix?",
        "c": "Coalesce rebuilds with single-flight (or a short lock), so only one request recomputes the key while the rest wait for it or receive the previous value.",
        "w": [
            "Jitter the TTL of the homepage key by a random amount, so that its expiration time is unpredictable and no longer lines up with traffic peaks on the site.",
            "Move the homepage key to its own dedicated Redis instance, so that the rebuild traffic for that one key cannot interfere with the rest of the cache.",
            "Shorten the TTL from five minutes to ten seconds, so the cached value is always fresh and each rebuild has less stale state to replace when it runs.",
        ],
        "x": "**{C} is correct.** This is a *stampede* (thundering herd) on one hot key: every concurrent miss triggers its own 800 ms rebuild. Single-flight collapses them into one rebuild. Refresh-ahead or probabilistic early expiration (XFetch) are good additions.\n\n- **{W1}:** Jitter helps when **many** keys expire together. With one key, the herd happens whenever it expires, at a random time or not.\n- **{W2}:** Isolating the key doesn't reduce the number of rebuild queries hitting the database, which is the actual damage.\n- **{W3}:** A shorter TTL makes the stampede happen 30× more often.\n\nRelated: Ch. 06 §6.",
    },
    {
        "topic": "Caching",
        "q": "A team proposes write-behind (write-back) caching for user shopping carts to cut write latency: writes go to Redis and are flushed to Postgres every few seconds. What is the main risk they must accept?",
        "c": "Acknowledged writes can be lost if the cache node fails before its buffered changes are flushed, so the data must tolerate loss or the cache must be durable.",
        "w": [
            "Reads become noticeably slower, because every read must first check whether the cache has pending writes for that key before it can return a value to the caller.",
            "Consistency becomes stronger than needed, because every read is forced to go through the primary database, which adds load that the cache was supposed to remove.",
            "Cache invalidation becomes impossible, because the database no longer knows which keys exist in Redis, so stale entries must be cleared by restarting the cache.",
        ],
        "x": "**{C} is correct.** In write-behind, the cache acknowledges the write and the database is updated later. Anything in that buffer is lost if the cache node dies before the flush. That can be acceptable for carts (annoying, recoverable) with a replicated, AOF-persisted Redis. It is not acceptable for orders or payments.\n\n- **{W1}:** Reads hit the cache directly and are as fast as ever. Write-behind speeds up *writes*.\n- **{W2}:** It's the other way around: write-behind *weakens* consistency, because the database lags the cache.\n- **{W3}:** Invalidation still works the same way. The new risk is durability, not invalidation.\n\nRelated: Ch. 06 §3.",
    },
    {
        "topic": "Caching",
        "q": "Your CDN hit rate for a public product page fell from 95% to 3% right after a release. The only change was a new analytics library. What is the most likely cause?",
        "c": "The new library sets a per-visitor cookie, and the origin responds with `Vary: Cookie`, so every unique cookie value becomes a separate cache entry at the edge.",
        "w": [
            "The new library loads its scripts over HTTP/2, which the CDN cannot multiplex with cached HTML, so the edge forwards each page request to the origin instead.",
            "The library adds a `Content-Security-Policy` header, and CDNs refuse to cache any response that carries security headers, so every request now goes to origin.",
            "The library makes the HTML larger than the CDN's object size limit, so the edge stops storing the page and streams every response directly from the origin.",
        ],
        "x": "**{C} is correct.** `Vary` tells the cache which request headers are part of the cache key. `Vary: Cookie` plus a unique analytics cookie means every visitor has their own key, so nothing is ever shared. Fix it by stripping irrelevant cookies at the edge or by not varying on `Cookie` for public pages.\n\n- **{W1}:** The HTTP protocol version has no effect on cacheability.\n- **{W2}:** CDNs cache responses that carry CSP headers all the time.\n- **{W3}:** An analytics snippet doesn't push HTML anywhere near CDN object size limits, which are usually measured in GB.\n\nRelated: Ch. 11 §2.",
    },
    # ----------------------------------------------------------- Load Balancing
    {
        "topic": "Load Balancing",
        "q": "Your API servers keep user sessions in local memory, so the load balancer uses sticky sessions. During each rolling deploy, thousands of users get logged out. What change fixes the root cause?",
        "c": "Move session state into a shared store such as Redis (or into signed tokens), so any instance can serve any request and instances can be replaced at any time safely.",
        "w": [
            "Increase the sticky-session cookie lifetime on the load balancer so that users stay pinned to the same instance for longer, even while that instance is being deployed.",
            "Deploy the new version to all instances simultaneously instead of rolling, so that every session is lost once per release rather than gradually throughout the deploy.",
            "Add more instances behind the load balancer so that each one holds fewer sessions, which means fewer users are logged out each time a single instance is restarted.",
        ],
        "x": "**{C} is correct.** The root cause is that the instances are *stateful*. Once session state lives elsewhere, instances become interchangeable. That enables rolling deploys, autoscaling and failure recovery without user impact.\n\n- **{W1}:** Stickiness can't save a session once its instance is terminated. The memory is gone.\n- **{W2}:** This makes the outage bigger and adds downtime. It doesn't fix anything.\n- **{W3}:** It spreads the damage thinner, but every user is still logged out once per deploy.\n\nRelated: Ch. 01 §2.",
    },
    {
        "topic": "Load Balancing",
        "q": "A service spends most of each request waiting on downstream HTTP calls. CPU sits at 12% while p99 latency climbs from 200 ms to 2 s during peaks. Which autoscaling signal should you use?",
        "c": "In-flight requests per instance (concurrency), because waiting requests pile up long before CPU moves, and concurrency tracks the queueing that is behind the latency.",
        "w": [
            "CPU utilization with a lower target, such as 10%, because the service is clearly under-provisioned and a lower threshold will make the autoscaler react to the peaks earlier.",
            "Memory utilization, because each waiting request holds buffers and connections in memory, so memory is the most reliable proxy for load in an IO-bound service.",
            "The p99 latency alone, because latency is the user-facing symptom, and scaling directly on the symptom guarantees that the autoscaler fixes what users actually see.",
        ],
        "x": "**{C} is correct.** For IO-bound work the scarce resource is concurrency: threads, connections, event-loop slots. Little's law (L = λ·W) says in-flight work rises when latency or traffic rises, and it does so before queues explode.\n\n- **{W1}:** CPU doesn't track this workload. At a 10% target you'd scale on noise and still miss the real saturation.\n- **{W2}:** Memory moves slowly and is affected by GC and caches. It is a weak, lagging proxy.\n- **{W3}:** Latency is a good *alert* signal but a poor *scaling* signal on its own. A slow downstream raises your p99, and adding instances then makes that downstream worse.\n\nRelated: Ch. 01 §4.",
    },
    {
        "topic": "Load Balancing",
        "q": "An engineer adds a database query to the Kubernetes liveness probe \"so we restart pods that can't reach the DB.\" Why is this dangerous?",
        "c": "A short database outage makes every pod fail liveness at once, so Kubernetes restarts the entire fleet, turning a recoverable blip into a full outage with cold starts.",
        "w": [
            "Liveness probes run on the node rather than inside the pod, so they cannot open a database connection, and the probe will always fail and keep restarting the pods.",
            "A database query in the probe consumes a connection from the pool on every check, which reliably exhausts the pool within minutes even when everything is healthy.",
            "Kubernetes ignores liveness probe results whenever readiness is also configured, so the check would add load on the database without ever triggering a restart.",
        ],
        "x": "**{C} is correct.** Liveness should answer only \"is this process wedged?\" A shared dependency failing is not a reason to kill healthy processes. Use readiness (or better, circuit breakers and degraded responses) for dependency problems, and keep liveness local.\n\n- **{W1}:** Exec and HTTP probes can reach the DB. Network access is not the issue.\n- **{W2}:** With sensible probe intervals it uses a trivial number of connections. That isn't the failure mode that matters.\n- **{W3}:** Kubernetes acts on liveness and readiness independently.\n\nRelated: Ch. 01 §3, Ch. 15 §3.2.",
    },
    {
        "topic": "Load Balancing",
        "q": "You run 20 API instances behind a round-robin load balancer. Each instance enforces a per-API-key limit of 100 requests/second using an in-memory counter. What limit does a single API key actually get?",
        "c": "Roughly 2,000 requests/second, because each instance only counts the requests it sees itself, and round-robin spreads one key over 20 independent counters.",
        "w": [
            "Exactly 100 requests/second, because the load balancer forwards the per-key limit to every instance so the counters stay in sync with each other in real time.",
            "About 5 requests/second, because the 100 requests/second budget is divided across the 20 instances that each enforce their own share of the configured limit.",
            "An unpredictable value close to zero, because the instances reject each other's requests whenever their in-memory counters disagree about the current window.",
        ],
        "x": "**{C} is correct.** Local counters multiply the effective limit by the instance count, and the result also changes whenever the fleet autoscales. For a true global limit you need a shared store (e.g. Redis), or you set local limits to `global / N` and accept the imprecision.\n\n- **{W1}:** Load balancers don't synchronize application counters.\n- **{W2}:** Nothing divides the budget. Each instance independently allows 100.\n- **{W3}:** Instances don't coordinate at all, which is exactly the problem.\n\nRelated: Ch. 10 §4.",
    },
    {
        "topic": "Load Balancing",
        "q": "You need to route `/api/*` to one service and `/static/*` to another, terminate TLS at the edge, and retry idempotent requests on a different backend. Which load balancer layer do you need and why?",
        "c": "Layer 7, because path routing, TLS termination and per-request retries all require parsing HTTP, which an L4 balancer that only sees TCP flows cannot do.",
        "w": [
            "Layer 4, because it is faster and can inspect the first packet of each connection to find the URL path, which is enough for path routing and simple retries.",
            "Layer 4, because TLS must be terminated at the transport layer, and an L7 balancer would only be able to forward the encrypted bytes it receives unchanged.",
            "Either layer works equally well, because modern L4 and L7 balancers expose the same feature set and the choice only affects pricing and the console used.",
        ],
        "x": "**{C} is correct.** L7 balancers understand HTTP: paths, headers and individual requests. That is what path routing, TLS termination and per-request retries need. L4 balancers forward TCP/UDP flows without understanding them. They are cheaper and faster, and fine for non-HTTP protocols or TLS passthrough.\n\n- **{W1}:** The path lives inside the (usually encrypted) HTTP request, not in a TCP header, and an L4 balancer can't retry at the request level.\n- **{W2}:** It's backwards: L7 terminates TLS so that it can read the request.\n- **{W3}:** The two layers have genuinely different capabilities.\n\nRelated: Ch. 01 §3.",
    },
    # ---------------------------------------------------------------- Databases
    {
        "topic": "Databases",
        "q": "A multi-tenant SaaS table has the index `(tenant_id, status, created_at DESC)`. Which query can use this index to both filter and return rows already sorted?",
        "c": "`WHERE tenant_id = ? AND status = 'open' ORDER BY created_at DESC LIMIT 50`, because equality on the two leading columns leaves rows in `created_at` order.",
        "w": [
            "`WHERE status = 'open' ORDER BY created_at DESC LIMIT 50`, because the index contains both columns, so the planner can skip the tenant column and use the remaining two.",
            "`WHERE created_at > now() - interval '1 day'`, because the index stores `created_at` sorted, so a range on that column is always served directly from the index.",
            "`WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50`, because the first column matches, and the index stays sorted by `created_at` within each tenant.",
        ],
        "x": "**{C} is correct.** A composite B-tree index is sorted by its columns left to right. Equality on `tenant_id` and `status` narrows to one contiguous slice, which is already ordered by `created_at DESC`. That gives no extra sort, and `LIMIT` stops early.\n\n- **{W1}:** It skips the leading column. Without `tenant_id` the matching rows are scattered across the index (a few engines have skip scans, but don't design for that).\n- **{W2}:** `created_at` is the *third* column, so it is only sorted within each `(tenant_id, status)` group.\n- **{W3}:** This is the tempting one. Within one tenant the rows are sorted by `status` first, so `created_at` order is interrupted at each status boundary and the database must sort.\n\nRelated: Ch. 02 §3.",
    },
    {
        "topic": "Databases",
        "q": "An endpoint lists 50 orders and their customers. Tracing shows 51 database queries per request, each taking 2 ms, and latency grows linearly with page size. What is happening and what is the fix?",
        "c": "It's the N+1 pattern: one query for the orders, then one more per order for its customer. Fix it with a join or a single batched `WHERE id IN (...)` lookup.",
        "w": [
            "The connection pool is too small, so the 51 queries are queued one after another; increasing the pool size will let them run in parallel and flatten the latency.",
            "The orders table is missing an index, so each of the 51 queries does a full scan; adding an index on the customer ID column will reduce them to a single lookup.",
            "The ORM is opening a new transaction per query; wrapping the endpoint in one transaction will merge the 51 statements into one round trip to the database.",
        ],
        "x": "**{C} is correct.** The query count scaling with page size is the giveaway. Each query is fast; the cost is 50 round trips. Eager loading, a join, or one batched `IN` query (or a DataLoader in GraphQL) brings it back to one or two queries.\n\n- **{W1}:** The requests are issued *sequentially* by the code, so a bigger pool doesn't help. Each one is also only 2 ms, which means pool waiting isn't the cost.\n- **{W2}:** At 2 ms each, the queries are already using indexes. The count is the problem, not the speed of each one.\n- **{W3}:** A transaction doesn't merge statements. Each one is still a separate round trip.\n\nRelated: Ch. 02 §3.",
    },
    {
        "topic": "Databases",
        "q": "Two concurrent requests withdraw 10 from an account. Both run `SELECT balance` (read 100), compute 90 in application code, and `UPDATE ... SET balance = 90`. The final balance is 90, not 80. What is the anomaly and the simplest correct fix?",
        "c": "A lost update. Do the arithmetic in the database with `SET balance = balance - 10 WHERE id = ? AND balance >= 10`, or lock the row with `SELECT ... FOR UPDATE`.",
        "w": [
            "A dirty read. Raise the isolation level to READ COMMITTED so that each request only sees the other's value after it commits, which serializes the two withdrawals.",
            "A phantom read. Add a range lock on the accounts table so that no new rows can be inserted while either withdrawal is running, which prevents the double write.",
            "Write skew. Add a CHECK constraint that keeps the balance non-negative, so the database rejects the second write when the two transactions conflict with each other.",
        ],
        "x": "**{C} is correct.** Both transactions read the same value and the second write overwrites the first: a classic *lost update* from a read-modify-write in application code. An atomic update (or a row lock, or optimistic concurrency with a version column) fixes it.\n\n- **{W1}:** Neither transaction read uncommitted data, and READ COMMITTED (the default in Postgres) does not prevent this.\n- **{W2}:** Phantoms are about rows appearing in a range query. No rows were inserted here.\n- **{W3}:** Write skew involves two transactions writing *different* rows based on a shared premise. And a balance of 90 satisfies the constraint anyway.\n\nRelated: Ch. 02 §4.",
    },
    {
        "topic": "Databases",
        "q": "You're designing the backend for a new ride-sharing app: riders, drivers, trips, payments and refunds, with a few thousand trips per minute at launch. Which primary datastore is the best default?",
        "c": "A relational database such as Postgres, because the data is relational, payments need multi-row transactions, and this write rate is easy for a single primary.",
        "w": [
            "Cassandra, because ride data is write-heavy time-series data, and choosing a wide-column store up front avoids a painful migration once the service reaches global scale.",
            "MongoDB, because a trip is naturally one document containing the rider, the driver, the route and the payment, so storing it as one record avoids joins on every read.",
            "Redis as the primary store, because trip state changes every few seconds, and an in-memory database is the only option fast enough for real-time location updates.",
        ],
        "x": "**{C} is correct.** Start with the boring, correct default: relational data, transactional money movement, modest scale. Add specialised stores later for specific needs (e.g. Redis geo-indexes for live driver locations, a log for location streams).\n\n- **{W1}:** It optimizes for a scale you don't have, and gives up the transactions you do need for payments.\n- **{W2}:** Riders, drivers and payments are shared entities referenced by many trips. Embedding them duplicates data and makes updates and refunds painful.\n- **{W3}:** Hot location data can live in Redis, but it is a poor *system of record* for payments.\n\nRelated: Ch. 02 §1.",
    },
    {
        "topic": "Databases",
        "q": "In a document store, a blog post has an author, up to 10 tags, and comments that can grow into the tens of thousands on viral posts. How should you model it?",
        "c": "Embed the tags (small and bounded) in the post document, and store comments as separate documents that reference the post ID, paginated by an index on (post_id, created_at).",
        "w": [
            "Embed everything, including comments, in the post document, because a document store has no joins, and one read that returns the full post is always the most efficient design.",
            "Reference everything, including the tags, from separate collections, because small documents are always faster to read, and joins can be done in the application layer.",
            "Embed the comments and reference the tags, because comments are always displayed with the post while tags are shared across posts and need their own collection.",
        ],
        "x": "**{C} is correct.** Embed what is bounded and always read with the parent. Reference what is unbounded or independently accessed. Unbounded embedded arrays hit document size limits (16 MB in MongoDB), make every write rewrite a huge document, and cause contention.\n\n- **{W1}:** Viral posts would exceed document limits and every new comment would rewrite the whole post.\n- **{W2}:** It adds an extra lookup for every post read to save a few bytes of tags.\n- **{W3}:** It gets both decisions backwards. The unbounded part is embedded and the tiny bounded part is split out.\n\nRelated: Ch. 02 §5.",
    },
    # ----------------------------------------------------------------- Sharding
    {
        "topic": "Sharding",
        "q": "Your data is sharded with `shard = hash(user_id) % 8`. You need to add a 9th shard. What is the main problem with this scheme?",
        "c": "Changing the modulus from 8 to 9 changes the shard of almost every key, so nearly all data has to move instead of only the roughly one-ninth that should.",
        "w": [
            "Modulo hashing places keys unevenly as N grows, so the new 9th shard would receive almost no data until the hash function itself is replaced with a better one.",
            "Modulo hashing only works when the shard count is a power of two, so going from 8 to 9 shards requires jumping straight to 16 shards to keep the routing valid.",
            "The hash function must be recomputed for every row on every query after resharding, which permanently doubles the CPU cost of routing requests to their shard.",
        ],
        "x": "**{C} is correct.** With `% N`, a key's shard depends on N itself. Going from 8 to 9 keeps only ~1/9 of keys in place and moves the rest. Consistent hashing, or a fixed number of logical partitions mapped to physical nodes, limits movement to ~1/N.\n\n- **{W1}:** A good hash with modulo distributes evenly for any N. Distribution isn't the problem; movement is.\n- **{W2}:** There's no power-of-two requirement (some systems prefer it for splitting, but it isn't required).\n- **{W3}:** Routing costs one hash per request regardless.\n\nRelated: Ch. 03 §3.",
    },
    {
        "topic": "Sharding",
        "q": "A consistent-hashing ring with 4 physical nodes and one position per node shows one node holding 41% of keys and another 9%. What do virtual nodes change?",
        "c": "Each physical node owns many small ranges around the ring, so load averages out, and removing a node spreads its keys over all others rather than one neighbor.",
        "w": [
            "Virtual nodes keep a full replica of each physical node's data on the next node in the ring, so the imbalance stops mattering because any node can serve any key's reads.",
            "Virtual nodes let each physical node choose its own hash function, so a node that receives too many keys can switch functions until its share drops back to the average.",
            "Virtual nodes store the ring's membership and routing metadata in one place, so clients can see the imbalance and route traffic away from the overloaded node.",
        ],
        "x": "**{C} is correct.** With one position per node, arc sizes are random and very uneven. Hundreds of virtual positions per node make each node's total share converge to ~1/N. When a node leaves, its many small arcs go to many different successors instead of doubling one neighbor's load. You can also give bigger machines more vnodes.\n\n- **{W1}:** That describes replication, which is a separate concern.\n- **{W2}:** All nodes must share one hash function or routing breaks.\n- **{W3}:** Membership metadata is separate, and steering reads around a hot node doesn't fix where data lives.\n\nRelated: Ch. 03 §3.",
    },
    {
        "topic": "Sharding",
        "q": "A sports app shards its event and comment data by `country`. During a World Cup final hosted in Brazil, what is the most likely outcome?",
        "c": "The Brazil shard becomes a hot shard: one partition takes a huge share of writes and reads while the other shards sit mostly idle, and adding shards does not help.",
        "w": [
            "Nothing noticeable, because the hash function spreads each country's rows evenly across all shards, so a spike in one country is absorbed by the whole cluster.",
            "The cluster rebalances automatically, because sharded databases detect hot partitions and split them, so the Brazil shard is divided before users notice slowdowns.",
            "Writes to other countries start failing, because a shard key with low cardinality forces all shards to share a single write lock while the busiest shard is saturated.",
        ],
        "x": "**{C} is correct.** A low-cardinality, skewed shard key (country) puts all of one country's data on one shard. Traffic follows real-world events, so one shard melts while the others idle. Use a higher-cardinality key (e.g. `match_id` plus a bucket suffix) or split hot keys explicitly.\n\n- **{W1}:** Sharding by country means rows are placed **by** country, not spread across shards.\n- **{W2}:** Some systems split ranges automatically, but they can't split a single key value, and they react slowly.\n- **{W3}:** Shards don't share a global write lock. The others are fine, just underused.\n\nRelated: Ch. 03 §2.",
    },
    {
        "topic": "Sharding",
        "q": "A team running a single Postgres primary at 35% CPU wants to shard \"before we hit scale\". p99 latency issues trace to an N+1 query and a missing index. What's the senior response?",
        "c": "Don't shard yet: fix the query and the index, add replicas or caching if needed, and plan sharding only when a measured limit such as write throughput is getting near.",
        "w": [
            "Shard now, because resharding later is much harder than starting sharded, and every successful system eventually needs to partition its primary database anyway.",
            "Shard now, but only the tables with slow queries, because sharding those tables spreads the expensive scans across machines and removes the latency problem directly.",
            "Replace Postgres with a distributed SQL database now, because it shards automatically, so the team gets all the benefits of sharding with none of the operational cost.",
        ],
        "x": "**{C} is correct.** Sharding is expensive: cross-shard queries, joins and transactions, rebalancing, operational complexity, and it's hard to reverse. Here the database isn't the bottleneck; the queries are. A well-tuned single Postgres handles far more than most products ever need.\n\n- **{W1}:** \"Eventually\" is not a requirement, and premature sharding taxes every feature you build.\n- **{W2}:** Sharding doesn't fix an N+1 or a missing index; those queries would be just as wasteful on every shard.\n- **{W3}:** Distributed SQL has real costs (latency, money, new failure modes), and it still wouldn't fix the bad queries.\n\nRelated: Ch. 03 §2, Ch. 18 §6.",
    },
    {
        "topic": "Sharding",
        "q": "An order service must save an order to its database and publish `OrderPlaced` to Kafka. A crash between the two steps sometimes leaves orders without events. Which pattern fixes this?",
        "c": "A transactional outbox: insert the order and an event row in one local transaction, and have a relay (or CDC) publish the outbox rows to Kafka with retries.",
        "w": [
            "Publish to Kafka first and then write to the database, so that if the database write fails the consumer can detect the missing order and simply ignore the event.",
            "Enable Kafka's exactly-once semantics on the producer, which makes the database write and the publish atomic so that either both happen or neither does.",
            "Wrap the database write and the Kafka publish in a two-phase commit coordinated by the application, which is the standard pattern for most Kafka producers.",
        ],
        "x": "**{C} is correct.** You can't atomically write to two systems, but you *can* atomically write two rows to one database. The relay then delivers outbox rows at least once, so consumers must be idempotent.\n\n- **{W1}:** It just reverses the failure: now you can get events for orders that don't exist, and consumers may act on them before anyone notices.\n- **{W2}:** Kafka's EOS covers Kafka-to-Kafka processing, not your database.\n- **{W3}:** Kafka doesn't participate in XA two-phase commit, and 2PC adds blocking and a coordinator failure mode.\n\nRelated: Ch. 05 §6, Ch. 07 §10.",
    },
]
