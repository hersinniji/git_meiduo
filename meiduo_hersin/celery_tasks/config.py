# 这里选择redis作为任务队列

# 选择redis的14号库
broker_url = "redis://127.0.0.1/14"

# 结果后端选择redis的15号库
result_backend = "redis://127.0.0.1/15"