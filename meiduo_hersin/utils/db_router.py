

# ②：这里是第二步，创建数据库读写路由
# 在setting里面进行主从配置之后，在此处进行定义说明，slave为读，default为写
class MasterSlaveDBRouter(object):
    """数据库读写路由"""

    def db_for_read(self, model, **hints):
        """读"""
        return "slave"

    def db_for_write(self, model, **hints):
        """写"""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """是否运行关联操作"""
        return True
