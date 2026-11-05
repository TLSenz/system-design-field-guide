package dev.thalium.systemdesign

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import dev.thalium.systemdesign.data.ContentRepository
import dev.thalium.systemdesign.data.ProgressRepository
import java.time.LocalDate

sealed interface Route {
    data object Library : Route
    data object Practice : Route
    data object Review : Route
    data object Stats : Route
    data object Search : Route
    data class Chapter(val id: String, val sectionId: String? = null) : Route
}

data class SearchHit(
    val chapterId: String,
    val chapterTitle: String,
    val number: String,
    val sectionId: String,
    val sectionTitle: String,
    val snippet: String
)

class MainViewModel(app: Application) : AndroidViewModel(app) {

    val content = ContentRepository(app)
    val progress = ProgressRepository(app)

    var route by mutableStateOf<Route>(Route.Library)
        private set

    private val backStack = mutableListOf<Route>()

    val canGoBack: Boolean get() = backStack.isNotEmpty()

    fun go(next: Route) {
        backStack.add(route)
        route = next
    }

    fun goTab(next: Route) {
        backStack.clear()
        route = next
    }

    fun back(): Boolean {
        val previous = backStack.removeLastOrNull() ?: return false
        route = previous
        return true
    }

    fun dueQuestions() = progress.dueQuestionIds(LocalDate.now())

    fun search(query: String): List<SearchHit> {
        val q = query.trim()
        if (q.length < 2) return emptyList()
        val needle = q.lowercase()
        val hits = mutableListOf<SearchHit>()

        for (meta in content.index.chapters) {
            val chapter = content.chapter(meta.id)
            for (section in chapter.sections) {
                var found = false
                for (block in section.blocks) {
                    if (found) break
                    val text = when (block.type) {
                        "paragraph", "quote" -> block.text
                        "list" -> block.items.joinToString(" ") { it.text }
                        "code" -> block.code
                        else -> ""
                    }
                    if (text.isBlank()) continue
                    val at = text.lowercase().indexOf(needle)
                    if (at >= 0) {
                        val start = (at - 60).coerceAtLeast(0)
                        val end = (at + needle.length + 100).coerceAtMost(text.length)
                        val snippet = buildString {
                            if (start > 0) append("… ")
                            append(text.substring(start, end).replace("\n", " "))
                            if (end < text.length) append(" …")
                        }
                        hits.add(
                            SearchHit(
                                chapterId = meta.id,
                                chapterTitle = meta.title,
                                number = meta.number,
                                sectionId = section.id,
                                sectionTitle = section.title,
                                snippet = snippet
                            )
                        )
                        found = true
                    }
                }
                if (hits.size >= 60) return hits
            }
        }
        return hits
    }
}
