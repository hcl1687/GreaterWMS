from rest_framework_csv.renderers import CSVStreamingRenderer

def file_headers():
    return [
        'shop_name',
        'shop_type',
        'platform_id',
        'platform_warehouse_id',
        'posting_number',
        'dn_code',
        'status',
        'handle_status',
        'handle_message',
        'order_data',
        'stockbin_data',
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
        ('posting_number', u'平台发货单号'),
        ('dn_code', u'发货单单号'),
        ('status', u'状态'),
        ('handle_status', u'处理状态'),
        ('handle_message', u'处理信息'),
        ('order_data', u'订单信息'),
        ('stockbin_data', u'库存信息'),
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
        ('posting_number', u'Platform Posting Number'),
        ('dn_code', u' DN Code'),
        ('status', u'Status'),
        ('handle_status', u'Handle Status'),
        ('handle_message', u'Handle Message'),
        ('order_data', u'Order Data'),
        ('stockbin_data', u'Stock Bin Data'),
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
