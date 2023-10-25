class StaffType(object):
    def is_valid(staff_type):
        staff_type_list = ['Manager', 'Supervisor', 'Inbount', 'Outbound', 'StockControl', 'Customer', 'Supplier']
        return staff_type in staff_type_list

