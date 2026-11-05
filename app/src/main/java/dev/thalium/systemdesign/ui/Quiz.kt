package dev.thalium.systemdesign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
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
import dev.thalium.systemdesign.data.Mcq

@Composable
fun QuestionCard(
    mcq: Mcq,
    position: Int,
    total: Int,
    onAnswered: (Int) -> Unit,
    onNext: () -> Unit,
    nextLabel: String = "Next"
) {
    var selected by remember(mcq.id) { mutableIntStateOf(-1) }
    var submitted by remember(mcq.id) { mutableStateOf(false) }

    val cs = MaterialTheme.colorScheme
    val correct = submitted && selected == mcq.answerIndex

    Column(Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = "QUESTION ${position + 1} OF $total",
                style = MaterialTheme.typography.labelSmall,
                color = cs.primary
            )
            Spacer(Modifier.weight(1f))
            Text(
                text = mcq.topic,
                style = MaterialTheme.typography.labelSmall,
                color = cs.onSurfaceVariant
            )
        }

        Spacer(Modifier.height(12.dp))
        Md(mcq.question, style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(18.dp))

        mcq.options.forEachIndexed { i, option ->
            val isSelected = selected == i
            val isCorrect = i == mcq.answerIndex

            val borderColor = when {
                submitted && isCorrect -> cs.secondary
                submitted && isSelected && !isCorrect -> cs.error
                !submitted && isSelected -> cs.primary
                else -> cs.outlineVariant
            }
            val background = when {
                submitted && isCorrect -> cs.secondary.copy(alpha = 0.12f)
                submitted && isSelected && !isCorrect -> cs.error.copy(alpha = 0.10f)
                !submitted && isSelected -> cs.primary.copy(alpha = 0.10f)
                else -> cs.surface
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 9.dp)
                    .clip(RoundedCornerShape(13.dp))
                    .background(background)
                    .border(1.dp, borderColor, RoundedCornerShape(13.dp))
                    .clickable(enabled = !submitted) { selected = i }
                    .padding(14.dp),
                verticalAlignment = Alignment.Top
            ) {
                Text(
                    text = ('A' + i).toString(),
                    style = MaterialTheme.typography.labelLarge,
                    color = when {
                        submitted && isCorrect -> cs.secondary
                        isSelected -> cs.primary
                        else -> cs.onSurfaceVariant
                    },
                    modifier = Modifier.width(24.dp)
                )
                Md(option, modifier = Modifier.weight(1f))
                if (submitted && isCorrect) {
                    Icon(
                        Icons.Filled.Check,
                        contentDescription = null,
                        tint = cs.secondary,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
        }

        if (submitted) {
            Spacer(Modifier.height(6.dp))
            Column(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(13.dp))
                    .background(cs.surfaceVariant.copy(alpha = 0.55f))
                    .padding(14.dp)
            ) {
                Text(
                    text = if (correct) "Correct" else "Not quite",
                    style = MaterialTheme.typography.labelLarge,
                    color = if (correct) cs.secondary else cs.error
                )
                Spacer(Modifier.height(6.dp))
                Md(
                    text = mcq.explanation,
                    style = MaterialTheme.typography.bodyMedium,
                    color = cs.onSurfaceVariant
                )
            }
        }

        Spacer(Modifier.height(16.dp))
        Button(
            onClick = {
                if (!submitted) {
                    submitted = true
                    onAnswered(selected)
                } else {
                    onNext()
                }
            },
            enabled = submitted || selected >= 0,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
            shape = RoundedCornerShape(14.dp)
        ) {
            Text(if (submitted) nextLabel else "Submit answer")
        }
    }
}

@Composable
fun SessionResult(correct: Int, total: Int, onAgain: () -> Unit, againLabel: String = "Start a new session") {
    val cs = MaterialTheme.colorScheme
    val pct = if (total == 0) 0 else correct * 100 / total
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 28.dp, vertical = 48.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "$pct%",
            style = MaterialTheme.typography.displaySmall,
            color = if (pct >= 70) cs.secondary else cs.primary
        )
        Spacer(Modifier.height(8.dp))
        Text(
            text = "$correct of $total correct",
            style = MaterialTheme.typography.bodyLarge,
            color = cs.onSurfaceVariant
        )
        Spacer(Modifier.height(24.dp))
        Button(
            onClick = onAgain,
            modifier = Modifier.fillMaxWidth().height(52.dp),
            shape = RoundedCornerShape(14.dp)
        ) {
            Text(againLabel)
        }
    }
}
