# dict = {'Google': 'www.google.com', 'Runoob': 'www.runoob.com', 'taobao': 'www.taobao.com'}
#
# print ("字典值 : %s" % dict.items())
#
# # 遍历字典列表
# for key, values in dict.items():
#     print (key, values)

# a = '11'.encode()
# print(a)
# print(int(a))
# print(a.decode())


"""
我们登陆的时候合并 (普通登陆/QQ登陆的时候都能合并)

将cookie数据合并到redis中

1.获取到cookie数据
    carts: {1:{count:10,selected:True},3:{count:10,selected:True}}
2.读取redis的数据
    hash:   {2:20,3:20}
    set     {2,3}
3.合并之后形成新的数据
    3.1 对cookie数据进行遍历

    合并的原则:
        ① cookie中有的,redis中没有的,则将cookie中的数据添加到redis中
        ② cookie中有的,redis中也有,count怎么办?
            count以 cookie为主
        ③ 选中状态以cookie为主

    hash 新增一个 {1:10}
    hash 更新一个 {3:10}

    选中的增加一个 [1,3]
    选中的减少一个 []


4.把新的数据更新到redis中
    {2:20,3:10,1:10}
    {2,1}

5.删除cookie数据


"""


def add(a, b):
    return a + b


data = [4, 3]
print (add(*data))
# equals to print add(4, 3)
data = {'a': 4, 'b': 3}
print (add(**data))
# equals to print add(4, 3)