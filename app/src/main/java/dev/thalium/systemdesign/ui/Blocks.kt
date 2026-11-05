package dev.thalium.systemdesign.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.thalium.systemdesign.data.Block

private fun inlineMd(text: String, accent: Color, codeBg: Color) = buildAnnotatedString {
    var i = 0
    while (i < text.length) {
        when {
            text.startsWith("**", i) -> {
                val end = text.indexOf("**", i + 2)
                if (end > i) {
                    withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) {
                        append(text.substring(i + 2, end))
                    }
                    i = end + 2
                } else {
                    append(text[i]); i++
                }
            }

            text[i] == '`' -> {
                val end = text.indexOf('`', i + 1)
                if (end > i) {
                    withStyle(
                        SpanStyle(
                            fontFamily = FontFamily.Monospace,
                            background = codeBg,
                            fontSize = 14.sp
                        )
                    ) { append(text.substring(i + 1, end)) }
                    i = end + 1
                } else {
                    append(text[i]); i++
                }
            }

            text.startsWith("[", i) -> {
                val close = text.indexOf("](", i)
                val end = if (close > i) text.indexOf(")", close + 2) else -1
                if (close > i && end > close) {
                    withStyle(SpanStyle(color = accent)) {
                        append(text.substring(i + 1, close))
                    }
                    i = end + 1
                } else {
                    append(text[i]); i++
                }
            }

            text[i] == '*' -> {
                val end = text.indexOf('*', i + 1)
                if (end > i) {
                    withStyle(SpanStyle(fontStyle = FontStyle.Italic)) {
                        append(text.substring(i + 1, end))
                    }
                    i = end + 1
                } else {
                    append(text[i]); i++
                }
            }

            else -> {
                append(text[i]); i++
            }
        }
    }
}

@Composable
fun Md(
    text: String,
    modifier: Modifier = Modifier,
    style: TextStyle = MaterialTheme.typography.bodyLarge,
    color: Color = MaterialTheme.colorScheme.onSurface
) {
    Text(
        text = inlineMd(text, MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.surfaceVariant),
        modifier = modifier,
        style = style,
        color = color
    )
}

@Composable
fun BlockView(block: Block) {
    val cs = MaterialTheme.colorScheme
    when (block.type) {
        "heading" -> Text(
            text = block.text,
            style = MaterialTheme.typography.titleLarge,
            color = cs.onSurface,
            modifier = Modifier.padding(top = 10.dp, bottom = 2.dp)
        )

        "list" -> Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            block.items.forEachIndexed { index, item ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .padding(start = if (item.level > 0) 20.dp else 0.dp)
                ) {
                    Text(
                        text = if (block.ordered) "${index + 1}." else "•",
                        style = MaterialTheme.typography.bodyMedium,
                        color = cs.primary,
                        modifier = Modifier.width(24.dp)
                    )
                    Md(item.text, modifier = Modifier.weight(1f))
                }
            }
        }

        "table" -> TableBlock(block)

        "code" -> CodeBlock(block)

        "quote" -> Row(
            Modifier
                .fillMaxWidth()
                .height(IntrinsicSize.Min)
        ) {
            Box(
                Modifier
                    .width(2.dp)
                    .fillMaxHeight()
                    .background(cs.primary.copy(alpha = 0.55f))
            )
            Spacer(Modifier.width(12.dp))
            Md(
                text = block.text,
                modifier = Modifier.weight(1f),
                color = cs.onSurfaceVariant
            )
        }

        "divider" -> HorizontalDivider(
            color = cs.outlineVariant,
            modifier = Modifier.padding(vertical = 6.dp)
        )

        else -> Md(block.text)
    }
}

@Composable
private fun CodeBlock(block: Block) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Color(0xFF0C1015))
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
            .padding(14.dp)
    ) {
        if (block.lang.isNotBlank() && block.lang != "text") {
            Text(
                text = block.lang.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF8A94A0)
            )
            Spacer(Modifier.height(8.dp))
        }
        Text(
            text = block.code,
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            fontFamily = FontFamily.Monospace,
            fontSize = 12.sp,
            lineHeight = 18.sp,
            softWrap = false,
            color = Color(0xFFD8E0EA)
        )
    }
}

@Composable
private fun TableBlock(block: Block) {
    if (block.header.isEmpty()) return
    val cs = MaterialTheme.colorScheme
    val widths = remember(block.header, block.rows) {
        block.header.indices.map { i ->
            val longest = maxOf(
                block.header.getOrNull(i)?.length ?: 0,
                block.rows.maxOfOrNull { it.getOrNull(i)?.length ?: 0 } ?: 0
            )
            (longest * 7 + 30).coerceIn(96, 300)
        }
    }

    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, cs.outlineVariant, RoundedCornerShape(12.dp))
            .horizontalScroll(rememberScrollState())
    ) {
        Row(Modifier.background(cs.surfaceVariant)) {
            block.header.forEachIndexed { i, cell ->
                TableCell(cell, widths.getOrElse(i) { 120 }, header = true)
            }
        }
        block.rows.forEach { row ->
            HorizontalDivider(color = cs.outlineVariant)
            Row {
                row.forEachIndexed { i, cell ->
                    TableCell(cell, widths.getOrElse(i) { 120 }, header = false)
                }
            }
        }
    }
}

@Composable
private fun TableCell(text: String, width: Int, header: Boolean) {
    Text(
        text = inlineMd(text, MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.surfaceVariant),
        modifier = Modifier
            .width(width.dp)
            .padding(horizontal = 10.dp, vertical = 9.dp),
        style = MaterialTheme.typography.bodySmall.copy(fontSize = 13.sp, lineHeight = 18.sp),
        fontWeight = if (header) FontWeight.SemiBold else FontWeight.Normal,
        color = if (header) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant
    )
}
