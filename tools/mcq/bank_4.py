# MCQ bank, part 4: Microservices, Observability, Reliability, Senior Judgment.
# Format: see bank_1.py.

QUESTIONS = [
    # ------------------------------------------------------------ Microservices
    {
        "topic": "Microservices",
        "q": "A 12-engineer startup's monolith has become tangled: any change risks breaking unrelated features. The CTO proposes splitting it into 15 microservices. What's usually the better first step?",
        "c": "A modular monolith: one deployable, but with enforced module boundaries, a schema per module and calls only through defined interfaces, so services can be extracted later.",
        "w": [
            "Split into microservices now, because independent deployability is the only reliable way to enforce boundaries, and the team will need the separation anyway as it grows.",
            "Split into three or four services sharing the existing database, so that teams can deploy independently while avoiding the cost of migrating data between separate schemas.",
            "Rewrite the monolith from scratch in a new framework with a cleaner structure, because the tangled code is a sign that the original technology choices were the real problem.",
        ],
        "x": "**{C} is correct.** The problem is *coupling*, not deployment units. Microservices add network failures, distributed data, deployment overhead and observability needs, which is a lot for 12 engineers. A modular monolith fixes the boundaries first, and well-bounded modules are cheap to extract later if a real need appears (scaling, team autonomy).\n\n- **{W1}:** Splitting a tangled codebase usually gives a *distributed* tangle, which is worse.\n- **{W2}:** A shared database keeps the coupling and adds network hops: the \"distributed monolith\".\n- **{W3}:** Big-bang rewrites are notoriously risky, and the coupling problem is about design, not the framework.\n\nRelated: Ch. 16 §2.",
    },
    {
        "topic": "Microservices",
        "q": "Sales, Shipping and Billing teams all have a `Customer` model, with different fields and rules. An architect wants one shared `Customer` service used by all three. What does domain-driven design suggest?",
        "c": "Let each bounded context keep its own customer model and language, linked by a shared ID and integrated through events or APIs, instead of forcing one model to serve all three.",
        "w": [
            "Build the shared Customer service, because a single canonical model removes duplication and guarantees that all three teams always see consistent customer data everywhere.",
            "Put the three models in one shared database schema with a column for each team's fields, so the data stays in one place while each team only reads the columns it needs.",
            "Merge the Sales, Shipping and Billing teams into one team, because three different models of the same entity show the organization is split along the wrong lines.",
        ],
        "x": "**{C} is correct.** A *bounded context* is a boundary within which a model is consistent. \"Customer\" legitimately means different things to Sales (lead, segment), Shipping (addresses) and Billing (payment terms). A single shared model becomes a bloated, coupled bottleneck that every team must coordinate changes on.\n\n- **{W1}:** Canonical enterprise models are a well-known anti-pattern for exactly this reason.\n- **{W2}:** That's still shared coupling, just at the schema level.\n- **{W3}:** Different models in different contexts are normal, not a sign of bad org design.\n\nRelated: Ch. 16 §3.",
    },
    {
        "topic": "Microservices",
        "q": "Which of these observations is the weakest evidence that your microservice boundaries are drawn in the wrong place?",
        "c": "Each service is small and owns a single, narrowly scoped responsibility, so the system has many services and each one changes only for one kind of business reason.",
        "w": [
            "Rendering a single page requires a chain of eight synchronous calls across services, so latency and failure probability grow with every hop added to a request.",
            "Most features require coordinated changes and deploys across three or more services, so teams constantly wait for each other before anything can ship to users.",
            "Several services read and write the same database tables directly, so a schema change in one service regularly breaks the other services that depend on those tables.",
        ],
        "x": "**{C} is correct** (it's the *weakest* evidence). Single, cohesive responsibilities are what you want. The other three are classic symptoms of wrong boundaries:\n\n- **{W1}:** Chattiness means the data and behavior needed together were split apart.\n- **{W2}:** Lockstep changes mean the services aren't independent in practice.\n- **{W3}:** Shared tables mean shared coupling. It's a distributed monolith.\n\nToo many tiny services can be its own problem, but it isn't evidence that the boundaries are misplaced.\n\nRelated: Ch. 16 §3.",
    },
    {
        "topic": "Microservices",
        "q": "The Orders service publishes `OrderPlaced`. The Payments team asks Orders to instead publish `ChargeCard` to their topic. What's the difference between the two messages?",
        "c": "`OrderPlaced` is an event, a past-tense fact any number of services can react to; `ChargeCard` is a command, a request for one handler to act, which couples Orders to Payments.",
        "w": [
            "`OrderPlaced` is a command because it triggers work in other services, while `ChargeCard` is an event, because it describes something that will happen to the card later.",
            "They are equivalent: both are messages on a topic, the name is a naming convention only, and consumers behave the same way no matter how the message is phrased.",
            "`OrderPlaced` must be consumed synchronously, because it is a fact other services depend on, while `ChargeCard` can be asynchronous, because commands may be retried later.",
        ],
        "x": "**{C} is correct.** Events announce what happened. The publisher doesn't know or care who listens, so adding a new consumer requires no change to Orders. Commands tell a specific receiver what to do, with an expected outcome. Both are useful, but publishing commands for other teams' work moves their logic into your service.\n\n- **{W1}:** It gets the two definitions backwards.\n- **{W2}:** The semantics matter for ownership, coupling and error handling.\n- **{W3}:** Either can be sync or async; that's not the distinction.\n\nRelated: Ch. 16 §4.",
    },
    {
        "topic": "Microservices",
        "q": "The Recommendations service needs each user's recent purchases, which the Orders service owns. Which approach is NOT appropriate?",
        "c": "Recommendations reads the Orders service's database tables directly with a read-only user, since read-only access can't corrupt the data that the Orders service owns.",
        "w": [
            "Recommendations calls the Orders service's API for recent purchases, with caching and a timeout, accepting a runtime dependency on Orders being available.",
            "Recommendations subscribes to `OrderPlaced` events and keeps its own local read model of recent purchases per user, accepting that it may lag a few seconds behind.",
            "Orders publishes its data to a shared analytics store such as a warehouse, and Recommendations reads it from there for its batch jobs that run once per day.",
        ],
        "x": "**{C} is the inappropriate one.** Read-only access still couples Recommendations to Orders' *internal schema*. Orders can no longer rename a column, split a table or change storage without breaking another team, so the boundary is gone.\n\nThe others are all valid trade-offs:\n\n- **{W1}:** A synchronous API is simple and fresh, but adds runtime coupling.\n- **{W2}:** Events plus a local read model give autonomy and speed, at the cost of eventual consistency.\n- **{W3}:** A shared *derived* store works well for analytics and batch use.\n\nRelated: Ch. 16 §5.",
    },
    # ------------------------------------------------------------ Observability
    {
        "topic": "Observability",
        "q": "A team writes: \"Our SLA is that 99.9% of requests succeed, measured by our SLO.\" Which definition set is correct?",
        "c": "The SLI is the measured indicator (share of successful requests), the SLO is the internal target for it (99.9%), and the SLA is the customer contract with penalties.",
        "w": [
            "The SLA is the internal target the team aims for, the SLO is the external contract that carries penalties, and the SLI is the dashboard where both are displayed.",
            "The SLI is the target (99.9%), the SLO is the contract with customers, and the SLA is the raw measurement that the monitoring system collects for each request.",
            "All three terms are interchangeable names for an availability percentage; vendors use different words for the same thing depending on their marketing material.",
        ],
        "x": "**{C} is correct.** Indicator → objective → agreement. SLOs should be *stricter* than SLAs, so you get warned and react before you owe customers money. Internal services often have SLOs without any SLA.\n\n- **{W1}:** It swaps SLA and SLO.\n- **{W2}:** It shuffles all three.\n- **{W3}:** The distinctions matter, because they are owned by different people (engineering vs. legal) and have different consequences.\n\nRelated: Ch. 14 §5.",
    },
    {
        "topic": "Observability",
        "q": "A service has a 99.9% availability SLO over a 30-day window and handles 100M requests in that window. What is its error budget?",
        "c": "100,000 failed requests (0.1% of 100M) over the 30 days, which in time terms is about 43 minutes of full downtime spread across the whole window.",
        "w": [
            "99.9M successful requests over the 30 days, because the error budget is the number of requests that must succeed to meet the objective set for the window.",
            "1M failed requests (1% of 100M) over the 30 days, because the budget includes a safety margin of ten times the SLO's allowed failure rate for the period.",
            "43 minutes per day of allowed downtime, because the 0.1% budget is applied to each day separately to keep the service from spending it all at once.",
        ],
        "x": "**{C} is correct.** Error budget = 1 − SLO = 0.1% of events in the window: 100k bad requests, or about 43.2 minutes if you think in full-outage time (30 × 24 × 60 × 0.001). Spend it on risk (deploys, experiments). When it's gone, prioritize reliability.\n\n- **{W1}:** That's the success target, not the budget.\n- **{W2}:** There's no built-in 10× margin; 1% would be a 99% SLO.\n- **{W3}:** 43 minutes is per *30 days*, not per day (per day it's about 1.4 minutes).\n\nRelated: Ch. 14 §6.",
    },
    {
        "topic": "Observability",
        "q": "Your multi-window burn-rate alert fires: over the last hour the service burned its 30-day error budget at 14.4×. What does this mean and what's the right response?",
        "c": "At this pace the whole 30-day budget would be gone in about two days, and roughly 2% of it was spent in the last hour alone, so it's a page-worthy fast burn.",
        "w": [
            "The error rate over the last hour was 14.4%, which is above the 10% threshold for a page, so an engineer should be woken up to investigate the failures right away.",
            "The p99 latency was 14.4× the baseline for the last hour, which affects few users, so the right response is a ticket for the team to look at during working hours.",
            "The service used 14.4% of its CPU budget in the last hour, which means it is close to saturation, so the autoscaler should be triggered to add capacity immediately.",
        ],
        "x": "**{C} is correct.** Burn rate = how fast you're consuming budget relative to a pace that would use exactly 100% over the window. 30 days ÷ 14.4 ≈ 2.08 days, and 1 h × 14.4 / 720 h ≈ 2% of the budget. Google's SRE workbook uses 14.4× over 1 h (confirmed by a short window) as the classic fast-burn page.\n\n- **{W1}:** For a 99.9% SLO, a 14.4× burn means an error rate of 1.44%, not 14.4%.\n- **{W2}:** Burn rate is about the SLI the SLO is defined on, and this pace is urgent.\n- **{W3}:** It isn't a CPU metric.\n\nRelated: Ch. 14 §6.",
    },
    {
        "topic": "Observability",
        "q": "A developer adds `user_id` as a Prometheus label on the request-latency histogram \"to debug slow users.\" The metrics backend starts falling over. Why, and where should `user_id` go instead?",
        "c": "Every distinct label value creates new time series, so millions of users multiply the series count past what the TSDB can hold; put `user_id` in logs or trace attributes.",
        "w": [
            "Prometheus labels must be numeric, so string IDs force a conversion on every scrape that overloads the server; hash `user_id` to an integer before using it as a label.",
            "Histograms don't support labels at all, so the extra label makes every scrape fail and retry repeatedly; move `user_id` to a separate counter metric used for debugging.",
            "User IDs are personal data, and Prometheus throttles any metric containing personal data, which slows ingestion down; encrypt `user_id` before attaching it as a label.",
        ],
        "x": "**{C} is correct.** Metrics cost scales with *cardinality*: series = product of label value counts. A histogram already has ~10–20 bucket series per label combination, so adding a million users means tens of millions of series. Logs and traces are per-event documents where high-cardinality fields are fine. Use exemplars to link a metric to specific traces.\n\n- **{W1}:** Labels are strings. Hashing still leaves a million distinct values.\n- **{W2}:** Histograms support labels. Moving to a counter has the same cardinality problem.\n- **{W3}:** PII is a real concern, but it isn't why the backend fell over, and encryption keeps the cardinality.\n\nRelated: Ch. 14 §2.",
    },
    {
        "topic": "Observability",
        "q": "The on-call engineer gets paged for \"CPU > 85%\" several times a week; each time, users were unaffected. What alerting change does SRE practice recommend?",
        "c": "Page on user-facing symptoms such as SLO burn rate on errors and latency, and move cause metrics like CPU to dashboards and tickets for investigation and capacity planning.",
        "w": [
            "Raise the CPU threshold to 95% and require it to last five minutes, so the alert only fires when the machine is truly saturated and users are more likely to be affected.",
            "Keep the CPU page but route it to a secondary on-call engineer, so the primary is only disturbed by alerts that have proven to be more serious over the past month.",
            "Add more cause-based pages, such as memory, disk and connection counts, so the on-call engineer gets a complete picture and can tell real problems from noisy ones.",
        ],
        "x": "**{C} is correct.** High CPU is often fine (that's what you pay for). A page should mean \"users are hurting or soon will be, act now\". Pages that are routinely ignorable train people to ignore pages, which is how real incidents get missed.\n\n- **{W1}:** It's still a cause-based page that can fire while users are fine, or stay silent while they suffer from something else.\n- **{W2}:** It just moves the alert fatigue to someone else.\n- **{W3}:** More noise makes it worse.\n\nRelated: Ch. 14 §7.",
    },
    {
        "topic": "Observability",
        "q": "You sample 1% of traces with head-based sampling. During an incident, almost none of the slow or failing requests have a trace. What would tail-based sampling change?",
        "c": "The keep-or-drop decision is made after the trace finishes, so you can keep every error and slow trace plus a small baseline, at the cost of buffering spans in a collector.",
        "w": [
            "The keep-or-drop decision is made by each service independently, so services under stress can raise their own sampling rate automatically to capture more of the failures.",
            "The sampling rate is applied only to the last span of each trace, so the full set of earlier spans is always stored, which captures the request path for slow requests.",
            "Tail sampling is cheaper because it drops spans at the source, before they are sent, so the saved budget can be spent on a higher sampling rate for all of the traces.",
        ],
        "x": "**{C} is correct.** Head sampling decides at the root span, before anyone knows whether the request will be interesting, so 99% of failures are thrown away. Tail sampling waits for the whole trace (in an OpenTelemetry Collector, for example) and keeps traces by policy: errors, latency above a threshold, specific routes.\n\n- **{W1}:** Independent per-service decisions produce *broken* traces with missing spans.\n- **{W2}:** That isn't a real sampling scheme.\n- **{W3}:** It's the other way around: tail sampling is *more* expensive, because every span must be sent and buffered before the decision.\n\nRelated: Ch. 14 §3.",
    },
    # -------------------------------------------------------------- Reliability
    {
        "topic": "Reliability",
        "q": "The business says: \"After a disaster we can lose at most 5 minutes of orders, and we must be taking orders again within 1 hour.\" How do these map to RPO and RTO?",
        "c": "RPO is 5 minutes, the maximum data loss measured in time, and RTO is 1 hour, the maximum time until the service is restored to working order again.",
        "w": [
            "RTO is 5 minutes, the maximum data loss measured in time, and RPO is 1 hour, the maximum time until the service is restored to working order.",
            "RPO is 1 hour and RTO is 5 minutes, because the recovery point is about how long the restore takes and the recovery time is about the backups.",
            "Both are 1 hour, because RPO and RTO are two names for the same recovery target and the business always states the stricter number on its own.",
        ],
        "x": "**{C} is correct.** RPO (Recovery Point Objective) is how far back in time the data you recover may be, which drives backup frequency and replication. RTO (Recovery Time Objective) is how long you can be down, which drives failover automation and runbooks. Here: continuous WAL archiving or async replication (RPO 5 min) and a rehearsed one-hour failover (RTO).\n\n- **{W1}:** It swaps the two definitions.\n- **{W2}:** It also swaps them, with made-up reasoning.\n- **{W3}:** They are different targets with different costs.\n\nRelated: Ch. 15 §1.",
    },
    {
        "topic": "Reliability",
        "q": "A circuit breaker opened after a downstream service failed. After the 30-second cooldown, it moves to HALF_OPEN. What happens in that state?",
        "c": "A limited number of trial requests are let through; if they succeed the breaker closes, and if they fail it opens again, so recovery is tested without a full flood.",
        "w": [
            "Half of all requests are let through, and the other half fail fast, so the downstream receives a reduced but steady load while it recovers from the failure.",
            "All requests are let through with a doubled timeout, so slow responses from a recovering downstream are tolerated instead of tripping the breaker open again.",
            "No requests are let through, but the breaker reports its state to the metrics system so that an operator can decide manually whether to close it again.",
        ],
        "x": "**{C} is correct.** HALF_OPEN is a probe state: let a few requests through to test whether the dependency recovered. If you immediately sent full traffic, a barely recovered service would be knocked over again, and the breaker would flap.\n\n- **{W1}:** It isn't a 50% throttle. Typically only one or a handful of probes are allowed.\n- **{W2}:** Longer timeouts would make callers hang on a still-broken dependency.\n- **{W3}:** Breakers recover automatically. Manual-only reset defeats the point.\n\nRelated: Ch. 15 §3.4.",
    },
    {
        "topic": "Reliability",
        "q": "For a multi-region active-passive setup between Virginia and Frankfurt (~90 ms round trip), someone proposes synchronous database replication to get zero data loss on failover. Why is it usually rejected?",
        "c": "Every commit would wait at least one ~90 ms cross-ocean round trip, adding that to write latency and throttling throughput, and a Frankfurt outage would stall all writes.",
        "w": [
            "Synchronous replication is physically impossible beyond about 50 ms of latency, because the database's protocol times out and refuses to commit transactions at that distance.",
            "Synchronous replication doubles storage costs in both regions, because each region has to keep a full extra copy of the other region's write-ahead log for every write.",
            "Synchronous replication prevents taking backups in either region, because the replication stream holds a lock on the data files while transactions are being committed.",
        ],
        "x": "**{C} is correct.** The speed of light sets the floor. Each commit waits for the remote acknowledgement, so per-transaction latency rises by ~90 ms+ and contention on hot rows grows. Most teams accept a small RPO with async replication, or use region-local quorums with async cross-region copies. Systems like Spanner pay this cost deliberately where it's worth it.\n\n- **{W1}:** It's possible, just slow. Spanner-style systems do it.\n- **{W2}:** Storage isn't the concern.\n- **{W3}:** Backups work fine with sync replication.\n\nRelated: Ch. 04 §8, Ch. 15 §5.",
    },
    {
        "topic": "Reliability",
        "q": "A SaaS platform splits its customers into 20 independent \"cells\", each with its own app servers, database and queues, behind a thin routing layer. What's the main benefit?",
        "c": "Blast-radius containment: a bad deploy, a poison message or an overloaded tenant takes down one cell, about 5% of customers, instead of the entire platform at once.",
        "w": [
            "Lower latency for every request, because each cell is smaller than one large deployment, so requests always travel a shorter network path to reach the right database.",
            "No need for a routing layer, because each customer is permanently assigned to a cell by DNS, so the platform has no shared component that could fail on its own.",
            "Strong consistency across all customers, because each cell has its own database, so transactions that span customers in different cells are always serializable.",
        ],
        "x": "**{C} is correct.** Cells bound the damage of any single failure. You also deploy cell by cell (an extra canary dimension) and scale by adding cells. The costs are a routing layer, harder cross-cell operations, and more infrastructure to run.\n\n- **{W1}:** Latency isn't automatically lower; the router adds a hop.\n- **{W2}:** You *need* a router (or a cell-aware DNS mapping), and it must be kept extremely simple.\n- **{W3}:** Cross-cell operations get *harder*, not consistent for free.\n\nRelated: Ch. 15 §7.",
    },
    {
        "topic": "Reliability",
        "q": "Your database backups run nightly, are encrypted, and are copied to a second region. An auditor asks how you know you can recover. Which answer actually demonstrates it?",
        "c": "We restore a recent backup to an isolated environment on a schedule, time it against our RTO, and run integrity checks and row counts against the expected values.",
        "w": [
            "Backups are produced by our provider's managed service, which reports a 100% success rate for every scheduled job over the past year in its monitoring dashboard.",
            "Backups are encrypted with keys in a hardware security module and stored in two regions, so they cannot be lost or tampered with even if one region fails entirely.",
            "Backups are checked for size and checksum right after they are written, so we know each file is complete and matches exactly what the database wrote out that night.",
        ],
        "x": "**{C} is correct.** A backup you haven't restored is a hope, not a backup. Only a regular restore test proves the backup is complete and usable, the keys are accessible, the procedure works, and it fits your RTO.\n\n- **{W1}:** \"Job succeeded\" doesn't mean \"data is restorable\".\n- **{W2}:** Encryption and geography are necessary but don't prove recoverability. Lost keys make perfect backups useless.\n- **{W3}:** Checksums prove the file wasn't corrupted after writing, not that it contains a consistent, restorable database.\n\nRelated: Ch. 15 §6.",
    },
    # ------------------------------------------------- Cross-cutting / Senior Judgment
    {
        "topic": "Cross-cutting / Senior Judgment",
        "q": "During a traffic spike the database is at 100% CPU and the app tier at 20%. Someone scales the app tier from 10 to 60 instances. What most likely happens?",
        "c": "It gets worse: more instances open more connections and send more concurrent queries to an already saturated database, so latency and error rates rise.",
        "w": [
            "Latency improves, because each app instance now handles fewer requests at once, so requests spend less time queued in the app before reaching the database.",
            "The database scales with the load, because managed databases add CPU automatically when connection counts grow, so the extra instances are absorbed safely.",
            "Little changes, because the cache in front of the database absorbs the extra queries, so the larger app tier only adds cost without affecting the database.",
        ],
        "x": "**{C} is correct.** Scale the bottleneck, not whatever is easy to scale. Extra app instances add connection pressure, lock contention and retries to the saturated component. Better moves: shed or queue load, fix the expensive queries, add caching or replicas, and bound concurrency with connection pools or a proxy like PgBouncer.\n\n- **{W1}:** The app wasn't where the time was spent.\n- **{W2}:** Most databases don't scale CPU instantly with connections. More connections usually *reduce* throughput.\n- **{W3}:** If the cache were absorbing load, the database wouldn't be at 100%.\n\nRelated: Ch. 18 §6.",
    },
    {
        "topic": "Cross-cutting / Senior Judgment",
        "q": "An order's status lives in Postgres, is cached in Redis, indexed in Elasticsearch and copied to the warehouse. The four disagree. Which statement reflects good \"source of truth\" thinking?",
        "c": "One store is designated where the status is decided (here Postgres); the other copies are derived, can be rebuilt from it, and on any conflict the source wins.",
        "w": [
            "Whichever store was updated most recently is the source of truth for that order, so conflicts should be resolved by comparing timestamps across the four stores.",
            "The cache is the source of truth, because it is what users actually see, so the database and the search index should be corrected to match the cached value.",
            "Each store is its own source of truth for its readers, and there is no single authority, because every system was built for a different purpose and audience.",
        ],
        "x": "**{C} is correct.** For each fact there should be one place where it is *decided*. Everything else is a derived projection (cache, index, warehouse) that can lag and must be rebuildable. That makes conflict resolution obvious and recovery possible. Different facts can have different sources of truth.\n\n- **{W1}:** Last-write-wins across copies gives clock-skew bugs and lets a stale derived copy overwrite the truth.\n- **{W2}:** The cache is the most disposable copy of all.\n- **{W3}:** Without a designated authority, disagreements can never be resolved.\n\nRelated: Ch. 00 §2, Ch. 05 §1.",
    },
    {
        "topic": "Cross-cutting / Senior Judgment",
        "q": "An endpoint has a 150 ms latency budget and calls three independent downstream services, each with p99 ≈ 40 ms. How should it call them?",
        "c": "In parallel with per-call timeouts, so total latency is roughly that of the slowest call, about 40–60 ms at p99, leaving room for its own work and the network.",
        "w": [
            "Sequentially, in order of importance, so the most critical call finishes first and the endpoint can return early if a later call goes over the latency budget.",
            "Sequentially with a cache in front of each call, because cache hits make the sequential path fast enough and keep the code simpler than handling concurrency.",
            "In parallel with hedged requests to every dependency on every call, so each call takes the faster of two attempts and the tail latency drops to the median.",
        ],
        "x": "**{C} is correct.** Independent calls should run concurrently: total ≈ max, not sum. Sequential p99s add up to ~120 ms before any of your own work, and the overall p99 of a sequential chain is worse than the sum suggests. Timeouts keep one slow dependency from consuming the budget.\n\n- **{W1}:** Sequential calls burn most of the budget, and \"returning early\" means partial responses by design.\n- **{W2}:** Misses still pay the full sequential cost, so the p99 is unchanged.\n- **{W3}:** Hedging every call doubles downstream load. Hedge selectively, after a delay near p95.\n\nRelated: Ch. 00 §5.",
    },
    {
        "topic": "Cross-cutting / Senior Judgment",
        "q": "Thirty minutes into a design interview for a URL shortener, which statement best demonstrates senior-level judgment?",
        "c": "\"The mapping table in Postgres is the source of truth; the cache and analytics are derived. At 10× traffic, cache memory runs out first, so here's how we'd shard it.\"",
        "w": [
            "\"We'll use Kafka for events, Redis for caching and Cassandra for storage, because these are the proven technologies that large companies use for this kind of system.\"",
            "\"This is a well-known pattern, so it will scale well; let's use microservices for each component so that every part of the design can be scaled independently later.\"",
            "\"Let's design for a billion requests per second from day one, so that we never need to re-architect, since rewriting a system later is always more costly than building big.\"",
        ],
        "x": "**{C} is correct.** It names the source of truth, separates it from derived state, and reasons about what breaks first under growth and what you'd do about it. That's what interviewers look for: trade-offs grounded in numbers, not technology lists.\n\n- **{W1}:** Tool-naming without requirements or reasons.\n- **{W2}:** \"Scales well\" and \"microservices\" without justification are red flags.\n- **{W3}:** Over-engineering with no requirements behind it ignores cost and complexity.\n\nRelated: Ch. 22 §11.",
    },
    {
        "topic": "Cross-cutting / Senior Judgment",
        "q": "You're replacing 30 instances behind a load balancer with a new version and must not drop any requests. Which sequence achieves a true zero-downtime rolling deploy?",
        "c": "Per batch: fail readiness so the LB stops routing, let in-flight requests drain, send SIGTERM and shut down gracefully, start new instances, wait until healthy, then continue.",
        "w": [
            "Start all 30 new instances at once, switch the load balancer over to them in one step, and immediately terminate the old instances once the first health checks pass.",
            "Per batch: send SIGKILL to the old instances so they stop quickly, start the new ones, and let client retries absorb any requests that were in flight during the swap.",
            "Per batch: start the new instances and add them to the load balancer immediately, then stop the old ones; health checks can be skipped because the build was tested.",
        ],
        "x": "**{C} is correct.** Zero downtime needs three things: no new traffic to an instance that's about to stop (readiness off, then deregistration), in-flight work finishes (connection draining plus graceful SIGTERM handling), and new instances only take traffic once they're actually ready. Keep enough capacity serving during each batch.\n\n- **{W1}:** Blue/green can work, but terminating old instances right away drops their in-flight requests, and one early health check isn't proof of readiness.\n- **{W2}:** SIGKILL drops in-flight requests, and non-idempotent requests can't be safely retried.\n- **{W3}:** Without readiness gating, cold or broken instances receive traffic.\n\nRelated: Ch. 01 §5.",
    },
]
