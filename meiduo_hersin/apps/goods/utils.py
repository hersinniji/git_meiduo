
"""
生成面包屑
"""


def get_breadcrumb(category):

    # 根据分类id,获取它的上级/下级
    # 如果是一级  一个信息
    # 如果是二级  两个信息
    # 如果是三级  三个信息
    breadcrumb = {
        'cat1': '',
        'cat2': '',
        'cat3': '',
    }

    # 判断传递过来的分类是几级
    # 一级
    if category.parent is None:
        breadcrumb['cat1'] = category
    # 三级
    elif category.subs.count() == 0:
        breadcrumb['cat1'] = category.parent.parent
        breadcrumb['cat2'] = category.parent
        breadcrumb['cat3'] = category
    # 二级
    else:
        breadcrumb['cat1'] = category.parent
        breadcrumb['cat2'] = category
    return breadcrumb
