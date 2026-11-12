package dev.thalium.systemdesign.data

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class QuestionPromptsTest {

    private val mcq = Mcq(
        id = "mcq-1",
        topic = "Caching",
        question = "Which caching approach fits a 60-second staleness budget?",
        options = listOf("Write-behind", "Write-through", "Cache-aside", "Read-through"),
        answerIndex = 2,
        explanation = "Cache-aside with a 60-second TTL."
    )

    @Test
    fun `mcq prompt includes topic question and lettered options`() {
        val text = mcqPrompt(mcq)

        assertTrue(text.contains("Caching"))
        assertTrue(text.contains(mcq.question))
        assertTrue(text.contains("A. Write-behind"))
        assertTrue(text.contains("B. Write-through"))
        assertTrue(text.contains("C. Cache-aside"))
        assertTrue(text.contains("D. Read-through"))
        assertTrue(text.endsWith("Explain the correct answer and why the other options are wrong."))
    }

    @Test
    fun `mcq prompt does not mention an answer before submission`() {
        assertFalse(mcqPrompt(mcq).contains("I answered"))
    }

    @Test
    fun `mcq prompt includes the submitted answer`() {
        val text = mcqPrompt(mcq, selectedIndex = 1, submitted = true)

        assertTrue(text.contains("I answered B: Write-through"))
    }

    @Test
    fun `mcq prompt ignores a submitted answer outside the option range`() {
        val text = mcqPrompt(mcq, selectedIndex = 9, submitted = true)

        assertFalse(text.contains("I answered"))
    }

    @Test
    fun `self check prompt includes the question but not the answer`() {
        val item = SelfCheck(
            q = "How does a CDN invalidate content?",
            a = "Versioned URLs and short TTLs."
        )
        val text = selfCheckPrompt(item)

        assertTrue(text.contains(item.q))
        assertFalse(text.contains(item.a))
        assertTrue(text.endsWith("Answer this like a senior engineer in a system design interview, with the key trade-offs."))
    }

    @Test
    fun `revealed self check prompt includes the answer`() {
        val item = SelfCheck(
            q = "How does a CDN invalidate content?",
            a = "Versioned URLs and short TTLs."
        )
        val text = selfCheckPrompt(item, revealed = true)

        assertTrue(text.contains(item.q))
        assertTrue(text.contains(item.a))
        assertTrue(text.endsWith("Expand on this answer with the key trade-offs and a concrete example."))
    }
}
