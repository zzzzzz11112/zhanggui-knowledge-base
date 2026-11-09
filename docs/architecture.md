# 架构与数据流

## 文档导入

入口 `web/api/import_service.py` 接收文件，生成 task_id，保存到本地并尝试上传 MinIO，再执行 `processor/import_processor/main_graph.py`。

1. `node_entry` 检查输入并选择 PDF 或 Markdown 分支。当前图实际引用 `nodes/node_enrty.py`。
2. `node_pdf_to_md` 上传 MinerU、轮询任务、下载结果 ZIP 并读取 Markdown；MD 输入跳过这一步。
3. `node_md_img` 为文档图片生成摘要，上传 MinIO，并保存增强后的 `_new.md`。
4. `node_document_split` 按标题切分、拆长合短，保存任务目录下的 `chunks.json`。
5. `node_item_name_recognition` 识别产品名称，回填切片，并将产品名和向量写入产品集合。
6. `node_bge_embedding` 生成切片的稠密与稀疏向量。
7. `node_import_milvus` 更新同 file_title 的切片，写入正文、元数据和向量。

`ImportGraphState` 在节点间传递 task_id、file_dir、file_title、md_path、md_content、chunks 和 item_name 等数据。网页轮询 `/status/{task_id}` 显示进度。

## 检索问答

入口 `web/api/query_service.py` 调用 `processor/query_processor/main_graph.py`。

1. 产品确认节点读取历史、保存用户问题、提取型号并改写问题，再查询产品名称库。
2. 产品不明确时输出澄清或未找到产品的回复；确认后进入检索。
3. 普通混合检索、HyDE 辅助检索、MCP 网络搜索并行执行。
4. RRF 只融合两路本地检索结果；网络摘要在 Rerank 阶段加入。
5. 重排后的资料和历史组成提示词，由模型生成回答。
6. 保存 MongoDB 历史，通过 JSON 或 SSE 返回页面。

`QueryGraphState` 包含 session_id、original_query、rewritten_query、item_names、history、各路检索结果、reranked_docs 和 answer。

## 关键参数

- BGE-M3 当前处理链路使用 1024 维稠密向量和变长稀疏向量。
- 普通与 HyDE 检索均按已确认的 item_name 过滤。
- 稠密与稀疏召回权重为 0.8 / 0.2。
- RRF 默认 k=60，最多保留 5 条本地结果。
- Rerank 动态保留至多 5 条参考资料。
- 当前 MCP 使用 Streamable HTTP，地址应匹配 `/WebSearch/mcp`。

## 前端与状态

聊天页面内嵌 Markdown 渲染器，当前仅显示文字。后台仍会保存图片摘要与对象，用于文档理解及检索。

导入任务以 task_id 标识；多轮问答以 session_id 标识。历史保存在 MongoDB，任务进度和事件队列保存在当前 Python 进程内存中。
