from rest_framework_csv.renderers import CSVStreamingRenderer

def file_headers():
    return [
        'shop_name',
        'shop_type',
        'platform_id',
        'platform_warehouse_id',
        'dn_code',
        'status',
        'order_data',
        'order_time',
        'supplier',
        'create_time',
        'update_time'
    ]

def cn_data_header():
    return dict([
        ('shop_name', u'店铺名称'),
        ('shop_type', u'店铺类型'),
        ('platform_id', u'平台订单ID'),
        ('platform_warehouse_id', u'平台仓库ID'),
        ('dn_code', u'发货单单号'),
        ('status', u'状态'),
        ('order_data', u'订单信息'),
        ('order_time', u'平台订单创建时间'),
        ('supplier', u'供应商'),
        ('create_time', u'创建时间'),
        ('update_time', u'更新时间')
    ])

def en_data_header():
    return dict([
        ('shop_name', u'Shop Name'),
        ('shop_type', u'Shop Type'),
        ('platform_id', u'Platform ID'),
        ('platform_warehouse_id', u'Platform Warehouse ID'),
        ('dn_code', u' DN Code'),
        ('status', u'Status'),
        ('order_data', u'Order Data'),
        ('order_time', u'Platform Order Time'),
        ('supplier', u'Supplier'),
        ('create_time', u'Create Time'),
        ('update_time', u'Update Time')
    ])

class FileRenderCN(CSVStreamingRenderer):
    header = file_headers()
    labels = cn_data_header()

class FileRenderEN(CSVStreamingRenderer):
    header = file_headers()
    labels = en_data_header()
