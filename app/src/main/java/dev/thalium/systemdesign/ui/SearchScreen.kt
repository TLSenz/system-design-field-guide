package dev.thalium.systemdesign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import dev.thalium.systemdesign.MainViewModel
import dev.thalium.systemdesign.Route
import dev.thalium.systemdesign.SearchHit

@Composable
fun SearchScreen(vm: MainViewModel) {
    var query by rememberSaveable { mutableStateOf("") }
    val results = remember(query) { vm.search(query) }
    val cs = MaterialTheme.colorScheme

    Column(Modifier.fillMaxSize()) {
        ScreenHeader(title = "Search", onBack = { vm.back() })

        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp),
            placeholder = { Text("Concepts, chapters, code…") },
            leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
            singleLine = true,
            shape = RoundedCornerShape(14.dp)
        )

        Spacer(Modifier.height(8.dp))

        if (query.length >= 2) {
            Text(
                text = "${results.size} results",
                style = MaterialTheme.typography.labelSmall,
                color = cs.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp)
            )
        }

        LazyColumn(
            contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 4.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(9.dp)
        ) {
            items(results, key = { "${it.chapterId}-${it.sectionId}-${it.snippet.take(24)}" }) { hit ->
                SearchRow(hit) {
                    vm.go(Route.Chapter(hit.chapterId, hit.sectionId))
                }
            }
        }
    }
}

@Composable
private fun SearchRow(hit: SearchHit, onClick: () -> Unit) {
    val cs = MaterialTheme.colorScheme
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(cs.surface)
            .border(1.dp, cs.outlineVariant, RoundedCornerShape(14.dp))
            .clickable(onClick = onClick)
            .padding(14.dp)
    ) {
        Text(
            text = "${hit.number} · ${hit.chapterTitle}",
            style = MaterialTheme.typography.labelSmall,
            color = cs.primary
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = hit.sectionTitle,
            style = MaterialTheme.typography.titleMedium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = hit.snippet,
            style = MaterialTheme.typography.bodySmall,
            color = cs.onSurfaceVariant,
            maxLines = 3,
            overflow = TextOverflow.Ellipsis
        )
    }
}
