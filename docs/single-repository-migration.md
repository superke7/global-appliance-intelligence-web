# 全球家电资讯：单公开仓库迁移方案（尚未生产切换）

## 目标架构
- 唯一代码和正式公开数据仓库：`superke7/global-appliance-intelligence-web`，保留现有 GitHub Pages 网站和同源 RSS。
- Google Sheets 保持非公开的业务事实、审核和运行日志真源；ChatGPT 候选采集与正式审核仍分开运行。
- 发布前就必须取得正式批次 QA=PASS、完整条目数 N、Event 身份检查及公开字段白名单检查。
- 由发布任务**直接调用公开仓库的 GitHub contents API**，只把符合公开合同的最终 JSON 写入 `public-batches/YYYYMMDD/public-batch.json`；不得使用**公开 Issue/PR/暂存分支**承载待审核内容。
- GitHub Pages 自动读取最终 JSON 构建网站与 RSS；公开站在线验收保持独立。
- 原私有仓库仅在迁移验收前保留为生产退路；完成切换并观察稳定之后归档，不公开私有 Git 历史、PR/Issue、运维记录和 Secrets。

## 单仓库发布（北京时间；任务时间由 Schedule 控制）
1. 06:45候选采集：只写Google Sheets候选池，无GitHub权限和内容生产。
2. 07:15正式早报：原文核验、筛选、Event归并、Google Sheets正式行及QA。公开JSON以 `YYYYMMDD-0715` 为固定批次ID（非任务启动时间）。此阶段必须在GitHub外完成内容安全审查。
3. 07:35发布：校验正式批次日志与N；根据公开仓库的 `config/public-batch-contract.json`、`config/public-event-registry.json`及既有批次做 preflight；如果合格且目标缺失，直接创建当天公开JSON。如果已有且完全一致，记ALREADY_SYNCED；如有新增，只允许原有items不变的尾部追加；不同或缺少审核证据则拒绝。
4. 公开仓库 `Refresh public event registry` 在正式批次提交后，从已经公开的 `public-batches/**` 自动重建 `config/public-event-registry.json`；Event 身份只能来源于公开批次，不得写入Google Sheets内部Event字段或内部摘要。此派生更新不应重复触发Pages构建。GitHub `Deploy GitHub Pages` 随正式批次写入自动运行。
5. 08:05补偿：先读公开同日JSON和正式日志；已经一致→不重复发；缺失或有效尾部追加→按同样preflight规则执行单次补偿。不能重新检索新闻或重新定义Event。
6. `Verify daily Pages publication and RSS` 负责部署完成后的线上校验；未见实际结果则记UNVERIFIED。现有定时验收作为异常兜底，绝不把workflow成功自动等同于页面成功。

## 公开前的必检项
- 完整复核正式批次 `COMPLETE`、Sheets更新成功、当日QA PASS、Event映射QA PASS、公开JSON预校验 SUCCESS；合法审核的零条批次仍然可发布。
- 对所有字段实施强制白名单；拒绝敏感字段、内部意见/行动建议、非公开经营数据、内部域名/文件路径及凭据；不能仅凭某几个关键词判断安全。
- 复核标题、日期、摘要、完整正文、原始来源URL、Event Key/title/date关联，保留真实原始新闻发布日期，不允许从未审原始候选直接生成公开文件。
- 对全历史公开 batch 的 `public_id` 和规范URL去重；当天原有items不得改写、删除或重排；只接受合法尾部追加。
- 涉及同日并发更新时，GitHub Contents API 使用当前文件SHA进行CAS更新，冲突后只复读一次；绝不强制覆盖。任何数据修订须另行走纠错审核机制，不能绕过仅追加规则。
- 本仓库 `publishing/preflight_public_batch.py` 提供本地**提交前**确定性检测示范，执行输入和输出必须位于公开Git工作区之外，且只能使用已经完成内容审查的公开候选。CI和Pages构建验证是第二道防线：提交到公开GitHub后再失败不代表从未泄露。

## 关键测试与切换条件
- `python3 -m publishing.test_preflight_public_batch` 验证安全创建、重复写入、只追加、历史去重、敏感字段及Event身份拒绝。
- `python3 publishing/validate_repository.py` 对已公开历史批次校验，保留旧日期既有 public_id 格式，现代批次采用严格数据合同。
- 需要一条合法的下一次正式发布记录证明 **Google Sheets→公共JSON→Pages/RSS** 成功，且自动公开事件库生成成功；观察期内保留08:05补偿。
- **未完成正式任务提示词切换前，不允许删除私有仓库或撤销目前的跨仓库镜像Token。** 日后迁移完成应撤销 `GAI_PUBLIC_MIRROR_TOKEN`，仅保留必要的 GitHub 访问授权。
- 迁移前不调整任何定时任务的Schedule，避免当天同时存在两种具有写入能力的自动流程。

## 迁移状态
- 阶段1（公开合同、历史批次与Event映射代码）：已通过CI并合并。
- 阶段2（发布前preflight、模拟测试和公开站构建QA）：PR演练中，未启用单仓库生产写入。
- 阶段3（公开Event登记自动派生）：开发测试中；提示词切换、真实发布、7天观察及退役私有仓库尚未开始。
