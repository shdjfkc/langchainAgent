---
name: memory-tier-plan
description: 记忆模块热/温/冷三层存储规划
metadata:
  type: project
---

# 记忆模块三层架构

## 目标
- **热层 (Redis)**: 当前活跃会话，1 小时 TTL，即时读写
- **温层 (MySQL)**: 近期完成会话，7 天 TTL，可查询
- **冷层 (Disk)**: 长期归档，30 天 TTL，超期删除

## 现有基础（已就位）
- `RedisStore` — 热层，支持 get/save/delete，连接失败静默降级
- `DBStore` — 温层，MySQL + SQLAlchemy，自动建表
- `DiskStore` — 冷层，JSON 文件落盘，始终可用
- `MigrationPolicy` — `promote()` 读取时逐级提升（冷→温→热），`demote()` TTL 超时逐级沉降（热→温→冷→删除）
- `MemoryManager` — 统一接口，save/load/delete

## 待完善
1. **`config.yaml` 加 Redis 配置段** — host/port/db/ttl
2. **`RedisStore` 读 config** — 不用硬编码参数
3. **三个 Store 加 `list_keys()`** — GC 全量扫描需要
4. **`manager.gc()` 实现** — 调用 `demote()` 扫描全部 key
5. **冷层超期删除** — `MigrationPolicy` 加 COLD_TTL，超 30 天删文件
6. **定时 GC 触发** — 在 main.py 或调度器里周期性调用 `manager.gc()`

## 迁移方向
```
读取: Disk ← DB ← Redis (找到后逐级提升)
写入: Redis → DB → Disk (失败逐级降级)
GC:   Redis → DB → Disk → 删除 (TTL 超时逐级沉降)
```
