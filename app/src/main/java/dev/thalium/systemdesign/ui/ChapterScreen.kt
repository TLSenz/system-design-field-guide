package dev.thalium.systemdesign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.thalium.systemdesign.MainViewModel
import dev.thalium.systemdesign.data.Chapter
import dev.thalium.systemdesign.data.SelfCheck

@Composable
fun ChapterScreen(vm: MainViewModel, id: String, focusSection: String?) {
    val chapter = remember(id) { vm.content.chapter(id) }
    val progress by vm.progress.state.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()
    val completed = id in progress.completed

    LaunchedEffect(id) { vm.progress.markStudied() }

    LaunchedEffect(id, focusSection) {
        if (focusSection != null) {
            var itemIndex = 1
            for (section in chapter.sections) {
                if (section.id == focusSection) break
                itemIndex += 1 + section.blocks.size
            }
            listState.scrollToItem(itemIndex)
        } else {
            val saved = progress.scroll[id] ?: 0
            if (saved > 0) listState.scrollToItem(saved)
        }
    }

    DisposableEffect(id) {
        onDispose { vm.progress.saveScroll(id, listState.firstVisibleItemIndex) }
    }

    Column(Modifier.fillMaxSize()) {
        ScreenHeader(
            title = chapter.title,
            subtitle = "Chapter ${chapter.number} · ${chapter.minutes} min read",
            onBack = { vm.back() },
            actions = {
                IconButton(
                    onClick = {
                        vm.progress.toggleBookmark(id, chapter.title, "", chapter.title)
                    }
                ) {
                    Icon(
                        Icons.Filled.Star,
                        contentDescription = "Bookmark chapter",
                        tint = if (progress.bookmarks.any { it.chapterId == id && it.sectionId == "" })
                            MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        )

        LazyColumn(
            state = listState,
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 4.dp, bottom = 36.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item(key = "chapter-header") {
                ChapterHeader(chapter)
            }

            chapter.sections.forEach { section ->
                item(key = section.id) {
                    val bookmarked = progress.bookmarks.any {
                        it.chapterId == id && it.sectionId == section.id
                    }
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = section.title,
                            style = MaterialTheme.typography.headlineMedium,
                            modifier = Modifier.weight(1f)
                        )
                        IconButton(
                            onClick = {
                                vm.progress.toggleBookmark(id, chapter.title, section.id, section.title)
                            },
                            modifier = Modifier.size(36.dp)
                        ) {
                            Icon(
                                Icons.Filled.Star,
                                contentDescription = "Bookmark section",
                                tint = if (bookmarked) MaterialTheme.colorScheme.primary
                                else MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }
                }
                items(
                    count = section.blocks.size,
                    key = { index -> "${section.id}-$index" }
                ) { index ->
                    BlockView(section.blocks[index])
                }
            }

            if (chapter.selfCheck.isNotEmpty()) {
                item(key = "self-check") {
                    SelfCheckSection(chapter.selfCheck)
                }
            }

            item(key = "complete") {
                Spacer(Modifier.height(10.dp))
                Button(
                    onClick = { vm.progress.toggleComplete(id) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp)
                ) {
                    Icon(Icons.Filled.Check, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text(if (completed) "Completed" else "Mark chapter complete")
                }
            }
        }
    }
}

@Composable
private fun ChapterHeader(chapter: Chapter) {
    val cs = MaterialTheme.colorScheme
    Column(Modifier.fillMaxWidth().padding(top = 8.dp, bottom = 4.dp)) {
        Text(
            text = "CHAPTER ${chapter.number}",
            style = MaterialTheme.typography.labelSmall,
            color = cs.primary
        )
        Spacer(Modifier.height(6.dp))
        Text(
            text = chapter.title,
            style = MaterialTheme.typography.displaySmall
        )
        Spacer(Modifier.height(10.dp))
        Text(
            text = "${chapter.sections.size} sections · ${chapter.minutes} min · ${chapter.wordCount} words",
            style = MaterialTheme.typography.bodyMedium,
            color = cs.onSurfaceVariant
        )
        Spacer(Modifier.height(14.dp))
        androidx.compose.material3.HorizontalDivider(color = cs.outlineVariant)
    }
}

@Composable
private fun SelfCheckSection(items: List<SelfCheck>) {
    val cs = MaterialTheme.colorScheme
    var open by remember { mutableStateOf(setOf<Int>()) }

    Column(Modifier.fillMaxWidth().padding(top = 20.dp)) {
        Text("Self-check", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(4.dp))
        Text(
            "Answer first, then reveal. These are the interview signals.",
            style = MaterialTheme.typography.bodyMedium,
            color = cs.onSurfaceVariant
        )
        Spacer(Modifier.height(14.dp))

        items.forEachIndexed { index, item ->
            Column(
                Modifier
                    .fillMaxWidth()
                    .padding(bottom = 10.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(cs.surface)
                    .border(1.dp, cs.outlineVariant, RoundedCornerShape(14.dp))
                    .padding(14.dp)
            ) {
                Md(
                    text = item.q,
                    style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Medium)
                )
                TextButton(onClick = {
                    open = if (index in open) open - index else open + index
                }) {
                    Text(if (index in open) "Hide answer" else "Reveal answer")
                }
                if (index in open) {
                    Md(
                        text = item.a,
                        style = MaterialTheme.typography.bodyMedium,
                        color = cs.onSurfaceVariant
                    )
                }
            }
        }
    }
}
