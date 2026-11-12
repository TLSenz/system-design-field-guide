package dev.thalium.systemdesign.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import dev.thalium.systemdesign.R

@Composable
fun CopyQuestionButton(
    text: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    IconButton(
        onClick = { copyQuestion(context, text) },
        modifier = modifier
    ) {
        Icon(
            painter = painterResource(R.drawable.ic_content_copy),
            contentDescription = "Copy question for AI",
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.size(18.dp)
        )
    }
}

private fun copyQuestion(context: Context, text: String) {
    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager ?: return
    clipboard.setPrimaryClip(ClipData.newPlainText("System design question", text))
    Toast.makeText(context, "Question copied", Toast.LENGTH_SHORT).show()
}
