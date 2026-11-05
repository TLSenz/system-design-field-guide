package dev.thalium.systemdesign.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

class ContentRepository(private val context: Context) {

    private val chapterCache = mutableMapOf<String, Chapter>()
    private var indexCache: LibraryIndex? = null
    private var questionsCache: List<Mcq>? = null

    val index: LibraryIndex
        get() = indexCache ?: loadIndex().also { indexCache = it }

    val questions: List<Mcq>
        get() = questionsCache ?: loadQuestions().also { questionsCache = it }

    fun chapter(id: String): Chapter = chapterCache.getOrPut(id) { loadChapter(id) }

    private fun asset(name: String): String =
        context.assets.open("content/$name").bufferedReader().use { it.readText() }

    private fun JSONArray.strings(): List<String> =
        (0 until length()).map { optString(it, "") }

    private fun JSONArray.objects(): List<JSONObject> =
        (0 until length()).map { getJSONObject(it) }

    private fun loadIndex(): LibraryIndex {
        val o = JSONObject(asset("index.json"))
        val parts = o.getJSONArray("parts").objects().map { p ->
            Part(
                id = p.getString("id"),
                title = p.getString("title"),
                chapterIds = p.getJSONArray("chapterIds").strings()
            )
        }
        val chapters = o.getJSONArray("chapters").objects().map { c ->
            ChapterMeta(
                id = c.getString("id"),
                number = c.getString("number"),
                title = c.getString("title"),
                minutes = c.optInt("minutes", 5),
                wordCount = c.optInt("wordCount", 0),
                sectionCount = c.optInt("sectionCount", 0),
                questionCount = c.optInt("questionCount", 0)
            )
        }
        return LibraryIndex(
            title = o.optString("title", "System Design"),
            subtitle = o.optString("subtitle", ""),
            parts = parts,
            chapters = chapters
        )
    }

    private fun loadChapter(id: String): Chapter {
        val o = JSONObject(asset("ch-$id.json"))
        val sections = o.getJSONArray("sections").objects().map { s ->
            Section(
                id = s.getString("id"),
                title = s.getString("title"),
                blocks = s.getJSONArray("blocks").objects().map(::parseBlock)
            )
        }
        val selfCheck = o.optJSONArray("selfCheck")?.objects()?.map {
            SelfCheck(it.optString("q", ""), it.optString("a", ""))
        } ?: emptyList()
        return Chapter(
            id = o.getString("id"),
            number = o.getString("number"),
            title = o.getString("title"),
            minutes = o.optInt("minutes", 5),
            wordCount = o.optInt("wordCount", 0),
            sections = sections,
            selfCheck = selfCheck
        )
    }

    private fun parseBlock(o: JSONObject): Block = Block(
        type = o.optString("type", "paragraph"),
        text = o.optString("text", ""),
        level = o.optInt("level", 0),
        ordered = o.optBoolean("ordered", false),
        header = o.optJSONArray("header")?.strings() ?: emptyList(),
        rows = o.optJSONArray("rows")?.let { arr ->
            (0 until arr.length()).map { arr.getJSONArray(it).strings() }
        } ?: emptyList(),
        items = o.optJSONArray("items")?.objects()?.map {
            ListItem(it.optString("text", ""), it.optInt("level", 0))
        } ?: emptyList(),
        lang = o.optString("lang", ""),
        code = o.optString("code", "")
    )

    private fun loadQuestions(): List<Mcq> {
        val o = JSONObject(asset("questions.json"))
        return o.getJSONArray("mcq").objects().map { q ->
            Mcq(
                id = q.getString("id"),
                topic = q.getString("topic"),
                question = q.getString("question"),
                options = q.getJSONArray("options").strings(),
                answerIndex = q.getInt("answerIndex"),
                explanation = q.optString("explanation", "")
            )
        }
    }
}
