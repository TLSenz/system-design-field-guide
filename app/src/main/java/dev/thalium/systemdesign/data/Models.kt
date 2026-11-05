package dev.thalium.systemdesign.data

data class LibraryIndex(
    val title: String,
    val subtitle: String,
    val parts: List<Part>,
    val chapters: List<ChapterMeta>
)

data class Part(
    val id: String,
    val title: String,
    val chapterIds: List<String>
)

data class ChapterMeta(
    val id: String,
    val number: String,
    val title: String,
    val minutes: Int,
    val wordCount: Int,
    val sectionCount: Int,
    val questionCount: Int
)

data class Chapter(
    val id: String,
    val number: String,
    val title: String,
    val minutes: Int,
    val wordCount: Int,
    val sections: List<Section>,
    val selfCheck: List<SelfCheck>
)

data class Section(
    val id: String,
    val title: String,
    val blocks: List<Block>
)

data class SelfCheck(
    val q: String,
    val a: String
)

data class Block(
    val type: String,
    val text: String = "",
    val level: Int = 0,
    val items: List<ListItem> = emptyList(),
    val ordered: Boolean = false,
    val header: List<String> = emptyList(),
    val rows: List<List<String>> = emptyList(),
    val lang: String = "",
    val code: String = ""
)

data class ListItem(
    val text: String,
    val level: Int
)

data class Mcq(
    val id: String,
    val topic: String,
    val question: String,
    val options: List<String>,
    val answerIndex: Int,
    val explanation: String
)
