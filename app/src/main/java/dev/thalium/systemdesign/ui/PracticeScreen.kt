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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.thalium.systemdesign.MainViewModel
import dev.thalium.systemdesign.data.Attempt
import dev.thalium.systemdesign.data.Mcq

@Composable
fun PracticeScreen(vm: MainViewModel) {
    val all = remember { vm.content.questions }
    val progress by vm.progress.state.collectAsStateWithLifecycle()

    var queue by remember { mutableStateOf<List<Mcq>>(emptyList()) }
    var index by remember { mutableIntStateOf(0) }
    var correctCount by remember { mutableIntStateOf(0) }
    var finished by remember { mutableStateOf(false) }

    val reset = {
        queue = emptyList()
        index = 0
        correctCount = 0
        finished = false
    }

    Column(Modifier.fillMaxSize()) {
        ScreenHeader(
            title = "Practice",
            subtitle = when {
                queue.isEmpty() -> "${all.size} questions · ${all.map { it.topic }.distinct().size} topics"
                finished -> "Session complete"
                else -> "Question ${index + 1} of ${queue.size}"
            },
            onBack = if (queue.isNotEmpty()) ({ reset() }) else null
        )

        when {
            queue.isEmpty() -> TopicPicker(
                all = all,
                attempts = progress.attempts,
                onStart = { topic ->
                    queue = (if (topic == null) all else all.filter { it.topic == topic }).shuffled()
                    index = 0
                    correctCount = 0
                    finished = false
                }
            )

            finished -> SessionResult(
                correct = correctCount,
                total = queue.size,
                onAgain = reset
            )

            else -> {
                val question = queue[index]
                LazyColumn(contentPadding = PaddingValues(20.dp)) {
                    item(key = question.id) {
                        QuestionCard(
                            mcq = question,
                            position = index,
                            total = queue.size,
                            onAnswered = { chosen ->
                                vm.progress.recordAttempt(question, chosen)
                                if (chosen == question.answerIndex) correctCount += 1
                            },
                            onNext = {
                                if (index + 1 >= queue.size) finished = true else index += 1
                            },
                            nextLabel = if (index + 1 >= queue.size) "See results" else "Next question"
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun TopicPicker(
    all: List<Mcq>,
    attempts: Map<String, Attempt>,
    onStart: (String?) -> Unit
) {
    val groups = remember(all) {
        all.groupBy { it.topic }.toList().sortedBy { it.first }
    }

    LazyColumn(
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            TopicCard(
                title = "Mixed session",
                detail = "${all.size} questions from every topic",
                answered = attempts.count { it.key in all.map { q -> q.id } },
                total = all.size,
                onClick = { onStart(null) }
            )
        }

        items(groups, key = { it.first }) { entry ->
            val topic = entry.first
            val questions = entry.second
            val answered = questions.count { it.id in attempts }
            val correct = questions.count { attempts[it.id]?.correct == true }
            TopicCard(
                title = topic,
                detail = if (answered == 0) "${questions.size} questions"
                else "$correct of $answered correct",
                answered = answered,
                total = questions.size,
                onClick = { onStart(topic) }
            )
        }
    }
}

@Composable
private fun TopicCard(
    title: String,
    detail: String,
    answered: Int,
    total: Int,
    onClick: () -> Unit
) {
    val cs = MaterialTheme.colorScheme
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(cs.surface)
            .border(1.dp, cs.outlineVariant, RoundedCornerShape(14.dp))
            .clickable(onClick = onClick)
            .padding(16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(
                    detail,
                    style = MaterialTheme.typography.labelSmall,
                    color = cs.onSurfaceVariant
                )
            }
            Text(
                text = if (answered == 0) "—" else "$answered/$total",
                style = MaterialTheme.typography.labelLarge,
                color = cs.primary
            )
        }
        if (answered > 0) {
            Spacer(Modifier.height(10.dp))
            LinearProgressIndicator(
                progress = { if (total == 0) 0f else answered.toFloat() / total },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(3.dp)
                    .clip(RoundedCornerShape(2.dp)),
                color = cs.primary,
                trackColor = cs.surfaceVariant
            )
        }
    }
}
