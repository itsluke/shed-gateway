#!/usr/bin/python
class FilterModule(object):
    def filters(self):
        return {
            'add_mount': self.add_mount,
            'drive2mount': self.drive2mount,
            'drives2mount': self.drives2mount,
            'bluegreen': self.bluegreen
        }
    
    def add_mount(self, item, prefix='/mnt'):
        return "/".join((prefix, item))

    def drive2mount(self, drive_dict):
        return self.add_mount(
            "_".join( (drive_dict['drive'], str(drive_dict['partition'])))
            )

    def drives2mount(self, drive_list, seperator=':'):
        pool = []
        for drive in drive_list:
            pool.append( self.drive2mount(drive) )
        return seperator.join(pool)
    
    def bluegreen(self, container, prefix='blue'):
        return "-".join((prefix, container))
