package dev.thalium.systemdesign.data

/**
 * Formats a practice question as a self-contained prompt that can be pasted
 * into an AI assistant. Kept free of Android APIs so it is easy to unit test.
 */
fun mcqPrompt(
    mcq: Mcq,
    selectedIndex: Int = -1,
    submitted: Boolean = false
): String = buildString {
    appendLine("System design practice question (${mcq.topic})")
    appendLine()
    appendLine(mcq.question)
    appendLine()
    mcq.options.forEachIndexed { index, option ->
        appendLine("${'A' + index}. $option")
    }
    if (submitted && selectedIndex in mcq.options.indices) {
        appendLine()
        appendLine("I answered ${'A' + selectedIndex}: ${mcq.options[selectedIndex]}")
    }
    appendLine()
    append("Explain the correct answer and why the other options are wrong.")
}

/**
 * Formats a self-check question as a prompt. If the answer has already been
 * revealed, it is included so the AI can expand on it instead of starting over.
 */
fun selfCheckPrompt(
    item: SelfCheck,
    revealed: Boolean = false
): String = buildString {
    appendLine("System design self-check question:")
    appendLine()
    appendLine(item.q)
    appendLine()
    if (revealed) {
        appendLine("The field guide's answer:")
        appendLine(item.a)
        appendLine()
        append("Expand on this answer with the key trade-offs and a concrete example.")
    } else {
        append("Answer this like a senior engineer in a system design interview, with the key trade-offs.")
    }
}
