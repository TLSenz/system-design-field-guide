package dev.thalium.systemdesign.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dev.thalium.systemdesign.MainViewModel
import dev.thalium.systemdesign.Route
import java.time.LocalDate

@Composable
fun ReviewScreen(vm: MainViewModel) {
    val progress by vm.progress.state.collectAsStateWithLifecycle()
    val all = remember { vm.content.questions }
    val today = remember { LocalDate.now().toEpochDay() }
    val due = remember {
        all.filter { question ->
            (progress.srs[question.id]?.dueDay ?: Long.MAX_VALUE) <= today
        }
    }

    var index by remember { mutableIntStateOf(0) }
    var correct by remember { mutableIntStateOf(0) }
    var done by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize()) {
        ScreenHeader(
            title = "Review",
            subtitle = if (due.isEmpty()) "Spaced repetition" else "${due.size} cards due today"
        )

        when {
            due.isEmpty() -> EmptyReview(
                nextDay = progress.srs.values.map { it.dueDay }.filter { it > today }.minOrNull(),
                onPractice = { vm.goTab(Route.Practice) }
            )

            done -> SessionResult(
                correct = correct,
                total = due.size,
                onAgain = { vm.goTab(Route.Practice) },
                againLabel = "Practice more"
            )

            else -> {
                val question = due[index]
                LazyColumn(contentPadding = PaddingValues(20.dp)) {
                    item(key = question.id) {
                        QuestionCard(
                            mcq = question,
                            position = index,
                            total = due.size,
                            onAnswered = { chosen ->
                                val ok = chosen == question.answerIndex
                                if (ok) correct += 1
                                vm.progress.review(question, ok)
                            },
                            onNext = {
                                if (index + 1 >= due.size) done = true else index += 1
                            },
                            nextLabel = if (index + 1 >= due.size) "Finish review" else "Next card"
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun EmptyReview(nextDay: Long?, onPractice: () -> Unit) {
    val cs = MaterialTheme.colorScheme
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("Nothing due", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(10.dp))
        Text(
            text = if (nextDay != null) {
                val days = (nextDay - LocalDate.now().toEpochDay()).coerceAtLeast(1)
                "Next card comes back in $days day${if (days == 1L) "" else "s"}."
            } else {
                "Answer practice questions and missed ones return here on a spaced schedule."
            },
            style = MaterialTheme.typography.bodyMedium,
            color = cs.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(26.dp))
        Button(
            onClick = onPractice,
            modifier = Modifier.fillMaxWidth().height(52.dp),
            shape = RoundedCornerShape(14.dp)
        ) {
            Text("Go to practice")
        }
    }
}
