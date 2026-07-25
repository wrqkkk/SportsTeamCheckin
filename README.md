# ChatCheckin

ChatCheckin 用于将导出的群聊记录转换为结构化打卡记录、每周统计和 Excel 汇总表。

第一版本采用明确、可复现的格式规则，不对普通聊天文本进行推测。

> 当前版本：Version 1 文档准备阶段

---

# 中文说明

## 推荐格式

### 普通打卡

```text
打卡：训练内容
```

例如：

```text
打卡：篮球基本功1.5h，投篮50个
```

普通打卡归入消息提交当天。

### 补卡

```text
补卡：周X 训练内容
```

例如：

```text
补卡：周五 篮球基本功1.5h
```

一周从周一开始，到周日结束。

没有额外说明时，`周X` 指消息提交日期所在周的对应星期，并且该日期必须早于消息提交日期。

例如，消息在 2026-07-19 周日提交：

```text
补卡：周五 篮球3v3 2h
```

该记录归入：

```text
2026-07-17 周五
```

如果目标星期与提交日期相同，或者晚于提交日期，系统不会自动猜测为上一周，而会将其标记为日期指代不明确。

例如，消息在 2026-07-15 周三提交：

```text
补卡：周五 篮球训练1.5h
```

该记录不会自动计入。

如果实际想补上一周周五，应明确写为：

```text
补卡：上周五 篮球训练1.5h
```

## 补充兼容格式

Version 1 还兼容以下明确表达：

```text
补卡：昨天 篮球1.5h
补卡：昨日 篮球1.5h
补卡：前天 跑步0.5h
补卡：上周五 健身1h
补卡：2026-07-10 篮球1.5h
补卡：7月10日 篮球1.5h
```

普通打卡也兼容没有冒号的写法：

```text
打卡 篮球1.5h
打卡篮球1.5h
```

但仍推荐使用：

```text
打卡：训练内容
补卡：周X 训练内容
```

## 基本使用流程

```text
导出群聊 JSON
        ↓
配置成员名单和姓名别名
        ↓
识别普通打卡与补卡
        ↓
解析实际训练日期
        ↓
按成员和训练日期去重
        ↓
生成 Excel 汇总表
```

程序将同时保留：

- 消息提交时间；
- 实际训练日期；
- 原始消息内容；
- 自动识别结果。

## Version 1 支持范围

Version 1 计划支持：

- 以“打卡”开头的普通打卡；
- 以“补卡”开头的补卡；
- `昨天`、`昨日`和`前天`；
- `上周一`至`上周日`；
- `周一`至`周日`；
- 明确年月日和月日；
- 周一至周日的周统计；
- 同一成员同一训练日期最多计一次；
- Excel 汇总表和记录明细表；
- 原始消息追溯。

Version 1 暂不支持：

- 图片文字识别；
- 语音或视频内容识别；
- 自动理解未以“打卡”或“补卡”开头的普通文本；
- 自动猜测含糊日期；
- 从聊天内容中自动推断请假。

完整规则见 [`docs/rules.md`](docs/rules.md)。

## 计划输出

Version 1 计划生成一个 Excel 工作簿，包括：

- `total`：正式汇总；
- 每周工作表：每日训练内容和周累计；
- `record_details`：可追溯记录明细。

未匹配的普通文本不会自动计入统计，但可以保留供后续检查。

---

# English

ChatCheckin converts exported group-chat records into structured check-in records, weekly statistics, and Excel summary reports.

Version 1 uses explicit and reproducible format rules. It does not infer activities from ordinary chat messages.

> Current status: Version 1 documentation stage

## Recommended Formats

### Normal Check-in

```text
打卡：activity content
```

Example:

```text
打卡：篮球基本功1.5h，投篮50个
```

A normal check-in is assigned to the message submission date.

### Makeup Check-in

```text
补卡：周X activity content
```

Example:

```text
补卡：周五 篮球基本功1.5h
```

A week begins on Monday and ends on Sunday.

Without an additional week modifier, `周X` refers to the corresponding weekday within the message submission week, and the resolved date must be earlier than the submission date.

For example, when a message is submitted on Sunday, 2026-07-19:

```text
补卡：周五 篮球3v3 2h
```

The record is assigned to:

```text
Friday, 2026-07-17
```

If the target weekday is the same as or later than the submission date, the system does not reinterpret it as the previous week. The date reference is marked as ambiguous.

For example, when a message is submitted on Wednesday, 2026-07-15:

```text
补卡：周五 篮球训练1.5h
```

The record is not counted automatically.

To refer to Friday of the previous week, write:

```text
补卡：上周五 篮球训练1.5h
```

## Additional Compatible Formats

Version 1 also supports the following explicit expressions:

```text
补卡：昨天 篮球1.5h
补卡：昨日 篮球1.5h
补卡：前天 跑步0.5h
补卡：上周五 健身1h
补卡：2026-07-10 篮球1.5h
补卡：7月10日 篮球1.5h
```

Normal check-ins without a colon are also supported:

```text
打卡 篮球1.5h
打卡篮球1.5h
```

The recommended formats remain:

```text
打卡：activity content
补卡：周X activity content
```

## Basic Workflow

```text
Export group-chat JSON
        ↓
Configure members and name aliases
        ↓
Recognize normal and makeup check-ins
        ↓
Resolve the actual training date
        ↓
Deduplicate by member and training date
        ↓
Generate an Excel report
```

The program preserves:

- the message submission time;
- the actual training date;
- the original message content;
- the automatic classification result.

## Version 1 Scope

Version 1 is planned to support:

- normal check-ins beginning with `打卡`;
- makeup check-ins beginning with `补卡`;
- `昨天`, `昨日`, and `前天`;
- `上周一` through `上周日`;
- `周一` through `周日`;
- explicit full dates and month-day dates;
- Monday-to-Sunday weekly statistics;
- at most one counted check-in per member per training date;
- Excel summary and detail sheets;
- source-message traceability.

Version 1 does not currently support:

- OCR for images;
- recognition of voice or video content;
- automatic interpretation of ordinary text that does not begin with `打卡` or `补卡`;
- guessing ambiguous dates;
- automatic extraction of leave information from chat messages.

See the complete rules in [`docs/rules.md`](docs/rules.md).

## Planned Output

Version 1 is planned to generate one Excel workbook containing:

- `total`: the formal summary;
- weekly sheets: daily activity content and weekly totals;
- `record_details`: traceable structured records.

Unmatched ordinary text is not counted automatically, but may be retained for later review.
