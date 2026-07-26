# ChatCheckin Version 1 Rules

---

# 中文规则

## 1. 目的

本文档定义 ChatCheckin Version 1 的消息识别、补卡日期解析、周次归属、去重、统计和审计规则。

Version 1 只处理具有明确格式的打卡记录，不尝试理解任意自然语言。

核心原则是：

- 规则确定；
- 结果可复现；
- 原始消息可追溯；
- 无法确定的记录不自动计入；
- 自动识别结果和后续人工修正相互分离。

## 2. Version 1 支持范围

Version 1 支持：

- 以“打卡”开头的文本消息；
- 以“补卡”开头的文本消息；
- “打卡”消息中附带的补卡片段；
- 明确年月日；
- 明确月日；
- `昨天`、`昨日`和`前天`；
- `周一`至`周日`；
- `上周一`至`上周日`；
- 周一至周日的周次划分；
- 成员名单和姓名别名；
- 同一成员同一训练日期最多计一次；
- 原始消息追溯；
- Excel 汇总和记录明细。

Version 1 暂不支持：

- 图片 OCR；
- 语音识别；
- 视频内容识别；
- 自动理解普通自然语言训练记录；
- 猜测含糊日期；
- 从聊天消息中自动推断请假。

## 3. 输入要求

输入为聊天记录导出的详细 JSON 文件。每条消息应尽可能包含消息 ID、时间戳、消息类型、内容、发送者账号和发送者显示名称。

程序不得修改原始 JSON 文件。

## 4. 时区和周次

所有时间必须先转换到配置时区。默认时区为：

```yaml
timezone: Asia/Shanghai
```

一周从周一开始，到周日结束。

普通打卡使用消息提交日期归属周次；补卡使用解析后的训练日期归属周次。

## 5. 文本标准化

程序可以在解析前：

- 删除开头和结尾空格；
- 压缩重复空格；
- 兼容中文和英文冒号；
- 兼容中文和英文逗号；
- 兼容中文和英文分号；
- 统一换行符。

标准化只用于解析，不得覆盖原始消息内容。

## 6. 普通打卡识别

文本标准化后，只要开头为 `打卡`，就进入普通打卡解析流程。

以下格式均应识别：

```text
打卡：篮球1.5h
打卡:篮球1.5h
打卡 篮球1.5h
打卡篮球1.5h
打卡，篮球1.5h
打卡；篮球1.5h
```

识别后，程序删除 `打卡`、紧随其后的空格及冒号、逗号或分号，剩余文本作为训练内容。

如果消息只有 `打卡` 或 `打卡：`，则标记为：

```text
CHECKIN_MISSING_CONTENT
```

并设置 `counted: false`。

## 7. 未匹配文本

不以“打卡”或“补卡”开头的文本不进入 Version 1 自动统计，可标记为 `UNMATCHED_TEXT`，默认不计入。

## 8. 补卡识别

文本标准化后，如果开头为 `补卡`，则进入补卡解析流程。

推荐格式：

```text
补卡：日期表达 训练内容
```

补卡记录必须同时保留消息提交时间、提交日期和实际训练日期，并按照实际训练日期统计。

## 9. “打卡”消息中的补卡片段

以“打卡”开头的消息可以同时包含普通打卡和补卡：

```text
打卡：健身1h，补周五：篮球基本功1.5h
```

系统生成一条提交当天的普通打卡和一条解析到目标日期的补卡。

也可以包含多个补卡片段。若第一段没有普通训练内容，例如 `打卡：补周五 篮球1.5h`，则只生成补卡记录。

## 10. 支持的明确日期

完整日期支持：

```text
2026-07-10
2026/07/10
2026.07.10
2026年7月10日
2026年7月10号
```

月日支持：

```text
7月10日
7月10号
7/10
7-10
7.10
```

月日年份根据报告周期确定；无法唯一确定时标记为 `MAKEUP_DATE_UNRESOLVED`，不自动计入。

## 11. Day 类型相对日期

Version 1 只支持：

```text
昨天
昨日
前天
```

解析规则：

```text
昨天 = submission_date - 1 日
昨日 = submission_date - 1 日
前天 = submission_date - 2 日
```

暂不支持 `昨晚`、`前一天`、`两天前`、`大前天`、`前几天`、`之前那天`。

## 12. 当前周星期表达

支持 `周一`至`周日`、`周天`以及 `星期一`至`星期日`、`星期天`。

没有额外周次修饰时，星期表达首先指消息提交日期所在周的对应日期。一周从周一开始，到周日结束。

## 13. 补卡日期必须指向过去

补卡训练日期必须严格早于消息提交日期：

```text
training_date < submission_date
```

如果目标日期与提交日期相同或晚于提交日期，则日期指代不明确，标记为：

```text
MAKEUP_DATE_AMBIGUOUS
```

并设置：

```yaml
training_date: null
counted: false
```

程序不得自动改为上一周对应星期。

例如，消息在 2026-07-15 周三提交：

```text
补卡：周五 篮球训练1.5h
```

提交日所在周的周五为 2026-07-17，晚于提交日期，因此不自动计入。

若实际指上一周周五，应写为：

```text
补卡：上周五 篮球训练1.5h
```

若训练发生在提交当天，应写为：

```text
打卡：篮球训练1.5h
```

## 14. 上周星期表达

Version 1 支持 `上周一`至`上周日`及 `上周天`。

解析步骤：

1. 找到提交日期所在周的周一；
2. 向前移动 7 日；
3. 在上一周中选择指定星期。

该规则可以跨月和跨年。

暂不支持 `上周`、`上周末`、`上个星期`、`上星期五`、`上一周五`、`上上周五`、`本周五`、`这周五`、`下周五`。

## 15. 日期表达匹配优先级

解析器应按以下顺序匹配：

1. 完整年月日；
2. 月日；
3. `上周 + 星期`；
4. `昨天`、`昨日`、`前天`；
5. 当前周的 `周X` 或 `星期X`。

必须优先识别完整且更具体的表达，例如 `上周五` 不得被部分识别为 `周五`。

## 16. 无法解析和含糊日期

`之前`、`上次`、`前几天`、`那天`、`上周`、`周末`、`最近一次`、`前一次`等暂不自动解析，标记为 `MAKEUP_DATE_UNRESOLVED`。

日期可解析但训练内容为空时，标记为 `MAKEUP_MISSING_CONTENT`，不自动计入。

## 17. 非文本消息

图片消息标记为：

```yaml
activity_content: 图片
record_type: IMAGE_UNRECOGNIZED
counted: false
```

语音、视频和文件消息分别标记为 `VOICE_UNRECOGNIZED`、`VIDEO_UNRECOGNIZED`、`FILE_UNRECOGNIZED`，均不自动计入。

## 18. 成员与别名

只有配置名单中的成员进入正式统计。可以通过别名配置将群昵称映射为标准姓名，所有输出使用标准姓名。

## 19. 去重规则

同一成员同一训练日期最多计一次。

若同一天存在多条有效记录，所有原始记录保留在明细中，训练内容可以合并展示，但每日和每周次数只增加一次。

普通打卡与补卡归入同一天时也只计一次。

## 20. 自动计入状态

自动计入：

```text
NORMAL_CHECKIN
MAKEUP_CHECKIN
```

不自动计入：

```text
CHECKIN_MISSING_CONTENT
MAKEUP_MISSING_CONTENT
MAKEUP_DATE_UNRESOLVED
MAKEUP_DATE_AMBIGUOUS
IMAGE_UNRECOGNIZED
VOICE_UNRECOGNIZED
VIDEO_UNRECOGNIZED
FILE_UNRECOGNIZED
UNMATCHED_TEXT
```

## 21. 记录结构

每条结构化记录至少包含：

```yaml
message_id: string
person: string
sender_username: string
submit_time: datetime
submission_date: date
training_date: date | null
activity_content: string
record_type: string
counted: boolean
source_message_type: string
original_content: string
raw_content: string | null
resolution_note: string | null
```

## 22. 输出工作簿

Version 1 计划生成一个 Excel 工作簿：

- `total`：正式汇总；
- 每周工作表：每日训练内容、每周累计和每日小计；
- `record_details`：训练日期、提交时间、姓名、内容、记录类型、计入状态、周次、原始消息和解析说明。

## 23. 审计原则

程序不得删除、覆盖或修改原始消息。

每条结构化记录必须能追溯到原始消息 ID、原始发送者、原始提交时间和原始消息内容。

后续人工修正必须作为独立修正记录保存，不得冒充自动识别结果。

## 24. 必测案例

| 提交日期 | 消息 | 预期结果 |
|---|---|---|
| 2026-07-19 | `打卡：篮球1.5h` | 2026-07-19，正常打卡 |
| 2026-07-19 | `补卡：周五 篮球1.5h` | 2026-07-17，有效 |
| 2026-07-15 | `补卡：周二 篮球1.5h` | 2026-07-14，有效 |
| 2026-07-15 | `补卡：周五 篮球1.5h` | 日期含糊，不计入 |
| 2026-07-17 | `补卡：周五 篮球1.5h` | 日期含糊，不计入 |
| 2026-07-19 | `补卡：昨天 篮球1.5h` | 2026-07-18，有效 |
| 2026-07-19 | `补卡：昨日 篮球1.5h` | 2026-07-18，有效 |
| 2026-07-19 | `补卡：前天 篮球1.5h` | 2026-07-17，有效 |
| 2026-07-19 | `补卡：上周五 篮球1.5h` | 2026-07-10，有效 |
| 2026-07-13 | `补卡：上周日 篮球1.5h` | 2026-07-12，有效 |
| 2027-01-04 | `补卡：上周五 篮球1.5h` | 2027-01-01，有效 |
| 2026-07-19 | `补卡：上周 篮球1.5h` | 无法解析，不计入 |
| 2026-07-19 | `补卡：之前的篮球训练` | 无法解析，不计入 |

## 25. Version 1 边界

Version 1 优先保证明确、稳定、可测试和可追溯，而不是尽可能识别所有消息。

未以“打卡”或“补卡”开头的文本不会自动计入。

后续版本可以扩展智能文本识别、人工审核、图片 OCR 和 Web 界面，但不得改变 Version 1 已冻结规则的基础行为。

---

# English Rules

## 1. Purpose

This document defines the message recognition, makeup-date resolution, weekly assignment, deduplication, reporting, and audit rules for ChatCheckin Version 1.

Version 1 handles only explicitly formatted check-in records and does not attempt to interpret arbitrary natural-language messages.

The core principles are:

- deterministic rules;
- reproducible results;
- complete source-message traceability;
- no automatic counting of uncertain records;
- separation between automatic classifications and future manual corrections.

## 2. Version 1 Scope

Version 1 supports:

- text messages beginning with `打卡`;
- text messages beginning with `补卡`;
- makeup segments embedded inside a `打卡` message;
- explicit full dates;
- explicit month-day dates;
- `昨天`, `昨日`, and `前天`;
- `周一` through `周日`;
- `上周一` through `上周日`;
- Monday-to-Sunday weekly grouping;
- configured members and name aliases;
- at most one counted check-in per member per training date;
- source-message traceability;
- Excel summaries and record details.

Version 1 does not currently support image OCR, speech recognition, video-content recognition, automatic interpretation of ordinary natural-language activity messages, guessing ambiguous dates, or automatic extraction of leave information from chat messages.

## 3. Input Requirements

The input is a detailed JSON chat export. Each message should contain as many source fields as possible, including message ID, timestamp, message type, content, sender username, and sender display name.

The program must not modify the source JSON file.

## 4. Timezone and Week Definition

All timestamps must first be converted into the configured timezone. The default timezone is:

```yaml
timezone: Asia/Shanghai
```

A week begins on Monday and ends on Sunday.

Normal check-ins are assigned using the submission date. Makeup check-ins are assigned using the resolved training date.

## 5. Text Normalization

Before parsing, the program may remove leading and trailing whitespace, collapse repeated whitespace, support Chinese and English punctuation, and normalize line endings.

Normalization is used only for parsing and must not overwrite the original message content.

## 6. Normal Check-in Recognition

After normalization, a text message enters the normal check-in parser whenever it begins with `打卡`.

Supported examples:

```text
打卡：篮球1.5h
打卡:篮球1.5h
打卡 篮球1.5h
打卡篮球1.5h
打卡，篮球1.5h
打卡；篮球1.5h
```

The parser removes the prefix and immediately following separators. The remaining text becomes the activity content.

A message containing only `打卡` or `打卡：` is classified as `CHECKIN_MISSING_CONTENT` with `counted: false`.

## 7. Unmatched Text

Text that does not begin with `打卡` or `补卡` is outside the Version 1 automatic-recognition scope. It may be classified as `UNMATCHED_TEXT` and is not counted automatically.

## 8. Makeup Check-in Recognition

A normalized message beginning with `补卡` enters the makeup parser.

Recommended format:

```text
补卡：date expression activity content
```

Each makeup record preserves the submission time, submission date, and actual training date. Statistics use the training date.

## 9. Makeup Segments Inside a `打卡` Message

A message beginning with `打卡` may contain both a normal check-in and one or more makeup segments:

```text
打卡：健身1h，补周五：篮球基本功1.5h
```

The system creates one normal check-in for the submission date and one makeup record for the resolved target date.

If no normal activity appears before the first makeup segment, the parser creates only the makeup record.

## 10. Supported Explicit Dates

Supported full-date formats include:

```text
2026-07-10
2026/07/10
2026.07.10
2026年7月10日
2026年7月10号
```

Supported month-day formats include:

```text
7月10日
7月10号
7/10
7-10
7.10
```

The year is resolved from the reporting period. If it cannot be resolved uniquely, the record is classified as `MAKEUP_DATE_UNRESOLVED` and is not counted automatically.

## 11. Day-based Relative Dates

Version 1 supports only:

```text
昨天
昨日
前天
```

Resolution rules:

```text
昨天 = submission_date - 1 day
昨日 = submission_date - 1 day
前天 = submission_date - 2 days
```

Expressions such as `昨晚`, `前一天`, `两天前`, `大前天`, `前几天`, and `之前那天` are not supported.

## 12. Weekdays Within the Submission Week

Version 1 supports `周一` through `周日`, `周天`, and the corresponding `星期X` expressions.

Without an additional week modifier, a weekday expression first refers to the corresponding date within the message submission week. A week begins on Monday and ends on Sunday.

## 13. A Makeup Date Must Refer to the Past

A makeup training date must be strictly earlier than the submission date:

```text
training_date < submission_date
```

If the resolved date is the same as or later than the submission date, the reference is ambiguous. The record is classified as `MAKEUP_DATE_AMBIGUOUS` with `training_date: null` and `counted: false`.

The parser must not reinterpret the expression as the corresponding weekday of the previous week.

For example, when a message is submitted on Wednesday, 2026-07-15:

```text
补卡：周五 篮球训练1.5h
```

Friday of the submission week is 2026-07-17, which is later than the submission date. The record is therefore not counted automatically.

To refer to Friday of the previous week, write:

```text
补卡：上周五 篮球训练1.5h
```

For an activity completed on the submission date, write:

```text
打卡：篮球训练1.5h
```

## 14. Previous-week Weekday Expressions

Version 1 supports `上周一` through `上周日` and `上周天`.

Resolution steps:

1. find Monday of the submission date's week;
2. move backward by seven days;
3. select the requested weekday within the previous week.

The rule applies across month and year boundaries.

Expressions such as `上周`, `上周末`, `上个星期`, `上星期五`, `上一周五`, `上上周五`, `本周五`, `这周五`, and `下周五` are not supported.

## 15. Date-expression Matching Priority

The parser applies the following matching priority:

1. full year-month-day dates;
2. month-day dates;
3. `上周 + weekday`;
4. `昨天`, `昨日`, or `前天`;
5. current-week `周X` or `星期X`.

Complete and more specific expressions must be matched first. For example, `上周五` must not be partially interpreted as `周五`.

## 16. Unresolved and Ambiguous Dates

Expressions such as `之前`, `上次`, `前几天`, `那天`, `上周`, `周末`, `最近一次`, and `前一次` are not resolved automatically and are classified as `MAKEUP_DATE_UNRESOLVED`.

If a date is resolved but activity content is missing, the record is classified as `MAKEUP_MISSING_CONTENT` and is not counted automatically.

## 17. Non-text Messages

Image messages are stored as:

```yaml
activity_content: 图片
record_type: IMAGE_UNRECOGNIZED
counted: false
```

Voice, video, and file messages are classified as `VOICE_UNRECOGNIZED`, `VIDEO_UNRECOGNIZED`, and `FILE_UNRECOGNIZED`. They are not counted automatically.

## 18. Members and Aliases

Only configured members are included in formal statistics. Name aliases may map group nicknames to canonical names. All outputs use canonical member names.

## 19. Deduplication

A member may contribute at most one counted check-in per training date.

When multiple valid records exist for the same member and training date, all source records remain in the detail output and activity content may be combined for display, but the daily and weekly count increases by only one.

A normal check-in and a makeup check-in assigned to the same date also count as one.

## 20. Automatically Counted Statuses

Automatically counted:

```text
NORMAL_CHECKIN
MAKEUP_CHECKIN
```

Not automatically counted:

```text
CHECKIN_MISSING_CONTENT
MAKEUP_MISSING_CONTENT
MAKEUP_DATE_UNRESOLVED
MAKEUP_DATE_AMBIGUOUS
IMAGE_UNRECOGNIZED
VOICE_UNRECOGNIZED
VIDEO_UNRECOGNIZED
FILE_UNRECOGNIZED
UNMATCHED_TEXT
```

## 21. Record Model

Each structured record contains at least:

```yaml
message_id: string
person: string
sender_username: string
submit_time: datetime
submission_date: date
training_date: date | null
activity_content: string
record_type: string
counted: boolean
source_message_type: string
original_content: string
raw_content: string | null
resolution_note: string | null
```

## 22. Output Workbook

Version 1 is planned to generate one Excel workbook containing:

- `total`: the formal summary;
- weekly sheets: daily activity content, weekly totals, and daily totals;
- `record_details`: training date, submission time, member name, activity content, record type, counted status, assigned week, original message, and resolution note.

## 23. Audit Principles

The program must not delete, overwrite, or modify source messages.

Every structured record must be traceable to the original message ID, sender, submission time, and message content.

Future manual corrections must be stored as separate correction records and must not be presented as original automatic classifications.

## 24. Required Test Cases

| Submission date | Message | Expected result |
|---|---|---|
| 2026-07-19 | `打卡：篮球1.5h` | 2026-07-19, normal check-in |
| 2026-07-19 | `补卡：周五 篮球1.5h` | 2026-07-17, valid |
| 2026-07-15 | `补卡：周二 篮球1.5h` | 2026-07-14, valid |
| 2026-07-15 | `补卡：周五 篮球1.5h` | Ambiguous date, not counted |
| 2026-07-17 | `补卡：周五 篮球1.5h` | Ambiguous date, not counted |
| 2026-07-19 | `补卡：昨天 篮球1.5h` | 2026-07-18, valid |
| 2026-07-19 | `补卡：昨日 篮球1.5h` | 2026-07-18, valid |
| 2026-07-19 | `补卡：前天 篮球1.5h` | 2026-07-17, valid |
| 2026-07-19 | `补卡：上周五 篮球1.5h` | 2026-07-10, valid |
| 2026-07-13 | `补卡：上周日 篮球1.5h` | 2026-07-12, valid |
| 2027-01-04 | `补卡：上周五 篮球1.5h` | 2027-01-01, valid |
| 2026-07-19 | `补卡：上周 篮球1.5h` | Unresolved, not counted |
| 2026-07-19 | `补卡：之前的篮球训练` | Unresolved, not counted |

## 25. Version 1 Boundary

Version 1 prioritizes deterministic, stable, testable, and auditable behavior rather than maximum message recall.

Text that does not begin with `打卡` or `补卡` is not counted automatically.

Future versions may add semantic text recognition, manual-review workflows, image OCR, and a web interface, but they must not change the frozen foundational behavior of the Version 1 rule set.
