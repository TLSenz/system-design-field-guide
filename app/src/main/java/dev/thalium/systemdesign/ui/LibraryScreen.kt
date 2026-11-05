package dev.thalium.systemdesign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.thalium.systemdesign.MainViewModel
import dev.thalium.systemdesign.Route
import dev.thalium.systemdesign.data.ChapterMeta

@Composable
fun LibraryScreen(vm: MainViewModel) {
    val index = remember { vm.content.index }
    val progress by vm.progress.state.collectAsStateWithLifecycle()
    val total = index.chapters.size
    val done = progress.completed.size

    Column(Modifier.fillMaxSize()) {
        ScreenHeader(
            title = "System Design",
            subtitle = "A field guide to senior engineering",
            actions = {
                IconButton(onClick = { vm.go(Route.Search) }) {
                    Icon(Icons.Filled.Search, contentDescription = "Search")
                }
            }
        )

        LazyColumn(
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 4.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            item { StreakCard(progress.streak, done, total) }

            index.parts.forEach { part ->
                item(key = "part-${part.id}") {
                    Text(
                        text = part.title.uppercase(),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 18.dp, bottom = 2.dp)
                    )
                }
                items(part.chapterIds, key = { it }) { id ->
                    val meta = index.chapters.firstOrNull { it.id == id }
                    if (meta != null) {
                        ChapterRow(
                            meta = meta,
                            completed = id in progress.completed,
                            onClick = { vm.go(Route.Chapter(id)) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun StreakCard(streak: Int, done: Int, total: Int) {
    val cs = MaterialTheme.colorScheme
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(18.dp))
            .background(cs.surface)
            .border(1.dp, cs.outlineVariant, RoundedCornerShape(18.dp))
            .padding(18.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                text = if (streak > 0) "$streak day streak" else "Start your streak",
                style = MaterialTheme.typography.titleLarge
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = "$done of $total chapters complete",
                style = MaterialTheme.typography.bodyMedium,
                color = cs.onSurfaceVariant
            )
            Spacer(Modifier.height(12.dp))
            LinearProgressIndicator(
                progress = { if (total == 0) 0f else done.toFloat() / total },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .clip(RoundedCornerShape(2.dp)),
                color = cs.primary,
                trackColor = cs.surfaceVariant
            )
        }
        Spacer(Modifier.width(18.dp))
        Text(
            text = "${if (total == 0) 0 else done * 100 / total}%",
            style = MaterialTheme.typography.headlineMedium,
            color = cs.primary
        )
    }
}

@Composable
private fun ChapterRow(meta: ChapterMeta, completed: Boolean, onClick: () -> Unit) {
    val cs = MaterialTheme.colorScheme
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(cs.surface)
            .border(1.dp, cs.outlineVariant, RoundedCornerShape(14.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(38.dp)
                .clip(CircleShape)
                .background(if (completed) cs.primary.copy(alpha = 0.16f) else cs.surfaceVariant),
            contentAlignment = Alignment.Center
        ) {
            if (completed) {
                Icon(
                    Icons.Filled.Check,
                    contentDescription = null,
                    tint = cs.primary,
                    modifier = Modifier.size(18.dp)
                )
            } else {
                Text(
                    text = meta.number,
                    style = MaterialTheme.typography.labelLarge,
                    color = cs.onSurfaceVariant
                )
            }
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(
                text = meta.title,
                style = MaterialTheme.typography.titleMedium,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            Text(
                text = "${meta.minutes} min · ${meta.sectionCount} sections",
                style = MaterialTheme.typography.labelSmall,
                color = cs.onSurfaceVariant
            )
        }
        Icon(
            Icons.Filled.KeyboardArrowRight,
            contentDescription = null,
            tint = cs.onSurfaceVariant,
            modifier = Modifier.size(18.dp)
        )
    }
}
