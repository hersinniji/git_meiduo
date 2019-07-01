# 这里选择redis作为任务队列

# # 选择redis的14号库
# broker_url = "redis://127.0.0.1/14"
#
# # 结果后端选择redis的15号库
# result_backend = "redis://127.0.0.1/15"

# 这里改用rabbitMQ作为中间的消息队列
# guest//guest为管理界面用户名和密码,5672为rabbitMQ容器的端口号
broker_url = 'amqp://guest:guest@127.0.0.1:5672'