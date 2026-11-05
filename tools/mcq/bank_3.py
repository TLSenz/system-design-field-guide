# MCQ bank, part 3: CDNs, API Design, Search, Storage.
# Format: see bank_1.py.

QUESTIONS = [
    # --------------------------------------------------------------------- CDNs
    {
        "topic": "CDNs",
        "q": "Your SPA serves `app.js` from a CDN with `Cache-Control: max-age=31536000`. After each deploy, some users run old JavaScript for hours. What's the standard fix?",
        "c": "Put a content hash into the file name (`app.3f9a1c.js`) and reference it from a short-lived `index.html`, so every deploy creates new URLs that the CDN has never cached.",
        "w": [
            "Purge `app.js` from every CDN edge as the last step of the deploy pipeline, and wait for the purge to complete in all regions before shifting any traffic to the new release.",
            "Lower `max-age` on `app.js` to 60 seconds, so every edge revalidates the file each minute and picks up the new version shortly after a deploy has finished rolling out.",
            "Add a `?v=` query string with the deploy timestamp to the script tag, and configure the CDN to ignore query strings when building cache keys for static asset requests.",
        ],
        "x": "**{C} is correct.** Immutable, content-addressed assets can be cached forever because a changed file is a *different URL*. Only the small HTML entry point needs a short TTL or revalidation. No purge is needed, and old and new versions can coexist during the rollout.\n\n- **{W1}:** Purges are slow, not atomic across PoPs, often rate-limited, and they don't touch browser caches at all.\n- **{W2}:** This throws away most of the caching benefit and still leaves a stale window.\n- **{W3}:** A version query string can work, but telling the CDN to *ignore* query strings means every version shares one cache entry, which defeats the purpose.\n\nRelated: Ch. 11 §4.2.",
    },
    {
        "topic": "CDNs",
        "q": "A news site's origin goes down for 20 minutes. Pages are cached with `Cache-Control: max-age=60, stale-if-error=86400`. What do readers see?",
        "c": "The CDN keeps serving the last cached copy of each page after its 60 seconds run out, because the origin is erroring and the stale copy is still inside the 24-hour error window.",
        "w": [
            "Error pages after 60 seconds, because `max-age` sets the hard limit on how long a cached page may be served, and `stale-if-error` only controls how long the error is cached.",
            "Fresh pages throughout the outage, because `stale-if-error` makes the CDN retry the origin in the background for up to 24 hours until it gets back a successful response.",
            "Cached pages for up to 24 hours regardless of the origin's health, because `stale-if-error` extends the effective TTL of every response to a full day, not only during errors.",
        ],
        "x": "**{C} is correct.** `stale-if-error` lets a cache serve an expired response if revalidation fails with an error (5xx or unreachable), here for up to 24 hours after it went stale. When the origin is healthy, the normal 60-second freshness applies. It's cheap insurance against origin outages.\n\n- **{W1}:** That's the behavior *without* the directive.\n- **{W2}:** It doesn't make anything fresh; it allows serving stale content.\n- **{W3}:** It applies only when the origin errors, not as a general TTL extension.\n\nRelated: Ch. 11 §3.",
    },
    {
        "topic": "CDNs",
        "q": "Your CDN has 300 edge locations. After a cache purge, each edge misses and fetches from your origin at once, and the origin falls over. What does origin shielding do about this?",
        "c": "It adds a regional mid-tier cache that edges fetch through, so 300 edge misses collapse into one or a few origin requests, and the origin is protected from miss storms.",
        "w": [
            "It encrypts traffic between the CDN and the origin with mutual TLS, so only the CDN's own edge servers can reach the origin, which blocks floods from other sources.",
            "It adds firewall rules that block every request to the origin not coming from the CDN, so attackers cannot bypass the CDN and send traffic straight to the origin servers.",
            "It sends traffic to a standby origin in another region whenever the primary origin is slow, so a miss storm is split between two origins instead of hitting only one of them.",
        ],
        "x": "**{C} is correct.** A shield (tiered cache) is a designated regional cache between edges and origin. Edges miss into the shield, the shield coalesces duplicate requests, and only the shield talks to origin. It also raises the overall hit rate for long-tail content.\n\n- **{W1}:** mTLS authenticates the CDN but doesn't reduce request volume.\n- **{W2}:** IP allowlisting is good hygiene, but these are legitimate CDN requests.\n- **{W3}:** That's origin failover, not shielding, and it doesn't coalesce anything.\n\nRelated: Ch. 11 §9.",
    },
    {
        "topic": "CDNs",
        "q": "A team wants to put their logged-in dashboard HTML (which shows the user's name and balances) behind the shared CDN cache to speed it up. What's the core problem?",
        "c": "If the cache key includes the session, every user gets a private entry and the hit rate is near zero; if it doesn't, one user's dashboard can be served to someone else.",
        "w": [
            "CDNs cannot cache HTML responses, only static assets such as images and scripts, so the dashboard would always be fetched from the origin and nothing would be gained.",
            "Caching dashboard pages at the CDN breaks TLS, because the edge would need the user's session key to decrypt the response before it could store a copy for later requests.",
            "Personalized pages are larger than static ones, so caching them would fill the CDN's storage quickly and evict the static assets that actually benefit from being cached.",
        ],
        "x": "**{C} is correct.** A shared cache is only useful for responses many users share. Personalized responses are either uncacheable in practice or a data leak waiting to happen. Instead, cache the shared shell and static assets at the edge, fetch the personal data via an API with `Cache-Control: private`, or use edge compute that assembles personalized pages.\n\n- **{W1}:** CDNs cache HTML routinely.\n- **{W2}:** The CDN terminates TLS anyway; caching doesn't change that.\n- **{W3}:** Size isn't the real issue; correctness and hit rate are.\n\nRelated: Ch. 11 §2, §6.",
    },
    # --------------------------------------------------------------- API Design
    {
        "topic": "API Design",
        "q": "A mobile client calls `POST /payments`. The request times out on a flaky network, and the user taps \"Pay\" again. How should the API prevent a double charge?",
        "c": "Have the client send an `Idempotency-Key` that it reuses on retry; the server stores the key with the result and returns the stored result instead of charging the card again.",
        "w": [
            "Change the endpoint to `PUT /payments`, because the HTTP spec defines PUT as idempotent, so the server will automatically ignore a second identical request from the client.",
            "Reject any second payment from the same user within 60 seconds, because a real user is unlikely to make two different payments that close together within the same minute.",
            "Increase the server-side timeout to 60 seconds, so the original request has time to finish and the client always receives the response before the user can tap again.",
        ],
        "x": "**{C} is correct.** After a timeout, the client can't know whether the charge committed. An idempotency key turns \"retry\" into \"give me the result of attempt X\". The server must store the key atomically with the effect and handle concurrent duplicates (e.g. with a unique constraint).\n\n- **{W1}:** PUT is idempotent by *contract*. The server still has to implement that, and verb choice alone does nothing.\n- **{W2}:** It blocks legitimate payments and still double-charges after 61 seconds.\n- **{W3}:** Networks fail regardless of your timeout, and clients have their own timeouts.\n\nRelated: Ch. 08 §4, Ch. 09 §2.",
    },
    {
        "topic": "API Design",
        "q": "An activity feed API uses `?offset=200&limit=50`. Users report seeing duplicate items and missing items while scrolling, and deep pages are slow. What's the better design?",
        "c": "Cursor (keyset) pagination: return an opaque cursor encoding the last item's sort key and ID, and fetch the next page with `WHERE (created_at, id) < (cursor values)`.",
        "w": [
            "Keep offsets but cache each page for 5 minutes, so that rows inserted while the user scrolls do not shift the window and deep pages are served from the cache instead.",
            "Keep offsets but sort by a random seed stored in the session, so each user sees a stable order that new inserts cannot disturb while they scroll through the feed.",
            "Return the full feed in one response with gzip compression, so the client can page locally and never sees duplicates, missing items or slow pages again while scrolling.",
        ],
        "x": "**{C} is correct.** An offset is a *position*, so inserts and deletes shift what's at position 200, which causes duplicates and gaps. `OFFSET N` also makes the database read and discard N rows. A keyset cursor anchors on *identity* and uses the index directly, so every page costs the same.\n\n- **{W1}:** Cached pages go stale inconsistently with each other, and it doesn't fix deep-offset cost on a miss.\n- **{W2}:** A random sort can't use an index and still shifts when rows are inserted.\n- **{W3}:** Unbounded responses grow forever and waste bandwidth on mobile.\n\nRelated: Ch. 09 §2.",
    },
    {
        "topic": "API Design",
        "q": "Your service verifies JWTs with `jwt.verify(token, key)`, where the algorithm is taken from the token's own header. Why is this a vulnerability?",
        "c": "An attacker can set `alg` to `none`, or to HS256 using your public RSA key as the HMAC secret, and forge tokens your code accepts; always pin the expected algorithms server-side.",
        "w": [
            "It skips the expiry check, because the expiry claim is only verified when the algorithm is passed in explicitly, so expired tokens are accepted until they are revoked by hand.",
            "It slows every request down, because the library has to try every supported algorithm in turn until one of them succeeds, which adds noticeable latency under heavy load.",
            "It breaks key rotation, because the `alg` header tells the library which key ID to use, and trusting it lets clients pick an old key that should already have been retired.",
        ],
        "x": "**{C} is correct.** The token is attacker-controlled input, so letting it choose how it is verified is the bug. `alg: none` skips signatures entirely. *Algorithm confusion* makes the server use a public key as an HMAC secret, which the attacker also has. Pin allowed algorithms server-side, and validate `iss`, `aud` and `exp` too.\n\n- **{W1}:** Expiry checking is independent of algorithm selection.\n- **{W2}:** It doesn't try them all, and performance isn't the issue.\n- **{W3}:** Key selection uses `kid`, not `alg`, and the real risk is forgery, not rotation.\n\nRelated: Ch. 09 §4.",
    },
    {
        "topic": "API Design",
        "q": "A mobile app gets an error from `GET /admin/reports`. How should the client react differently to a 401 versus a 403?",
        "c": "On 401 it should refresh its credentials or send the user to sign in, then retry; on 403 it should stop, because the user is known but not permitted to access the resource.",
        "w": [
            "On 401 it should retry the same request with backoff, because 401 marks a transient server problem; on 403 it should log the user out, because their session has expired.",
            "Both mean the same thing, so the client should handle them identically by clearing the stored token and showing the sign-in screen, then retrying the request afterwards.",
            "On 401 it should show a not-found page, because 401 hides whether the resource exists; on 403 it should refresh the token, since 403 means the token has run out of scopes.",
        ],
        "x": "**{C} is correct.** 401 Unauthorized really means *unauthenticated*: credentials are missing, expired or invalid, so getting new ones may help. 403 Forbidden means the identity is known and the answer is no, and re-authenticating won't change it. (Returning 404 instead of 403 to hide a resource's existence is a separate, valid choice.)\n\n- **{W1}:** 401 isn't a server error, and 403 isn't expiry.\n- **{W2}:** Treating 403 like 401 causes sign-in loops.\n- **{W3}:** It gets both codes wrong.\n\nRelated: Ch. 09 §2.",
    },
    {
        "topic": "API Design",
        "q": "A public API field `price` holds an integer number of cents. You need to support currencies with different minor units. How do you change it without breaking existing clients?",
        "c": "Expand and contract: add a new `amount` object alongside `price`, write both, move clients over and measure usage, then remove `price` after a deprecation period ends.",
        "w": [
            "Change `price` to a decimal string in place and announce it in the changelog, because clients that parse integers will get a clear error and can update their code quickly.",
            "Release `/v2` of every endpoint with the new field right away, and turn `/v1` off the same day so the team doesn't have to maintain two versions of the API in production.",
            "Keep `price` but redefine it to use each currency's minor unit, because the type is still an integer and so no client code needs to change when the meaning changes.",
        ],
        "x": "**{C} is correct.** Additive changes are safe; removals and meaning changes are not. Expand-and-contract lets old and new clients coexist. Track usage of the old field so you know when it's safe to remove.\n\n- **{W1}:** A breaking type change. Mobile clients in the wild can't update quickly.\n- **{W2}:** Versioning may be justified for big changes, but killing v1 the same day breaks everyone.\n- **{W3}:** The worst option: same type, new meaning. Old clients silently show wrong amounts.\n\nRelated: Ch. 09 §3.",
    },
    {
        "topic": "API Design",
        "q": "Your webhook receiver verifies the HMAC signature of each payload but ignores the signed timestamp header. What attack is still possible?",
        "c": "Replay: an attacker who captures one valid signed request can resend it later and it still verifies, so reject timestamps outside a few minutes and dedupe event IDs.",
        "w": [
            "Forgery: without the timestamp, an attacker can create new payloads with valid signatures, because the HMAC secret is derived from the time the webhook was registered.",
            "Reordering: events may arrive out of order, and the timestamp is the only field that lets the receiver apply them in sequence, so the data will slowly become inconsistent.",
            "Nothing: the signature already covers the entire payload, so checking the timestamp too is redundant and only adds failures for senders whose clocks drift a little.",
        ],
        "x": "**{C} is correct.** A signature proves *who* sent the message and that it wasn't modified. It doesn't prove *when*. A tolerance window bounds the replay window, and deduping event IDs closes it entirely.\n\n- **{W1}:** Forging requires the secret; the timestamp doesn't change that.\n- **{W2}:** Ordering is a real concern, but it's a separate one, and timestamps are a weak ordering mechanism anyway.\n- **{W3}:** The payload being intact is exactly why a replay verifies.\n\nRelated: Ch. 09 §6.",
    },
    # ------------------------------------------------------------------- Search
    {
        "topic": "Search",
        "q": "Why can a search engine answer \"documents containing *distributed* AND *consensus*\" over 100M documents in milliseconds, while `LIKE '%consensus%'` in SQL takes minutes?",
        "c": "It keeps an inverted index mapping each term to a sorted posting list of document IDs, so it just intersects two short lists instead of scanning every document's text.",
        "w": [
            "It keeps every document fully in memory as raw text, while SQL reads from disk, so the same full scan runs faster in a search engine because RAM is far quicker than disk.",
            "It keeps a forward index mapping each document to its terms, sorted by document ID, so it can check each document's term list quickly using a binary search per document.",
            "It precomputes and caches the results of every common query at index time, so popular term combinations never have to be evaluated against the documents when queried.",
        ],
        "x": "**{C} is correct.** The inverted index flips the relationship: term → postings (doc IDs, plus frequencies and positions for scoring and phrase queries). A boolean query becomes a merge of sorted lists, with skip lists making it faster still. A leading-wildcard `LIKE` can't use a B-tree and has to scan everything.\n\n- **{W1}:** Being in memory doesn't help if you still scan 100M documents.\n- **{W2}:** That's a forward index, which still visits every document.\n- **{W3}:** Query caches exist, but they're an optimization, not how arbitrary queries are answered.\n\nRelated: Ch. 12 §2.",
    },
    {
        "topic": "Search",
        "q": "In BM25 scoring for the query \"the raft paper\", a document containing *raft* once outranks one containing *the* forty times. Which part of the formula causes this?",
        "c": "Inverse document frequency: *raft* appears in few documents so it carries a high weight, while *the* appears almost everywhere and so contributes close to nothing.",
        "w": [
            "Length normalization: the document with forty occurrences of *the* is longer, and BM25 penalizes long documents hard enough to outweigh any number of term matches.",
            "Term-frequency saturation: after the first few occurrences each extra match adds nothing, so forty matches of *the* score the same as a single match of the term *raft*.",
            "Stop-word removal: BM25 drops common words such as *the* before scoring, so the second document matches no query terms at all and receives a score of exactly zero.",
        ],
        "x": "**{C} is correct.** IDF ≈ log(N / df): rare, discriminative terms dominate the score. Term-frequency saturation (k1) and length normalization (b) also shape BM25, but they aren't what makes *raft* outweigh *the*.\n\n- **{W1}:** Length normalization is a modest adjustment, not an override.\n- **{W2}:** Saturation caps repeated matches, but *the* still contributes. The weights per term differ because of IDF.\n- **{W3}:** Stop-word removal is an analyzer choice, not part of BM25, and many modern setups keep stop words.\n\nRelated: Ch. 12 §3.",
    },
    {
        "topic": "Search",
        "q": "You run hybrid search: BM25 gives scores like 12.7 and 3.1, while vector similarity gives cosine scores like 0.83 and 0.79. How should you combine the two result lists?",
        "c": "Fuse by rank, for example with Reciprocal Rank Fusion (sum of 1/(k + rank)), because the two scores are on unrelated scales and their raw values can't be compared.",
        "w": [
            "Add the raw scores together, because both are relevance scores, and documents that do well on both signals will rise to the top of the combined list on their own.",
            "Min-max normalize each list to 0–1 and average them, which always gives a fair combination, because after normalization both signals are on exactly the same scale.",
            "Use BM25 for queries with fewer than three words and vectors for longer queries, because each method only works well in one of those ranges and combining them adds noise.",
        ],
        "x": "**{C} is correct.** BM25 scores are unbounded and depend on the query and corpus; cosine scores are bounded and tightly clustered. RRF ignores magnitudes and rewards documents that rank well in both lists. It's robust and needs no tuning beyond k (≈60).\n\n- **{W1}:** BM25 would swamp the vector scores completely.\n- **{W2}:** Normalization can work with tuning, but it's sensitive to outliers and per-query distributions. \"Always fair\" is false.\n- **{W3}:** It's a crude heuristic that throws away the benefit of combining both.\n\nRelated: Ch. 12 §3.",
    },
    {
        "topic": "Search",
        "q": "An enterprise search returns the top 20 hits, then removes those the user isn't allowed to see. Users see \"About 1,200 results\" with pages containing 3 items. What's the right design?",
        "c": "Apply permissions inside the query as a filter (e.g. on ACL group IDs indexed with each document), so counts, pages and facets only ever reflect documents the user can see.",
        "w": [
            "Fetch the top 200 hits instead of 20 before filtering, so that after the restricted documents are removed there are almost always enough results left to fill every page.",
            "Keep post-filtering but hide the total count and the facet numbers, so users cannot see that the page sizes don't match and the inconsistency goes unnoticed by them.",
            "Build a separate index for every user containing only the documents they can access, so no filtering at query time is needed and each user's results are always correct.",
        ],
        "x": "**{C} is correct.** Post-filtering breaks pagination and counts, and the counts and facets can *leak* that restricted documents exist (\"3 results in Legal/Layoffs\"). Index the ACL (groups, tenant) and filter in the query. Filters are cached and cheap.\n\n- **{W1}:** It's still wrong at the margins, costs 10× the work, and still leaks counts.\n- **{W2}:** It hides the symptom; the leak and broken pages remain.\n- **{W3}:** Per-user indexes multiply storage and indexing by the number of users. That only works for a handful of tenants.\n\nRelated: Ch. 12 §9, §10.",
    },
    {
        "topic": "Search",
        "q": "You index arbitrary customer JSON into Elasticsearch with dynamic mapping. Over months the cluster slows down, master nodes run out of heap, and you hit the field limit. What happened?",
        "c": "Mapping explosion: every new JSON key became a new field in the mapping, so the cluster state grew to thousands of fields that every node has to hold and synchronize.",
        "w": [
            "Shard explosion: dynamic mapping creates a new shard each time a new field appears, so the cluster now has thousands of tiny shards that the master node has to track.",
            "Result explosion: queries over arbitrary JSON match far too many documents, so every search returns millions of hits and the coordinating nodes run out of heap memory.",
            "Segment explosion: arbitrary JSON prevents segment merging, so each index accumulates thousands of small segments that slow both indexing and searching down over time.",
        ],
        "x": "**{C} is correct.** Field definitions live in the cluster state, which is replicated to every node. Unbounded keys (user IDs as keys, free-form attributes) make it grow without limit. Use explicit mappings with `dynamic: strict` or `false`, the `flattened` type, or a key/value nested pattern for arbitrary attributes.\n\n- **{W1}:** Fields don't create shards.\n- **{W2}:** Hit counts don't grow because of mappings.\n- **{W3}:** Segment merging is unaffected by the shape of the JSON.\n\nRelated: Ch. 12 §6.",
    },
    # ------------------------------------------------------------------ Storage
    {
        "topic": "Storage",
        "q": "Users upload videos up to 4 GB through your API servers, which stream the bytes on to S3. During peaks the API runs out of memory and uploads time out. What's the better design?",
        "c": "Have the API issue presigned (multipart) upload URLs, so clients send the bytes straight to object storage while the API only handles authorization and metadata.",
        "w": [
            "Give the API servers more memory and raise the request timeout to 30 minutes, so the largest uploads can be buffered and forwarded completely without ever timing out.",
            "Compress each upload on the API server before forwarding it to S3, so fewer bytes cross the network and the API spends less time holding each upload in its memory.",
            "Store the uploads on the API servers' local disks and copy them to S3 with a nightly batch job, so the API does not have to wait for S3 while the client is uploading.",
        ],
        "x": "**{C} is correct.** Proxying bulk bytes ties up API memory, bandwidth, threads and connections, and makes deploys and timeouts painful. Presigned URLs keep the API in the control plane while object storage handles the data plane, with multipart giving resumable uploads.\n\n- **{W1}:** It's expensive and still caps your concurrency.\n- **{W2}:** Video is already compressed, and compressing it again burns CPU for nothing.\n- **{W3}:** Local disks make instances stateful, and files are lost if an instance dies before the batch runs.\n\nRelated: Ch. 13 §3.",
    },
    {
        "topic": "Storage",
        "q": "Your S3 bill keeps rising although the number of stored objects is flat. Investigation shows thousands of multipart uploads that clients started but never completed. What's going on?",
        "c": "Incomplete multipart uploads keep their parts stored and billed until someone aborts them; add a lifecycle rule that aborts incomplete uploads after a few days.",
        "w": [
            "Incomplete multipart uploads are completed automatically after 7 days with whatever parts arrived, creating corrupt objects that are hidden from normal listings but billed.",
            "Incomplete multipart uploads are deleted by S3 after 24 hours, so the rising bill must come from request charges on the retries that the clients keep making.",
            "Incomplete multipart uploads lock their bucket's storage class at the most expensive tier, so every other object in the bucket is billed at that higher rate too.",
        ],
        "x": "**{C} is correct.** Parts of an unfinished multipart upload are stored and billed, and they don't show up as objects in a normal listing, which is why the object count looks flat. An `AbortIncompleteMultipartUpload` lifecycle rule is standard hygiene.\n\n- **{W1}:** S3 never auto-completes uploads.\n- **{W2}:** There is no automatic cleanup unless you configure it.\n- **{W3}:** Storage classes are per object; no such effect exists.\n\nRelated: Ch. 13 §3.3.",
    },
    {
        "topic": "Storage",
        "q": "A team stores user-uploaded images as `bytea` columns in their main Postgres database, next to the image metadata. As the product grows, what's the main reason to move the bytes to object storage?",
        "c": "Blobs bloat the database: backups, replication, vacuum and restores all slow down, and expensive database storage is used for bytes that need none of its querying or transactions.",
        "w": [
            "Postgres cannot store values larger than 1 MB in a single column, so as users upload higher-resolution images the inserts will start failing with size errors in production.",
            "Storing images in a database is a security risk, because anyone with read access to the metadata table can also read every image, while object storage is encrypted by default.",
            "Databases cannot serve binary data over HTTP, so a separate image server must read each image from Postgres and serve it, which doubles the latency of every image request.",
        ],
        "x": "**{C} is correct.** Use each store for what it's good at. Object storage is cheap, effectively unlimited, durable and CDN-friendly. The database is good for small, structured, queryable, transactional metadata. Keep a row with the object key, size, type, owner and status.\n\n- **{W1}:** Postgres `bytea` can hold up to 1 GB (via TOAST). It's a bad idea, but not a hard limit at 1 MB.\n- **{W2}:** Access control applies either way, and databases support encryption too.\n- **{W3}:** Serving through an app is an inefficiency, but the bigger problems are database size, backups and cost.\n\nRelated: Ch. 13 §1, §8.",
    },
    {
        "topic": "Storage",
        "q": "You're estimating costs for a photo-sharing app: 1M uploads/day at 2 MB average, and each photo is viewed about 200 times. Which cost tends to dominate?",
        "c": "Egress (bandwidth for serving), because each stored byte is served about 200 times, so delivery quickly outgrows storage; CDN caching and resized variants matter most.",
        "w": [
            "Storage, because 2 TB of new data per day adds up to petabytes within a few years, and keeping every photo forever in hot object storage costs far more than serving it.",
            "Compute for image resizing, because every photo must be resized into several formats on upload, and the CPU time for that work is larger than any storage or network cost.",
            "Database costs, because each photo needs a metadata row and every view updates a counter, so the database ends up as the most expensive component in the system.",
        ],
        "x": "**{C} is correct.** Rough math: 2 TB/day stored, but ~400 TB/day served at 200 views per photo. Bandwidth pricing per GB is typically several times storage pricing per GB-month, and the served volume is 200× larger. Cut it with CDN caching, right-sized variants, and modern formats like WebP and AVIF.\n\n- **{W1}:** Storage grows steadily but stays far below egress (and can be tiered to colder classes).\n- **{W2}:** Resizing is a one-time cost per upload.\n- **{W3}:** Metadata is tiny, and view counters should be batched anyway.\n\nRelated: Ch. 11 §7, Ch. 13 §4.",
    },
]
