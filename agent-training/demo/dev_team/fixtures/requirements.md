# 任务看板需求与验收契约

新增任务、列表查询、修改状态；数据使用 SQLite 保存，刷新页面和重新创建 TaskStore 后必须保留。

- `TaskStore(db_path)` 创建或连接数据库；`close()` 关闭连接。
- `create_task(title)` 返回包含 `id / title / status` 的字典。标题去除首尾空白，空标题及超过 120 字的标题抛出 ValueError。默认状态为 todo。
- `list_tasks()` 返回按 id 升序排列的任务字典列表。
- `update_status(task_id, status)` 更新并返回任务字典。状态只允许 todo / doing / done；非法状态抛出 ValueError，而且不得改变原记录。不存在的任务抛出 KeyError。
- 服务接口：GET /api/tasks，POST /api/tasks 接收 title，PATCH /api/tasks/{id} 接收 status；参数错误返回 400，不存在返回 404。
- 前端使用文本节点呈现用户输入；这次教学 PR 的变更范围是 board.py 的状态修改逻辑。

固定验收测试由讲师维护。开发角色仅可修改 board.py，不能修改需求、测试或调用方；修改公共契约需人工重新设计。
