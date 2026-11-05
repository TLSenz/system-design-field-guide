package dev.thalium.systemdesign.data

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONArray
import org.json.JSONObject
import java.time.LocalDate

data class Bookmark(
    val chapterId: String,
    val chapterTitle: String,
    val sectionId: String,
    val sectionTitle: String
)

data class Attempt(
    val chosen: Int,
    val correct: Boolean,
    val at: Long
)

data class SrsCard(
    val dueDay: Long,
    val intervalDays: Int,
    val reps: Int
)

data class ProgressState(
    val completed: Set<String> = emptySet(),
    val bookmarks: List<Bookmark> = emptyList(),
    val streak: Int = 0,
    val totalStudyDays: Int = 0,
    val lastStudyDay: String = "",
    val attempts: Map<String, Attempt> = emptyMap(),
    val srs: Map<String, SrsCard> = emptyMap(),
    val scroll: Map<String, Int> = emptyMap()
) {
    val answered: Int get() = attempts.size
    val correct: Int get() = attempts.values.count { it.correct }
    val accuracy: Int get() = if (answered == 0) 0 else (correct * 100) / answered
}

class ProgressRepository(context: Context) {

    private val prefs = context.getSharedPreferences("system_design_progress", Context.MODE_PRIVATE)
    private val _state = MutableStateFlow(load())
    val state: StateFlow<ProgressState> = _state.asStateFlow()

    fun markStudied() = update { it.studied(LocalDate.now()) }

    fun toggleComplete(chapterId: String) = update { s ->
        val next = if (chapterId in s.completed) s.completed - chapterId else s.completed + chapterId
        s.copy(completed = next).studied(LocalDate.now())
    }

    fun toggleBookmark(chapterId: String, chapterTitle: String, sectionId: String, sectionTitle: String) = update { s ->
        val existing = s.bookmarks.firstOrNull { it.chapterId == chapterId && it.sectionId == sectionId }
        if (existing != null) {
            s.copy(bookmarks = s.bookmarks - existing)
        } else {
            s.copy(bookmarks = s.bookmarks + Bookmark(chapterId, chapterTitle, sectionId, sectionTitle))
        }
    }

    fun isBookmarked(chapterId: String, sectionId: String): Boolean =
        _state.value.bookmarks.any { it.chapterId == chapterId && it.sectionId == sectionId }

    fun saveScroll(chapterId: String, index: Int) = update { s ->
        s.copy(scroll = s.scroll + (chapterId to index))
    }

    fun recordAttempt(mcq: Mcq, chosen: Int) {
        val correct = chosen == mcq.answerIndex
        update { s -> s.answered(mcq.id, chosen, correct).studied(LocalDate.now()) }
    }

    fun review(mcq: Mcq, correct: Boolean) {
        update { s -> s.answered(mcq.id, if (correct) mcq.answerIndex else -1, correct).studied(LocalDate.now()) }
    }

    private fun ProgressState.answered(id: String, chosen: Int, correct: Boolean): ProgressState {
        val today = LocalDate.now()
        val prev = srs[id]
        val interval = if (correct) {
            val base = prev?.intervalDays ?: 0
            if (base <= 0) 3 else minOf(45, base * 2)
        } else {
            1
        }
        val card = SrsCard(
            dueDay = today.plusDays(interval.toLong()).toEpochDay(),
            intervalDays = interval,
            reps = (prev?.reps ?: 0) + 1
        )
        return copy(
            attempts = attempts + (id to Attempt(chosen, correct, System.currentTimeMillis())),
            srs = srs + (id to card)
        )
    }

    private fun ProgressState.studied(today: LocalDate): ProgressState {
        val key = today.toString()
        if (lastStudyDay == key) return this
        val yesterday = today.minusDays(1).toString()
        val nextStreak = if (lastStudyDay == yesterday) streak + 1 else 1
        return copy(streak = nextStreak, lastStudyDay = key, totalStudyDays = totalStudyDays + 1)
    }

    fun dueQuestionIds(today: LocalDate = LocalDate.now()): Set<String> =
        _state.value.srs.filterValues { it.dueDay <= today.toEpochDay() }.keys

    private fun update(block: (ProgressState) -> ProgressState) {
        val next = block(_state.value)
        _state.value = next
        save(next)
    }

    private fun save(s: ProgressState) {
        val root = JSONObject()
        root.put("completed", JSONArray(s.completed.toList()))
        val bookmarks = JSONArray()
        s.bookmarks.forEach { b ->
            bookmarks.put(
                JSONObject()
                    .put("chapterId", b.chapterId)
                    .put("chapterTitle", b.chapterTitle)
                    .put("sectionId", b.sectionId)
                    .put("sectionTitle", b.sectionTitle)
            )
        }
        root.put("bookmarks", bookmarks)
        root.put("streak", s.streak)
        root.put("totalStudyDays", s.totalStudyDays)
        root.put("lastStudyDay", s.lastStudyDay)

        val attempts = JSONObject()
        s.attempts.forEach { (k, v) ->
            attempts.put(k, JSONObject().put("chosen", v.chosen).put("correct", v.correct).put("at", v.at))
        }
        root.put("attempts", attempts)

        val srs = JSONObject()
        s.srs.forEach { (k, v) ->
            srs.put(k, JSONObject().put("dueDay", v.dueDay).put("intervalDays", v.intervalDays).put("reps", v.reps))
        }
        root.put("srs", srs)

        val scroll = JSONObject()
        s.scroll.forEach { (k, v) -> scroll.put(k, v) }
        root.put("scroll", scroll)

        prefs.edit().putString(KEY, root.toString()).apply()
    }

    private fun load(): ProgressState {
        val raw = prefs.getString(KEY, null) ?: return ProgressState()
        return runCatching {
            val root = JSONObject(raw)
            val completed = root.optJSONArray("completed")
                ?.let { a -> (0 until a.length()).map { a.getString(it) }.toSet() }
                ?: emptySet()
            val bookmarks = root.optJSONArray("bookmarks")?.let { a ->
                (0 until a.length()).map { i ->
                    val o = a.getJSONObject(i)
                    Bookmark(
                        o.optString("chapterId"),
                        o.optString("chapterTitle"),
                        o.optString("sectionId"),
                        o.optString("sectionTitle")
                    )
                }
            } ?: emptyList()
            val attemptsObj = root.optJSONObject("attempts")
            val attempts = mutableMapOf<String, Attempt>()
            attemptsObj?.keys()?.forEach { k ->
                val o = attemptsObj.getJSONObject(k)
                attempts[k] = Attempt(o.optInt("chosen"), o.optBoolean("correct"), o.optLong("at"))
            }
            val srsObj = root.optJSONObject("srs")
            val srs = mutableMapOf<String, SrsCard>()
            srsObj?.keys()?.forEach { k ->
                val o = srsObj.getJSONObject(k)
                srs[k] = SrsCard(o.optLong("dueDay"), o.optInt("intervalDays", 1), o.optInt("reps", 0))
            }
            val scrollObj = root.optJSONObject("scroll")
            val scroll = mutableMapOf<String, Int>()
            scrollObj?.keys()?.forEach { k -> scroll[k] = scrollObj.optInt(k, 0) }

            ProgressState(
                completed = completed,
                bookmarks = bookmarks,
                streak = root.optInt("streak", 0),
                totalStudyDays = root.optInt("totalStudyDays", 0),
                lastStudyDay = root.optString("lastStudyDay", ""),
                attempts = attempts,
                srs = srs,
                scroll = scroll
            )
        }.getOrElse { ProgressState() }
    }

    private companion object {
        const val KEY = "state"
    }
}
