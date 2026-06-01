# 观世音菩萨写作法评估矩阵

## Positive Routing

| User prompt | Expected routing | Expected behavior |
| --- | --- | --- |
| “请用观世音菩萨写作法改这篇中文文章。” | Load `guanshiyin-writing` | 直接改稿，重点补足观 / 世 / 音 / 菩萨四维。 |
| “按观世音四维评审这篇随笔。” | Load `guanshiyin-writing` | 按四项给简洁诊断和修改建议。 |
| “用刘文典该方法帮我写一篇中文演讲稿。” | Load `guanshiyin-writing` | 先识别文体与对象，再按四维组织成稿。 |
| “请从观、世、音、菩萨四项评价这篇文章。” | Load `guanshiyin-writing` | 四项分别评分或诊断，并给可执行改法。 |

## Negative Routing

| User prompt | Expected routing | Reason |
| --- | --- | --- |
| “帮我把这段话去 AI 味。” | Use `humanizer` | 未点名观世音方法，需求是普通自然化。 |
| “把这个按钮文案写得更清楚。” | Use `clarify` | UX copy 和表达澄清不属于四维写作法。 |
| “最后帮我 polish 一下交付稿。” | Use `polish` | 交付润色不是观世音方法触发条件。 |
| “总结这篇文章的核心观点。” | No skill or extraction skill | 普通摘要/提取不应加载本 skill。 |
| “让文章更有细节、洞察、节奏和悲悯。” | Do not load by default | 这些是四维特征，但用户没有明确点名该方法。 |

## Forbidden Load

- 不因“中文写作”“润色”“改稿”“评审文章”单独触发本 skill。
- 不因用户要求“更有生活感”“更有人味”“更有节奏”“更温暖”单独触发本 skill。
- 不把本 skill 当作通用 humanizer、UX copy、polish、摘要或提取工具。
- 不在英文写作、代码文档、需求文档、PR 描述中加载本 skill，除非用户明确要求用四维方法写中文表达。

## End-to-End Paired Eval

| Pair | Prompt A | Prompt B | Pass condition |
| --- | --- | --- | --- |
| A | “帮我把这篇中文文章去 AI 味。” | “按观世音菩萨写作法帮我改这篇中文文章。” | A 不加载本 skill；B 加载并按四维改稿。 |
| B | “评审这篇随笔，指出问题。” | “从观 / 世 / 音 / 菩萨四项评审这篇随笔。” | A 做普通评审；B 输出四项诊断。 |
| C | “总结这篇文章。” | “用观世音四维总结并评审这篇文章。” | A 只摘要；B 可摘要后按四维评审。 |
| D | “这个空状态提示怎么写更清楚？” | “用刘文典该方法写一段中文短文。” | A 路由到 `clarify`；B 路由到本 skill。 |

每组 paired eval 必须检查两点：触发边界是否正确，加载后是否真正执行四维，而不是只替换措辞。

## Progressive Loading Eval

| Case | Prompt | Expected loading | Evidence |
| --- | --- | --- | --- |
| Normal use | “按观世音四维评审这篇文章。” | 只需读取 `SKILL.md` | 输出按四维诊断，不引用 eval matrix。 |
| Skill review | “评估 guanshiyin-writing 的路由边界。” | 读取 `references/eval-matrix.md` | 输出包含 positive、negative、forbidden load 或 paired eval。 |
| Regression check | “跑一遍该 skill 的路由评估计划。” | 读取 `references/eval-matrix.md` | 输出包含实际路由记录和 pass/fail。 |

普通写作、改稿或评文不应为了完成正文而读取 `references/eval-matrix.md`；该文件只服务 skill 评估、路由回归和维护。

## Execution Record Template

| eval_id | prompt | actual_routing | actual_behavior | pass/fail | notes |
| --- | --- | --- | --- | --- | --- |
| positive-1 |  |  |  |  |  |
| negative-1 |  |  |  |  |  |
| forbidden-1 |  |  |  |  |  |

记录时同时保留 `with_skill` 与 `without_skill` 的关键差异；若只让输出变长但没有改善四维执行，判为 fail。
