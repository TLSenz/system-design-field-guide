package dev.thalium.systemdesign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.thalium.systemdesign.MainViewModel
import dev.thalium.systemdesign.Route
import java.time.LocalDate

@Composable
fun StatsScreen(vm: MainViewModel) {
    val index = remember { vm.content.index }
    val all = remember { vm.content.questions }
    val progress by vm.progress.state.collectAsStateWithLifecycle()
    val today = LocalDate.now().toEpochDay()
    val due = remember(progress.srs) {
        all.count { (progress.srs[it.id]?.dueDay ?: Long.MAX_VALUE) <= today }
    }

    val topics = remember(all, progress.attempts) {
        all.groupBy { it.topic }
            .map { (topic, questions) ->
                val results = questions.mapNotNull { q -> progress.attempts[q.id]?.correct }
                Triple(topic, results.count { it }, results.size)
            }
            .sortedByDescending { it.third }
    }

    Column(Modifier.fillMaxSize()) {
        ScreenHeader(
            title = "Progress",
            subtitle = "${progress.totalStudyDays} study days · ${progress.streak} day streak"
        )

        LazyColumn(
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 4.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    StatTile("Answered", "${progress.answered}", Modifier.weight(1f))
                    StatTile("Accuracy", "${progress.accuracy}%", Modifier.weight(1f))
                    StatTile("Due", "$due", Modifier.weight(1f))
                }
            }

            item {
                ChapterProgress(
                    done = progress.completed.size,
                    total = index.chapters.size
                )
            }

            item { SectionLabel("Topic mastery") }

            items(topics, key = { it.first }) { (topic, correct, answered) ->
                TopicMastery(topic, correct, answered)
            }

            if (progress.bookmarks.isNotEmpty()) {
                item { SectionLabel("Bookmarks") }
                items(progress.bookmarks, key = { "${it.chapterId}-${it.sectionId}" }) { bookmark ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(13.dp))
                            .background(MaterialTheme.colorScheme.surface)
                            .border(
                                1.dp,
                                MaterialTheme.colorScheme.outlineVariant,
                                RoundedCornerShape(13.dp)
                            )
                            .clickable {
                                vm.go(
                                    Route.Chapter(
                                        bookmark.chapterId,
                                        if (bookmark.sectionId.isBlank()) null else bookmark.sectionId
                                    )
                                )
                            }
                            .padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Filled.Star,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(16.dp)
                        )
                        Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f)) {
                            Text(
                                text = bookmark.chapterTitle,
                                style = MaterialTheme.typography.titleMedium,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Text(
                                text = if (bookmark.sectionTitle.isBlank()) "Chapter overview" else bookmark.sectionTitle,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                }
            }

            item {
                Text(
                    text = "Content bundled offline · v1.0.0",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 20.dp)
                )
            }
        }
    }
}

@Composable
private fun StatTile(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(14.dp))
            .padding(14.dp)
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.primary
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun ChapterProgress(done: Int, total: Int) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(14.dp))
            .padding(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Chapters complete", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.weight(1f))
            Text(
                "$done/$total",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary
            )
        }
        Spacer(Modifier.height(10.dp))
        LinearProgressIndicator(
            progress = { if (total == 0) 0f else done.toFloat() / total },
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp)),
            color = MaterialTheme.colorScheme.primary,
            trackColor = MaterialTheme.colorScheme.surfaceVariant
        )
    }
}

@Composable
private fun TopicMastery(topic: String, correct: Int, answered: Int) {
    val cs = MaterialTheme.colorScheme
    val pct = if (answered == 0) 0 else correct * 100 / answered
    Column(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = topic,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = if (answered == 0) "—" else "$pct%",
                style = MaterialTheme.typography.labelLarge,
                color = when {
                    answered == 0 -> cs.onSurfaceVariant
                    pct >= 70 -> cs.secondary
                    else -> cs.primary
                }
            )
        }
        Spacer(Modifier.height(6.dp))
        LinearProgressIndicator(
            progress = { if (answered == 0) 0f else correct.toFloat() / answered },
            modifier = Modifier
                .fillMaxWidth()
                .height(3.dp)
                .clip(RoundedCornerShape(2.dp)),
            color = if (pct >= 70 && answered > 0) cs.secondary else cs.primary,
            trackColor = cs.surfaceVariant
        )
        Spacer(Modifier.height(2.dp))
        Text(
            text = if (answered == 0) "Not started" else "$correct of $answered correct",
            style = MaterialTheme.typography.labelSmall,
            color = cs.onSurfaceVariant
        )
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(
        text = text.uppercase(),
        style = MaterialTheme.typography.labelSmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(top = 10.dp, bottom = 2.dp)
    )
}
