# 最终公开JSON批次

本目录只保存已经定稿、已经公开化处理并通过标准合同校验的公开JSON。

固定路径：

```text
public-batches/YYYYMMDD/public-batch.json
```

规则：

- 每个北京时间日期最多一个文件；
- 只能create，不得update或覆盖；
- 一次提交只新增一个批次；
- 文件必须符合`schema_version: 1.0`合同；
- 文件不得超过25 MiB；
- 文件不得包含海尔内部信息、内部字段、内部风险评级、内部负责人或“对海尔全球布局的启示”；
- 不在本目录保存SSH密钥、服务器地址、`known_hosts`、WordPress凭据或其他Secrets；
- 07:50、08:05、08:20重试均使用同一不可变文件，不重新生成内容。

该目录的新增文件会触发`.github/workflows/deliver-public-payload.yml`。修改既有文件不会被投递，并会导致工作流失败。
