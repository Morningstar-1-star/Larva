Android integration notes
This repository is the remote catalogue, not the parser runtime. Keep those responsibilities separate.
Recommended flow
The Android app downloads the relevant catalogue JSON from the repository's raw.githubusercontent.com URL.
It parses schemaVersion, category, and sources.
A record containing refFile/refId is a category reference. Resolve it to the canonical full record from that file.
For a full record with integration: "kotatsu_redo", look up parser.sourceId in the Kotatsu-Redo parser library that is already bundled/ported into the app.
Read health/status.json only as a hint. A blocked result is not a dead-source verdict.
Mark a source working only after the app itself completes: list/search → details → chapter list → page list/image fetch.
Kotlin data model sketch
Use kotlinx.serialization or Gson according to the dependencies already used by your app. The model should tolerate optional fields and unknown future properties.
@kotlinx.serialization.Serializable
data class SourceCatalog(
    val schemaVersion: Int,
    val category: String,
    val sources: List<kotlinx.serialization.json.JsonObject>,
    val notes: String? = null,
)
Keep parser execution in the Android app. Never download and execute arbitrary Kotlin, JavaScript, DEX, or APK code from a source catalogue. The catalogue is metadata only.
Health levels to implement inside the app
HOST_REACHABLE: HTTP host responds.
PARSER_LIST_OK: search/list parsing returns valid entries.
DETAILS_OK: manga details and chapters parse.
PAGES_OK: page URLs resolve and at least one page image loads.
BLOCKED: anti-bot/auth/rate-limit response; do not call it dead.
DEAD: confirmed DNS/host failure or repeated definitive not-found/closed-site evidence.
Use bounded concurrency, a per-host cooldown, and a circuit breaker. Avoid launching every source simultaneously on a low-memory phone.
