from haystack import indexes

from apps.goods.models import SKU


class SKUIndex(indexes.SearchIndex,indexes.Indexable):
    # 每个都SearchIndex需要有一个（也是唯一一个）字段 document=True。
    # 这向Haystack和搜索引擎指示哪个字段是用于在其中搜索的主要字段。

    # 允许我们使用数据模板（而不是容易出错的串联）来构建搜索引擎将索引的文档
    # 'name,caption,id'

    # 惯例是命名此字段text
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回对哪个模型进行检索
        return SKU

    def index_queryset(self, using=None):
        # 返回对哪些数据进行检索
        return self.get_model().objects.filter(is_launched=True)
        # return SKU.objects.filter(is_launched=True)

    # class SPUIndex(indexes.SearchIndex, indexes.Indexable):
    #     # 每个都SearchIndex需要有一个（也是唯一一个）字段 document=True。
    #     # 这向Haystack和搜索引擎指示哪个字段是用于在其中搜索的主要字段。
    #
    #     # 惯例是命名此字段text
    #     text = indexes.CharField(document=True, use_template=True)
