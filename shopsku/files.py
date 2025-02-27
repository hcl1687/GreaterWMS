from rest_framework_csv.renderers import CSVStreamingRenderer

def file_headers():
    return [
        'shop_name',
        'shop_type',
        'platform_id',
        'platform_sku',
        'goods_code',
        'platform_stock',
        'sys_stock',
        'supplier',
        'create_time',
        'update_time'
    ]

def cn_data_header():
    return dict([
        ('shop_name', u'店铺名称'),
        ('shop_type', u'店铺类型'),
        ('platform_id', u'平台ID'),
        ('platform_sku', u'平台SKU'),
        ('goods_code', u'系统SKU'),
        ('platform_stock', u'平台库存'),
        ('sys_stock', u'系统库存'),
        ('supplier', u'供应商'),
        ('create_time', u'创建时间'),
        ('update_time', u'更新时间')
    ])

def en_data_header():
    return dict([
        ('shop_name', u'Shop Name'),
        ('shop_type', u'Shop Type'),
        ('platform_id', u'Platform ID'),
        ('platform_sku', u'Platform SKU'),
        ('goods_code', u'System SKU'),
        ('platform_stock', u'Platform Stock'),
        ('sys_stock', u'System Stock'),
        ('supplier', u'Supplier'),
        ('create_time', u'Create Time'),
        ('update_time', u'Update Time')
    ])

def cn_sku_data_header():
    return dict([
        ('platform_sku', u'平台SKU'),
        ('goods_code', u'商品编码'),
        ('new_goods_code', u'新商品编码')
    ])

def en_sku_data_header():
    return dict([
        ('platform_sku', u'Platform SKU'),
        ('goods_code', u'Goods Code'),
        ('new_goods_code', u'New Goods Code')
    ])

class FileRenderCN(CSVStreamingRenderer):
    header = file_headers()
    labels = cn_data_header()

class FileRenderEN(CSVStreamingRenderer):
    header = file_headers()
    labels = en_data_header()
